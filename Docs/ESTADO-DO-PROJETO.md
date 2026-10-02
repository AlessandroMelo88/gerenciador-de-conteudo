# Estado do projeto — leia primeiro

**Última atualização:** 02/10/2026
**Produção:** commit `59b0eb1`, no ar em https://toolscut.alessandromelo.com.br

Este arquivo existe para uma conversa nova começar sabendo o que já foi feito e para onde se quer ir.
Ele resume e aponta; o detalhe fica nos arquivos citados. A lista completa do que está feito, em
andamento, planejado e pendente é o [`PROGRESSO.md`](PROGRESSO.md) — não é duplicada aqui.

---

## 0. Para onde vamos

> A intenção, não o histórico. Mantida pelo dono do projeto.
> **Rascunho — confirmar.**

**Objetivo do produto.** Operação de canais de corte no YouTube que roda quase sozinha: o robô acha
vídeo novo nos canais-fonte, transcreve, escolhe os melhores trechos com IA, corta, legenda e publica.
O operador entra só para aprovar ou rejeitar na fila. Dois canais destino hoje: Futebol em Cortes e
Fatos & Debates (política).

**Fase atual.** Sair da dependência da monetização do YouTube. O pipeline de vídeo está estável na VM
nova; o esforço agora é receita por afiliados e conteúdo próprio.

**Próximos passos, em ordem:**

1. **Primeira oferta real de afiliado.** O sistema está em produção com 0 ofertas. Falta cadastrar uma
   oferta de verdade e validar o caminho inteiro: aprovar, copiar o link rastreável, conferir o clique.
2. **Canais do Telegram** criados e com o bot como administrador, para a divulgação automática.
3. **Domínio Umbrella Solutions**: DNS, vhost, certificado e logo. O tema já troca pelo host.
4. ~~Deploy das correções dos bugs 11, 4 e 17~~ — feito em 01/10/2026 (`99fbba4`). Em seu lugar: decidir
   os planos novos de `Docs/planos/` (revisão de palavrão, vídeo longo por canal) e responder a PR #1.
5. Cursos e produto próprio.

**Fora de escopo por enquanto:** separar as contas Google dos dois canais (decidido adiar em
16/09/2026); reescrever o pipeline em framework Python.

## 1. Onde está cada coisa

| Preciso de… | Arquivo |
|---|---|
| O que foi feito, o que falta, o que é ideia | `Docs/PROGRESSO.md` |
| Índice de toda a documentação (por tipo: sistema, operacao, planos, adr, estudos, historico) | `Docs/README.md` e `Docs/sistema/README.md` |
| Decisões estratégicas e ordem das fases | `Docs/planos/PLANO-MESTRE.md` |
| Bugs, com status e histórico de incidente | `Docs/operacao/BUGS.md` |
| Como o pipeline funciona por dentro | `Docs/sistema/SISTEMA-CLIP-PROCESSOR.md` |
| Afiliados (ofertas, API, worker, Telegram) | `Docs/sistema/SISTEMA-AFILIADOS.md` |
| Deploy e regra de branch | `DEPLOY.md` e skill `.claude/skills/gitflow` |
| Migração para a VM A1 | `Docs/planos/MIGRACAO-A1.md` |
| Comandos de operação e destrave | `Docs/operacao/RUNBOOK.md` |
| Regras destrutivas e armadilhas | `CLAUDE.md` |
| Lint, testes locais e CI | `Docs/operacao/DESENVOLVIMENTO.md` (`make help`) |

## 2. Produção

| | |
|---|---|
| Servidor | VM Oracle A1 `129.80.236.185` (2 OCPU, 12 GB), desde 17/09/2026 |
| Banco | PostgreSQL 17, base `clips_automation` |
| Vídeos | volume dedicado em `/mnt/videos` (147 GB) |
| Acesso | chave SSH em `~/.ssh/oracle-a1-2026-09-16.key`; segredos no `.env` do servidor, fora do git |
| Deploy | `./deploy.sh` a partir da `master`; grava `REVISION` no servidor |
| Backups | dump diário do PostgreSQL em `/mnt/videos/backups` |
| Downloads | worker no Mac (`scripts/local_download_worker.py`), porque o IP do servidor é bloqueado pelo YouTube |

A VM antiga (E2.1.Micro, 1 GB) virou rollback.

## 3. Linha do tempo

