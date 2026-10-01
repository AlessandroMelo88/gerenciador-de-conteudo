"""
Modo de formato longo por canal destino (`destination_channels.long_format_mode`).

Cobre: leitura tolerante do modo, decisão do formato na ingestão (`_detect_format`), as seleções do
pipeline por modo × fonte curta/longa, idempotência, seletor estrito/janelas e finalização do raw com
clips de dois formatos. `auto` tem que ser idêntico ao comportamento anterior.
"""
from unittest.mock import MagicMock

import pytest

from src import format_mode
from src.format_mode import get_long_format_mode, normalize_mode
from src.selector import (
    MAX_LONGFORM_SECONDS,
    MIN_LONGFORM_SECONDS,
    _sample_transcript_windows,
    select_moments,
)


@pytest.fixture(autouse=True)
def _limpa_cache_de_colunas():
    format_mode._column_cache.clear()
    yield
    format_mode._column_cache.clear()


class FakeCursor:
    """Banco em memória mínimo: responde por trecho de SQL e guarda o estado de clips/fonte."""

    def __init__(self, db):
        self.db = db
        self._one = None
        self._all = []
        self.rowcount = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        db = self.db
        db.executed.append((sql, params))
        self._one, self._all = None, []
        if 'information_schema.columns' in sql:
            if (params[0], params[1]) in db.columns:
                self._one = {'present': 1}
        elif 'FROM destination_channels WHERE niche' in sql and 'long_format_mode' in sql:
            if db.raise_on_mode_query:
                raise RuntimeError('column long_format_mode does not exist')
            self._all = list(db.dest_rows)
        elif 'FROM source_videos sv' in sql and 'LEFT JOIN source_channels' in sql:
            self._one = {'id': 1, 'format': db.source_format, 'target_niche': db.niche}
        elif 'SELECT COUNT(*) AS n FROM generated_clips' in sql:
            fmt = params[1]
            self._one = {'n': sum(1 for c in db.clips if (c['format'] or db.source_format) == fmt)}
        elif sql.startswith('UPDATE source_videos SET format'):
            db.source_format = 'curto'
        elif 'SELECT sc.target_niche' in sql:
            self._one = {'target_niche': db.niche}
        elif 'SELECT id FROM destination_channels' in sql:
            self._one = {'id': 7}
        elif sql.startswith('INSERT INTO generated_clips'):
            fmt = params[7] if len(params) == 8 else None
            db.clips.append({'format': fmt, 'status': 'pending_cut', 'start': params[1], 'end': params[2]})

    def fetchone(self):
        return self._one

    def fetchall(self):
        return self._all


class FakeDb:
    def __init__(self, columns=(), dest_modes=(), source_format='longo', niche='futebol'):
        self.columns = set(columns)
        self.dest_rows = [{'long_format_mode': m} for m in dest_modes]
        self.source_format = source_format
        self.niche = niche
        self.clips = []
        self.executed = []
        self.raise_on_mode_query = False
        self.conn = MagicMock()
        self.conn._driver = 'pgsql'
        self.conn.cursor.side_effect = lambda: FakeCursor(self)

    def sqls(self):
        return [s for s, _ in self.executed]


MODE_COL = ('destination_channels', 'long_format_mode')
FORMAT_COL = ('generated_clips', 'format')


# ---------------------------------------------------------------- leitura do modo

