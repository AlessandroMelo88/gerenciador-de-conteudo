# Phase 6: Controle Manual N8N + Telegram - Context

**Gathered:** 2026-06-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Dar ao operador alavancas manuais sobre um pipeline que hoje é 100% autônomo — via comandos no Telegram orquestrados por workflows n8n. A automação continua existindo (RSS → download → transcribe → select → cut → metadata), mas um novo passo de **aprovação humana** entra entre a geração do clip e o upload: o `publisher.py` passa a publicar apenas clips com status `approved`. Edição de clips, busca por tema/tendências e gerenciamento via UI continuam fora do escopo.

</domain>

<decisions>
## Implementation Decisions

### Comandos v1

Apenas 6 comandos entram nesta fase:

- `/status` — métricas do pipeline (clips gerados hoje, quota usada, próximo upload agendado)
- `/clipes` — lista enxuta dos clips com status `pending`, formato `<id> | <título> | <duração>s`, máximo 10
- `/aprovar <id>` — muda status do clip de `pending` para `approved` (um por vez, sem lote)
- `/rejeitar <id>` — muda status para `rejected`, apaga o MP4 do clip, **mantém o raw video** para recorte futuro
- `/processar <url>` — força download e pipeline de um vídeo arbitrário (inclusive de canais não monitorados): insere em `source_videos` com status `pending`, escapando do RSS
- `/ajuda` — lista os comandos

Comandos do README original que **não entram** (movidos para deferred): `/buscar`, `/trending`, `/fila`, `/publicar`, `/canal`.

### Schema MySQL — novos status

Migration adiciona dois valores ao ENUM da tabela `generated_clips`:

- `approved` — clip aprovado pelo operador, na fila para publicação
- `rejected` — clip rejeitado pelo operador (via comando) ou pelo TTL (auto)

Fluxos válidos:
- `pending → approved → publishing → published` (caminho feliz)
- `pending → rejected` (rejeição manual ou TTL)

`publisher.py` muda a query de seleção: hoje pega `pending`, passa a pegar `approved`.

### Manual × Automação

O bot é alavanca, não bypass. As regras existentes do pipeline continuam soberanas:

- **Quota:** máx 2 uploads/dia (configurável até 6) — `/aprovar` não força upload imediato
- **Janela horária:** 19h-22h America/Sao_Paulo — clips approved entram na fila e saem na próxima janela
- **Ordem:** publisher escolhe o próximo approved seguindo a lógica já existente (FIFO por created_at)

Não existe `/publicar` ou bypass de quota — protege o canal de strikes do YouTube.

### TTL de pending

- Clips em `pending` viram `rejected` automaticamente após **48 horas**
- Aviso proativo do bot **24 horas antes** da expiração ("Clip <id> expira em 24h")
- Worker de TTL roda periodicamente (cron do n8n ou tarefa APScheduler no clip-processor — definir na pesquisa)

### Segurança e acesso

- **Allowlist hardcoded:** apenas `chat_id=5760918317` é autorizado
- Comandos vindos de qualquer outro chat retornam silêncio (sem mensagem, para não revelar a existência do bot)
- **Exposição do webhook:** Cloudflare Tunnel apontando para `http://localhost:5678` do n8n
- Sem ngrok, sem IP público direto, sem porta aberta no firewall
- TLS terminado pelo Cloudflare

### Notificações proativas

O bot fala sozinho em **3 situações apenas**:

1. **Upload publicado com sucesso** — "✓ Clip <id> publicado: <url do YouTube>"
2. **Falha crítica no pipeline** — falhas em download/transcribe/select/cut/upload com detalhe do erro
3. **Resumo diário às 18h BRT** — "X clips aguardando aprovação" (skip se X=0)

Sem push em "novo clip pronto" individual — vira ruído quando o pipeline está saudável.

### Workflows n8n existentes

- `telegram-n8n/workflows/01-telegram-handler.json` — **reaproveitar** como base do roteador de webhook (361 linhas, já tem skeleton de parse de comando)
- `telegram-n8n/workflows/02-busca-videos.json` — **descartar** (escopo `/buscar` saiu do v1)
- `telegram-n8n/workflows/03-tendencias.json` — **descartar** (escopo `/trending` saiu do v1)
- `telegram-n8n/workflows/04-notificador-fila.json` — **descartar** (substituído pelo resumo diário + notificações pontuais)

Arquivos descartados ficam como referência histórica (não removidos), mas não são importados no n8n.

### /processar <url> — comportamento

- Aceita URL do YouTube (padrão `youtube.com/watch?v=<id>` ou `youtu.be/<id>`)
- Extrai `youtube_video_id`, busca metadata pública (título, channel_id) via YouTube Data API
- Insere/atualiza linha em `source_videos` com status `pending`
- Idempotente: se o vídeo já existe, retorna o status atual sem duplicar
- Pipeline normal cuida do resto (download → transcribe → select → cut → metadata → pending)
- **Não bypassa** nenhuma regra — vídeo entra na fila como qualquer outro

### Claude's Discretion

