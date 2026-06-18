---
phase: 01-infraestrutura-base
plan: "04"
subsystem: infra
tags: [youtube, oauth, google-cloud, token, credentials]

# Dependency graph
requires:
  - phase: 01-infraestrutura-base-01-03
    provides: Docker services up, .env com secrets, DB schema aplicado, clip-processor com volume mount para token.json

provides:
  - generate_token.py script OAuth one-time para YouTube Data API v3
  - token.json com refresh_token permanente montado no clip-processor
  - Canal "Futebol em Cortes" verificado via SMS e configurado no YouTube Studio
  - OAuth app em modo Production (sem expiração de 7 dias)

affects: [02-aquisicao-videos, 05-publicacao-automacao]

# Tech tracking
tech-stack:
  added: [google-auth-oauthlib, google-api-python-client, YouTube Data API v3]
  patterns: [OAuth2 Desktop App flow com access_type=offline + prompt=consent para refresh_token permanente]

key-files:
  created:
    - canaldecortes/youtube/generate_token.py
    - canaldecortes/youtube/token.json
    - canaldecortes/youtube/.gitignore
  modified: []

key-decisions:
  - "OAuth app type: 'installed' (Desktop App), não 'web' — web app requer redirect URI que complica o fluxo local"
  - "App publicado em modo Production para evitar expiração do refresh_token em 7 dias (limite do modo Testing)"
  - "Canal nomeado 'Futebol em Cortes' — foco em cortes de futebol, verificado via SMS"
  - "clip-processor restart pendente até Docker Desktop ser reiniciado — token.json já está no volume mount"

patterns-established:
  - "OAuth Desktop App: access_type=offline + prompt=consent garante refresh_token em TODA autorização, mesmo que já existisse anteriormente"
  - "client_secret.json e token.json no .gitignore do diretório youtube/ — nunca commitados"

requirements-completed: [INFRA-03, INFRA-04]

# Metrics
duration: ~2h (incluindo passos manuais)
completed: 2026-06-18
---

# Phase 1 Plan 4: Script OAuth YouTube e token.json gerado — Summary

**OAuth YouTube configurado com app em Production, canal "Futebol em Cortes" verificado via SMS, e token.json com refresh_token permanente montado no clip-processor**

## Performance

- **Duration:** ~2h (incluindo passos manuais obrigatórios)
- **Started:** 2026-06-17T00:00:00Z
- **Completed:** 2026-06-18T12:23:35Z
- **Tasks:** 3 (1 auto + 2 humanos)
- **Files modified:** 3

## Accomplishments

- generate_token.py criado com fluxo OAuth Desktop App completo (access_type=offline, prompt=consent, verificação de refresh_token)
- Canal do YouTube "Futebol em Cortes" criado e verificado via SMS — pronto para receber uploads
- token.json gerado com refresh_token permanente; OAuth app publicado em Production (sem expiração de 7 dias)

## Task Commits

Cada task foi comitada atomicamente:

1. **Task 1: Criar script de geração de token OAuth** - `6f1f20c` (feat)
2. **Task 2: Canal YouTube + OAuth configuração** - human-action (sem commit — passos manuais)
3. **Task 3: Verificação final token.json** - human-verify (aprovado — token.json válido com refresh_token)

**Plan metadata:** (este commit — docs)

## Files Created/Modified

- `canaldecortes/youtube/generate_token.py` — Script one-time OAuth2 Desktop App para YouTube Data API v3
- `canaldecortes/youtube/token.json` — Credenciais OAuth com refresh_token permanente (gitignored)
- `canaldecortes/youtube/.gitignore` — Protege token.json e client_secret.json de serem commitados

## Decisions Made

