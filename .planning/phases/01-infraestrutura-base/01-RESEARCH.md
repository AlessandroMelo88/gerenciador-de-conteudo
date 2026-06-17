# Phase 1: Infraestrutura Base - Research

**Researched:** 2026-06-17
**Domain:** Docker Compose integration, n8n self-hosted, faster-whisper, MySQL schema, YouTube OAuth
**Confidence:** HIGH (stack choices verified; one critical pitfall confirmed from official docs)

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INFRA-01 | Sistema roda inteiramente em Docker no docker-compose existente (novos servicos: n8n, clip-processor, whisper) | Patterns for extending existing Compose stacks with external networks; n8n image `docker.n8n.io/n8nio/n8n`; faster-whisper image `fedirz/faster-whisper-server:latest-cpu`; custom Python Dockerfile for clip-processor |
| INFRA-02 | Banco de dados `clips_automation` criado no MySQL existente com tabelas source_channels, source_videos e generated_clips | `docker exec` SQL injection pattern; no restart required; GRANT user dedicated ao projeto |
| INFRA-03 | Canal do YouTube criado, conta verificada, banner e bio preenchidos antes do primeiro upload | Verificacao por SMS obrigatoria; recursos desbloqueados apos verificacao; passos manuais documentados |
| INFRA-04 | Variaveis de ambiente e secrets configurados (.env com Claude API key, YouTube OAuth credentials) | OAuth 2.0 flow com `access_type=offline`; token.json persistido em volume; N8N_ENCRYPTION_KEY obrigatorio |
</phase_requirements>

---

## Summary

Phase 1 estabelece quatro pilares independentes: (1) estender o docker-compose existente com tres novos servicos sem quebrar nginx/PHP/MySQL/Redis; (2) criar o schema `clips_automation` no MySQL em execucao via `docker exec`; (3) configurar manualmente o canal do YouTube com verificacao por SMS; e (4) gerar e persistir credenciais OAuth 2.0 do YouTube e a Claude API key.

A descoberta mais critica desta pesquisa: **n8n 2.0+ removeu suporte a MySQL como banco interno de n8n** (breaking change confirmado na documentacao oficial). Isso nao afeta o schema `clips_automation` — o projeto usa MySQL para os dados do pipeline, nao para n8n. O n8n usara SQLite por padrao (sem dependencia extra), o que e adequado para um Mac local com uso moderado.

O segundo ponto critico e o `N8N_ENCRYPTION_KEY`: sem defini-lo explicitamente antes do primeiro boot, as credenciais se tornam irrecuperaveis se o volume for recriado. Deve ser gerado uma vez e comprometido no `.env` antes de qualquer `docker-compose up`.

**Primary recommendation:** Adicionar n8n, clip-processor e whisper ao docker-compose existente via rede Docker compartilhada (external network); usar SQLite para n8n; MySQL exclusivamente para `clips_automation`; OAuth do YouTube exige uma sessao manual de browser uma unica vez para gerar o refresh token.

---

## Standard Stack

### Core

| Library/Image | Version | Purpose | Why Standard |
|---|---|---|---|
| `docker.n8n.io/n8nio/n8n` | `2.27.0` (atual junho/2026) | Orquestrador de workflow visual | Self-hosted, sem vendor lock-in, nodes prontos para YouTube/HTTP/MySQL |
| `fedirz/faster-whisper-server:latest-cpu` | latest-cpu | Servidor de transcricao OpenAI-compatible | CPU-only (Mac sem GPU), API compativel com OpenAI, modelo configuravel via env |
| Python 3.12-slim + FFmpeg + yt-dlp | custom Dockerfile | clip-processor: download, corte e processamento | Imagem customizada — sem imagem publica que combine os tres com arm64 |
| MySQL 8.x (ja existente) | existente | Schema `clips_automation` | Reuso do servico existente; sem nova instancia |

### Supporting

