"""Testes da transcrição multiplataforma feita pelo worker do Mac.

Rodar: python3 -m pytest scripts/test_transcription_worker.py -q
"""
import importlib.util
import sys
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    'transcription_worker', Path(__file__).with_name('transcription_worker.py')
)
tw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tw)


@pytest.fixture(autouse=True)
def _sem_indexador_real(monkeypatch):
    """Os testes nunca chamam o indexador real (modelo/rede): ligado só nos testes que injetam um."""
    monkeypatch.setenv('TRANSCRICAO_INDEXAR', '0')


@pytest.fixture(autouse=True)
def _sem_media_urls_real(monkeypatch, tmp_path_factory):
    """Nenhum teste lê ou grava o ~/.config/canaldecortes/media-urls.json de verdade."""
    monkeypatch.setattr(tw, 'MEDIA_URLS_FILE', tmp_path_factory.mktemp('cfg') / 'media-urls.json')


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


class TestArquivoDaAula:
    def _roda(self, remote, tmp_path, guardar):
        def baixa(url, workdir, on_progress=None):
            media = workdir / 'aula.mp4'
            media.write_bytes(b'video')
            return media, {'title': 'Aula 1'}

        return tw.process_one_job(
            run_sql=remote.sql, run_sql_stdin=remote.sql_stdin, workdir_root=tmp_path,
            download=baixa, split=lambda a, w: [(0.0, w / 'p.mp3')],
            transcribe=lambda c: [_seg(0, 2, 'Olá turma.')], guardar=guardar,
        )

    def test_por_padrao_baixa_so_o_audio(self, tmp_path):
        args = tw.yt_dlp_args('https://x', tmp_path / 'aula.%(ext)s', cookies_file=tmp_path / 'n')

        assert args[args.index('-f') + 1] == tw.AUDIO_FORMAT
        assert '--merge-output-format' not in args

    def test_guardar_aula_e_opcional_e_desligado_por_padrao(self, monkeypatch, tmp_path):
        monkeypatch.delenv('TRANSCRICAO_GUARDAR_AULA', raising=False)
        env = tmp_path / '.env'
        env.write_text('GROQ_API_KEY=x\n')
        assert tw.guardar_aula_ligado(env) is False

        env.write_text('TRANSCRICAO_GUARDAR_AULA=1\n')
        assert tw.guardar_aula_ligado(env) is True

    def test_arquivo_baixado_e_apagado_depois_de_transcrever(self, tmp_path):
        remote = FakeRemote(claim_row='7\thttps://x')
        vistos = {}

        def transcreve(chunk):
            vistos['existia_na_transcricao'] = any(tmp_path.glob('transcricao_7_*/aula.mp4'))
            return [_seg(0, 2, 'Olá turma.')]

        def baixa(url, workdir, on_progress=None):
            media = workdir / 'aula.mp4'
            media.write_bytes(b'video')
            return media, {}

        tw.process_one_job(run_sql=remote.sql, run_sql_stdin=remote.sql_stdin, workdir_root=tmp_path,
                           download=baixa, split=lambda a, w: [(0.0, w / 'p.mp3')], transcribe=transcreve)

        assert vistos['existia_na_transcricao'] is True
        assert "status = 'done'" in remote.stdin_sql[-1]
        assert list(tmp_path.iterdir()) == []

    def test_com_guardar_baixa_video_ate_720p_em_mp4(self, tmp_path):
        args = tw.yt_dlp_args('https://x', tmp_path / 'aula.%(ext)s', cookies_file=tmp_path / 'n', video=True)

        assert args[args.index('-f') + 1] == tw.MEDIA_FORMAT
        assert 'height<=720' in tw.MEDIA_FORMAT
        assert args[args.index('--merge-output-format') + 1] == 'mp4'

    def test_acha_o_arquivo_final_e_ignora_faixas_e_metadados(self, tmp_path):
        for nome in ('aula.info.json', 'aula.f137.mp4', 'aula.mp4.part', 'aula.mp4'):
            (tmp_path / nome).write_text('x')

        assert tw._arquivo_baixado(tmp_path) == tmp_path / 'aula.mp4'

    def test_guarda_no_mac_pela_chave_do_job_e_manda_a_mesma_arvore(self, tmp_path):
        media = tmp_path / 'aula.MP4'
        media.write_bytes(b'12345')
        enviados = []

        rel, tamanho = tw.guardar_aula(7, media, local_root=tmp_path / 'cursos',
                                       upload=lambda arq, r: enviados.append((arq, r)))

        assert rel == 'aulas/7.mp4'
        assert tamanho == 5
        assert (tmp_path / 'cursos/aulas/7.mp4').read_bytes() == b'12345'
        assert enviados == [(tmp_path / 'cursos/aulas/7.mp4', 'aulas/7.mp4')]

    def test_grava_caminho_e_tamanho_da_aula_no_banco(self, tmp_path):
        remote = FakeRemote(claim_row='7\thttps://x')

        self._roda(remote, tmp_path, guardar=lambda jid, m: (f'aulas/{jid}.mp4', 5))

        final = remote.stdin_sql[-1]
        assert "status = 'done'" in final
        assert 'aulas/7.mp4' in final
        assert 'media_bytes = 5' in final
        assert 'error_message = NULL' in final

    def test_envio_que_falha_nao_perde_a_transcricao(self, tmp_path):
        remote = FakeRemote(claim_row='7\thttps://x')

        def quebra(jid, m):
            raise RuntimeError('rsync falhou: conexão recusada')

        self._roda(remote, tmp_path, guardar=quebra)

        final = remote.stdin_sql[-1]
        assert "status = 'done'" in final
        assert 'Olá turma.' in final
        assert 'media_path = NULL' in final
        assert 'conexão recusada' in final

    def test_sem_guardar_nao_grava_arquivo(self, tmp_path):
        remote = FakeRemote(claim_row='7\thttps://x')

        self._roda(remote, tmp_path, guardar=None)

        assert 'media_path = NULL' in remote.stdin_sql[-1]


