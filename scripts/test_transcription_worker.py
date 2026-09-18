"""Testes da transcrição multiplataforma feita pelo worker do Mac.

Rodar: python3 -m pytest scripts/test_transcription_worker.py -q
"""
import importlib.util
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    'transcription_worker', Path(__file__).with_name('transcription_worker.py')
)
tw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tw)


def _seg(start, end, text):
    return {'start': start, 'end': end, 'text': text}


class TestTimestamps:
    def test_formata_no_padrao_srt(self):
        assert tw.format_srt_time(0) == '00:00:00,000'
        assert tw.format_srt_time(3725.5) == '01:02:05,500'

    def test_arredonda_milissegundo_sem_passar_de_999(self):
        assert tw.format_srt_time(1.9999) == '00:00:02,000'


class TestSrt:
    def test_numera_e_separa_blocos(self):
        srt = tw.segments_to_srt([_seg(0, 1.5, ' Olá '), _seg(1.5, 3, 'mundo')])

        assert srt == (
            '1\n00:00:00,000 --> 00:00:01,500\nOlá\n\n'
            '2\n00:00:01,500 --> 00:00:03,000\nmundo\n'
        )

    def test_pula_segmento_vazio(self):
        srt = tw.segments_to_srt([_seg(0, 1, '  '), _seg(1, 2, 'fala')])

        assert srt.startswith('1\n00:00:01,000')


class TestTexto:
    def test_junta_frases_no_mesmo_paragrafo(self):
        texto = tw.segments_to_text([_seg(0, 1, 'Primeira.'), _seg(1.2, 2, 'Segunda.')])

        assert texto == 'Primeira. Segunda.'

    def test_pausa_longa_abre_paragrafo_novo(self):
        texto = tw.segments_to_text([_seg(0, 1, 'Antes.'), _seg(4, 5, 'Depois.')])

        assert texto == 'Antes.\n\nDepois.'


class TestPedacos:
    def test_desloca_timestamps_pelo_inicio_de_cada_pedaco(self):
        merged = tw.merge_chunks([
            (0.0, [_seg(0, 10, 'a')]),
            (1200.0, [_seg(0, 5, 'b')]),
        ])

        assert merged == [_seg(0, 10, 'a'), _seg(1200, 1205, 'b')]


class TestDollarQuote:
    def test_envolve_texto_sem_escapar_aspas(self):
        quoted = tw.dollar_quote("it's O'Neil; DROP TABLE x;")

        tag = quoted[:quoted.index('$', 1) + 1]
        assert quoted == f"{tag}it's O'Neil; DROP TABLE x;{tag}"

    def test_tag_nunca_aparece_dentro_do_texto(self):
        texto = '$t$ $q$ $x$'
        quoted = tw.dollar_quote(texto)

        tag = quoted[:quoted.index('$', 1) + 1]
        assert tag not in texto


class TestChaveGroq:
    def test_prefere_a_variavel_de_ambiente(self, monkeypatch, tmp_path):
        monkeypatch.setenv('GROQ_API_KEY', 'da-env')
        (tmp_path / '.env').write_text('GROQ_API_KEY=do-arquivo\n')

        assert tw.load_groq_key(tmp_path / '.env') == 'da-env'

    def test_le_do_env_do_projeto_sem_aspas(self, monkeypatch, tmp_path):
        monkeypatch.delenv('GROQ_API_KEY', raising=False)
        (tmp_path / '.env').write_text('OUTRA=1\nGROQ_API_KEY="do-arquivo"\n')

        assert tw.load_groq_key(tmp_path / '.env') == 'do-arquivo'

    def test_sem_chave_devolve_none(self, monkeypatch, tmp_path):
        monkeypatch.delenv('GROQ_API_KEY', raising=False)

        assert tw.load_groq_key(tmp_path / 'nao-existe.env') is None


class FakeRemote:
    """Banco de mentira: responde ao claim e guarda o que o worker grava.

    `cancela_no_heartbeat=N`: a partir do N-ésimo aviso de progresso o job
    "sumiu" (pausado ou apagado no painel) e o UPDATE não devolve linha.
    """

    def __init__(self, claim_row='', cancela_no_heartbeat=None):
        self.claim_row = claim_row
        self.cancela_no_heartbeat = cancela_no_heartbeat
        self.heartbeats = 0
        self.queries = []
        self.stdin_sql = []

    def sql(self, query):
        self.queries.append(query)
        if 'FOR UPDATE SKIP LOCKED' in query:
            return self.claim_row
        if 'RETURNING id' in query:
            self.heartbeats += 1
            if self.cancela_no_heartbeat and self.heartbeats >= self.cancela_no_heartbeat:
                return ''
            return self.claim_row.split('\t')[0]
        return ''

    def sql_stdin(self, sql):
        self.stdin_sql.append(sql)
        return True


