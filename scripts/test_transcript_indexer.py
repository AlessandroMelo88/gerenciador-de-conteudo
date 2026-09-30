"""Testes do indexador de transcrições (chunker, SRT, SQL, backfill). Sem rede nem modelo.

Rodar: python3 -m pytest scripts/test_transcript_indexer.py -q
"""
import base64
import importlib.util
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    'transcript_indexer', Path(__file__).with_name('transcript_indexer.py')
)
ti = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ti)


def _seg(start, end, text):
    return {'start': start, 'end': end, 'text': text}


def _fala(n, tamanho=80, passo=5.0):
    """n segmentos consecutivos de `tamanho` caracteres, `passo` segundos cada."""
    return [_seg(i * passo, (i + 1) * passo, f'{i:04d} ' + 'x' * (tamanho - 5)) for i in range(n)]


class FakeDb:
    def __init__(self, ok=True):
        self.ok = ok
        self.sql = []

    def stdin(self, sql):
        self.sql.append(sql)
        return self.ok


def fake_embed(texts, kind):
    fake_embed.calls.append((list(texts), kind))
    return [[0.5, 0.5, 0.5, 0.5] for _ in texts]


fake_embed.calls = []


class TestParseSrt:
    def test_le_tempos_e_texto(self):
        srt = ('1\n00:00:00,000 --> 00:00:02,500\nOlá turma.\n\n'
               '2\n01:02:03,250 --> 01:02:05,000\nSegunda fala\ncom duas linhas.\n')

        assert ti.parse_srt(srt) == [
            _seg(0.0, 2.5, 'Olá turma.'),
            _seg(3723.25, 3725.0, 'Segunda fala com duas linhas.'),
        ]

    def test_crlf_ponto_no_lugar_da_virgula_e_sem_numero(self):
        srt = '00:00:01.5 --> 00:00:03.0\r\nfala\r\n\r\n'

        assert ti.parse_srt(srt) == [_seg(1.5, 3.0, 'fala')]

    def test_bloco_sem_texto_ou_sem_tempo_e_descartado(self):
        srt = '1\n00:00:00,000 --> 00:00:01,000\n\n\n2\nlixo sem tempo\n\n3\n00:00:02,000 --> 00:00:03,000\nok\n'

        assert ti.parse_srt(srt) == [_seg(2.0, 3.0, 'ok')]

    @pytest.mark.parametrize('entrada', ['', None, '   \n\n'])
    def test_vazio(self, entrada):
        assert ti.parse_srt(entrada) == []

    def test_ida_e_volta_com_o_srt_do_worker(self):
        spec = importlib.util.spec_from_file_location('tw', Path(__file__).with_name('transcription_worker.py'))
        tw = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tw)
        segs = [_seg(0, 1.5, 'a'), _seg(1.5, 3725.5, 'b')]

        assert ti.parse_srt(tw.segments_to_srt(segs)) == segs


