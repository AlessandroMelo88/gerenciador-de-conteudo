# ADR-0001 — Busca híbrida (texto + vetor) nas transcrições, com embeddings locais e degradação para texto

**Status:** Aceita  
**Data:** 29/09/2026

## Contexto

A busca de transcrições era um `ILIKE` sobre `transcript_text` (varredura de `longText`, sem ranking,
sem acento, sem noção de sentido, sem apontar o minuto). O projeto só tem chaves Anthropic e Groq,
nenhuma delas com embeddings. Opções para embeddings: APIs pagas (OpenAI, Voyage, Cohere, Gemini),
`bge-m3` local ou `multilingual-e5-small` local. A produção é uma VM A1 de 12 GB, já dividida com o
`clip-processor`.

## Decisão

Chunks de ~1.000 caracteres em `transcript_chunks` no próprio PostgreSQL 17 (pgvector, HNSW cosseno,
mais FTS `pt_unaccent`), busca híbrida por RRF, embeddings **locais** com `intfloat/multilingual-e5-small`
(384d) num sidecar `embedder`, indexação no worker do Mac. Se o embedder falhar, a busca **degrada para
texto** (`degraded: true`); não existe fallback para outro provedor de embeddings.

## Consequências

- Sem chave nova, sem custo, sem dado saindo do servidor; cabe na RAM da A1.
- Vetores de modelos diferentes não se misturam: trocar de modelo exige reindexar tudo
  (`embedding_model` por linha).
- O Postgres de produção precisa de imagem própria com pgvector (alpine 17 + extensão compilada, mesmo
  volume) e recriação manual antes do deploy; o deploy comum não troca a imagem.
- O Postgres compartilhado de dev não tem a extensão: migrations e testes toleram a ausência.
- Descartados: `bge-m3` (RAM), APIs externas (chave, privacidade, sem fallback coerente), banco vetorial
  separado (mais um serviço para 65 mil vetores por 1.000 aulas).
- Detalhes: `Docs/sistema/SISTEMA-BUSCA-TRANSCRICOES.md`.