- Formato visual exato das mensagens do bot (emojis, quebras de linha, formatação Markdown vs HTML do Telegram)
- Layout do `/status` (quais métricas, ordem)
- Mensagem de erro padrão quando id inválido em `/aprovar`/`/rejeitar`
- Implementação técnica do worker de TTL (cron n8n vs APScheduler no clip-processor — pesquisar tradeoff)
- Estrutura interna dos workflows n8n (quantos sub-workflows, como reusar o roteador)
- Logging/auditoria das ações do bot (level, destino — stdout, arquivo, MySQL)

</decisions>

<specifics>
## Specific Ideas

- O fluxo se inspira em "moderação humana num pipeline autônomo" — clipes pré-cortados aguardam um nod humano antes de ir ao ar. Isso muda a definição de "100% automatizado" do PROJECT.md para "100% autônomo até a aprovação"; vale registrar essa evolução em STATE.md (Roadmap Evolution).
- O bot **não revela existência** para quem não está na allowlist — silêncio total em vez de "acesso negado".
- A janela 19h-22h BRT existente continua intocada — toda a UX dos comandos respeita isso.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets

- `clip-processor/src/publisher.py` — já implementa quota guard + janela horária + cleanup. Único ponto de mudança: trocar `WHERE status = 'pending'` por `WHERE status = 'approved'` na seleção
- `clip-processor/src/db.py` — DictCursor + connection lifecycle, padrão de uso já estabelecido
- `clip-processor/src/quota_manager.py` — Redis-based daily counter e janela 19h-22h America/Sao_Paulo (reuso direto pelo /status)
- `clip-processor/src/pipeline_runner.py` — uma execução completa do pipeline (chamado pelo APScheduler); /processar pode reusar via `INSERT ... ON DUPLICATE KEY` em source_videos
- `telegram-n8n/workflows/01-telegram-handler.json` — esqueleto de webhook handler + roteador (361 linhas)
- `n8n/workflows/canaldecortes-pipeline.json` — exemplo de workflow já com Telegram notification node + retry; mostra o padrão de credencial "Telegram Canal de Cortes"
- `telegram-n8n/SETUP.md` — passo a passo de bot creation, MySQL credential, webhook setup; aproveitar e atualizar (trocar ngrok por Cloudflare Tunnel)

### Established Patterns

- **Migrations:** alterações de schema versionadas em SQL files (padrão das fases anteriores)
- **Status enum em `source_videos` e `generated_clips`:** pipeline usa estados nomeados — não introduzir status novo fora do ENUM
- **APScheduler dentro do clip-processor:** Phase 5 estabeleceu APScheduler para jobs autônomos; TTL worker pode ser mais um job
- **Tests RED first:** Phase 02 mostrou padrão de imports no topo + ModuleNotFoundError como RED válido
- **Credenciais n8n:** referenciadas por nome ("Telegram Canal de Cortes", "MySQL Canal de Cortes") — não duplicar
- **Comando n8n via docker exec:** pipeline n8n hoje chama `docker exec clip-processor python -m src.pipeline_runner` — mesmo padrão serve para /processar

### Integration Points

- **MySQL `generated_clips`:** ENUM precisa de migration; publisher.py precisa do swap pending → approved
- **MySQL `source_videos`:** /processar insere/atualiza aqui
- **Telegram Bot API:** novo bot ou reusar `Canal de Cortes Bot` do SETUP.md
- **Cloudflare Tunnel:** novo serviço (não havia antes) — provavelmente container `cloudflared` no docker-compose ou serviço local rodando como agente
- **n8n credentials:** "Telegram Canal de Cortes" (já existe), "MySQL Canal de Cortes" (já existe)
- **`.env`:** novas variáveis — `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID_ALLOWED=5760918317`, `CLOUDFLARE_TUNNEL_TOKEN`, possivelmente `YOUTUBE_API_KEY` (caso /processar use Data API para buscar metadata)

</code_context>

<deferred>
## Deferred Ideas

Itens que apareceram na discussão ou estavam no rascunho original do `telegram-n8n/`, mas saem do v1 desta fase:

- `/buscar <tema>` — descoberta ativa de vídeos por tema via YouTube Data API search.list (alto custo de quota — 100 unidades/busca vs 10.000/dia totais)
- `/trending` — top assuntos em alta no futebol BR via Google Trends RSS
- `/fila` — visão da fila de upload (substituível por /clipes + /status)
- `/publicar` — upload imediato bypassando janela horária (deliberadamente recusado para proteger contra strikes)
- `/canal <URL>` — adicionar canal RSS ao pool de monitoramento via Telegram (manter por enquanto como edição direta da seed SQL)
- Inline keyboard de aprovar/rejeitar (1-tap UX) — ganha em ergonomia mas dobra a complexidade do workflow; passar quando o volume justificar
- Thumbnail do clip anexada em /clipes — útil mas come bandwidth e complica o handler
- Aprovação em lote (`/aprovar all` ou `/aprovar 1 2 3`) — adiar até sentir o atrito do 1-por-vez
- Cleanup imediato do raw video em /rejeitar — adiar para rotina dedicada de housekeeping
- Logging/auditoria em MySQL (tabela clip_approvals) — adiar; stdout + Telegram bastam no v1
- Dashboard web de aprovação (alternativa ao Telegram) — fora do escopo, possivelmente futuro
- Notificações OPT-04 mais ricas (email + Telegram) — esta fase cobre só Telegram

</deferred>

---

*Phase: 06-controle-manual-n8n-telegram*
*Context gathered: 2026-06-19*
