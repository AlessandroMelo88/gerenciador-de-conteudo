"""transcript_indexer.py — indexa transcrições em `transcript_chunks` (busca vetorial + textual).

Roda no Mac. O `transcription_worker` chama `index_job` logo depois de gravar o job como
`done`; o CLI faz o backfill dos jobs antigos.

    python3 scripts/transcript_indexer.py --backfill              # jobs done sem chunks
    python3 scripts/transcript_indexer.py --backfill --job 12     # só o job 12
    python3 scripts/transcript_indexer.py --backfill --reindex    # apaga e refaz os chunks
    python3 scripts/transcript_indexer.py --backfill --sem-vetor  # só texto (embedding NULL)

Como funciona
  * Chunks de ~900-1200 caracteres com ~180 de sobreposição, sempre em fronteira de segmento.
    A fonte dos tempos é a lista de segmentos do Whisper (worker) ou o `transcript_srt`
    (backfill); job legado sem SRT cai em `chunk_text_only` (sem tempos).
  * Idempotente: DELETE + INSERT dos chunks do job numa transação só.
  * Vetor: `embedder/embed_lib.py` (multilingual-e5-small, prefixo `passage: `, L2). Vai no SQL
    como literal '[..]'::vector, num UPDATE dentro de um bloco DO com EXCEPTION: se a coluna
    `embedding` (ou o tipo `vector`) não existir no banco, os chunks ficam gravados sem
    vetor e o banco só emite um WARNING. Se o embed falhar (dependência ausente, modelo
    fora), idem: chunks sem embedding + aviso no log, sem exceção. A busca textual segue
    funcionando; um `--backfill --reindex` completa os vetores depois.

Dependência do vetor no Mac: ver a docstring de `embedder/embed_lib.py` (sentence-transformers;
o fastembed não suporta o e5-small).
"""
import argparse
import base64
import importlib.util
import math
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
EMBEDDER_DIR = SCRIPTS_DIR.parent / 'embedder'

TARGET_CHARS = 1000    # fecha o chunk ao passar disso
MAX_CHARS = 1200       # teto duro (o e5 corta em 512 tokens)
OVERLAP_CHARS = 180    # cauda do chunk anterior repetida no próximo
EMBED_BATCH = 32

EMBEDDING_MODEL_DEFAULT = 'intfloat/multilingual-e5-small'

_DEFAULT = object()  # `embed=` não informado -> usa embed_lib


@dataclass
class Chunk:
    index: int
    content: str
    start: float | None
    end: float | None

    @property
    def token_estimate(self) -> int:
        return max(1, math.ceil(len(self.content) / 4))


def _log(msg: str) -> None:
    print(f'[indexador] {msg}', flush=True)


# ---------------------------------------------------------------- SRT

_TIME = r'(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})'
_TIME_LINE = re.compile(rf'^\s*{_TIME}\s*-->\s*{_TIME}')


def _to_seconds(h, m, s, ms) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms.ljust(3, '0')) / 1000


def parse_srt(text: str) -> list[dict]:
    """SRT -> [{'start','end','text'}]. Tolera CRLF, número do bloco ausente, ponto no
    lugar da vírgula e texto em várias linhas. Bloco sem texto é descartado."""
    segments = []
    for block in re.split(r'\n\s*\n', (text or '').replace('\r\n', '\n').replace('\r', '\n')):
        lines = [l for l in block.split('\n') if l.strip()]
        for i, line in enumerate(lines):
            m = _TIME_LINE.match(line)
            if not m:
                continue
            g = m.groups()
            body = ' '.join(l.strip() for l in lines[i + 1:]).strip()
            if body:
                segments.append({'start': _to_seconds(*g[0:4]), 'end': _to_seconds(*g[4:8]),
                                 'text': body})
            break
    return segments


# ---------------------------------------------------------------- chunker

_SENTENCE_END = re.compile(r'(?<=[.!?…])\s+')


