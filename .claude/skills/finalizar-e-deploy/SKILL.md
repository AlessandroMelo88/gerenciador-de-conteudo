---
name: finalizar-e-deploy
description: Use quando um serviço do Canal de Cortes terminou numa branch e precisa ir para produção — "terminei", "finaliza a branch", "manda pra produção", "faz o merge e o deploy", "sobe isso", "publica as correções". Roda testes, atualiza docs e grafo, faz merge na master, push para o GitHub e deploy a partir do que está no GitHub, e confere a versão no ar.
---

# Finalizar branch e fazer deploy

Fluxo único: **branch → testes → master → GitHub → servidor.** Produção roda a `master`; todo commit
passa pelo GitHub antes de chegar ao servidor. O `deploy.sh` bloqueia deploy fora da `master`, com
alteração não commitada ou com a `master` local diferente de `origin/master`.

Repositório: `/Users/alessandrobm1/develop/server/wordpress/canaldecortes`.
Branches em desenvolvimento que **não** entram na master até o usuário pedir: `afiliadas`, `afiliadas-fase2`.

## Passo a passo

Anunciar cada passo em uma linha. Parar e relatar na primeira falha — não contornar.

### 1. Conferir a branch

```bash
git rev-parse --abbrev-ref HEAD
git status --short --untracked-files=no
```

- Se já estiver na `master`, perguntar qual branch finalizar.
- Se a branch for `afiliadas` ou `afiliadas-fase2`, confirmar com o usuário antes de seguir.
- Alteração não commitada: mostrar o `git status` e perguntar se commita junto. Nunca descartar.

### 2. Testes da branch

Rodar só as suítes das áreas alteradas (`git diff --name-only master...HEAD`):

| Mudou em | Comando |
|---|---|
| `painel/` | `docker exec -w /var/www/html/painel php php artisan test` |
| `clip-processor/` | `C=$PWD/clip-processor; docker run --rm --network none -v "$C/src:/app/src" -v "$C/tests:/app/tests" -w /app --entrypoint python wordpress-clip-processor -m pytest -q -p no:cacheprovider` |
| `scripts/local_download_worker.py` | `python3 -m pytest scripts/test_local_download_worker.py -q` (em venv com pytest) |
| `affiliate-worker/` | `cd affiliate-worker && .venv/bin/python -m pytest -q` |

Falha nova → parar. Se o container `php` estiver parado ou o Docker travar (containers presos em
"Created"), avisar o usuário em vez de contornar (ver bug 8 em `Docs/sistema/BUGS.md`).

### 3. Documentação e grafo, ainda na branch

- Mudou regra, tela, rota, config ou fluxo → atualizar `Docs/` (skill `documentacao-viva`).
- `graphify update .` e commitar `graphify-out/` — o grafo modificado deixa a árvore suja e bloqueia o deploy.

### 4. Merge na master

```bash
git fetch origin --prune
git switch master
git merge --ff-only origin/master      # traz o que já está no GitHub
git merge --no-edit <branch>
```

Conflito entre a branch e a master: parar, listar os arquivos e resolver com o usuário.

### 5. Push para o GitHub

O repositório é **público**. Antes do push, varrer o que vai subir:

```bash
git diff --name-only origin/master..master | grep -Ei '(^|/)\.env($|\.)|\.pem$|\.key$|client_secret|token.*\.json|\.sqlite$|cookies' | grep -v '\.env\.example$'
git log -p origin/master..master | grep -E '^\+' | grep -E 'sk-ant-|gsk_|AIza|ghp_|github_pat_|PRIVATE KEY|APP_KEY=base64:|[0-9]{8,10}:AA[A-Za-z0-9_-]{30,}'
```

Qualquer ocorrência → parar e mostrar ao usuário (mascarado). Limpo:

```bash
git push origin master
```

**Push rejeitado porque o GitHub divergiu:** o usuário definiu que a máquina local prevalece. Mostrar os
commits que só existem no GitHub (`git log master..origin/master`), guardar uma tag de backup e só então
sobrescrever:

```bash
git tag backup/origin-master-$(date +%Y%m%d-%H%M) origin/master
git push origin --tags
git push --force-with-lease origin master
```

### 6. Deploy

```bash
./deploy.sh              # mudou algo em painel/resources → precisa do build do Vite
./deploy.sh --skip-vite  # só backend, Python, migrations ou docs
```

Antes, se o deploy vai reiniciar o `clip-processor`, conferir clip em trânsito
(`generated_clips.status IN ('cutting','publishing')`) — ver bug 11.

### 7. Conferir a versão no ar

```bash
ssh -i ~/.ssh/oracle-a1-2026-09-16.key ubuntu@129.80.236.185 cat /home/ubuntu/canaldecortes/REVISION
git rev-parse HEAD
curl -s -o /dev/null -w '%{http_code}\n' https://toolscut.alessandromelo.com.br/login
```

`commit` do REVISION tem que ser igual ao `HEAD` e o painel responder 200.

### 8. Relatório

Uma tabela curta: branch finalizada, testes (contagem), commit na master, push, deploy, REVISION e
status do painel. Lembrar que `afiliadas`/`afiliadas-fase2` precisam receber a master
(`git merge master`) antes do merge delas.

## Não fazer

- Deploy de outra branch, ou editar o `deploy.sh` para pular a trava.
- `git reset --hard`, `git clean` ou force push sem a tag de backup.
- Commitar `.env`, chave SSH, `client_secret`, token ou `database.sqlite`.