class TestChunkSegments:
    def test_texto_vazio_nao_gera_chunk(self):
        assert ti.chunk_segments([]) == []
        assert ti.chunk_segments([_seg(0, 1, '   '), _seg(1, 2, '')]) == []

    def test_um_segmento_curto_vira_um_chunk_com_tempos(self):
        [c] = ti.chunk_segments([_seg(3.0, 7.5, ' Olá   mundo ')])

        assert (c.index, c.content, c.start, c.end) == (0, 'Olá mundo', 3.0, 7.5)

    def test_tamanho_dentro_da_faixa_e_tempos_contiguos(self):
        chunks = ti.chunk_segments(_fala(200))

        assert len(chunks) > 5
        for c in chunks[:-1]:
            assert 900 <= len(c.content) <= 1200
        assert all(len(c.content) <= 1200 for c in chunks)
        assert [c.index for c in chunks] == list(range(len(chunks)))
        assert chunks[0].start == 0.0 and chunks[-1].end == 1000.0
        for a, b in zip(chunks, chunks[1:]):
            assert b.start <= a.end  # sobreposição, nunca buraco
            assert b.start > a.start  # e sempre avança

    def test_todo_segmento_aparece_em_algum_chunk(self):
        chunks = ti.chunk_segments(_fala(120))
        texto = ' '.join(c.content for c in chunks)

        for i in range(120):
            assert f'{i:04d} ' in texto

    def test_sobreposicao_repete_a_cauda_em_fronteira_de_segmento(self):
        segs = _fala(60)
        chunks = ti.chunk_segments(segs)
        segmentos = {s['text'] for s in segs}

        for a, b in zip(chunks, chunks[1:]):
            # o começo do próximo chunk é um segmento inteiro que já estava no fim do anterior
            primeiro = next(s for s in segmentos if b.content.startswith(s))
            assert a.content.endswith(primeiro) or primeiro in a.content
            sobra = len(a.content) - a.content.index(primeiro)
            assert sobra <= ti.OVERLAP_CHARS + 1

    def test_chunks_comecam_e_terminam_em_segmento_inteiro(self):
        segs = _fala(60)
        textos = [s['text'] for s in segs]
        for c in ti.chunk_segments(segs):
            assert any(c.content.startswith(t) for t in textos)
            assert any(c.content.endswith(t) for t in textos)

    def test_segmento_gigante_e_dividido_em_frases_com_tempo_repartido(self):
        frase = 'Esta é uma frase de tamanho razoável para o teste. '
        gigante = _seg(100.0, 200.0, frase * 100)  # ~5000 caracteres num segmento só

        chunks = ti.chunk_segments([gigante])

        assert len(chunks) >= 4
        assert all(len(c.content) <= 1200 for c in chunks)
        assert chunks[0].start == pytest.approx(100.0)
        assert chunks[-1].end == pytest.approx(200.0)
        assert all(100.0 <= c.start <= c.end <= 200.0 for c in chunks)
        for c in chunks:
            assert c.content.endswith('teste.')  # cortou em fim de frase

    def test_palavra_gigante_sem_espaco_e_cortada_no_teto(self):
        chunks = ti.chunk_segments([_seg(0, 10, 'a' * 3000)])

        assert all(len(c.content) <= 1200 for c in chunks)
        assert sum(len(c.content) for c in chunks) >= 3000

    def test_segmento_sem_tempo_gera_chunk_sem_tempo(self):
        [c] = ti.chunk_segments([_seg(None, None, 'sem tempo')])

        assert c.start is None and c.end is None

    def test_termina_mesmo_com_segmentos_no_limite_do_teto(self):
        # cada segmento tem 700 chars: dois não cabem juntos, sobreposição não cabe
        chunks = ti.chunk_segments([_seg(i, i + 1, 'y' * 700) for i in range(10)])

        assert len(chunks) == 10
        assert all(len(c.content) == 700 for c in chunks)

    def test_estimativa_de_tokens(self):
        [c] = ti.chunk_segments([_seg(0, 1, 'x' * 400)])

        assert c.token_estimate == 100


class TestChunkTextOnly:
    def test_vazio(self):
        assert ti.chunk_text_only('') == []
        assert ti.chunk_text_only(None) == []
        assert ti.chunk_text_only('\n\n  \n\n') == []

    def test_paragrafos_viram_chunks_sem_tempo(self):
        texto = '\n\n'.join('Parágrafo %d. ' % i + 'z' * 400 for i in range(12))

        chunks = ti.chunk_text_only(texto)

        assert len(chunks) > 1
        assert all(c.start is None and c.end is None for c in chunks)
        assert all(len(c.content) <= 1200 for c in chunks)
        assert 'Parágrafo 0.' in chunks[0].content and 'Parágrafo 11.' in chunks[-1].content

    def test_build_chunks_escolhe_a_fonte(self):
        assert ti.build_chunks('1\n00:00:01,000 --> 00:00:02,000\nfala\n')[0].start == 1.0
        assert ti.build_chunks('só texto corrido')[0].start is None
        assert ti.build_chunks([_seg(2, 3, 'lista')])[0].start == 2
        assert ti.build_chunks(None) == []