| Library | Version | Purpose | When to Use |
|---|---|---|---|
| `google-auth-oauthlib` | latest pip | Gerar e renovar tokens OAuth do YouTube | Uma vez no setup inicial; token persistido em volume |
| `google-api-python-client` | latest pip | Cliente YouTube Data API v3 | Fase 5 (uploads); incluir no clip-processor Dockerfile |
| `anthropic` (Python SDK) | latest pip | Claude Haiku API calls | Fases 3 e 4; incluir no clip-processor Dockerfile |
| `mysql-connector-python` ou `pymysql` | latest pip | Conexao ao MySQL `clips_automation` | Em todo o clip-processor que precisar de DB |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|---|---|---|
| SQLite (n8n default) | PostgreSQL para n8n | PostgreSQL necessario so para queue mode (workers); SQLite suficiente para Mac local single-node |
| `fedirz/faster-whisper-server` | `lscr.io/linuxserver/faster-whisper` | linuxserver usa Wyoming protocol (Home Assistant); fedirz expoe REST OpenAI-compatible — mais facil integrar com n8n/Python |
| Custom Dockerfile clip-processor | `nandyalu/python-ffmpeg` | python-ffmpeg inclui FFmpeg+yt-dlp+Python arm64, mas nao inclui `google-api-python-client` nem `anthropic`; criar Dockerfile proprio e mais controlavel |

### Installation

```bash
# Nao ha instalacao local — tudo via Docker.
# Dependencias do clip-processor vao no Dockerfile:
# pip install faster-whisper google-api-python-client google-auth-oauthlib anthropic pymysql yt-dlp

# Para gerar o token OAuth do YouTube (uma vez, com browser):
pip install google-auth-oauthlib google-api-python-client
python generate_youtube_token.py
```

---

## Architecture Patterns

### Recommended Project Structure

```
canaldecortes/                    # raiz do projeto (docker-compose.yml existente aqui)
├── docker-compose.yml            # EXISTENTE — adicionar n8n, clip-processor, whisper
├── .env                          # secrets (nao commitar)
├── clip-processor/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src/
│       └── main.py
├── whisper/
│   └── models/                   # volume montado — modelos baixados aqui
├── n8n/
│   └── data/                     # volume montado — workflows, credenciais, SQLite
├── mysql/
│   └── init/
│       └── 01-clips-schema.sql   # script de criacao do schema (executado via docker exec)
└── youtube/
    └── token.json                # OAuth credentials (nao commitar — no .gitignore)
```

### Pattern 1: Extend Existing Compose with External Network

**What:** Usar uma rede Docker externa (pre-criada) que conecta o docker-compose existente ao novo bloco de servicos.
**When to use:** Quando ha dois grupos de servicos que precisam se comunicar mas estao em arquivos docker-compose separados ou foram adicionados incrementalmente.

```yaml
# Criar a rede uma vez:
# docker network create canaldecortes_net

# No docker-compose.yml EXISTENTE — adicionar ao final:
networks:
  canaldecortes_net:
    external: true
    name: canaldecortes_net

# E adicionar a cada servico existente:
# services:
#   nginx:
#     networks:
#       - canaldecortes_net
#   mysql:
#     networks:
#       - canaldecortes_net

# Novos servicos no mesmo arquivo (ou arquivo separado):
services:
  n8n:
    image: docker.n8n.io/n8nio/n8n:2.27.0
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - GENERIC_TIMEZONE=America/Sao_Paulo
      - TZ=America/Sao_Paulo
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
    volumes:
      - ./n8n/data:/home/node/.n8n
    networks:
      - canaldecortes_net

  clip-processor:
    build: ./clip-processor
    restart: unless-stopped
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - MYSQL_HOST=mysql         # nome do servico MySQL existente
      - MYSQL_DATABASE=clips_automation
      - MYSQL_USER=${CLIPS_DB_USER}
      - MYSQL_PASSWORD=${CLIPS_DB_PASSWORD}
    volumes:
      - ./youtube/token.json:/app/token.json:ro
      - /tmp/clips:/tmp/clips   # espaco de trabalho para videos
    networks:
      - canaldecortes_net
    depends_on:
      - whisper

  whisper:
    image: fedirz/faster-whisper-server:latest-cpu
    restart: unless-stopped
    environment:
      - WHISPER_MODEL=Systran/faster-whisper-small
    volumes:
      - ./whisper/models:/root/.cache/huggingface
    ports:
      - "8000:8000"
    networks:
      - canaldecortes_net

networks:
  canaldecortes_net:
    external: true
    name: canaldecortes_net
```

### Pattern 2: clip-processor Dockerfile

**What:** Imagem Python customizada com FFmpeg, yt-dlp e dependencias Python.
**When to use:** Unica opcao — nenhuma imagem publica combina todos os requisitos.

