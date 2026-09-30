# Transcrições completas por assunto Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task by task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persistir as transcrições completas de Hacker Libertário organizadas por assuntos cronológicos, começando pelos vídeos de Fabio Akita.

**Architecture:** Manter `transcript_text` e `transcript_data` como registro canônico em `source_videos`; salvar os grupos numa tabela filha PostgreSQL. O processador usa o provedor de IA já configurado para identificar intervalos e reconstrói o texto dos grupos diretamente dos segmentos originais. Uma falha temática mantém a transcrição intacta e deixa o vídeo elegível para uma nova tentativa.

**Tech Stack:** PostgreSQL 18.3 nativo para o cron local do Hacker Libertário, Laravel migrations/Eloquent, Python, Groq ou Anthropic conforme `AI_PROVIDER`, yt-dlp e Groq Whisper já usados pelo projeto. Produção PostgreSQL 17 é um ambiente separado.

**Spec:** `docs/superpowers/specs/2026-09-29-transcricoes-por-assunto-design.md`

## Global Constraints

- Usar o PostgreSQL existente `clips_automation`; não criar outro banco.
- Preservar `source_videos.transcript_text` e `source_videos.transcript_data` como transcrição integral canônica.
- O modelo de IA devolve somente títulos e intervalos; o texto é remontado dos segmentos originais.
- A falha de segmentação não pode falhar o pipeline de cortes nem descartar a transcrição.
- Arquivos brutos só podem ser removidos pelo backfill após confirmação de que a transcrição integral foi salva no banco.
- Trabalhar diretamente em `release/rico`, sem abrir branch; fazer commit apenas dos arquivos/hunks deste plano.
- Preservar alterações paralelas existentes, sobretudo nos arquivos Python, migrations, `docker-compose.yml` e documentação.
- Não adicionar nem executar testes automatizados sem pedido explícito para testar/verificar; revisar os diffs sem alegar cobertura de testes.
- Não iniciar consumidores do Compose enquanto a referência inválida ao volume `videos` persistir.

## Review Focus

- Segmento omitido, repetido ou fora de ordem pela IA: rejeitar o resultado antes de substituir grupos.
- Transcrição maior que o limite de contexto: cobrir todos os segmentos em blocos com contexto de fronteira e índices globais.
- Falha da IA após salvar a transcrição: deixar texto e JSON consultáveis, status temático recuperável e cortes seguirem seu fluxo.
- Regravação de sidecar idêntico durante recuperação: não invalidar nem apagar tópicos já corretos.
- Vídeo sem captions e sem transcrição: tentar obter mídia apenas no backfill explícito; conservar o raw se a persistência integral falhar.

---

### Task 1: Schema e relação Laravel

**Files:**
- Create: `painel/database/migrations/2026_09_29_020000_create_source_video_topics_table.php`
- Create: `painel/app/Models/SourceVideoTopic.php`
- Modify: `painel/app/Models/SourceVideo.php`

**Interfaces:**
- Produces: `SourceVideo::topics(): HasMany`, ordenada por `position`.
- Produces: tabela `source_video_topics` com `source_video_id`, `position`, `title`, `start_seconds`, `end_seconds`, `first_segment_index`, `last_segment_index`, `transcript_text`, `created_at` e `updated_at`.
- Produces: `source_videos.topic_segmentation_status` (`not_ready`, `pending`, `processing`, `completed`, `failed`) e `topic_segmentation_error` nullable.

- [ ] **Step 1: Criar migration idempotente**

Criar a tabela filha com FK sem cascade, unicidade `(source_video_id, position)`, índice por `(source_video_id, position)` e checagens `end_seconds >= start_seconds` e `last_segment_index >= first_segment_index`. Adicionar os dois campos de estado a `source_videos`; preencher como `pending` apenas vídeos já portadores de transcript não vazio e deixar os demais em `not_ready`.

- [ ] **Step 2: Criar modelo e relação Eloquent**

Criar `SourceVideoTopic` com tabela, `$fillable` e casts numéricos necessários. Adicionar `topics()` a `SourceVideo`, usando `hasMany(SourceVideoTopic::class, 'source_video_id')->orderBy('position')`.

### Task 2: Segmentação validada e persistência Python

**Files:**
- Create: `clip-processor/src/topic_segmenter.py`
- Modify: `clip-processor/src/transcriber.py`

**Interfaces:**
- Produces: `segment_transcript_topics(transcript: dict, ai_client=None) -> list[dict]`.
- Cada item produzido contém `position`, `title`, `start_seconds`, `end_seconds`, `first_segment_index`, `last_segment_index` e `transcript_text`.
- Produces: `process_transcript_topics(conn, source_video_id: int, transcript: dict, ai_client=None) -> bool`.