class TestSql:
    def test_transacao_com_delete_e_insert(self):
        chunks = ti.chunk_segments([_seg(1.0, 2.0, 'Olá')])

        sql = ti.build_index_sql(7, chunks)

        assert sql.startswith('BEGIN;') and sql.rstrip().endswith('COMMIT;')
        assert 'DELETE FROM transcript_chunks WHERE job_id = 7;' in sql
        assert sql.index('DELETE') < sql.index('INSERT INTO transcript_chunks')
        assert '(7, 0, ' in sql and '1.000, 2.000' in sql
        assert 'embedding' not in sql.split('INSERT', 1)[1].split('VALUES')[0]
        assert 'DO $emb$' not in sql  # sem vetores, sem bloco

    def test_texto_com_aspas_e_cifrao_nao_fecha_o_literal(self):
        chunks = ti.chunk_segments([_seg(0, 1, "It's $$ '; DROP TABLE x; -- $t1$")])

        sql = ti.build_index_sql(1, chunks)

        assert "DROP TABLE x" in sql
        assert sql.count('DROP TABLE') == 1
        # o conteúdo está entre tags aleatórias: nenhum literal com aspas simples abertas
        assert "'It's" not in sql

    def test_tempo_ausente_vira_null(self):
        chunks = ti.chunk_text_only('sem tempo')

        assert 'NULL, NULL' in ti.build_index_sql(1, chunks)

    def test_vetor_como_literal_pgvector_num_bloco_tolerante(self):
        chunks = ti.chunk_segments([_seg(0, 1, 'a')])

        sql = ti.build_index_sql(3, chunks, [[0.5, 0.25, 0.125, 0.0625]], model='m/x')

        assert "'[0.5,0.25,0.125,0.0625]'::vector" in sql
        assert 'DO $emb$' in sql and 'EXCEPTION WHEN OTHERS' in sql
        assert 'embedding_model' in sql and 'm/x' in sql
        assert 't.job_id = 3 AND t.chunk_index = v.i' in sql

    def test_job_id_e_forcado_a_inteiro(self):
        with pytest.raises(ValueError):
            ti.build_index_sql('1; DROP TABLE x', [])


class TestIndexJob:
    def setup_method(self):
        fake_embed.calls.clear()

    def test_grava_chunks_e_vetores_em_uma_chamada(self):
        db = FakeDb()

        n = ti.index_job(5, _fala(40), db.stdin, embed=fake_embed)

        assert n > 1 and len(db.sql) == 1
        assert "::vector" in db.sql[0]
        assert all(kind == 'passage' for _, kind in fake_embed.calls)
        assert sum(len(t) for t, _ in fake_embed.calls) == n

    def test_aceita_srt_como_fonte(self):
        db = FakeDb()

        n = ti.index_job(5, '1\n00:00:00,000 --> 00:00:02,000\nOlá\n', db.stdin, embed=fake_embed)

        assert n == 1 and '0.000, 2.000' in db.sql[0]

    def test_sem_vetor(self):
        db = FakeDb()

        ti.index_job(5, _fala(3), db.stdin, embed=None)

        assert '::vector' not in db.sql[0]

    def test_falha_do_embed_grava_chunks_sem_vetor_e_avisa(self, capsys):
        db = FakeDb()

        def quebra(texts, kind):
            raise ImportError('No module named sentence_transformers')

        n = ti.index_job(5, _fala(3), db.stdin, embed=quebra)

        assert n == 1
        assert 'INSERT INTO transcript_chunks' in db.sql[0] and '::vector' not in db.sql[0]
        assert 'sem vetor' in capsys.readouterr().out

    def test_quantidade_errada_de_vetores_e_tratada_como_falha(self):
        db = FakeDb()

        n = ti.index_job(5, _fala(40), db.stdin, embed=lambda texts, kind: [[1.0]])

        assert n > 1 and '::vector' not in db.sql[0]

    def test_embed_em_lotes(self):
        db = FakeDb()

        n = ti.index_job(5, _fala(600), db.stdin, embed=fake_embed)

        assert n > ti.EMBED_BATCH
        assert all(len(t) <= ti.EMBED_BATCH for t, _ in fake_embed.calls)
        assert len(fake_embed.calls) > 1

    def test_banco_recusando_levanta(self):
        with pytest.raises(RuntimeError, match='job 5'):
            ti.index_job(5, _fala(3), FakeDb(ok=False).stdin, embed=None)

    def test_transcricao_vazia_so_limpa_os_chunks_antigos(self):
        db = FakeDb()

        assert ti.index_job(5, '', db.stdin, embed=fake_embed) == 0
        assert 'DELETE FROM transcript_chunks' in db.sql[0] and 'INSERT' not in db.sql[0]
        assert fake_embed.calls == []

    def test_idempotente_mesmo_sql_duas_vezes(self):
        a, b = FakeDb(), FakeDb()
        segs = _fala(10)

        ti.index_job(5, segs, a.stdin, embed=None)
        ti.index_job(5, segs, b.stdin, embed=None)

        # cada execução começa com DELETE do job: reprocessar não duplica
        assert a.sql[0].count('DELETE') == b.sql[0].count('DELETE') == 1