```dockerfile
# Source: padrao recomendado pela comunidade Docker/Python
FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app
COPY src/ .

CMD ["python", "main.py"]
```

```
# requirements.txt
yt-dlp
google-api-python-client
google-auth-oauthlib
anthropic
pymysql
faster-whisper   # cliente Python, nao o servidor
```

### Pattern 3: MySQL Schema via docker exec

**What:** Criar banco e tabelas no MySQL em execucao sem restart.
**When to use:** Sempre que o MySQL ja esta rodando (nao e uma instalacao nova).

```sql
-- mysql/init/01-clips-schema.sql
CREATE DATABASE IF NOT EXISTS clips_automation
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE clips_automation;

CREATE TABLE IF NOT EXISTS source_channels (
  id INT AUTO_INCREMENT PRIMARY KEY,
  youtube_channel_id VARCHAR(64) NOT NULL UNIQUE,
  channel_name VARCHAR(255) NOT NULL,
  rss_url VARCHAR(512) NOT NULL,
  active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS source_videos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  youtube_video_id VARCHAR(64) NOT NULL UNIQUE,
  channel_id INT NOT NULL REFERENCES source_channels(id),
  title VARCHAR(500),
  published_at TIMESTAMP,
  status ENUM('pending','downloading','downloaded','transcribing','selecting','cutting','publishing','published','failed') DEFAULT 'pending',
  local_path VARCHAR(1024),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS generated_clips (
  id INT AUTO_INCREMENT PRIMARY KEY,
  source_video_id INT NOT NULL REFERENCES source_videos(id),
  clip_path VARCHAR(1024),
  thumbnail_path VARCHAR(1024),
  title VARCHAR(200),
  description TEXT,
  tags TEXT,
  score TINYINT,
  start_time FLOAT,
  end_time FLOAT,
  youtube_video_id VARCHAR(64),
  status ENUM('pending','published','failed') DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE USER IF NOT EXISTS 'clips_user'@'%' IDENTIFIED BY '${CLIPS_DB_PASSWORD}';
GRANT ALL PRIVILEGES ON clips_automation.* TO 'clips_user'@'%';
FLUSH PRIVILEGES;
```

```bash
# Executar no MySQL existente (sem restart):
docker exec -i <mysql_container_name> mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" < mysql/init/01-clips-schema.sql
```

### Pattern 4: YouTube OAuth — One-Time Token Generation

**What:** Rodar um script Python local (fora do Docker) para autorizar via browser e gerar token.json persistente.
**When to use:** Uma vez durante o setup; o token.json e montado como volume no clip-processor.

```python
# Source: Google official OAuth2 guide for installed apps
# generate_youtube_token.py
from google_auth_oauthlib.flow import InstalledAppFlow
import json

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]

flow = InstalledAppFlow.from_client_secrets_file(
    "client_secret.json",  # baixado do Google Cloud Console
    scopes=SCOPES
)
# Isso abre o browser UMA VEZ para autorizacao
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")

# Salvar token (inclui refresh_token para uso permanente)
with open("youtube/token.json", "w") as f:
    f.write(creds.to_json())
print("token.json salvo. Nao commitar no git!")
```

### Anti-Patterns to Avoid

- **Usar MySQL como banco interno do n8n:** MySQL foi removido no n8n 2.0. SQLite (default) ou PostgreSQL sao as unicas opcoes. O MySQL existente e APENAS para `clips_automation`.
- **Nao definir N8N_ENCRYPTION_KEY:** Sem isso, uma recreacao de volume torna as credenciais do n8n irrecuperaveis. Gerar antes do primeiro boot.
- **Montar token.json como read-write sem backup:** O token.json contem o refresh_token do YouTube. Perder esse arquivo exige re-autorizacao manual. Incluir no `.gitignore` e manter backup seguro.
- **Usar `latest` sem pin de versao para n8n:** n8n tem historico de breaking changes entre versoes. Pinar em `2.27.0` ou versao especifica.
- **Publicar porta 5678 na internet sem autenticacao:** Em Mac local isso e OK, mas nao expor ao mundo externo sem HTTPS e auth.
- **Criar dois containers MySQL:** Nao adicionar um novo servico `db` no compose para n8n — usar SQLite ou o PostgreSQL separado se quiser persistencia mais robusta. Nao reusar o MySQL existente para n8n (MySQL nao e mais suportado pelo n8n 2.x).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| Transcricao de audio | Script Python com subprocess whisper | `fedirz/faster-whisper-server` via Docker | API HTTP pronta, model caching, suporte a PT-BR nativo, zero codigo de servidor |
| OAuth token refresh | Logica manual de refresh de access token | `google-auth-oauthlib` + `google.oauth2.credentials.Credentials` | Gerencia expiracao, refresh automatico, formato correto do token |
| Orquestracao de pipeline | Script bash/Python que chama etapas em sequencia | n8n workflows | Retry automatico, logs visuais, triggers agendados, sem gerenciar processos manualmente |
| Networking entre containers | Expose de portas no host + IPs hardcoded | Docker service names na mesma rede | Containers se comunicam por nome (`http://whisper:8000`), sem portas expostas desnecessariamente |