def _pieces(text: str, max_chars: int) -> list[str]:
    """Quebra um texto maior que `max_chars` em pedaços <= max_chars: por frase, depois
    por palavra, e por caractere só se uma "palavra" sozinha passar do teto."""
    if len(text) <= max_chars:
        return [text]
    out: list[str] = []
    cur = ''

    def flush():
        nonlocal cur
        if cur:
            out.append(cur)
            cur = ''

    for sentence in _SENTENCE_END.split(text):
        if len(sentence) > max_chars:
            flush()
            for word in sentence.split():
                while len(word) > max_chars:
                    flush()
                    out.append(word[:max_chars])
                    word = word[max_chars:]
                if cur and len(cur) + 1 + len(word) > max_chars:
                    flush()
                cur = f'{cur} {word}' if cur else word
            continue
        if cur and len(cur) + 1 + len(sentence) > max_chars:
            flush()
        cur = f'{cur} {sentence}' if cur else sentence
    flush()
    return out


def _normalize_segments(segments: list[dict], max_chars: int) -> list[dict]:
    """Descarta vazios e divide segmento gigante em sub-segmentos, repartindo o tempo
    em proporção ao tamanho do texto."""
    out = []
    for seg in segments:
        text = re.sub(r'\s+', ' ', (seg.get('text') or '')).strip()
        if not text:
            continue
        start, end = seg.get('start'), seg.get('end')
        parts = _pieces(text, max_chars)
        if len(parts) == 1 or start is None or end is None:
            for p in parts:
                out.append({'start': start, 'end': end, 'text': p})
            continue
        total, pos = sum(len(p) for p in parts), 0
        for p in parts:
            a = start + (end - start) * pos / total
            pos += len(p)
            out.append({'start': a, 'end': start + (end - start) * pos / total, 'text': p})
    return out


def chunk_segments(segments: list[dict], target_chars: int = TARGET_CHARS,
                   max_chars: int = MAX_CHARS, overlap_chars: int = OVERLAP_CHARS) -> list[Chunk]:
    """Agrupa segmentos (start, end, text) em chunks de ~target_chars, nunca acima de
    max_chars, com a cauda do anterior (até overlap_chars) repetida no início do próximo.

    Só corta entre segmentos; um segmento maior que max_chars é antes dividido em frases.
    `start`/`end` do chunk = início do primeiro e fim do último segmento (None se faltarem).
    """
    segs = _normalize_segments(segments, max_chars)
    chunks: list[Chunk] = []
    cur: list[dict] = []
    novos = 0  # segmentos em `cur` que ainda não saíram em nenhum chunk

    def length(items):
        return sum(len(s['text']) for s in items) + max(len(items) - 1, 0)

    def emit():
        nonlocal cur, novos
        chunks.append(Chunk(
            index=len(chunks), content=' '.join(s['text'] for s in cur),
            start=cur[0]['start'], end=cur[-1]['end'],
        ))
        tail: list[dict] = []
        for s in reversed(cur[1:]):  # nunca repete o chunk inteiro: garante avanço
            if length([s] + tail) > overlap_chars:
                break
            tail.insert(0, s)
        cur = tail
        novos = 0

    for seg in segs:
        if cur and length(cur) + 1 + len(seg['text']) > max_chars:
            if novos:
                emit()
            # a cauda de sobreposição + o segmento novo ainda pode estourar o teto: descarta a cauda
            if cur and length(cur) + 1 + len(seg['text']) > max_chars:
                cur = []
        cur.append(seg)
        novos += 1
        if length(cur) >= target_chars:
            emit()
    if novos:
        emit()
    return chunks


def chunk_text_only(text: str, target_chars: int = TARGET_CHARS, max_chars: int = MAX_CHARS,
                    overlap_chars: int = OVERLAP_CHARS) -> list[Chunk]:
    """Texto corrido sem tempos (job legado): cada parágrafo (\\n\\n) é um segmento sem tempo."""
    paragraphs = [p for p in re.split(r'\n\s*\n', text or '') if p.strip()]
    return chunk_segments([{'start': None, 'end': None, 'text': p} for p in paragraphs],
                          target_chars, max_chars, overlap_chars)


def build_chunks(segments_or_srt) -> list[Chunk]:
    """Lista de segmentos, SRT (texto com '-->') ou texto corrido -> chunks."""
    if isinstance(segments_or_srt, str):
        if '-->' in segments_or_srt:
            return chunk_segments(parse_srt(segments_or_srt))
        return chunk_text_only(segments_or_srt)
    return chunk_segments(list(segments_or_srt or []))