class FakeRemote:
    """Banco de mentira do backfill: ids e a fonte de cada job."""

    def __init__(self, sources):
        self.sources = sources  # {id: (kind, texto)}
        self.queries = []

    def sql(self, query):
        self.queries.append(query)
        if query.startswith('SELECT id FROM'):
            return '\n'.join(str(i) for i in self.sources)
        job = int(query.rsplit('id = ', 1)[1].rstrip(';'))
        kind, text = self.sources[job]
        return f"{kind}\t{base64.b64encode(text.encode()).decode()}"


class TestBackfill:
    def test_indexa_cada_job_e_soma(self):
        remote = FakeRemote({1: ('srt', '1\n00:00:00,000 --> 00:00:01,000\nfala\n'),
                             2: ('text', 'texto corrido legado com acentuação')})
        db = FakeDb()

        res = ti.backfill(remote.sql, db.stdin, embed=None)

        assert res == {'jobs': 2, 'chunks': 2, 'falhas': []}
        assert len(db.sql) == 2
        assert 'acentuação' in db.sql[1]

    def test_falha_de_um_job_nao_para_os_outros(self):
        remote = FakeRemote({1: ('text', 'a'), 2: ('text', 'b')})
        chamadas = []

        def stdin(sql):
            chamadas.append(sql)
            return len(chamadas) != 1  # o primeiro é recusado

        res = ti.backfill(remote.sql, stdin, embed=None)

        assert res['falhas'] == [1] and res['jobs'] == 1

    def test_filtros_do_sql(self):
        remote = FakeRemote({})
        ti.backfill(remote.sql, FakeDb().stdin, embed=None)
        ti.backfill(remote.sql, FakeDb().stdin, job=9, reindex=True, embed=None)

        sem_reindex, com_reindex = remote.queries
        assert "status = 'done'" in sem_reindex and 'NOT EXISTS' in sem_reindex
        assert 'id = 9' in com_reindex and 'NOT EXISTS' not in com_reindex

    def test_fonte_ilegivel_conta_como_falha(self):
        remote = FakeRemote({1: ('text', 'a')})
        remote.sql_original = remote.sql
        remote.sql = lambda q: '1' if q.startswith('SELECT id') else ''

        assert ti.backfill(remote.sql, FakeDb().stdin, embed=None)['falhas'] == [1]

    def test_cli_exige_um_modo(self):
        with pytest.raises(SystemExit):
            ti.main([], run_sql=lambda q: '', run_sql_stdin=lambda s: True)

    def test_cli_sem_vetor_e_codigo_de_saida(self):
        remote = FakeRemote({1: ('text', 'olá')})
        db = FakeDb()

        assert ti.main(['--backfill', '--sem-vetor'], run_sql=remote.sql, run_sql_stdin=db.stdin) == 0
        assert '::vector' not in db.sql[0]
        assert ti.main(['--backfill', '--sem-vetor'], run_sql=remote.sql,
                       run_sql_stdin=FakeDb(ok=False).stdin) == 1
