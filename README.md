# Canal de Cortes

Pipeline automatizado que monitora canais de futebol no YouTube, corta os melhores momentos com IA e publica os clips (shorts e vídeos longos) em canais próprios — sem intervenção manual no fluxo padrão.

## Visão geral

O sistema é composto por dois serviços principais rodando em Docker:

- **`clip-processor`** (Python) — daemon que roda o pipeline completo: monitora RSS dos canais fonte, baixa vídeos novos, transcreve com Whisper (via Groq), seleciona os melhores momentos com IA (Claude, com fallback para Groq/LLaMA), corta os clips, queima legenda, aplica marca d'água e publica no YouTube respeitando uma cota diária de uploads.
- **`painel`** (Laravel + Inertia.js + React + shadcn UI) — painel administrativo web onde o operador acompanha e controla o pipeline: aprova/rejeita clips, cadastra canais fonte e destino, processa vídeos manualmente e limpa vídeos antigos do disco/banco.

Os dois se comunicam por um sidecar HTTP interno (`clip-processor`, porta 8090, sem exposição no host) — o painel nunca acessa o banco/disco do pipeline diretamente para ações de escrita, sempre via essa API interna autenticada por token compartilhado.

## Como o pipeline funciona

1. **Descoberta** — `rss_poller.py` varre o feed RSS de cada canal fonte cadastrado (ativo e não-blacklistado) e insere vídeos novos em `source_videos`.
2. **Classificação de formato** — cada vídeo é classificado automaticamente como `curto` (shorts verticais) ou `longo` (corte único horizontal, 10-20min) com base na duração real do vídeo original.
3. **Download** — a cada ciclo, o pipeline baixa até 2 vídeos `longo` + 3 `curto` pendentes (por padrão), priorizando sempre a notícia mais recente (`published_at DESC`), não a ordem de descoberta.
4. **Transcrição** — o áudio é transcrito via Whisper (Groq).
5. **Seleção de momentos** — a IA (Claude, com fallback Groq/LLaMA) escolhe os melhores trechos do vídeo, com uma pontuação (score) de 0 a 10; abaixo de um limiar, o momento é descartado.
6. **Corte e pós-produção** — cada momento vira um clip: Shorts são convertidos para vertical e recebem legenda queimada (SRT → libass); vídeos longos permanecem horizontais e seguem sem legenda. O worker escolhe intro, encerramento e música na biblioteca configurada por canal/formato, aplica a marca d'água do canal-destino quando existir e gera a thumbnail.
7. **Metadata** — título, descrição e tags são gerados por IA (Claude) a partir da transcrição do trecho; se a IA falhar (ex.: chave de API ausente/inválida), cai no fallback e usa o título bruto do vídeo original.
8. **Aprovação** — por padrão o clip vai direto para `pending` (100% automático); pode ser configurado para exigir aprovação manual via painel ou Telegram antes de publicar.
9. **Publicação** — respeitando a cota diária de uploads por canal-destino (`MAX_UPLOADS_PER_DAY`) e uma janela de horário (19h–22h), os clips aprovados são publicados no YouTube em ordem justa entre os canais fonte (round-robin), para que um canal com muitos vídeos represados não monopolize a cota por dias seguidos.
10. **Créditos** — a descrição do clip publicado inclui automaticamente crédito ao canal fonte (`@handle`), quando configurado.

## O painel (Inertia.js + React + shadcn UI)

- **Dashboard** — fila de aprovação, fila aguardando cota diária, últimas falhas e o consumo de cota de uploads do dia por canal-destino.
- **Canais Destino** — canais do YouTube onde os clips são publicados (nome, nicho, OAuth, template de créditos).
- **Configurações** — biblioteca de intros, encerramentos e músicas, com escopo global ou por canal/formato; o painel sinaliza quando a identidade mínima ainda não foi configurada.
- **Canais Fonte** — canais monitorados via RSS (ativo/blacklisted, nicho, handle).
- **Vídeos** — todo vídeo bruto já baixado/tentado, com filtro por status e data de publicação, e uma ferramenta de limpeza que apaga do banco vídeos antigos nunca processados e libera do disco o arquivo bruto de vídeos que já geraram clip e não precisam mais dele.
- **Processar Vídeo** — envio manual de uma URL específica do YouTube pro pipeline, fora do monitoramento automático.
- **Documentação** — página de ajuda dentro do próprio painel explicando cada seção.

## Stack técnica

- **clip-processor**: Python, APScheduler (agendamento), yt-dlp (download/metadados), Whisper via Groq (transcrição), Anthropic Claude (seleção de momentos + metadata), FFmpeg (corte/legenda/watermark), PyMySQL, Redis (deduplicação + cota diária + cache de sessão do pipeline).
- **painel**: Laravel, Inertia.js, React, Tailwind CSS, shadcn UI, MySQL.
- **Infraestrutura**: Docker Compose (MySQL, Redis, painel PHP/Nginx, clip-processor), rede interna dedicada para o sidecar HTTP entre painel e clip-processor.