class TestProcessaUmJob:
    def _roda(self, remote, tmp_path, **overrides):
        deps = dict(
            download=lambda url, workdir, on_progress=None: (workdir / 'audio.m4a', {
                'title': 'Aula 1', 'duration': 90, 'extractor_key': 'Vimeo',
            }),
            split=lambda audio, workdir: [(0.0, workdir / 'p0.mp3')],
            transcribe=lambda chunk: [_seg(0, 2, 'Olá turma.')],
        )
        deps.update(overrides)
        return tw.process_one_job(
            run_sql=remote.sql, run_sql_stdin=remote.sql_stdin,
            workdir_root=tmp_path, **deps,
        )

    def test_sem_job_pendente_nao_faz_nada(self, tmp_path):
        remote = FakeRemote(claim_row='')

        assert self._roda(remote, tmp_path) is False
        assert remote.stdin_sql == []

    def test_job_concluido_grava_texto_srt_e_metadados(self, tmp_path):
        remote = FakeRemote(claim_row='7\thttps://vimeo.com/123')

        assert self._roda(remote, tmp_path) is True

        final = remote.stdin_sql[-1]
        assert "status = 'done'" in final
        assert 'Olá turma.' in final
        assert '00:00:00,000 --> 00:00:02,000' in final
        assert 'Aula 1' in final and 'Vimeo' in final
        assert 'WHERE id = 7' in final

    def test_falha_no_download_marca_failed_com_a_mensagem(self, tmp_path):
        remote = FakeRemote(claim_row='8\thttps://exemplo.com/x')

        def quebra(url, workdir, on_progress=None):
            raise RuntimeError('ERROR: Unsupported URL')

        assert self._roda(remote, tmp_path, download=quebra) is True

        final = remote.stdin_sql[-1]
        assert "status = 'failed'" in final
        assert 'Unsupported URL' in final

    def test_pasta_temporaria_e_apagada_mesmo_com_falha(self, tmp_path):
        remote = FakeRemote(claim_row='9\thttps://exemplo.com/x')

        def quebra(chunk):
            raise RuntimeError('groq fora')

        self._roda(remote, tmp_path, transcribe=quebra)

        assert list(tmp_path.iterdir()) == []


class TestChamadaGroq:
    def test_manda_user_agent_proprio(self, monkeypatch, tmp_path):
        """Sem isso o Cloudflare do Groq devolve 403 'error code: 1010'."""
        chunk = tmp_path / 'p.mp3'
        chunk.write_bytes(b'audio')
        capturado = {}

        class Resp:
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def read(self):
                return b'{"segments": [{"start": 0, "end": 1, "text": "oi"}]}'

        def fake_urlopen(req, timeout):
            capturado['headers'] = dict(req.header_items())
            return Resp()

        monkeypatch.setattr(tw.urllib.request, 'urlopen', fake_urlopen)

        segs = tw.groq_transcribe(chunk, api_key='k')

        assert segs == [{'start': 0.0, 'end': 1.0, 'text': 'oi'}]
        assert 'Python-urllib' not in capturado['headers'].get('User-agent', '')
        assert capturado['headers'].get('User-agent') == tw.USER_AGENT


class TestPausarEApagar:
    """Pausar ou apagar no painel faz o UPDATE de progresso não achar a linha."""

    def _roda(self, remote, tmp_path, **overrides):
        deps = dict(
            download=lambda url, workdir, on_progress=None: (workdir / 'a.m4a', {'title': 'x'}),
            split=lambda audio, workdir: [(0.0, workdir / 'p0.mp3'), (1200.0, workdir / 'p1.mp3')],
            transcribe=lambda chunk: [_seg(0, 1, 'oi')],
        )
        deps.update(overrides)
        return tw.process_one_job(run_sql=remote.sql, run_sql_stdin=remote.sql_stdin,
                                  workdir_root=tmp_path, **deps)

    def test_job_pausado_no_meio_para_sem_gravar_nada(self, tmp_path):
        remote = FakeRemote(claim_row='5\thttps://x', cancela_no_heartbeat=1)
        transcritos = []

        self._roda(remote, tmp_path, transcribe=lambda c: transcritos.append(c) or [])

        assert remote.stdin_sql == [], 'não pode gravar done nem failed num job pausado/apagado'
        assert transcritos == [], 'parou antes de gastar Groq'

    def test_cancelado_entre_pedacos_nao_transcreve_o_resto(self, tmp_path):
        remote = FakeRemote(claim_row='5\thttps://x', cancela_no_heartbeat=2)
        transcritos = []

        self._roda(remote, tmp_path, transcribe=lambda c: transcritos.append(c) or [])

        assert len(transcritos) == 1
        assert remote.stdin_sql == []

    def test_cancelado_apaga_a_pasta_temporaria(self, tmp_path):
        remote = FakeRemote(claim_row='5\thttps://x', cancela_no_heartbeat=1)

        self._roda(remote, tmp_path)

        assert list(tmp_path.iterdir()) == []

    def test_aviso_de_progresso_nao_ressuscita_job_pausado(self):
        sql = tw._progress_sql(5, 'transcribing', 40)

        assert "status IN ('downloading', 'transcribing')" in sql
        assert 'RETURNING id' in sql