**Key insight:** A tentacao de "so um script Python" para orquestracao e alta, mas n8n resolve retry, logging e scheduling com zero codigo — exatamente o que o requisito ORC-01 exige.

---

## Common Pitfalls

### Pitfall 1: n8n MySQL Deprecation Confusion

**What goes wrong:** O desenvolvedor ve que tem MySQL rodando e configura `DB_TYPE=mysqldb` para n8n, o container falha na inicializacao sem mensagem clara.
**Why it happens:** MySQL era suportado ate n8n 0.x; n8n 2.0 (dezembro 2025) removeu definitivamente. Documentacao antiga ainda aparece em buscas.
**How to avoid:** Nao configurar variaveis `DB_MYSQLDB_*` para n8n. Deixar n8n usar SQLite (default, sem configuracao extra). O MySQL existente e para `clips_automation`, nao para o banco interno do n8n.
**Warning signs:** Container n8n reiniciando em loop com erro de conexao de banco.

### Pitfall 2: N8N_ENCRYPTION_KEY nao definida antes do primeiro boot

**What goes wrong:** n8n gera uma chave aleatoria no primeiro boot e a salva no volume. Se o volume for recriado (erro de path, `docker-compose down -v`), a chave muda e todas as credenciais armazenadas (YouTube OAuth no n8n, Claude API key) ficam irrecuperaveis.
**Why it happens:** Comportamento silencioso — n8n sobe sem erro, mas credenciais antigas sao invalidas.
**How to avoid:** Gerar `N8N_ENCRYPTION_KEY` com `openssl rand -hex 32` ANTES do primeiro `docker-compose up`. Adicionar ao `.env`. Fazer backup do `.env`.
**Warning signs:** n8n inicia mas nenhuma credencial configurada previamente funciona.

### Pitfall 3: Rede Docker nao configurada antes do `docker-compose up`

**What goes wrong:** `docker-compose up` falha com "Network not found" para a rede externa que conecta os servicos novos aos existentes.
**Why it happens:** Redes externas (external: true) devem existir antes do compose rodar. Docker nao as cria automaticamente.
**How to avoid:** Criar a rede antes: `docker network create canaldecortes_net`. Documentar esse passo na ORDER de execucao do PLAN.
**Warning signs:** Erro imediato no `docker-compose up` com "network ... not found".

### Pitfall 4: YouTube OAuth em modo "Testing" com token expirando em 7 dias

**What goes wrong:** Em modo Testing no Google Cloud Console, tokens OAuth expiram em 7 dias. O pipeline para de funcionar silenciosamente uma semana apos o setup.
**Why it happens:** Apps em modo Testing tem restricao de duracao de token pelo Google.
**How to avoid:** Apos gerar o token inicial, mudar o app para modo "Production" no Google Cloud Console (sem necessidade de verificacao para uso proprio/interno). Com `access_type=offline` e `prompt=consent`, o refresh_token se torna permanente.
**Warning signs:** Uploads param de funcionar ~7 dias apos configuracao sem erro obvio.

### Pitfall 5: Numero de telefone virtual rejeitado pelo YouTube

**What goes wrong:** A verificacao por SMS do YouTube falha com numeros VOIP, temporarios ou virtuais.
**Why it happens:** YouTube rejeita numeros nao-fisicos para prevenir abusos. Um numero pode ser associado a no maximo 2 canais por ano.
**How to avoid:** Usar numero de celular pessoal real para verificacao. Nao usar servicos de SMS temporario.
**Warning signs:** YouTube exibe "este numero de telefone nao pode ser usado para verificacao".

