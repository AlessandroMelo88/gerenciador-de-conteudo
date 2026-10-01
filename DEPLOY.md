# Guia de Deploy Rápido (Produção)

Este documento explica como funciona o deploy do **Canal de Cortes**, como executá-lo em **~20 segundos** e a arquitetura adotada para evitar travamentos e lentidão na VPS Oracle Cloud.

---

## 🌿 Produção = branch `master`, via GitHub

Regra fixa (15/09/2026): **branch → testes → `master` → GitHub → servidor.**

1. Todo trabalho acontece numa branch própria (`fix/...`, `feature/...`, `afiliadas`).
2. **Terminou o serviço → merge na `master`.** Ela tem tudo que está pronto; só fica fora o que ainda
   está em desenvolvimento (hoje: `afiliadas` e `afiliadas-fase2`).
3. **Push antes do deploy.** O `deploy.sh` só aceita a `master` sem alteração pendente e **idêntica a
   `origin/master`** — commit que não está no GitHub não chega ao servidor.
4. Conflito com o GitHub: a máquina local prevalece, com tag `backup/origin-master-<data>` antes do
   force push.

O fluxo inteiro está na skill **`finalizar-e-deploy`** (`.claude/skills/finalizar-e-deploy/SKILL.md`):
basta pedir "finaliza a branch e sobe". Manualmente:

```bash
git switch master
git merge <branch>
git push origin master
./deploy.sh
```

O servidor não tem git — o código chega por rsync. Para saber qual versão está no ar:

```bash
ssh -i ~/.ssh/oracle-a1-2026-09-16.key ubuntu@129.80.236.185 cat /home/ubuntu/canaldecortes/REVISION
```

`REVISION` traz `commit`, `branch` e `deployed_at`, gravados a cada deploy.

---

## ⚡ Como Fazer Deploy

Na pasta raiz do projeto no seu ambiente local, execute:

### 1. Deploy Padrão (~20 a 25 segundos)
Compila o frontend (Vite/React), sincroniza os arquivos de backend (PHP, Python, assets) e reinicia os serviços no servidor:
```bash
./deploy.sh
```

### 2. Deploy Ultrarrápido Backend (~8 a 12 segundos)
Se você **não** alterou nada no React/CSS do painel (apenas código Python, regras PHP, migrations ou assets de branding), pule a compilação do Vite:
```bash
./deploy.sh --skip-vite
```

### 3. Deploy com Rebuild do Docker (Apenas quando estritamente necessário)
Se você adicionou novas dependências no `requirements.txt` do Python ou novos pacotes no sistema operacional via `apt`:
```bash
./deploy.sh --build-docker
```
> ⚠️ **Atenção**: O `--build-docker` reconstrói a imagem base do Whisper e faz compilação C++, levando cerca de 10 a 15 minutos na VPS Oracle Micro. **Evite usar no dia a dia.**

---

## 🧭 Postgres com pgvector — troca da imagem (busca vetorial, 29/09/2026)

A busca semântica nas transcrições precisa da extensão `vector`. O serviço `postgres` do
`docker-compose.yml` passou a usar uma imagem própria (`docker/postgres/Dockerfile`:
`postgres:17-alpine` + pgvector `v0.8.0` compilado). Mesma base alpine, mesmo volume, mesma
collation — o volume `postgres_data` abre sem `pg_upgrade`.

**O deploy comum NÃO troca a imagem** (ele faz `up -d --no-recreate`). Faça esta troca à mão,
**antes** do deploy do código que traz as migrations (com a imagem antiga, a migration falha em
produção de propósito, com a mensagem "Extensão pgvector indisponível").

> ⛔ **NUNCA** `docker compose down -v` nem `docker volume rm`: o volume `postgres_data` **é** o banco.
> Recriar só o serviço `postgres` preserva o volume.

> ⚠️ **O `deploy.sh` só envia `docker-compose.yml` e `Dockerfile.php`** — não envia
> `docker/postgres/` nem `embedder/`, que o compose agora precisa para o `build:`. Sem esses
> diretórios no servidor, o `docker compose up -d` do deploy falha ao tentar construir o
> `embedder`. Enquanto o `deploy.sh` não aprender a enviá-los, faça o passo 0 abaixo.