class TestIndexacaoDaBusca:
    def _roda(self, remote, tmp_path, **overrides):
        return TestProcessaUmJob()._roda(remote, tmp_path, **overrides)

    def test_indexa_depois_de_gravar_o_done_com_os_segmentos(self, tmp_path):
        remote = FakeRemote(claim_row='7\thttps://x')
        chamadas = []

        def indexar(job_id, segments, run_sql_stdin):
            # o `done` já foi gravado quando a indexação roda
            chamadas.append((job_id, segments, len(remote.stdin_sql), run_sql_stdin))
            return 3

        self._roda(remote, tmp_path, indexar=indexar)

        [(job_id, segments, gravacoes, run_stdin)] = chamadas
        assert job_id == 7
        assert segments == [_seg(0, 2, 'Olá turma.')]
        assert gravacoes == 1 and "status = 'done'" in remote.stdin_sql[0]
        assert run_stdin == remote.sql_stdin

    def test_falha_na_indexacao_nao_derruba_o_job(self, tmp_path, capsys):
        remote = FakeRemote(claim_row='7\thttps://x')

        def quebra(job_id, segments, run_sql_stdin):
            raise RuntimeError('embedder fora do ar')

        assert self._roda(remote, tmp_path, indexar=quebra) is True

        assert len(remote.stdin_sql) == 1  # nenhum `failed` por cima do `done`
        assert "status = 'done'" in remote.stdin_sql[0]
        assert 'indexação falhou' in capsys.readouterr().out

    def test_job_falho_nao_indexa(self, tmp_path):
        remote = FakeRemote(claim_row='8\thttps://x')
        chamadas = []

        def quebra(url, workdir, on_progress=None):
            raise RuntimeError('ERROR: Unsupported URL')

        self._roda(remote, tmp_path, download=quebra, indexar=lambda *a: chamadas.append(a))

        assert chamadas == []

    def test_desligado_por_padrao_de_teste_nao_chama_o_indexador_real(self, tmp_path):
        remote = FakeRemote(claim_row='7\thttps://x')

        self._roda(remote, tmp_path)  # indexar=None + TRANSCRICAO_INDEXAR=0

        assert len(remote.stdin_sql) == 1

    def test_ligado_usa_o_indexador_padrao(self, tmp_path, monkeypatch):
        monkeypatch.setenv('TRANSCRICAO_INDEXAR', '1')
        chamadas = []
        monkeypatch.setattr(tw, 'indexar_padrao', lambda *a: chamadas.append(a) or 1)
        remote = FakeRemote(claim_row='7\thttps://x')

        self._roda(remote, tmp_path)

        assert [c[0] for c in chamadas] == [7]

    @pytest.mark.parametrize('valor,esperado', [
        ('1', True), ('true', True), ('', True), ('0', False), ('false', False),
        ('OFF', False), ('no', False),
    ])
    def test_flag_transcricao_indexar(self, monkeypatch, tmp_path, valor, esperado):
        monkeypatch.setenv('TRANSCRICAO_INDEXAR', valor)

        assert tw.indexar_ligado(tmp_path / 'sem.env') is esperado

    def test_default_ligado_sem_a_variavel(self, monkeypatch, tmp_path):
        monkeypatch.delenv('TRANSCRICAO_INDEXAR')

        assert tw.indexar_ligado(tmp_path / 'sem.env') is True

    def test_indexador_real_grava_chunks_sem_vetor_quando_o_embed_falha(self, tmp_path, monkeypatch):
        """Ponta a ponta com o módulo de verdade: sem sentence-transformers/modelo, o job
        termina `done` e os chunks entram sem embedding."""
        monkeypatch.setenv('TRANSCRICAO_INDEXAR', '1')
        monkeypatch.setitem(sys.modules, 'sentence_transformers', None)  # import falha, sem rede
        remote = FakeRemote(claim_row='7\thttps://x')

        self._roda(remote, tmp_path)

        assert "status = 'done'" in remote.stdin_sql[0]
        assert 'INSERT INTO transcript_chunks' in remote.stdin_sql[-1]
        assert '::vector' not in remote.stdin_sql[-1]