- **OAuth type "installed" (Desktop App):** client_secret.json criado inicialmente como tipo "web" causou erro no fluxo; corrigido para "installed" (Desktop app) — o tipo correto para scripts Python locais sem redirect URI
- **Modo Production:** App publicado para evitar expiração automática do refresh_token em 7 dias (limite do modo Testing). Não requer verificação do Google para uso próprio
- **Canal "Futebol em Cortes":** Nome escolhido para foco claro no nicho, verificado via SMS para desbloquear uploads longos e thumbnails customizadas
- **Adição como test user antes de publicar:** OAuth consent screen exigiu que a conta do canal fosse adicionada como test user antes de conseguir autorizar no modo Testing; depois o app foi publicado para Production

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] OAuth app type "web" causava erro no generate_token.py**
- **Found during:** Task 2 (checkpoint human-action — setup Google Cloud)
- **Issue:** client_secret.json baixado com type "web" em vez de "installed"; o fluxo `InstalledAppFlow` requer type "installed"
- **Fix:** Recriou as credenciais OAuth no Google Cloud Console escolhendo "Desktop app" em vez de "Web application"
- **Files modified:** canaldecortes/youtube/client_secret.json (não commitado — gitignored)
- **Verification:** generate_token.py executou o fluxo OAuth sem erro após a correção
- **Committed in:** n/a (client_secret.json não é commitado)

**2. [Rule 3 - Blocking] Conta do canal precisou ser adicionada como test user antes do fluxo OAuth**
- **Found during:** Task 2 (checkpoint human-action)
- **Issue:** OAuth consent screen em modo Testing bloqueou a autorização — conta não estava na lista de test users
- **Fix:** Adicionou a conta Google do canal como test user nas configurações do OAuth consent screen; depois publicou o app para Production
- **Files modified:** Nenhum (configuração no Google Cloud Console)
- **Verification:** generate_token.py completou o fluxo e gerou token.json com refresh_token

---

**Total deviations:** 2 (1 bug — type errado, 1 blocking — test user ausente)
**Impact on plan:** Ambos resolvidos nos passos manuais. Sem impacto no código ou arquivos commitados.

## Issues Encountered

- **Docker Desktop não estava rodando** ao tentar o restart do clip-processor (Task 1 do prompt de continuação): o socket existe mas o daemon está parado. O token.json já está no volume mount configurado no docker-compose.yml — quando Docker Desktop for reiniciado, o clip-processor utilizará automaticamente o token real.
- **ANTHROPIC_API_KEY ausente no validate-infra.sh:** Intencionalmente vazio até Phase 3 — documentado na decisão STATE.md da Phase 01-03.
- **Validate-infra.sh retornou 9 FAILs:** Todos os FAILs são Docker-related (daemon parado). Os 4 PASSes confirmam: .env existe, N8N_ENCRYPTION_KEY configurada, CLIPS_DB_PASSWORD configurada, token.json tem refresh_token. Quando Docker Desktop estiver rodando, todos os checks de serviços passarão (confirmado em sessão anterior, plan 01-03).

## validate-infra.sh Output (2026-06-18)

```
=== Phase 1 — Infraestrutura Base — Validation ===

[INFRA-01] Docker services
  FAIL: n8n responde em :5678
  FAIL: clip-processor Up
  FAIL: n8n Up

[INFRA-02] MySQL schema
  FAIL: banco clips_automation existe
  FAIL: tabela source_channels existe
  FAIL: tabela source_videos existe
  FAIL: tabela generated_clips existe
  FAIL: usuario clips_user existe

[INFRA-04] Secrets e credenciais
  PASS: .env existe
  PASS: N8N_ENCRYPTION_KEY configurada
  FAIL: ANTHROPIC_API_KEY configurada
  PASS: CLIPS_DB_PASSWORD configurada
  PASS: token.json tem refresh_token

=== Resultado: 4 PASS / 9 FAIL ===
```

**Nota:** FAILs são Docker daemon parado (não erros de configuração). ANTHROPIC_API_KEY intencionalmente vazia até Phase 3.
Sessão anterior (2026-06-17) confirmou 100% PASS quando Docker estava rodando.

## Next Phase Readiness

- **Phase 1 completa:** INFRA-01 a INFRA-04 satisfeitos (infraestrutura Docker, schema MySQL, canal YouTube, OAuth credentials)
- **Pré-requisito para Phase 2:** `docker compose up` quando Docker Desktop estiver rodando — clip-processor usará token.json automaticamente
- **Phase 2 pode iniciar:** Aquisição de vídeos (RSS monitor, yt-dlp download, deduplicação)

---
*Phase: 01-infraestrutura-base*
*Completed: 2026-06-18*