class TestProgresso:
    def test_le_percentual_da_linha_do_yt_dlp(self):
        assert tw.parse_progress('[progresso]  42.3%') == 42.3
        assert tw.parse_progress('[progresso] 100.0%') == 100.0

    def test_linha_sem_percentual_devolve_none(self):
        assert tw.parse_progress('[youtube] Extracting URL') is None
        assert tw.parse_progress('[progresso]    N/A%') is None
        # sem o marcador, o yt-dlp imprime só "  42.3%" — não é nosso
        assert tw.parse_progress('  42.3%') is None

    def test_template_gera_linhas_que_o_parser_entende(self, tmp_path):
        """O prefixo 'download:' do template é seletor de tipo, não texto impresso."""
        args = tw.yt_dlp_args('https://x', tmp_path / 'a', cookies_file=tmp_path / 'n')
        template = args[args.index('--progress-template') + 1]

        tipo, modelo = template.split(':', 1)
        assert tipo == 'download'
        impresso = modelo.replace('%(progress._percent_str)s', ' 42.3%')
        assert tw.parse_progress(impresso) == 42.3

    def test_download_ocupa_a_faixa_de_5_a_30(self, tmp_path):
        remote = FakeRemote(claim_row='6\thttps://x')

        def baixa(url, workdir, on_progress=None):
            on_progress(50.0)
            on_progress(100.0)
            return workdir / 'a.m4a', {}

        tw.process_one_job(run_sql=remote.sql, run_sql_stdin=remote.sql_stdin, workdir_root=tmp_path,
                           download=baixa, split=lambda a, w: [(0.0, w / 'p.mp3')],
                           transcribe=lambda c: [])

        percentuais = [int(q.split('progress_percent = ')[1].split(',')[0])
                       for q in remote.queries if 'progress_percent = ' in q and 'RETURNING id' in q]
        assert 17 in percentuais, percentuais  # 5 + 50% de 25
        assert all(p <= 100 for p in percentuais)
        assert percentuais == sorted(percentuais), 'barra nunca anda para trás'


class TestLoginDosCursos:
    def test_usa_cookies_quando_o_arquivo_existe(self, tmp_path):
        cookies = tmp_path / 'cookies.txt'
        cookies.write_text('# Netscape HTTP Cookie File\n')

        args = tw.yt_dlp_args('https://hotmart.com/x', tmp_path / 'audio.%(ext)s', cookies_file=cookies)

        assert args[args.index('--cookies') + 1] == str(cookies)

    def test_sem_arquivo_de_cookies_nao_passa_cookies(self, tmp_path):
        args = tw.yt_dlp_args('https://youtube.com/x', tmp_path / 'a', cookies_file=tmp_path / 'nao.txt')

        assert '--cookies' not in args

    def test_sempre_se_passa_por_navegador_no_extractor_generico(self, tmp_path):
        args = tw.yt_dlp_args('https://x', tmp_path / 'a', cookies_file=tmp_path / 'nao.txt')

        assert args[args.index('--extractor-args') + 1] == 'generic:impersonate'

    def test_nunca_le_cookies_direto_do_navegador(self, tmp_path):
        """--cookies-from-browser abre a caixa do chaveiro do macOS a cada execução."""
        args = tw.yt_dlp_args('https://x', tmp_path / 'a', cookies_file=tmp_path / 'c.txt')

        assert '--cookies-from-browser' not in args

    def test_erro_de_login_sem_cookies_explica_o_que_fazer(self, tmp_path):
        msg = tw.explain_error('ERROR: Unsupported URL: https://hub.asimov.academy/login/',
                               cookies_file=tmp_path / 'nao.txt')

        assert 'cookies.txt' in msg
        assert str(tmp_path / 'nao.txt') in msg

    def test_erro_de_login_com_cookies_diz_que_expirou(self, tmp_path):
        cookies = tmp_path / 'c.txt'
        cookies.write_text('x')

        msg = tw.explain_error('ERROR: The web client only works when logged-in', cookies_file=cookies)

        assert 'expir' in msg.lower()

    def test_erro_que_nao_e_de_login_passa_intacto(self, tmp_path):
        assert tw.explain_error('ERROR: Video unavailable', cookies_file=tmp_path / 'n') == 'ERROR: Video unavailable'