ENTRY = {'media_url': 'https://cf-embed.play.hotmart.com/vod/a/hls/playlist.m3u8?get_qualities=1&x=1',
         'referer': 'https://cf-embed.play.hotmart.com/embed/?v=abc', 'title': 'Aula 3 - Hooks'}
AULA = 'https://hotmart.com/pt-BR/club/formula-youtube/products/8093188/content/V4VKj9GVe2'


class TestEnderecosDeMidia:
    def test_grava_fechado_so_para_o_dono_e_acha_pela_url_normalizada(self, tmp_path):
        arq = tmp_path / 'sub' / 'media-urls.json'

        tw.save_media_entry(AULA, ENTRY['media_url'], ENTRY['referer'], ENTRY['title'], path=arq)

        assert oct(arq.stat().st_mode & 0o777) == '0o600'
        achou = tw.lookup_media_entry(AULA.replace('https://hotmart.com', 'HTTPS://HotMart.com') + '#t=3', path=arq)
        assert achou['media_url'] == ENTRY['media_url'] and achou['title'] == 'Aula 3 - Hooks'

    def test_entrada_com_mais_de_24h_some_ao_procurar_e_ao_gravar(self, tmp_path):
        arq = tmp_path / 'm.json'
        tw.save_media_entry('https://hotmart.com/velha', 'https://a.hotmart.com/p.m3u8', path=arq, now=1000.0)

        assert tw.lookup_media_entry('https://hotmart.com/velha', path=arq, now=1000.0 + 24 * 3600 + 1) is None
        tw.save_media_entry('https://hotmart.com/nova', 'https://a.hotmart.com/q.m3u8', path=arq,
                            now=1000.0 + 24 * 3600 + 1)
        assert 'velha' not in arq.read_text() and 'nova' in arq.read_text()

    def test_esquecer_remove_so_aquela_entrada(self, tmp_path):
        arq = tmp_path / 'm.json'
        tw.save_media_entry('https://hotmart.com/a', 'https://a.hotmart.com/1.m3u8', path=arq)
        tw.save_media_entry('https://hotmart.com/b', 'https://a.hotmart.com/2.m3u8', path=arq)

        tw.forget_media_entry('https://hotmart.com/a', path=arq)

        assert tw.lookup_media_entry('https://hotmart.com/a', path=arq) is None
        assert tw.lookup_media_entry('https://hotmart.com/b', path=arq) is not None

    def test_arquivo_ausente_ou_corrompido_nao_quebra(self, tmp_path):
        arq = tmp_path / 'm.json'
        assert tw.lookup_media_entry('https://x.com/a', path=arq) is None
        arq.write_text('{lixo')
        assert tw.lookup_media_entry('https://x.com/a', path=arq) is None