### Pitfall 6: faster-whisper baixando modelo em cada restart

**What goes wrong:** Container whisper demora minutos para iniciar porque baixa o modelo `small` (~500MB) a cada recreacao.
**Why it happens:** O volume de cache do Hugging Face nao esta montado.
**How to avoid:** Montar `./whisper/models:/root/.cache/huggingface` como volume persistente.
**Warning signs:** Container whisper lento no inicio, alta banda de rede repetidamente.

---

## Code Examples

### Verificar schema MySQL apos criacao

```sql
-- Executar via docker exec para validar INFRA-02
USE clips_automation;
SHOW TABLES;
DESCRIBE source_channels;
DESCRIBE source_videos;
DESCRIBE generated_clips;
SELECT User, Host FROM mysql.user WHERE User = 'clips_user';
```

### Testar API do whisper (validar INFRA-01)

```bash
# Source: fedirz/faster-whisper-server README
curl http://localhost:8000/v1/audio/transcriptions \
  -F "file=@/tmp/test.mp3" \
  -F "model=Systran/faster-whisper-small" \
  -F "language=pt"
```

### Testar conectividade n8n → MySQL (validar INFRA-01 + INFRA-02)

```bash
# No n8n UI: criar workflow com node MySQL
# Host: mysql (nome do servico Docker)
# Port: 3306
# Database: clips_automation
# SELECT COUNT(*) FROM source_channels;
```

### Verificar token.json valido

```python
# Source: google-auth-oauthlib docs
from google.oauth2.credentials import Credentials
import json

with open("youtube/token.json") as f:
    creds_data = json.load(f)

creds = Credentials.from_authorized_user_info(creds_data)
print("Token valido:", creds.valid)
print("Tem refresh_token:", bool(creds.refresh_token))
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| n8n com MySQL como banco interno | n8n com SQLite (default) ou PostgreSQL | n8n 2.0, dezembro 2025 | Nao usar DB_TYPE=mysqldb para n8n |
| whisper original (openai/whisper) | faster-whisper (CTranslate2) | 2023-2024, maduro em 2025 | 4x mais rapido no CPU; mesmo formato de saida |
| OAuth via prompt a cada execucao | OAuth com refresh_token persistente em token.json | Padrao desde 2020; best practice atual | Uma autorizacao manual, uso permanente sem browser |
| `n8nio/n8n` no Docker Hub | `docker.n8n.io/n8nio/n8n` (registry proprio) | n8n migrou seu registry | Usar URL completa `docker.n8n.io/n8nio/n8n` |

**Deprecated/outdated:**
- `DB_TYPE=mysqldb` para n8n: removido em n8n 2.0 — nao usar
- `DB_TYPE=mariadb` para n8n: removido em n8n 2.0 — nao usar
- `openai/whisper` Docker direto: substituido por `faster-whisper` para uso em producao CPU

---

## Open Questions

1. **Nome exato do container/servico MySQL existente**
   - What we know: O projeto tem MySQL rodando no docker-compose existente
   - What's unclear: O nome do servico (provavelmente `mysql` ou `db`) — o clip-processor precisa desse nome como host
   - Recommendation: Verificar com `docker ps` ou ler o docker-compose.yml existente antes de planejar as tasks

2. **Versao atual do docker-compose.yml existente**
   - What we know: Ha nginx, PHP, MySQL, Redis ja rodando
   - What's unclear: Se usa versao antiga com `version:` no topo ou versao nova sem ele; se ja tem uma rede customizada
   - Recommendation: Ler o arquivo antes de planejar a modificacao

3. **Conta Google disponivel para o canal do YouTube**
   - What we know: Canal precisa ser criado com conta verificada por SMS
   - What's unclear: Se ha conta Google ja disponivel para isso ou se precisa criar uma nova
   - Recommendation: Confirmar com o usuario antes de planejar INFRA-03 — e passo 100% manual

---

## Validation Architecture

### Test Framework

| Property | Value |
|---|---|
| Framework | Shell scripts + SQL queries (sem framework de teste formal para infraestrutura) |
| Config file | Nenhum — validacao via comandos `docker`, `curl`, `mysql` |
| Quick run command | `docker-compose ps` + `curl http://localhost:5678/healthz` + `curl http://localhost:8000/health` |
| Full suite command | Executar todos os checks SQL + health endpoints + verificar token.json |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|---|---|---|---|---|
| INFRA-01 | `docker-compose up` sobe n8n, whisper e clip-processor sem erros | smoke | `docker-compose ps \| grep -E "(n8n\|whisper\|clip-processor)" \| grep Up` | Wave 0 |
| INFRA-01 | n8n responde na porta 5678 | smoke | `curl -sf http://localhost:5678/healthz && echo OK` | Wave 0 |
| INFRA-01 | whisper responde na porta 8000 | smoke | `curl -sf http://localhost:8000/health && echo OK` | Wave 0 |
| INFRA-02 | Banco `clips_automation` existe | integration | `docker exec <mysql> mysql -u root -p${ROOT_PW} -e "SHOW DATABASES;" \| grep clips_automation` | Wave 0 |
| INFRA-02 | Tabelas source_channels, source_videos, generated_clips existem | integration | `docker exec <mysql> mysql -u root -p${ROOT_PW} clips_automation -e "SHOW TABLES;"` | Wave 0 |
| INFRA-03 | Canal verificado (manual) | manual-only | Verificar no YouTube Studio > Channel status | N/A |
| INFRA-04 | .env tem todas as variaveis obrigatorias | smoke | `grep -E "N8N_ENCRYPTION_KEY|ANTHROPIC_API_KEY|CLIPS_DB_PASSWORD" .env` | Wave 0 |
| INFRA-04 | token.json existe e tem refresh_token | smoke | `python -c "import json; d=json.load(open('youtube/token.json')); assert d.get('refresh_token'), 'NO REFRESH TOKEN'"` | Wave 0 |