class TestLeituraDoModo:
    def test_coluna_ausente_vira_auto_sem_consultar_a_tabela(self):
        db = FakeDb(columns=(), dest_modes=('both',))
        assert get_long_format_mode(db.conn, 'futebol') == 'auto'
        assert not any('FROM destination_channels WHERE niche' in s for s in db.sqls())

    @pytest.mark.parametrize('valor', [None, '', 'lixo', 'BOTH_ALL'])
    def test_null_vazio_ou_invalido_vira_auto(self, valor):
        db = FakeDb(columns=[MODE_COL], dest_modes=(valor,))
        assert get_long_format_mode(db.conn, 'futebol') == 'auto'

    @pytest.mark.parametrize('modo', ['auto', 'short_only', 'both'])
    def test_valores_validos(self, modo):
        db = FakeDb(columns=[MODE_COL], dest_modes=(modo,))
        assert get_long_format_mode(db.conn, 'futebol') == modo

    def test_sem_canal_ativo_no_nicho_vira_auto(self):
        db = FakeDb(columns=[MODE_COL], dest_modes=())
        assert get_long_format_mode(db.conn, 'futebol') == 'auto'

    def test_sem_nicho_vira_auto(self):
        db = FakeDb(columns=[MODE_COL], dest_modes=('both',))
        assert get_long_format_mode(db.conn, None) == 'auto'

    @pytest.mark.parametrize('modos,esperado', [
        (('both', 'auto'), 'auto'),
        (('both', 'short_only'), 'short_only'),
        (('auto', 'short_only'), 'short_only'),
        (('both', 'both'), 'both'),
        (('both', None), 'auto'),
    ])
    def test_varios_canais_no_nicho_vale_o_mais_conservador(self, modos, esperado):
        db = FakeDb(columns=[MODE_COL], dest_modes=modos)
        assert get_long_format_mode(db.conn, 'futebol') == esperado

    def test_erro_na_consulta_nao_derruba_e_faz_rollback(self):
        db = FakeDb(columns=[MODE_COL], dest_modes=('both',))
        db.raise_on_mode_query = True
        assert get_long_format_mode(db.conn, 'futebol') == 'auto'
        db.conn.rollback.assert_called()

    def test_normalize_mode(self):
        assert normalize_mode(' Short_Only ') == 'short_only'
        assert normalize_mode(None) == 'auto'

    def test_clip_format_sql_depende_da_coluna(self):
        assert format_mode.clip_format_sql(FakeDb(columns=[]).conn) == 'sv.format'
        assert format_mode.clip_format_sql(FakeDb(columns=[FORMAT_COL]).conn) == 'COALESCE(gc.format, sv.format)'


# ---------------------------------------------------------------- _detect_format

def _detect(mocker, duration, resolver=None):
    from src import rss_poller

    ydl = MagicMock()
    ydl.__enter__.return_value.extract_info.return_value = {'duration': duration}
    mocker.patch('src.rss_poller.yt_dlp.YoutubeDL', return_value=ydl)
    if resolver is None:
        return rss_poller._detect_format('abc12345678')
    return rss_poller._detect_format('abc12345678', mode_resolver=resolver)


class TestDetectFormat:
    def test_auto_sem_resolver_e_identico_ao_historico(self, mocker):
        assert _detect(mocker, 600) == 'longo'
        assert _detect(mocker, 419) == 'curto'
        assert _detect(mocker, 420) == 'longo'

    @pytest.mark.parametrize('modo,esperado', [('auto', 'longo'), ('both', 'longo'), ('short_only', 'curto')])
    def test_fonte_longa_por_modo(self, mocker, modo, esperado):
        assert _detect(mocker, 900, resolver=lambda: modo) == esperado

    @pytest.mark.parametrize('modo', ['auto', 'short_only', 'both'])
    def test_fonte_curta_e_sempre_curto_e_nem_consulta_o_modo(self, mocker, modo):
        resolver = MagicMock(return_value=modo)
        assert _detect(mocker, 200, resolver=resolver) == 'curto'
        resolver.assert_not_called()


# ---------------------------------------------------------------- pipeline

TRANSCRIPT = {'video_id': 'vid001aaaaaa', 'text': 't', 'segments': [{'start': 0.0, 'end': 60.0, 'text': 'x'}]}


def _moment(start, end, score=8):
    return {'start_time': start, 'end_time': end, 'score': score, 'reason': 'ok'}


def _run_pipeline(mocker, db, shorts=None, longs=None):
    """Roda _process_ai_pipeline contra o FakeDb; devolve (select_mock, status_calls)."""
    from src.rss_poller import _process_ai_pipeline

    shorts = [_moment(10, 70)] if shorts is None else shorts
    longs = [_moment(0, 600)] if longs is None else longs
    mocker.patch('src.rss_poller.transcribe_video', return_value=TRANSCRIPT)
    mocker.patch('src.rss_poller.save_transcript')
    mocker.patch('src.queue_controls.is_paused', return_value=False)
    mocker.patch('src.rss_poller._cleanup_partial')
    statuses = []
    mocker.patch('src.rss_poller.update_status', side_effect=lambda c, v, s, **k: statuses.append(s))
    select = mocker.patch(
        'src.rss_poller.select_moments',
        side_effect=lambda transcript, **kw: list(longs if kw.get('fmt') == 'longo' else shorts),
    )
    _process_ai_pipeline(db.conn, 'vid001aaaaaa', '/app/videos/vid001aaaaaa.mp4')
    return select, statuses