- [ ] **Step 1: Implementar divisão em blocos e classificação**

Preparar os segmentos com índices globais. Limitar cada bloco por tamanho de entrada, mantendo segmentos de contexto nas bordas e atribuindo a cada resposta apenas uma faixa central sem sobreposição. Usar `AI_PROVIDER` e os provedores existentes (Groq/Anthropic), sem adicionar chamada à API OpenAI.

- [ ] **Step 2: Validar cobertura e reconstruir os grupos**

Rejeitar JSON inválido, intervalos vazios, títulos vazios, índices ausentes/duplicados/fora do bloco e ordenação inconsistente. Exigir cobertura exata de todos os segmentos não vazios uma vez. Mesclar faixas adjacentes com o mesmo título normalizado; derivar limites e texto apenas dos segmentos originais.

- [ ] **Step 3: Implementar substituição atômica e estados**

Marcar `processing`; após validação, em uma transação substituir os grupos antigos e marcar `completed`, limpando erro. Em qualquer exceção, fazer rollback dos grupos, marcar `failed` com mensagem limitada e retornar `False`; nunca alterar a transcrição canônica.

- [ ] **Step 4: Evitar invalidação de grupos quando o transcript salvo for idêntico**

Em `save_transcript`, comparar o `transcript_data` existente com o transcript recebido. Se mudou, atualizar os campos canônicos, limpar grupos anteriores e colocar o estado em `pending` na mesma transação PostgreSQL. Gravar o sidecar por arquivo temporário e `os.replace` após o commit; falha no banco mantém o sidecar anterior. Se for o mesmo JSON, preservar grupos e estado atuais. Não remover arquivo temporário antes da persistência integral.

### Task 3: Integração com a ingestão

**Files:**
- Modify: `clip-processor/src/rss_poller.py`
- Modify: `clip-processor/src/transcriber.py` (se necessário para o estado de transcript idêntico/alterado da Task 2)

**Interfaces:**
- Consumes: `process_transcript_topics` da Task 2.
- Produces: a etapa temática chamada depois de `save_transcript` e antes da seleção de cortes.

- [ ] **Step 1: Integrar segmentação após arquivamento**

Depois de salvar a transcrição, chamar `process_transcript_topics(conn, source_video_id, transcript, anthropic_client)`. Se retornar `False`, registrar o erro e continuar a seleção/publicação conforme o fluxo atual; não marcar `source_videos.status='failed'` por falha exclusivamente temática.

### Task 4: Backfill isolado de Fabio Akita

**Files:**
- Create: `scripts/backfill_source_video_topics.py`

**Interfaces:**
- Consumes: conexão do projeto via `src.db.get_db_connection`, `download_video`, `transcribe_video`, `save_transcript` e `process_transcript_topics`.
- Produces: comando seguro com `--dry-run` como padrão e `--apply` obrigatório para gravar/baixar; escopo pelo `youtube_channel_id` do Fabio Akita.

- [ ] **Step 1: Selecionar vídeos do canal e classificar transcrições existentes**

Resolver o canal por `youtube_channel_id=UCib793mnUOhWymCh2VJKplQ`; não codificar o ID interno local. Selecionar transcripts com estado temático `pending` ou `failed` para permitir retry, além de vídeos com transcript ausente. No modo dry-run, listar totais com transcript pronto, segmentação pendente/concluída e transcript ausente, sem chamar IA ou baixar mídia.

- [ ] **Step 2: Implementar execução de backfill**

Para transcripts completos, segmentar sem baixar o raw. Para vídeos sem transcript, tentar primeiro captions disponíveis pelo helper existente; sem captions utilizáveis, baixar para caminho temporário e transcrever. Persistir texto e segmentos integralmente antes de segmentar; apagar o raw temporário só depois da confirmação da gravação. Se falhar transcrição/persistência, conservar o raw e deixar o vídeo marcado como sem transcript/pendente.

- [ ] **Step 3: Executar backfill autorizado**

Rodar o comando em `--apply` no banco local acessível após a migration, conferir os estados/contagens de transcript e grupos de Fabio Akita e registrar qualquer vídeo que permaneça sem transcript. Não iniciar os consumidores do Compose.

### Task 5: Revisão e commit no branch atual

**Files:** apenas os arquivos criados/modificados neste plano.

- [ ] **Step 1: Revisar alterações próprias e confirmar escopo do stage**

Inspecionar os diffs próprios e preparar o stage por caminho/hunk, sem incluir nenhuma alteração paralela pré-existente nos arquivos compartilhados.

- [ ] **Step 2: Commitar em `release/rico`**

Usar mensagem: `feat: persistir transcricoes por assunto`. Não criar branch. Registrar no resumo o hash do commit e o resultado operacional do backfill; não alegar testes executados.