## Configuração

Copie `.env.example` para `.env` na raiz do projeto e preencha as chaves necessárias:

- `ANTHROPIC_API_KEY` — obrigatória para seleção de momentos e geração de metadata de qualidade (sem ela, o pipeline usa um fallback mais simples via Groq/LLaMA para seleção, e o título/descrição do clip cai para o título bruto do vídeo original).
- `GROQ_API_KEY` — transcrição de áudio (Whisper) e fallback de seleção de momentos.
- `CLIPS_DB_PASSWORD` — senha do usuário MySQL do pipeline.
- `CLIP_PROCESSOR_INTERNAL_TOKEN` — token compartilhado entre o painel e o sidecar HTTP interno do clip-processor (mesmo valor nos dois lados).
- `PIPELINE_ENABLED` — deixe `false` no primeiro boot; passe para `true` somente depois de configurar as chaves de IA e o OAuth do canal de destino.
- Variáveis opcionais (Telegram, Cloudflare Tunnel, TTL de clips pendentes, cota diária de uploads) — ver comentários em `.env.example`.

## Rodando localmente (Compose isolado)

O Compose deste repositório usa o projeto `canaldecortes`, a porta `8088`, volumes próprios e a rede padrão gerenciada pelo Compose. Não define `container_name`, não publica MySQL/Redis no host e não reutiliza mounts de outros projetos.

Na primeira execução:

```bash
cp .env.example .env
cp painel/.env.example painel/.env
# Preencha CLIPS_DB_PASSWORD, MYSQL_ROOT_PASSWORD, APP_KEY e o token interno
# antes de subir (os valores devem ser longos e aleatórios).
docker compose up -d --build mysql redis
docker compose run --rm panel-init
docker compose up -d php queue scheduler nginx clip-processor
```

O painel fica em [http://localhost:8088](http://localhost:8088). O serviço `clip-processor` sobe com o sidecar HTTP disponível, mas o pipeline permanece pausado enquanto `PIPELINE_ENABLED=false`.

Depois de configurar `GROQ_API_KEY`/`ANTHROPIC_API_KEY`, colocar o `client_secret.json` em `youtube/` e concluir o OAuth, habilite o processamento:

```bash
sed -i '' 's/^PIPELINE_ENABLED=.*/PIPELINE_ENABLED=true/' .env
docker compose up -d --force-recreate clip-processor
```

Comandos úteis:

```bash
docker compose ps
docker compose logs -f nginx php clip-processor
docker compose exec php php artisan migrate:status
```

## Desenvolvimento e qualidade

```bash
make setup      # venv Python + composer + npm
make lint       # ruff, Pint, PHPStan, tsc, oxlint, Prettier, shellcheck, yamllint
make format     # aplica formatação em tudo
make test-python
```

Hooks locais com `make hooks` (pre-commit); o mesmo conjunto roda no GitHub Actions (`.github/workflows/ci.yml`). Convenções de commit e changelog em [`CONTRIBUTING.md`](CONTRIBUTING.md); ferramentas, políticas e pendências em [`Docs/DESENVOLVIMENTO.md`](Docs/DESENVOLVIMENTO.md); dívida técnica mapeada em [`Docs/TODO-REFATORACAO.md`](Docs/TODO-REFATORACAO.md).

## Proteção dos dados

O banco atual é **MySQL 8.4**, não PostgreSQL. Não troque para SQLite neste stack: o painel Laravel, o worker Python e a fila fazem escritas concorrentes; SQLite é mais adequado para processo único e pode gerar bloqueios (`database is locked`) nesse cenário. A segurança dos dados vem de volume persistente, backup verificável e cópia fora do disco principal.

O backup diário fica no serviço opcional `mysql-backup`, com retenção padrão de 30 dias:

```bash
docker compose --profile backup up -d mysql-backup
./scripts/backup-mysql.sh
```

O backup manual gera `backups/mysql/*.sql.gz` e um arquivo `.sha256`. Por padrão ele fica no mesmo diretório do projeto; para proteger contra falha do disco, configure `MYSQL_BACKUP_DIR` em `.env` para outro disco ou armazenamento sincronizado e reinicie o serviço de backup. Os backups entram no `.gitignore` e não são enviados ao Git.

Para restaurar, pare o processamento antes e confirme explicitamente a operação:

```bash
docker compose stop clip-processor queue scheduler
CONFIRM_RESTORE=I_UNDERSTAND ./scripts/restore-mysql.sh ./backups/mysql/SEU_BACKUP.sql.gz
docker compose start queue scheduler clip-processor
```

Não use `docker compose down -v`: isso remove os volumes nomeados do MySQL e do Redis.