class TestPipelineAuto:
    def test_fonte_longa_auto_uma_selecao_longa_e_insert_sem_coluna_format(self, mocker):
        db = FakeDb(columns=[MODE_COL, FORMAT_COL], dest_modes=('auto',))
        select, _ = _run_pipeline(mocker, db)
        select.assert_called_once()
        assert select.call_args.kwargs == {'anthropic_client': None, 'fmt': 'longo', 'niche': 'futebol'}
        inserts = [(s, p) for s, p in db.executed if s.startswith('INSERT INTO generated_clips')]
        assert len(inserts) == 1 and 'format' not in inserts[0][0]
        assert db.source_format == 'longo'
        assert not any(s.startswith('UPDATE source_videos SET format') for s in db.sqls())

    def test_fonte_curta_auto_uma_selecao_e_nem_le_o_modo(self, mocker):
        db = FakeDb(columns=[MODE_COL, FORMAT_COL], dest_modes=('both',), source_format='curto')
        select, _ = _run_pipeline(mocker, db)
        select.assert_called_once()
        assert select.call_args.kwargs == {'anthropic_client': None, 'fmt': 'curto', 'niche': 'futebol'}
        assert not any('information_schema' in s for s in db.sqls())

    def test_coluna_ausente_cai_em_auto_e_nao_derruba(self, mocker):
        db = FakeDb(columns=[], dest_modes=('both',))
        select, statuses = _run_pipeline(mocker, db)
        select.assert_called_once()
        assert select.call_args.kwargs['fmt'] == 'longo'
        assert 'failed' not in statuses


class TestPipelineShortOnly:
    def test_fonte_longa_gera_so_shorts_amostrando_janelas_e_vira_curto(self, mocker):
        db = FakeDb(columns=[MODE_COL, FORMAT_COL], dest_modes=('short_only',))
        select, _ = _run_pipeline(mocker, db)
        select.assert_called_once()
        kw = select.call_args.kwargs
        assert kw['fmt'] == 'curto' and kw['sample_windows'] is True
        assert db.source_format == 'curto'
        assert len(db.clips) == 1
        assert not any(c['format'] == 'longo' for c in db.clips)

    def test_fonte_curta_continua_so_shorts(self, mocker):
        db = FakeDb(columns=[MODE_COL, FORMAT_COL], dest_modes=('short_only',), source_format='curto')
        select, _ = _run_pipeline(mocker, db)
        select.assert_called_once()
        assert select.call_args.kwargs['fmt'] == 'curto'


class TestPipelineBoth:
    def test_fonte_longa_duas_selecoes_com_formato_proprio(self, mocker):
        db = FakeDb(columns=[MODE_COL, FORMAT_COL], dest_modes=('both',))
        select, statuses = _run_pipeline(mocker, db)
        fmts = [c.kwargs['fmt'] for c in select.call_args_list]
        assert fmts == ['curto', 'longo']
        assert select.call_args_list[1].kwargs['strict_long'] is True
        assert sorted(c['format'] for c in db.clips) == ['curto', 'longo']
        assert db.source_format == 'longo'  # continua como padrão da fonte
        assert 'failed' not in statuses

    def test_fonte_curta_gera_so_shorts_sem_erro(self, mocker):
        db = FakeDb(columns=[MODE_COL, FORMAT_COL], dest_modes=('both',), source_format='curto')
        select, statuses = _run_pipeline(mocker, db)
        assert [c.kwargs['fmt'] for c in select.call_args_list] == ['curto']
        assert 'failed' not in statuses

    def test_ia_sem_longo_valido_entra_so_shorts_sem_fallback(self, mocker):
        db = FakeDb(columns=[MODE_COL, FORMAT_COL], dest_modes=('both',))
        _, statuses = _run_pipeline(mocker, db, longs=[])
        assert [c['format'] for c in db.clips] == ['curto']
        assert 'failed' not in statuses

    def test_sem_nenhum_clip_a_fonte_falha_e_libera_a_vaga(self, mocker):
        db = FakeDb(columns=[MODE_COL, FORMAT_COL], dest_modes=('both',))
        _, statuses = _run_pipeline(mocker, db, shorts=[], longs=[])
        assert db.clips == []
        assert statuses[-1] == 'failed'

    def test_reprocessar_nao_duplica_clips(self, mocker):
        db = FakeDb(columns=[MODE_COL, FORMAT_COL], dest_modes=('both',))
        _run_pipeline(mocker, db)
        assert len(db.clips) == 2
        select, _ = _run_pipeline(mocker, db)
        select.assert_not_called()
        assert len(db.clips) == 2

    def test_reprocessar_completa_so_o_formato_que_falta(self, mocker):
        db = FakeDb(columns=[MODE_COL, FORMAT_COL], dest_modes=('both',))
        _run_pipeline(mocker, db, longs=[])  # só o curto entrou
        select, _ = _run_pipeline(mocker, db)
        assert [c.kwargs['fmt'] for c in select.call_args_list] == ['longo']
        assert sorted(c['format'] for c in db.clips) == ['curto', 'longo']

    def test_sem_coluna_generated_clips_format_degrada_para_so_shorts(self, mocker):
        db = FakeDb(columns=[MODE_COL], dest_modes=('both',))
        select, _ = _run_pipeline(mocker, db)
        assert [c.kwargs['fmt'] for c in select.call_args_list] == ['curto']
        assert db.source_format == 'curto'
        assert all(c['format'] is None for c in db.clips)