| Fase | Período | O que foi |
|---|---|---|
| Início | 17/06/2026 | Primeiro commit; pipeline de corte |
| Painel | ago/2026 | Laravel + Inertia + React 19 + shadcn |
| Estabilização | ago–set/2026 | Bugs de disco, estados presos, recuperação automática |
| Direitos autorais | 14–15/09/2026 | Advertência da Supernova; emissoras desativadas; fontes de baixo risco |
| Afiliados | 15–18/09/2026 | Ofertas, API, worker, Telegram, tela de performance, tema Umbrella |
| Migração A1 | 17/09/2026 | VM nova, PostgreSQL, disco dedicado |
| Transcrições | 17–18/09/2026 | Base de conhecimento, extensão do Chrome, download de mídia |

## 4. Decisões que custaram caro para descobrir

- **Produção roda a `master`, e só o que está no GitHub vai para o servidor.** O `deploy.sh` recusa
  qualquer outro caminho. Gitflow obrigatório, inclusive para uma linha.
- **Janela de download = 10 vídeos por canal destino ativo.** Sem esse teto o worker baixou 306 vídeos
  num dia e encheu o disco, derrubando o painel (bug 12).
- **Rejeitar clip só apaga arquivo pelo sidecar.** O container `php` monta os vídeos como somente
  leitura; o `Storage::delete` falhava calado (bug 13).
- **Corte curto: descarta abaixo de 15 s, estica de 15 s a 30 s, teto de 180 s.** Clip de 2–5 s não tem
  assunto.
- **Nada de burlar detecção de direitos autorais.** O que muda o risco é a fonte: programa falado em vez
  de imagem de emissora.
- **PostgreSQL no lugar do MySQL.** O suporte já existia no código; a produção migrou junto com a VM.

## 5. Armadilhas operacionais

- `public/hot` do Vite em produção deixa a página em branco, com o backend respondendo 200. O
  `deploy.sh` já apaga, mas o monitor por status não pega (18/09/2026).
- Apagar as chaves `video:*` do Redis ressuscita todo o backlog no próximo poll RSS.
- Rodar a suíte contra o banco de produção deixa conta de teste com senha padrão (bug 14).
- Testes de Telegram dependem de `TELEGRAM_BOT_TOKEN` no `.env`; sem ele falham 8 testes sem ser
  regressão de código.
- `deploy.sh` faz `up -d --no-recreate` + `restart`: **não relê o `.env`**. Mudou variável (cota, etc.)? No servidor: `docker compose up -d --force-recreate --no-deps clip-processor php` (só com `publishing = 0`; `cutting` volta a `pending_cut` no boot) e depois `docker exec nginx nginx -s reload`, senão o painel dá 502 (IP novo do php). A variável também precisa estar no `environment:` do `docker-compose.yml`, senão não chega ao container (01/10/2026).
- `docker system prune` já apagou o `clip-processor` inteiro junto com os logs da falha.

## 6. Em aberto