class TestArgumentosHls:
    def test_yt_dlp_so_audio_com_referer_origin_e_opcoes_atuais(self, tmp_path):
        cookies = tmp_path / 'c.txt'
        cookies.write_text('x')

        args = tw.yt_dlp_hls_args(ENTRY, tmp_path / 'aula.%(ext)s', cookies_file=cookies)

        assert args[-1] == ENTRY['media_url']
        assert args[args.index('-f') + 1] == 'ba/b'
        assert '-x' in args and args[args.index('--audio-format') + 1] == 'mp3'
        headers = [args[i + 1] for i, a in enumerate(args) if a == '--add-header']
        assert 'Referer:https://cf-embed.play.hotmart.com/embed/?v=abc' in headers
        assert 'Origin:https://cf-embed.play.hotmart.com' in headers
        assert args[args.index('--extractor-args') + 1] == 'generic:impersonate'
        assert args[args.index('--cookies') + 1] == str(cookies)
        assert '--cookies-from-browser' not in args

    def test_sem_referer_nao_manda_cabecalho_vazio(self, tmp_path):
        args = tw.yt_dlp_hls_args({'media_url': ENTRY['media_url'], 'referer': ''}, tmp_path / 'a',
                                  cookies_file=tmp_path / 'n')

        assert '--add-header' not in args and '--cookies' not in args

    def test_ffmpeg_leva_os_cabecalhos_e_so_audio(self, tmp_path):
        args = tw.ffmpeg_hls_args(ENTRY, tmp_path / 'aula.mp3')

        assert args[args.index('-headers') + 1] == (
            'Referer: https://cf-embed.play.hotmart.com/embed/?v=abc\r\n'
            'Origin: https://cf-embed.play.hotmart.com\r\n')
        assert args[args.index('-i') + 1] == ENTRY['media_url'] and '-vn' in args


class TestDownloadHls:
    def _run_ok(self, workdir):
        def run(args, on_progress=None):
            (workdir / 'aula.mp3').write_bytes(b'mp3')
            return 0, ''
        return run

    def test_yt_dlp_ok_devolve_audio_e_titulo_da_aba(self, tmp_path):
        media, info = tw.download_hls_audio(ENTRY, tmp_path, run_yt_dlp=self._run_ok(tmp_path),
                                            run_ffmpeg=lambda a: pytest.fail('não devia cair no ffmpeg'),
                                            cookies_file=tmp_path / 'n')

        assert media == tmp_path / 'aula.mp3'
        assert info['title'] == 'Aula 3 - Hooks' and info['extractor_key'] == 'Hotmart'

    def test_cai_para_ffmpeg_quando_o_yt_dlp_falha(self, tmp_path):
        chamadas = []

        def ffmpeg(args):
            chamadas.append(args)
            (tmp_path / 'aula.mp3').write_bytes(b'mp3')
            return 0, ''

        media, _ = tw.download_hls_audio(ENTRY, tmp_path, run_yt_dlp=lambda a, p=None: (1, 'ERROR: boom'),
                                         run_ffmpeg=ffmpeg, cookies_file=tmp_path / 'n')

        assert media.name == 'aula.mp3' and len(chamadas) == 1

    @pytest.mark.parametrize('stderr', [
        'ERROR: [generic] This video is DRM protected',
        'ERROR: unsupported encryption method SAMPLE-AES',
        'Unable to open key file skd://abc',
        'Widevine PSSH found',
    ])
    def test_drm_falha_clara_e_nao_tenta_ffmpeg(self, tmp_path, stderr):
        with pytest.raises(RuntimeError) as e:
            tw.download_hls_audio(ENTRY, tmp_path, run_yt_dlp=lambda a, p=None: (1, stderr),
                                  run_ffmpeg=lambda a: pytest.fail('nunca tentar contornar DRM'),
                                  cookies_file=tmp_path / 'n')

        assert 'DRM' in str(e.value) and 'não dá para baixar' in str(e.value)

    def test_drm_detectado_so_no_ffmpeg_tambem_e_claro(self, tmp_path):
        with pytest.raises(RuntimeError) as e:
            tw.download_hls_audio(ENTRY, tmp_path, run_yt_dlp=lambda a, p=None: (1, 'ERROR: x'),
                                  run_ffmpeg=lambda a: (1, 'Invalid data; skd:// key'), cookies_file=tmp_path / 'n')

        assert 'DRM' in str(e.value)

    def test_falha_nos_dois_junta_os_motivos_e_avisa_de_link_expirado(self, tmp_path):
        with pytest.raises(RuntimeError) as e:
            tw.download_hls_audio(ENTRY, tmp_path,
                                  run_yt_dlp=lambda a, p=None: (1, 'ERROR: HTTP Error 403: Forbidden'),
                                  run_ffmpeg=lambda a: (1, 'Server returned 403 Forbidden'), cookies_file=tmp_path / 'n')

        assert 'expirou' in str(e.value) and 'ffmpeg' in str(e.value)


