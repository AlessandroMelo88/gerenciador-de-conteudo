"""embed_lib.py — embeddings do Canal de Cortes (busca vetorial nas transcrições).

Módulo único, compartilhado por:
  * o sidecar `embedder/app.py` (A1, só consulta: kind="query");
  * `scripts/transcript_indexer.py` (Mac, indexação: kind="passage").

Modelo: `intfloat/multilingual-e5-small` (384 dimensões, PT-BR razoável, ~470 MB de RAM).
O `fastembed` NÃO lista esse modelo (verificado na 0.8.1: só o e5-large), então usamos
`sentence-transformers`. Vetores de modelos diferentes não se misturam: trocar o modelo
exige reindexar tudo (a coluna `embedding_model` guarda qual foi usado).

Regras do e5, aplicadas AQUI dentro para nenhum chamador esquecer:
  * prefixo `passage: ` ao indexar e `query: ` ao consultar;
  * vetor L2-normalizado (cosseno == produto interno).

Instalação no Mac (worker de transcrição, que indexa):
    python3.12 -m venv ~/.venvs/canaldecortes-embed
    ~/.venvs/canaldecortes-embed/bin/pip install -r embedder/requirements-lib.txt
  e rode o worker com esse Python. Sem a dependência o indexador NÃO derruba nada:
  grava os chunks sem vetor (busca textual segue funcionando) e avisa no log.

Variáveis: EMBEDDING_MODEL, EMBEDDING_DIM, EMBEDDING_REVISION (opcional; fixa o commit
do Hugging Face), EMBEDDING_CACHE (pasta do cache do modelo).
"""
import math
import os
import threading

DEFAULT_MODEL = 'intfloat/multilingual-e5-small'
DEFAULT_DIM = 384
KINDS = ('query', 'passage')
PREFIXES = {'query': 'query: ', 'passage': 'passage: '}


class EmbedderError(RuntimeError):
    """Modelo indisponível, dimensão inesperada ou entrada inválida."""


def model_name() -> str:
    return os.environ.get('EMBEDDING_MODEL') or DEFAULT_MODEL


def model_dim() -> int:
    try:
        return int(os.environ.get('EMBEDDING_DIM') or DEFAULT_DIM)
    except ValueError:
        return DEFAULT_DIM


def add_prefix(texts: list[str], kind: str) -> list[str]:
    if kind not in PREFIXES:
        raise EmbedderError(f'kind inválido: {kind!r} (use "query" ou "passage")')
    prefix = PREFIXES[kind]
    return [prefix + t for t in texts]


def l2_normalize(vector) -> list[float]:
    """Norma 1. Vetor nulo volta como está (não divide por zero)."""
    values = [float(x) for x in vector]
    norm = math.sqrt(sum(x * x for x in values))
    if norm == 0.0:
        return values
    return [x / norm for x in values]


def _load_sentence_transformer(name: str):
    from sentence_transformers import SentenceTransformer  # import tardio: pesado

    kwargs = {}
    revision = os.environ.get('EMBEDDING_REVISION')
    if revision:
        kwargs['revision'] = revision
    cache = os.environ.get('EMBEDDING_CACHE')
    if cache:
        kwargs['cache_folder'] = cache
    return SentenceTransformer(name, device='cpu', **kwargs)


class Embedder:
    """Carrega o modelo uma vez e embute lotes de texto.

    `loader(name)` devolve um objeto com `.encode(list[str]) -> lista de vetores`;
    injetável para os testes não baixarem o modelo.
    """

    def __init__(self, name: str | None = None, dim: int | None = None,
                 loader=_load_sentence_transformer, batch_size: int = 32):
        self.name = name or model_name()
        self.dim = dim or model_dim()
        self._loader = loader
        self._batch_size = batch_size
        self._model = None
        self._lock = threading.Lock()

    @property
    def loaded(self) -> bool:
        return self._model is not None

    def load(self) -> None:
        with self._lock:
            if self._model is not None:
                return
            try:
                self._model = self._loader(self.name)
            except Exception as e:
                raise EmbedderError(f'não consegui carregar {self.name}: {e}') from e

    def embed(self, texts: list[str], kind: str) -> list[list[float]]:
        if not texts:
            return []
        prefixed = add_prefix(texts, kind)
        self.load()
        try:
            raw = self._model.encode(prefixed, batch_size=self._batch_size)
        except TypeError:
            raw = self._model.encode(prefixed)
        vectors = [l2_normalize(v) for v in raw]
        for v in vectors:
            if len(v) != self.dim:
                raise EmbedderError(f'dimensão {len(v)} != esperada {self.dim} para {self.name}')
        return vectors


_default: Embedder | None = None
_default_lock = threading.Lock()


def get_embedder() -> Embedder:
    global _default
    with _default_lock:
        if _default is None:
            _default = Embedder()
        return _default


def embed(texts: list[str], kind: str) -> list[list[float]]:
    """Atalho com o modelo padrão (env). Usado pelo indexador."""
    return get_embedder().embed(texts, kind)