| Item | Origem | Estado |
|---|---|---|
| Nenhuma oferta de afiliado cadastrada | Fase 6 | Sistema no ar, 0 ofertas, token já configurado |
| Canais do Telegram e bot como admin | Fase 8 | Pendente do operador |
| Domínio e logo da Umbrella | Fase 7 | Código pronto, falta DNS/certificado |
| Busca vetorial nas transcrições | 30/09 | **No ar.** Postgres com pgvector 0.8 (imagem própria sobre alpine), `embedder` saudável (e5-small, 384d), 2 transcrições / 41 trechos indexados. O launchd do worker do Mac (`com.canaldecortes.downloader`) roda desde 01/10/2026 com o python do venv `~/.config/canaldecortes/venv-busca`, então transcrições novas já ganham vetor (backup do plist em `~/.config/canaldecortes/`). Doc: `Docs/sistema/SISTEMA-BUSCA-TRANSCRICOES.md` |
| Integração da branch do Ricardo (`release/rico`) | 30/09 | Lotes 1–9 na `master` e em produção. Fora: Hacker Libertário (não é do dono), stage workers, captions via API interna, seletor com janelas distribuídas, painel de perfis por canal destino. PR #1 dele ainda aberta no GitHub (responder/fechar). Não trazer compose, `composer.lock`, docs nem defaults de publicação dele |
| Token do Telegram no histórico público (`.planning/.../09-01-PLAN.md`, commit `614092d`) | Comparação 29/09 | Token rotacionado em 30/09 (ver §8) e arquivo sanitizado em `5be2b2d`; o valor antigo continua no histórico público do git, inofensivo depois de rotacionado. Operador: confirmar a rotação no BotFather e dar baixa |
| Transcrição de aula Hotmart (HLS, só áudio) | 30/09 | **Validada em 01/10/2026** numa aula real (28 min transcritos). O Hotmart serve o vídeo pela Panda Video (`*.tv.pandavideo.com.br`), não por `hotmart.com`; extensão 1.1.1 e API local aceitam os dois hosts. Outro player = ajustar `SUFIXOS_PLAYER`, `host_permissions` e `MEDIA_HOSTS_PADRAO` (ver `Docs/sistema/SISTEMA-TRANSCRICAO.md`). Falta só ligar o launchd do worker ao venv da busca |
| Longo por canal destino + cota 10/dia + métricas | 01/10 | **No ar (`59b0eb1`).** Campo "Formato dos vídeos" em Canais Destino (`auto`, `short_only`, `both`); todos os canais seguem em `auto`. Cota no servidor: `MAX_UPLOADS_PER_DAY=10`, longos 4, curtos 6, espaçamento 15 min (backup `.env.bak-20261001`). Tela Métricas em `/painel/metricas` (coleta a cada hora). **Falta:** o dono trocar o futebol para `both` no painel; ligar `longo_teto_atingido` no worker de download. Plano: `Docs/planos/PLANO-LONGO-POR-CANAL.md` |
| Bugs 11, 4 e 17 (SIGTERM, recuperação de `cutting`/`publishing`/`transcribing`, vaga presa por aprovação) | `BUGS.md` | **Corrigidos e no ar em 01/10/2026 (`99fbba4`).** `docker stop clip-processor` conferido em produção: exit 0 e log "Scheduler encerrado". Bug 17 foi decisão: `pending` continua contando na janela (proteção de disco, bug 12); teto separado fica como alternativa de produto. Risco a vigiar: `cutting` volta a `pending_cut` após 3 h sem `updated_at` |
| Retenção por clip (SPEC-001) | 02/10 | Implementada em `feature/retencao-youtube-analytics`, 10 tarefas, 20 testes novos no pipeline e 5 no painel; suíte do clip-processor em 523 passando. **Fora de produção.** Falta merge, deploy, o dono reautorizar os canais com `yt-analytics.readonly` e rodar `python -m src.retention_backfill --dias 400` |
| Revisão de palavrão com JEV (SPEC-002) | 02/10 | Spec e plano na `master`; integração nasce **desligada** (`jev_enabled=false`). Implementação delegada a outra sessão |
| `queue_controls.py:24` lê `system_settings` com crase (MySQL) | 02/10 | **Bug vivo:** em PostgreSQL a consulta falha, o `except` engole e `allow_local_download` é sempre `false`. Não virou issue ainda |
| Banco local 7 migrations atrás da produção | 02/10 | As 5 sem pgvector foram aplicadas em 02/10. Faltam as duas da busca vetorial: a imagem em uso no Mac é `postgres:17.2-alpine`, sem a extensão |
| Bug 10 — 287 `clip_path` sem arquivo | `BUGS.md` | Aberto (número não reconferido após a migração) |
| Bug 6 — painel não apaga backlog de download | `BUGS.md` | Aberto |
| Monitor do Better Stack por palavra-chave | Incidente 18/09 | Sugerido, não feito |
| Senhas antigas no histórico público do git | Bug 16 | Rotacionadas; reescrita de histórico adiada |
| 3 branches locais já mescladas | Gitflow | `feature/fontes-seguras-futebol`, `fix/pendencias-fontes-e-seletor`, `fix/bug17-finaliza-video-rejeitado` |

## 7. Como começar uma rodada nova

1. Ler este arquivo.
2. Conferir produção: `ssh -i ~/.ssh/oracle-a1-2026-09-16.key ubuntu@129.80.236.185 cat /home/ubuntu/canaldecortes/REVISION`
   e `curl -s https://toolscut.alessandromelo.com.br/login | grep -c build/assets/app-` (tem que dar 1).
3. Sair da `master` atualizada e abrir branch com prefixo (skill `gitflow`).
4. Verificação antes de dizer que terminou:
   - painel: `php artisan test` (ou `vendor/bin/pest`) contra PostgreSQL;
   - pipeline: `pytest` dentro da imagem `wordpress-clip-processor`;
   - worker de afiliados: `pytest` em `affiliate-worker/`.
