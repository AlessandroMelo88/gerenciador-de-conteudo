# Roadmap: Canal de Cortes — Futebol & Esportes

## Overview

O pipeline é construído de baixo para cima: a infraestrutura Docker e o canal do YouTube são criados primeiro, depois a aquisição de vídeos, depois o processamento com IA, depois a edição final de vídeo e, por último, a publicação automatizada fecha o ciclo end-to-end. Cada fase entrega uma capacidade verificável antes da próxima começar — nenhuma fase depende de código da fase seguinte.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Infraestrutura Base** - Docker services, MySQL schema, canal do YouTube e secrets prontos
- [ ] **Phase 2: Aquisição de Vídeos** - Monitor RSS, download yt-dlp, deduplicação e rastreamento de jobs
- [ ] **Phase 3: IA — Transcrição e Seleção** - faster-whisper transcreve, Claude Haiku seleciona melhores momentos
- [ ] **Phase 4: Processamento de Vídeo** - FFmpeg corta, redimensiona 9:16, queima legendas e gera thumbnail + metadados
- [ ] **Phase 5: Publicação e Automação Total** - Upload YouTube API, quota management, agendamento e workflow n8n end-to-end

## Phase Details

### Phase 1: Infraestrutura Base
**Goal**: Todos os serviços necessários rodam no Docker, o banco de dados está criado, o canal do YouTube está pronto para receber uploads e todas as credenciais estão configuradas
**Depends on**: Nothing (first phase)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04
**Success Criteria** (what must be TRUE):
  1. `docker-compose up` sobe n8n, clip-processor e whisper sem erros, ao lado dos serviços já existentes (nginx, PHP, MySQL, Redis)
  2. Banco `clips_automation` existe no MySQL com tabelas `source_channels`, `source_videos` e `generated_clips` verificáveis via SQL
  3. Canal do YouTube existe com conta verificada, banner e bio preenchidos — pronto para receber o primeiro vídeo
  4. Variáveis `.env` (Claude API key, YouTube OAuth credentials) estão carregadas e os serviços sobem sem erro de configuração faltando
**Plans**: 4 plans

Plans:
- [x] 01-01-PLAN.md — Estrutura de diretórios, docker-compose extension (n8n + clip-processor + whisper) e clip-processor Dockerfile
- [x] 01-02-PLAN.md — Schema SQL clips_automation (3 tabelas) e script validate-infra.sh
- [x] 01-03-PLAN.md — Gerar .env com secrets reais, subir serviços Docker e aplicar schema MySQL
- [x] 01-04-PLAN.md — Script OAuth YouTube, geração de token.json e verificação do canal

### Phase 2: Aquisição de Vídeos
**Goal**: O sistema detecta novos vídeos nos canais configurados, baixa automaticamente e registra cada job — sem reprocessar o que já foi processado
**Depends on**: Phase 1
**Requirements**: ACQU-01, ACQU-02, ACQU-03, ORC-02
**Success Criteria** (what must be TRUE):
  1. Ao adicionar um canal à tabela `source_channels`, novos vídeos são detectados via RSS dentro de 6 horas sem consumir cota da YouTube API
  2. Um vídeo detectado aparece baixado em 720p no diretório de trabalho dentro de minutos após a detecção
  3. Rodar o pipeline duas vezes no mesmo vídeo não resulta em download ou reprocessamento duplicado
  4. Cada vídeo tem um registro em `source_videos` com status `pending/downloading/downloaded/failed` atualizado em tempo real
**Plans**: TBD

### Phase 3: IA — Transcrição e Seleção
**Goal**: Áudio de qualquer vídeo baixado é transcrito localmente e os melhores momentos são identificados e filtrados pela IA antes de qualquer processamento de vídeo acontecer
**Depends on**: Phase 2
**Requirements**: AI-01, AI-02, AI-03
**Success Criteria** (what must be TRUE):
  1. Um vídeo em PT-BR processado pelo faster-whisper produz um arquivo de transcrição com texto e timestamps por segmento
  2. A transcrição enviada ao Claude Haiku retorna uma lista estruturada de momentos com score 1-10, timestamps de início/fim e motivo para cada momento
  3. Apenas momentos com score maior ou igual a 7 avançam para a fila de corte — momentos com score inferior são descartados e registrados
**Plans**: TBD

### Phase 4: Processamento de Vídeo
**Goal**: Cada momento selecionado pela IA vira um clip completo: cortado, no formato correto para Shorts, com legendas visíveis, thumbnail extraída e metadados prontos para publicação
**Depends on**: Phase 3
**Requirements**: VID-01, VID-02, VID-03, VID-04
**Success Criteria** (what must be TRUE):
  1. Um clip é cortado nos timestamps exatos da IA e exportado em 1080x1920 (9:16) compatível com YouTube Shorts
  2. As legendas geradas pelo Whisper aparecem queimadas no clip com fonte legível e bordas visíveis mesmo em fundo variado
  3. Uma thumbnail válida (frame extraído do clip) existe como arquivo de imagem pronto para upload
  4. Título (máximo 100 caracteres), descrição e tags otimizados para futebol/PT-BR foram gerados pelo Claude Haiku e estão associados ao clip
**Plans**: TBD

### Phase 5: Publicação e Automação Total
**Goal**: Clips processados são publicados automaticamente no YouTube respeitando cota e horários, o pipeline completo roda do RSS ao upload sem intervenção manual, e vídeos brutos são limpos após sucesso
**Depends on**: Phase 4
**Requirements**: PUB-01, PUB-02, PUB-03, PUB-04, ORC-01
**Success Criteria** (what must be TRUE):
  1. Um clip com metadados prontos é publicado no YouTube com título, descrição, tags e thumbnail via YouTube Data API v3 sem intervenção manual
  2. O sistema nunca excede 6 uploads por dia — quando o limite é atingido, uploads adicionais ficam na fila para o próximo dia
  3. Uploads são agendados automaticamente entre 19h e 22h horário de Brasília
  4. Após um upload bem-sucedido, o vídeo bruto original é deletado do disco e o status do job muda para `published`
  5. O workflow n8n dispara automaticamente a cada ciclo (RSS poll → download → transcrição → seleção → corte → upload) com retry em caso de falha em qualquer etapa
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Infraestrutura Base | 4/4 | Complete | 2026-06-18 |
| 2. Aquisição de Vídeos | 0/TBD | Not started | - |
| 3. IA — Transcrição e Seleção | 0/TBD | Not started | - |
| 4. Processamento de Vídeo | 0/TBD | Not started | - |
| 5. Publicação e Automação Total | 0/TBD | Not started | - |
