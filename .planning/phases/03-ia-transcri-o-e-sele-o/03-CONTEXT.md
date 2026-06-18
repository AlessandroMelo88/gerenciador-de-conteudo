# Phase 3: IA — Transcrição e Seleção - Context

**Gathered:** 2026-06-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Vídeos com status `downloaded` são transcritos via Groq Whisper API (PT-BR) e analisados pelo Claude Haiku para identificar os melhores momentos (5-10 min cada). Momentos com score ≥ 7 avançam para a fila de corte — os demais são descartados. Corte de vídeo e publicação são fases separadas.

Conteúdo-alvo: futebol e podcasts de tópicos variados (os mesmos canais monitorados).

</domain>

<decisions>
## Implementation Decisions

### Trigger do processamento
- Transcrição e seleção são disparadas no mesmo poll (rss_poller), logo após o download concluir
- Sem job separado no scheduler — fluxo linear: download → transcribing → selecting → (fila de corte)
- Mesmo padrão do daemon atual: poll_all_channels chama o processamento completo

### Armazenamento da transcrição
- JSON de transcrição salvo em disco ao lado do vídeo: `videos/{youtube_video_id}_transcript.json`
- Banco MySQL armazena o caminho do arquivo (coluna `transcript_path` na tabela `source_videos`)
- A Fase 4 (FFmpeg) lê o arquivo JSON diretamente para acessar timestamps dos momentos selecionados

### Duração e tipo dos momentos
- Clips-alvo: 5-10 minutos por momento selecionado
- Claude Haiku instrução: "identifique segmentos de 5-10 minutos com alto engajamento"
- Futebol: momentos de análise, debate, gol + reação; Podcasts: trechos de discussão acalorada ou revelação importante

### Dados de cada momento selecionado
- Schema mínimo por momento: `start_time` (segundos), `end_time` (segundos), `score` (1-10), `reason` (string)
- Armazenado na tabela `generated_clips` (já existe no schema da Fase 1) com status `pending_cut`
- A Fase 5 (títulos/SEO) gera o título a partir do `reason` — não precisa de título aqui

### Limite de clips por vídeo
- Máximo 3 momentos por vídeo, sem overlap entre eles
- Se dois momentos se sobrepõem: mantém o de maior score, descarta o outro
- Claude Haiku instrução: "retorne no máximo 3 momentos não-sobrepostos, ordenados por score decrescente"

### Filtro de qualidade
- Score ≥ 7: insere em `generated_clips` com status `pending_cut`
- Score < 7: registrado no log com motivo, não persiste no banco
- Comportamento definido no REQUIREMENTS.md AI-03 — não alterar

### Formato da resposta do Claude Haiku
- Resposta em JSON estruturado forçado via system prompt + `prefill` com `[`
- Schema esperado: `[{"start_time": N, "end_time": N, "score": N, "reason": "..."}]`
- Fallback: se parse falhar, marcar vídeo como `failed` e logar a resposta bruta para diagnóstico

### Claude's Discretion
- Prompt exato para o Haiku (linguagem, exemplos, instruções de formatação)
- Implementação do merge de overlaps (algoritmo interno)
- Tratamento de transcrições muito longas (chunking se necessário)
- Estrutura interna dos módulos transcriber.py e selector.py

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `clip-processor/src/db.py`: `update_status(conn, video_id, status)` já implementado — reutilizar para transições `transcribing` e `selecting`
- `clip-processor/src/main.py`: daemon BlockingScheduler já rodando — a chamada de transcrição entra no fluxo do `poll_all_channels`
- `clip-processor/requirements.txt`: `anthropic` e `groq` já instalados — sem novas dependências a adicionar
- `clip-processor/tests/conftest.py`: fixtures `mock_db_conn`, `sample_video_id` já existem — reutilizar nos novos testes

### Established Patterns
- Status flow MySQL ENUM: `downloaded` → `transcribing` → `selecting` → (próximas fases) — estados já existem, não criar novos
- Módulos independentes: cada responsabilidade em arquivo separado (`dedup.py`, `downloader.py`, `rss_poller.py`) — seguir mesmo padrão com `transcriber.py` e `selector.py`
- Injeção de dependência nos testes: funções aceitam `db_conn` opcional (None = produção, injetado = teste)
- Logs em stdout: `[YYYY-MM-DD HH:MM:SS] [TAG] mensagem` — usar tag `[AI]` para transcrição/seleção

### Integration Points
- `source_videos` tabela: adicionar coluna `transcript_path VARCHAR(500)` — armazena caminho do JSON em disco
- `generated_clips` tabela (já existe no schema Fase 1): inserir momentos selecionados com `status = 'pending_cut'`
- `GROQ_API_KEY` já no `.env` e no container — usar para Whisper API
- `ANTHROPIC_API_KEY` no `.env` (vazia até agora) — configurar e usar para Claude Haiku nesta fase
- Volume `./canaldecortes/videos:/app/videos` já montado — JSONs de transcrição ficam no mesmo diretório

</code_context>

<specifics>
## Specific Ideas

- Conteúdo-alvo explícito: futebol (análise, gol + reação, debate) e podcasts de tópicos variados
- "5-10 minutos por clip" — diferente de Shorts curtos; formato horizontal, mais longo
- Objetivo de publicação: 2-3 vídeos/dia entre as duas categorias de conteúdo

</specifics>

<deferred>
## Deferred Ideas

- **Reposting de cortes prontos** — Pegar vídeo curto de outro canal, criar nova thumbnail com título chamativo e repostar com créditos. É um pipeline diferente (sem transcrição). Candidato a fase futura (ex: Phase 5.1) ou v2.
- **Estratégia de conteúdo por horário** — Agendar posts no horário de maior audiência (19h-22h) — já está no escopo da Fase 5 (PUB-03).
- **Detecção de momentos por pico de volume de áudio** — Complementar à análise textual do Haiku. Alinhado com OPT-03 (v2).

</deferred>

---

*Phase: 03-ia-transcri-o-e-sele-o*
*Context gathered: 2026-06-18*