# ---------------------------------------------------------------- seletor

def _client(moments):
    import json

    client = MagicMock()
    client.messages.create.return_value = MagicMock(content=[MagicMock(text=json.dumps({'moments': moments}))])
    return client


def _transcript(total_seconds, step=10, text='palavra ' * 12):
    segs = [{'start': t, 'end': t + step, 'text': text.strip()} for t in range(0, total_seconds, step)]
    return {'video_id': 'v', 'text': '', 'segments': segs}


class TestSeletor:
    def test_longo_estrito_nao_estica_trecho_curto(self):
        t = _transcript(1500)
        out = select_moments(t, anthropic_client=_client([_moment(100, 250)]), fmt='longo', strict_long=True)
        assert out == []

    def test_longo_padrao_continua_esticando_regressao(self):
        t = _transcript(1500)
        out = select_moments(t, anthropic_client=_client([_moment(100, 250)]), fmt='longo')
        assert len(out) == 1 and out[0]['end_time'] - out[0]['start_time'] >= MIN_LONGFORM_SECONDS

    def test_longo_estrito_aceita_valido_e_limita_o_teto(self):
        t = _transcript(1500)
        ok = select_moments(t, anthropic_client=_client([_moment(0, 500)]), fmt='longo', strict_long=True)
        assert len(ok) == 1 and 500 <= ok[0]['end_time'] - ok[0]['start_time'] <= 502
        longo = select_moments(t, anthropic_client=_client([_moment(0, 1400)]), fmt='longo', strict_long=True)
        assert longo[0]['end_time'] - longo[0]['start_time'] == MAX_LONGFORM_SECONDS

    def test_janelas_cobrem_o_video_inteiro_e_respeitam_o_limite(self):
        lines = [f'[{i}s-{i + 10}s] ' + 'palavra ' * 12 for i in range(0, 3000, 10)]
        kept = _sample_transcript_windows(lines)
        assert sum(len(lines[i]) + 1 for i in kept) <= 8000
        assert min(kept) == 0 and max(kept) > len(lines) * 0.7  # chega ao fim do vídeo, não só ao início

    def test_sem_amostragem_trunca_no_inicio_como_antes(self):
        t = _transcript(3000)
        client = _client([_moment(10, 60)])
        select_moments(t, anthropic_client=client, fmt='curto')
        enviado = client.messages.create.call_args.kwargs['messages'][0]['content']
        assert len(enviado) <= 8000 and '[2990s' not in enviado

    def test_amostragem_envia_trecho_do_fim_do_video(self):
        t = _transcript(3000)
        client = _client([_moment(10, 60)])
        select_moments(t, anthropic_client=client, fmt='curto', sample_windows=True)
        enviado = client.messages.create.call_args.kwargs['messages'][0]['content']
        assert len(enviado) <= 8000 and '[2250s' in enviado

    def test_amostragem_descarta_momento_sobre_trecho_nao_visto(self):
        t = _transcript(3000)
        # 10s-60s está dentro da janela 1; 700s-760s cai numa lacuna entre janelas
        out = select_moments(t, anthropic_client=_client([_moment(10, 60, 9), _moment(700, 760, 8)]),
                             fmt='curto', sample_windows=True)
        assert [m['start_time'] for m in out] == [10]

    def test_amostragem_sem_estouro_de_limite_nao_muda_nada(self):
        t = _transcript(120)
        client = _client([_moment(10, 60)])
        out = select_moments(t, anthropic_client=client, fmt='curto', sample_windows=True)
        assert len(out) == 1