No Mac, na raiz do projeto (passo 0):

```bash
rsync -rlz --no-perms --no-owner --no-group -e "ssh -i ~/.ssh/oracle-a1-2026-09-16.key" \
  docker/postgres/ ubuntu@129.80.236.185:/home/ubuntu/canaldecortes/docker/postgres/
rsync -rlz --no-perms --no-owner --no-group -e "ssh -i ~/.ssh/oracle-a1-2026-09-16.key" \
  --exclude '__pycache__' --exclude '.venv' embedder/ ubuntu@129.80.236.185:/home/ubuntu/canaldecortes/embedder/
rsync -z -e "ssh -i ~/.ssh/oracle-a1-2026-09-16.key" \
  docker-compose.yml ubuntu@129.80.236.185:/home/ubuntu/canaldecortes/
```

Na A1, dentro de `/home/ubuntu/canaldecortes`, nesta ordem:

```bash
# 1. dump manual em formato custom (não confiar só no dump diário das 06:15 UTC)
docker exec postgres pg_dump -U clips_user -d clips_automation -Fc \
  > /mnt/videos/backups/pre-pgvector-$(date +%F).dump
ls -lh /mnt/videos/backups/pre-pgvector-*.dump          # tamanho > 0; copie para o Mac (scp)

# 2. tag de backup do commit em produção (no Mac): git tag backup/pre-pgvector-AAAAMMDD && git push origin --tags

# 3. pausar quem escreve no banco
docker compose stop clip-processor
docker compose exec -T php php /var/www/html/painel/artisan down   # painel em manutenção

# 4. construir a imagem (compila o pgvector, ~2 min na A1) e recriar SÓ o postgres
docker compose build postgres
docker compose up -d --no-deps postgres
docker compose ps postgres                              # aguarde "healthy"

# 5. conferir que a extensão existe e que o banco abriu
docker exec postgres psql -U clips_user -d clips_automation \
  -c "SELECT name, default_version FROM pg_available_extensions WHERE name='vector'" \
  -c "SELECT count(*) FROM transcription_jobs"

# 6. religar
docker compose up -d clip-processor
docker compose exec -T php php /var/www/html/painel/artisan up
docker compose ps && docker compose logs --tail=30 postgres clip-processor
```

Indisponibilidade esperada: menos de 1 minuto (o reinício do Postgres). Se o Postgres não
subir, `docker compose logs postgres` primeiro; restauração do dump só em último caso
(`pg_restore -Fc --clean --if-exists -U clips_user -d clips_automation`).

Depois disso: `./deploy.sh` (roda as migrations `CREATE EXTENSION`, tabela e índices), defina
`EMBEDDER_TOKEN` no `.env` do servidor (nunca no git) e suba o sidecar com
`docker compose up -d embedder`. O Postgres passa a ter `mem_limit: 2g` e
`maintenance_work_mem=256MB` (o índice HNSW é construído em memória).

Dev local: `scripts/dev-pgvector.sh` sobe um Postgres com pgvector na porta 5433, sem tocar no
Postgres compartilhado do `../docker-compose.yml`.

---

## 🔧 Modo manutenção durante o deploy (18/09/2026)

Do rsync até o restart do `php`, o painel fica em `artisan down`: quem abrir vê **"Atualizando o
painel"** (503, recarrega sozinha a cada 15 s) em vez de uma página quebrada no meio da troca de
arquivos. São os ~20 s do deploy.

| Continua atendido na manutenção | Por quê |
|---|---|
| `/internal/*` (evento do pipeline) | o `clip-processor` não pode perder aviso de clip |
| `/telegramcanal` (webhook) | o Telegram não reenvia para sempre |
| `/o/*` (link rastreável de afiliado) | clique perdido é venda perdida |

- As funções `entrar_manutencao` e `sair_manutencao` ficam no `deploy.sh`; um `trap` no `EXIT`
  tira o painel da manutenção **mesmo se o deploy falhar no meio**.
