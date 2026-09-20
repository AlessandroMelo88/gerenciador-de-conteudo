# Estado do projeto — leia primeiro

**Última atualização:** 20/09/2026
**Produção:** commit `3cc729b`, no ar em https://toolscut.alessandromelo.com.br

Este arquivo existe para uma conversa nova começar sabendo o que já foi feito e para onde se quer ir.
Ele resume e aponta; o detalhe fica nos arquivos citados.

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
4. **Bugs 11 e 4** (SIGTERM e estados sem recuperação), que ainda prendem vaga da janela.
5. Cursos e produto próprio.

**Fora de escopo por enquanto:** separar as contas Google dos dois canais (decidido adiar em
16/09/2026); reescrever o pipeline em framework Python.

## 1. Onde está cada coisa

| Preciso de… | Arquivo |
|---|---|
| Índice de toda a documentação | `Docs/README.md` e `Docs/sistema/README.md` |
| Decisões estratégicas e ordem das fases | `Docs/sistema/PLANO-MESTRE.md` |
| Bugs, com status e histórico de incidente | `Docs/sistema/BUGS.md` |
| Como o pipeline funciona por dentro | `Docs/sistema/SISTEMA-CLIP-PROCESSOR.md` |
| Afiliados (ofertas, API, worker, Telegram) | `Docs/sistema/SISTEMA-AFILIADOS.md` |
| Deploy e regra de branch | `DEPLOY.md` e skill `.claude/skills/gitflow` |
| Migração para a VM A1 | `Docs/sistema/MIGRACAO-A1.md` |
| Comandos de operação e destrave | `Docs/sistema/RUNBOOK.md` |
| Regras destrutivas e armadilhas | `CLAUDE.md` |

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
- `docker system prune` já apagou o `clip-processor` inteiro junto com os logs da falha.

## 6. Em aberto

| Item | Origem | Estado |
|---|---|---|
| Nenhuma oferta de afiliado cadastrada | Fase 6 | Sistema no ar, 0 ofertas, token já configurado |
| Canais do Telegram e bot como admin | Fase 8 | Pendente do operador |
| Domínio e logo da Umbrella | Fase 7 | Código pronto, falta DNS/certificado |
| Bug 11 — container não honra SIGTERM | `BUGS.md` | Aberto; gera estado preso a cada restart |
| Bug 4 — `cutting` e `publishing` sem recuperação | `BUGS.md` | Parcial; `selecting` já tem |
| Bug 17 — vaga presa por clip aguardando aprovação | `BUGS.md` | Parcial; caso "todos rejeitados" resolvido |
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
| 20/09/2026 | Criação deste checkpoint | Produção em `3cc729b`, saudável: 141 clips publicados, 16 na fila de aprovação, 18 vídeos na janela, 0 ofertas | Cadastrar a primeira oferta real de afiliado |
| 18/09/2026 | Afiliados na master, modo manutenção, hotfix do Vite | Afiliados em produção com token configurado | Criar canais do Telegram |
| 17/09/2026 | Migração para a VM A1 | Produção em PostgreSQL, disco dedicado | Encerrar a VM antiga depois do período de rollback |