5. Ao terminar: atualizar este arquivo e usar a skill `finalizar-e-deploy`.

## 8. Registro de checkpoints

| Data | Rodada | Onde parou | Próximo passo combinado |
|---|---|---|---|
| 02/10/2026 | Retenção do YouTube Analytics (SPEC-001) implementada; spec e plano do JEV escritos; limpeza de branches | 10 tarefas feitas em `feature/retencao-youtube-analytics`, fora de produção; docs do JEV na `master` | Merge e deploy da retenção; reautorizar os canais no Google e rodar o backfill; decidir o `.gitignore` do graphify |
| 01/10/2026 | Longo por canal, cota 10/dia, revezamento e métricas no ar; PR #1 do Ricardo fechada com comentário; launchd do Mac no venv da busca; plano de palavrão registrado | Produção em `59b0eb1`, env de cota aplicado, tudo em `auto` | Trocar o futebol para `both` no painel e acompanhar a tela Métricas; reorganização dos docs aguarda merge (`docs/organizar-documentacao`) |
| 01/10/2026 | Reorganização de `Docs/` (`docs/organizar-documentacao`) | Docs por tipo (`sistema/`, `operacao/`, `planos/`, `historico/`, `estudos/`), `Docs/PROGRESSO.md` criado, `**Status:**` em cada plano, links conferidos por `scripts/check-doc-links.py`. Em branch, sem merge | Dono revisa e mescla; manter o PROGRESSO.md a cada rodada |
| 30/09/2026 | Áudio HLS do Hotmart via extensão (`feature/transcricao-audio-hls-extensao`) | Extensão captura o m3u8, API local guarda em `media-urls.json` (0600), worker baixa só o áudio; testes unitários passam, nada validado no Hotmart real | Dono recarrega a extensão, reinicia o worker e testa uma aula; depois merge |
| 30/09/2026 | Validação visual da busca (`fix/busca-transcricoes-ui`) | 5 bugs de UI/backend corrigidos, piso de similaridade calibrado (0,83); branch pronta para merge, ainda fora de produção | Merge na master, depois o runbook de rollout (imagem do Postgres, embedder, backfill) |
| 30/09/2026 | Lote 6 (prompts por perfil) do `release/rico` | Em `feature/prompts-por-perfil`, sem merge/deploy; sem canal versionado; migration pendente | Escrever `prompts/channels/mbl.yaml`, compilar `--apply`, ligar perfil no painel |
| 30/09/2026 | Lotes 3 e 9 do Ricardo | CI, Makefile, pre-commit e configs de lint sem reformatar o código; ADRs renumerados (0002–0007, PostgreSQL 17), `Docs/operacao/DESENVOLVIMENTO.md`, `restore-postgres.sh`. Em branches, sem merge | Revisar, mesclar e ligar o `CI gate` na proteção da `master` |
| 01/10/2026 | Bugs 11, 4 e 17 no ar; extensão 1.1.1 com host Panda Video; transcrição Hotmart validada | Produção em `99fbba4`, `docker stop` com exit 0, aula do Hotmart transcrita | Primeira oferta de afiliado; decidir e responder a PR #1 do Ricardo (worker do Mac já no venv da busca) |
| 30/09/2026 | Produção em `ace7714`: pgvector, embedder, lotes 1–9 do Ricardo, watchdog sem falso deadlock (janela cheia por aprovação é proposital), transcrição Hotmart só áudio (extensão 1.1.0, **não testada no Chrome**) | Token do Telegram rotacionado e webhook com segredo | Testar a extensão numa aula real; ligar o worker do Mac ao venv da busca; responder a PR #1 |
| 29/09/2026 | Busca vetorial + comparação com `release/rico` | Busca pronta em `feature/busca-vetorial`, fora de produção; lotes 1–2 do Ricardo em branches | Backup + trocar imagem do Postgres na A1, deploy, backfill; rotacionar token do Telegram |
| 20/09/2026 | Criação deste checkpoint | Produção em `3cc729b`, saudável: 141 clips publicados, 16 na fila de aprovação, 18 vídeos na janela, 0 ofertas | Cadastrar a primeira oferta real de afiliado |
| 18/09/2026 | Afiliados na master, modo manutenção, hotfix do Vite | Afiliados em produção com token configurado | Criar canais do Telegram |
| 17/09/2026 | Migração para a VM A1 | Produção em PostgreSQL, disco dedicado | Encerrar a VM antiga depois do período de rollback |