- Se o SSH cair e o painel ficar preso em 503: `./deploy.sh --sair-manutencao`.
- Falhar ao **entrar** na manutenção não bloqueia o deploy — só avisa.
- A página é `painel/resources/views/errors/503.blade.php`; as exceções, `bootstrap/app.php`.

## ⚠️ Página em branco depois do deploy (incidente 18/09/2026)

Com `composer dev` rodando no Mac, o Vite cria `painel/public/hot` apontando para
`http://127.0.0.1:5174`. Esse arquivo subiu no deploy e o painel de produção passou a carregar o JS
do Mac — tela branca para todo mundo. O `deploy.sh` agora exclui `public/hot` do rsync e apaga o
arquivo no servidor a cada deploy. Sintoma para reconhecer: HTML com `127.0.0.1:5174/@vite/client`.

## 🔍 O que o script `./deploy.sh` faz por você

1. **Compilação Local do Vite (`painel/`)**: Gera os bundles otimizados de produção no seu computador, poupando a CPU da VPS na nuvem.
2. **Sincronização Rsync Otimizada**:
   * Sincroniza `painel/` (excluindo `node_modules`, `.env`, `.git` e `storage`).
   * Sincroniza `clip-processor/src/` (código Python do robô).
   * Sincroniza `branding/` (logos, marcas d'água, fontes).
   * Ignora permissões e tempos de diretórios para evitar conflitos com o usuário `www-data` do PHP-FPM.
3. **Recarga Instantânea dos Containers**:
   * `docker compose restart clip-processor` (carrega novo código Python em **1 segundo**).
   * `php artisan optimize:clear` (limpa cache de rotas, views e config do Laravel).
   * `php artisan migrate --force` (executa migrações do banco de dados com segurança).
   * `docker compose restart php` (limpa o cache opcache do PHP).

---

## 🏗️ Por que antes demorava tanto e como foi resolvido?

### O Problema Antigo
Anteriormente, o `docker-compose.yml` não possuía bind mount para a pasta de código do `clip-processor`. A cada alteração em um arquivo `.py` (como ajustar títulos de capas ou prompt de IA), era disparado um `docker compose build`. 
Dentro do Dockerfile do `clip-processor`:
* O código C++ do motor de áudio Whisper (`whisper.cpp`) era clonado e compilado do zero via `cmake`.
* O modelo neural de IA (`ggml-small.bin`, ~500 MB) era baixado.
* Dezenas de bibliotecas pesadas de IA e vídeo eram instaladas.
* Na VPS Oracle Cloud Free Tier (1 vCPU e 1 GB de RAM com disco burstable), essa compilação esgotava os créditos de CPU, ativando **CPU Throttling** (CPU Steal de até 75%), travando a escrita em disco e demorando de 15 a 30 minutos.

### A Solução Definitiva
1. **Volume Mapeado no `docker-compose.yml`**:
   ```yaml
   clip-processor:
     volumes:
       - ./youtube:/app/youtube
       - ./videos:/app/videos
       - ./branding:/app/branding:ro
       - ./clip-processor/src:/app/src
   ```
   Agora, o código Python dentro de `/app/src` é lido diretamente do sistema de arquivos do servidor.
2. **Zero Rebuild**: Ao alterar arquivos `.py`, o `deploy.sh` apenas envia o arquivo via rsync e reinicia o container em **1 segundo**.
3. **Preservação de Memória e CPU**: O Whisper C++ e as bibliotecas compiladas permanecem intactos e em cache na imagem Docker fixa.

---

## 🌐 Informações do Servidor de Produção

* **IP**: `129.80.236.185` — VM A1.Flex 2 OCPU / 12 GB ARM, Ashburn, PostgreSQL 17 (desde 17/09/2026, ver `Docs/planos/MIGRACAO-A1.md`)
* **Usuário**: `ubuntu`
* **Chave SSH**: `~/.ssh/oracle-a1-2026-09-16.key`
* **Diretório da Aplicação**: `/home/ubuntu/canaldecortes`
* **URL Pública do Painel**: [https://toolscut.alessandromelo.com.br](https://toolscut.alessandromelo.com.br)