# ---------------------------------------------------------------- finalização do raw (dois formatos)

class TwoFormatDb:
    """Estado real de clips: o COUNT e o SELECT de clips respondem pelo que está na lista."""

    def __init__(self, clips, source_status='selecting', local_path=None):
        self.clips = clips
        self.source = {'status': source_status, 'local_path': local_path}
        self.updates = []
        self.conn = MagicMock()
        self.conn._driver = 'pgsql'
        self.conn.cursor.side_effect = lambda: _TwoFormatCursor(self)


class _TwoFormatCursor:
    def __init__(self, db):
        self.db = db
        self._last = ''
        self._params = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self._last, self._params = sql, params
        if sql.startswith('UPDATE source_videos'):
            self.db.updates.append(params)
            self.db.source['status'], self.db.source['local_path'] = params[0], None

    def fetchone(self):
        from src.publisher import NON_TERMINAL_CLIP_STATUSES as NT

        c = self.db.clips
        return {
            'total_count': len(c),
            'non_terminal_count': sum(1 for x in c if x['status'] in NT),
            'published_count': sum(1 for x in c if x['status'] == 'published'),
        }

    def fetchall(self):
        if 'clip_path, thumbnail_path' in self._last:
            return [{'clip_path': None, 'thumbnail_path': None} for _ in self.db.clips]
        return []


class TestFinalizacaoComDoisFormatos:
    def _db(self, tmp_path, curto, longo):
        raw = tmp_path / 'abc.mp4'
        raw.write_bytes(b'raw')
        clips = [{'format': 'curto', 'status': s} for s in curto] + [{'format': 'longo', 'status': s} for s in longo]
        return TwoFormatDb(clips, local_path=str(raw)), raw

    def test_shorts_terminais_mas_longo_em_corte_segura_o_raw(self, tmp_path):
        from src.publisher import _maybe_finalize_source_video

        db, raw = self._db(tmp_path, ['published', 'rejected'], ['pending_cut'])
        assert _maybe_finalize_source_video(db.conn, 1, str(raw)) is False
        assert raw.exists() and db.updates == []

    @pytest.mark.parametrize('longo', ['cutting', 'pending', 'approved', 'publishing'])
    def test_longo_nao_terminal_segura_o_raw(self, tmp_path, longo):
        from src.publisher import _maybe_finalize_source_video

        db, raw = self._db(tmp_path, ['published'], [longo])
        assert _maybe_finalize_source_video(db.conn, 1, str(raw)) is False
        assert raw.exists()

    def test_todos_terminais_nos_dois_formatos_apaga_o_raw(self, tmp_path):
        from src.publisher import _maybe_finalize_source_video

        db, raw = self._db(tmp_path, ['published', 'rejected'], ['failed'])
        assert _maybe_finalize_source_video(db.conn, 1, str(raw)) is True
        assert not raw.exists()
        assert db.source['status'] == 'published'

    def test_todos_terminais_sem_publicado_vira_failed(self, tmp_path):
        from src.publisher import _maybe_finalize_source_video

        db, raw = self._db(tmp_path, ['rejected'], ['failed'])
        assert _maybe_finalize_source_video(db.conn, 1, str(raw)) is True
        assert db.source['status'] == 'failed'

    def test_varredura_e_recovery_nao_filtram_por_formato(self):
        """Os SQLs que decidem raw/reprocesso olham TODOS os clips da fonte, de qualquer formato."""
        import inspect

        from src import db as db_mod
        from src import publisher

        for fn in (db_mod.recover_stuck_selecting, publisher.finalize_settled_source_videos,
                   publisher._maybe_finalize_source_video):
            src = inspect.getsource(fn)
            assert 'gc.format' not in src and "format =" not in src.replace('source_videos', '')

    def test_recovery_de_selecting_nao_reprocessa_fonte_que_ja_tem_clip_de_um_formato(self):
        import inspect

        from src import db as db_mod

        src = inspect.getsource(db_mod.recover_stuck_selecting)
        assert 'NOT EXISTS' in src and 'generated_clips gc WHERE gc.source_video_id' in src