# ---------------------------------------------------------------- SQL

def _load_sibling(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_dq = None


def _dollar_quote(text: str) -> str:
    """`dollar_quote` do transcription_worker (tag aleatória conferida contra o texto)."""
    global _dq
    if _dq is None:
        _dq = _load_sibling('transcription_worker', SCRIPTS_DIR / 'transcription_worker.py').dollar_quote
    return _dq(text)


def _num(value: float | None) -> str:
    return 'NULL' if value is None else f'{float(value):.3f}'


def vector_literal(vector) -> str:
    return "'[" + ','.join(f'{float(x):.6g}' for x in vector) + "]'::vector"


def build_index_sql(job_id: int, chunks: list[Chunk], vectors: list | None = None,
                    model: str = EMBEDDING_MODEL_DEFAULT) -> str:
    """Script de uma transação: apaga os chunks do job, insere os novos e, se houver
    vetores, preenche `embedding` num bloco DO tolerante (coluna/tipo ausente = WARNING)."""
    job_id = int(job_id)
    sql = ['BEGIN;', f'DELETE FROM transcript_chunks WHERE job_id = {job_id};']
    if chunks:
        rows = ',\n'.join(
            f'({job_id}, {c.index}, {_dollar_quote(c.content)}, {_num(c.start)}, {_num(c.end)}, '
            f'{c.token_estimate}, NOW())' for c in chunks
        )
        sql.append('INSERT INTO transcript_chunks (job_id, chunk_index, content, start_seconds, '
                   f'end_seconds, token_estimate, created_at) VALUES\n{rows};')
    if chunks and vectors:
        values = ',\n'.join(f'({c.index}, {vector_literal(v)})' for c, v in zip(chunks, vectors))
        sql.append(
            'DO $emb$ BEGIN\n'
            'UPDATE transcript_chunks t SET embedding = v.e, '
            f"embedding_model = {_dollar_quote(model)}\n"
            f'FROM (VALUES\n{values}\n) AS v(i, e) WHERE t.job_id = {job_id} AND t.chunk_index = v.i;\n'
            "EXCEPTION WHEN OTHERS THEN RAISE WARNING 'embedding nao gravado (job %): %', "
            f'{job_id}, SQLERRM;\n'
            'END $emb$;'
        )
    sql.append('COMMIT;')
    return '\n'.join(sql)


# ---------------------------------------------------------------- embed

def _default_embed(texts: list[str], kind: str):
    if str(EMBEDDER_DIR) not in sys.path:
        sys.path.insert(0, str(EMBEDDER_DIR))
    import embed_lib  # noqa: PLC0415 — import tardio: só o Mac com sentence-transformers tem

    return embed_lib.embed(texts, kind)


def _embed_all(texts: list[str], embed, model: str):
    """Vetores dos textos, ou None (com aviso) se qualquer coisa falhar."""
    try:
        vectors: list = []
        for i in range(0, len(texts), EMBED_BATCH):
            vectors.extend(embed(texts[i:i + EMBED_BATCH], 'passage'))
        if len(vectors) != len(texts):
            raise RuntimeError(f'{len(vectors)} vetores para {len(texts)} chunks')
        return vectors
    except Exception as e:  # ImportError, modelo ausente, rede: nunca derruba
        _log(f'AVISO: embedding indisponível ({model}): {e}. Chunks gravados sem vetor.')
        return None


def index_job(job_id: int, segments_or_srt, run_sql_stdin, embed=_DEFAULT,
              model: str | None = None) -> int:
    """Indexa um job. Devolve o nº de chunks gravados. Idempotente (reprocessar não duplica).

    `run_sql_stdin(sql) -> bool` é o do local_download_worker. `embed(texts, kind)` devolve
    os vetores; `None` = sem vetor (--sem-vetor). Levanta RuntimeError só se o banco recusar
    o SQL (tabela ausente, job apagado): quem chama decide.
    """
    model = model or os.environ.get('EMBEDDING_MODEL') or EMBEDDING_MODEL_DEFAULT
    chunks = build_chunks(segments_or_srt)
    vectors = None
    if chunks and embed is not None:
        embed_fn = _default_embed if embed is _DEFAULT else embed
        vectors = _embed_all([c.content for c in chunks], embed_fn, model)
    if not run_sql_stdin(build_index_sql(job_id, chunks, vectors, model)):
        raise RuntimeError(f'o banco recusou os chunks do job {int(job_id)}')
    return len(chunks)


# ---------------------------------------------------------------- backfill

def _job_ids_sql(job: int | None, reindex: bool) -> str:
    where = ["status = 'done'", "(COALESCE(transcript_srt, '') <> '' OR COALESCE(transcript_text, '') <> '')"]
    if job is not None:
        where.append(f'id = {int(job)}')
    if not reindex:
        where.append('NOT EXISTS (SELECT 1 FROM transcript_chunks c WHERE c.job_id = transcription_jobs.id)')
    return f"SELECT id FROM transcription_jobs WHERE {' AND '.join(where)} ORDER BY id;"


def _job_source_sql(job_id: int) -> str:
    # base64 sem quebra de linha: o run_remote_sql devolve texto separado por \n e \t.
    return (
        "SELECT CASE WHEN COALESCE(transcript_srt, '') <> '' THEN 'srt' ELSE 'text' END, "
        "replace(encode(convert_to(CASE WHEN COALESCE(transcript_srt, '') <> '' "
        "THEN transcript_srt ELSE transcript_text END, 'UTF8'), 'base64'), E'\\n', '') "
        f"FROM transcription_jobs WHERE id = {int(job_id)};"
    )


def backfill(run_sql, run_sql_stdin, job: int | None = None, reindex: bool = False,
             embed=_DEFAULT) -> dict:
    """Indexa os jobs `done` sem chunks (ou todos, com reindex). Um job que falha não para os outros."""
    resultado = {'jobs': 0, 'chunks': 0, 'falhas': []}
    ids = [int(l) for l in (run_sql(_job_ids_sql(job, reindex)) or '').splitlines() if l.strip().isdigit()]
    for job_id in ids:
        try:
            row = (run_sql(_job_source_sql(job_id)) or '').strip()
            kind, _, payload = row.partition('\t')
            if not payload:
                raise RuntimeError('não consegui ler a transcrição do banco')
            source = base64.b64decode(payload).decode('utf-8')
            n = index_job(job_id, source, run_sql_stdin, embed=embed)
            resultado['jobs'] += 1
            resultado['chunks'] += n
            _log(f'job {job_id}: {n} chunks ({kind})')
        except Exception as e:
            resultado['falhas'].append(job_id)
            _log(f'AVISO: job {job_id} falhou: {e}')
    return resultado


def main(argv: list[str] | None = None, run_sql=None, run_sql_stdin=None) -> int:
    parser = argparse.ArgumentParser(description='Indexa transcrições em transcript_chunks.')
    parser.add_argument('--backfill', action='store_true', help='indexa jobs done sem chunks')
    parser.add_argument('--job', type=int, help='só este job')
    parser.add_argument('--reindex', action='store_true', help='apaga e refaz os chunks já existentes')
    parser.add_argument('--sem-vetor', action='store_true', help='não gera embeddings (embedding NULL)')
    args = parser.parse_args(argv)
    if not (args.backfill or args.job is not None or args.reindex):
        parser.error('use --backfill (ou --job N / --reindex)')

    if run_sql is None or run_sql_stdin is None:
        ldw = _load_sibling('local_download_worker', SCRIPTS_DIR / 'local_download_worker.py')
        run_sql, run_sql_stdin = ldw.run_remote_sql, ldw.run_remote_sql_stdin

    res = backfill(run_sql, run_sql_stdin, job=args.job, reindex=args.reindex,
                   embed=None if args.sem_vetor else _DEFAULT)
    _log(f"{res['jobs']} jobs, {res['chunks']} chunks, {len(res['falhas'])} falhas {res['falhas']}")
    return 1 if res['falhas'] else 0


if __name__ == '__main__':
    sys.exit(main())