class TestJobComMidiaDaExtensao:
    def _roda(self, remote, tmp_path, **kw):
        return tw.process_one_job(
            run_sql=remote.sql, run_sql_stdin=remote.sql_stdin, workdir_root=tmp_path,
            split=lambda audio, workdir: [(0.0, workdir / 'p0.mp3')],
            transcribe=lambda chunk: [_seg(0, 2, 'Olá turma.')], **kw)

    def test_com_entrada_baixa_so_o_audio_do_m3u8_e_apaga_a_entrada(self, tmp_path):
        remote = FakeRemote(claim_row=f'11\t{AULA}')
        tw.save_media_entry(AULA, ENTRY['media_url'], ENTRY['referer'], ENTRY['title'])
        usado = {}

        def hls(entry, workdir, on_progress=None):
            usado['entry'] = entry
            return workdir / 'aula.mp3', {'title': entry['title'], 'extractor_key': 'Hotmart'}

        self._roda(remote, tmp_path, download=lambda *a, **k: pytest.fail('caminho antigo não devia rodar'),
                   download_hls=hls)

        assert usado['entry']['media_url'] == ENTRY['media_url']
        final = remote.stdin_sql[-1]
        assert "status = 'done'" in final and 'Aula 3 - Hooks' in final
        assert tw.lookup_media_entry(AULA) is None, 'endereço assinado não pode sobrar no disco'
        assert ENTRY['media_url'] not in ''.join(remote.queries + remote.stdin_sql), 'nunca vai ao banco'
        assert list(tmp_path.iterdir()) == []

    def test_falha_de_drm_vira_failed_e_tambem_apaga_a_entrada(self, tmp_path):
        remote = FakeRemote(claim_row=f'12\t{AULA}')
        tw.save_media_entry(AULA, ENTRY['media_url'], ENTRY['referer'])

        def hls(entry, workdir, on_progress=None):
            raise RuntimeError(tw.DRM_MESSAGE)

        self._roda(remote, tmp_path, download_hls=hls)

        assert "status = 'failed'" in remote.stdin_sql[-1] and 'DRM' in remote.stdin_sql[-1]
        assert tw.lookup_media_entry(AULA) is None

    def test_sem_entrada_o_caminho_antigo_fica_intacto(self, tmp_path):
        remote = FakeRemote(claim_row='13\thttps://vimeo.com/123')
        chamou = []

        def antigo(url, workdir, on_progress=None):
            chamou.append(url)
            return workdir / 'a.m4a', {'title': 'Aula 1', 'extractor_key': 'Vimeo'}

        self._roda(remote, tmp_path, download=antigo,
                   download_hls=lambda *a, **k: pytest.fail('sem entrada não usa HLS'))

        assert chamou == ['https://vimeo.com/123'] and "status = 'done'" in remote.stdin_sql[-1]


class TestErroHotmart:
    def test_unsupported_url_do_hotmart_manda_usar_a_extensao(self):
        msg = tw.explain_error(f'ERROR: Unsupported URL: {AULA}')

        assert msg.startswith('Use a extensão na página da aula (dê play e clique em Transcrever): '
                              'o yt-dlp não lê a área de membros do Hotmart')
