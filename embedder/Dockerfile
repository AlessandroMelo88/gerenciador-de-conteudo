# Sidecar de embeddings da busca vetorial. Multi-arch (linux/arm64 na A1, amd64 no dev).
# Build a partir da pasta embedder/:  docker build -t canaldecortes-embedder embedder/
FROM python:3.12-slim

# Modelo e revisão fixos: vetores de versões diferentes não se misturam no banco.
# Revisão = commit do Hugging Face de intfloat/multilingual-e5-small (validado em 29/09/2026).
ENV EMBEDDING_MODEL=intfloat/multilingual-e5-small \
    EMBEDDING_REVISION=614241f622f53c4eeff9890bdc4f31cfecc418b3 \
    EMBEDDING_DIM=384 \
    HF_HOME=/opt/hf-cache \
    EMBEDDING_CACHE=/opt/hf-cache \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
# torch CPU primeiro (o PyPI padrão puxaria os pacotes CUDA no amd64).
RUN pip install --index-url https://download.pytorch.org/whl/cpu "torch>=2.2" \
 && pip install -r requirements.txt

# Modelo baixado no build: o container nunca depende da internet para subir.
# cache_folder = o mesmo que embed_lib.py usa em execução (EMBEDDING_CACHE). Sem isso o modelo
# ia para /opt/hf-cache/hub e o runtime, offline, procurava em /opt/hf-cache e dava 503.
RUN python -c "import os; from sentence_transformers import SentenceTransformer; \
SentenceTransformer(os.environ['EMBEDDING_MODEL'], revision=os.environ['EMBEDDING_REVISION'], device='cpu', cache_folder=os.environ['EMBEDDING_CACHE'])"
ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1

COPY embed_lib.py app.py ./

RUN useradd --system --no-create-home embedder
USER embedder

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status==200 else 1)"

# Um worker só: o modelo ocupa ~470 MB e o mem_limit da A1 é 1g.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