### Sampling Rate

- **Per task commit:** `docker-compose ps` para verificar servicos em execucao
- **Per wave merge:** Executar todos os checks smoke acima + testar conexao MySQL do clip-processor
- **Phase gate:** Todos os checks passando + canal YouTube com status "verificado" + `docker-compose up` limpo

### Wave 0 Gaps

- [ ] `scripts/validate-infra.sh` — script shell com todos os health checks
- [ ] `mysql/init/01-clips-schema.sql` — script SQL do schema
- [ ] `youtube/.gitignore` — garantir que `token.json` nao va para o git
- [ ] `.env.example` — template com todas as variaveis necessarias (sem valores reais)

---

## Sources

### Primary (HIGH confidence)

- Hub Docker `hub.docker.com/r/n8nio/n8n` — versao atual 2.27.0, image name `docker.n8n.io/n8nio/n8n`
- `docs.n8n.io/2-0-breaking-changes/` — confirmacao oficial de remocao de MySQL/MariaDB no n8n 2.0
- `docs.docker.com/compose/how-tos/networking/` — padrao de external networks para conectar stacks
- `docs.linuxserver.io/images/docker-faster-whisper/` — configuracao da imagem linuxserver
- `hub.docker.com/r/fedirz/faster-whisper-server` — imagem CPU-only para Mac sem GPU

### Secondary (MEDIUM confidence)

- `developers.google.com/youtube/v3/guides/auth/installed-apps` — OAuth 2.0 para aplicacoes desktop/servidor, verificado com multiplas fontes
- `support.google.com/youtube/answer/171664` — verificacao de canal YouTube por SMS oficial
- Comunidade n8n + documentacao de variaveis de ambiente — N8N_ENCRYPTION_KEY como configuracao critica

### Tertiary (LOW confidence)

- Guides de terceiros sobre docker-compose com nginx/MySQL/Redis — padrao confirmado por documentacao oficial Docker

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — imagens verificadas no Docker Hub, versoes confirmadas
- Architecture: HIGH — padroes Docker documentados oficialmente; schema SQL e padrao MySQL
- Pitfalls: HIGH para n8n MySQL (confirmado em docs oficiais 2.0 breaking changes); HIGH para N8N_ENCRYPTION_KEY (multiplas fontes de suporte n8n); MEDIUM para YouTube token expiry (comportamento Google confirmado por multiplas fontes)

**Research date:** 2026-06-17
**Valid until:** 2026-09-17 (stack relativamente estavel; verificar versao n8n antes de usar)
