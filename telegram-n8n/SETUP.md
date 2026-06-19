# Setup — Telegram Bot + N8N

Guia passo a passo para configurar a integração Telegram + N8N para o Canal de Cortes.

## Pré-requisitos

- N8N rodando em `http://localhost:5678` (já configurado no docker-compose)
- Conta do Telegram no celular
- Acesso ao YouTube Data API v3 (já configurado no projeto)
- MySQL `clips_automation` funcionando

## Parte 1 — Criar o Telegram Bot

### 1.1 Criar bot no BotFather

1. Abra o Telegram e pesquise por `@BotFather`
2. Envie `/newbot`
3. Digite o nome de exibição: **Canal de Cortes Bot**
4. Digite o username (deve terminar em `bot`): **canaldecortes_bot** (ou variação disponível)
5. O BotFather responde com o **token** — anote-o:
   ```
   Token: 123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

### 1.2 Obter seu Chat ID

1. Pesquise por `@userinfobot` no Telegram
2. Envie qualquer mensagem
3. Ele responde com seu **ID** — anote-o:
   ```
   Id: 987654321
   ```

### 1.3 Configurar o bot (opcional mas recomendado)

No BotFather:
- `/setdescription` → "Bot de automação do Canal de Cortes"
- `/setcommands` → cole a lista:
  ```
  buscar - Busca vídeos por tema no YouTube
  trending - Top 5 assuntos em alta no futebol BR
  fila - Lista clipes prontos para upload
  publicar - Faz upload do próximo clipe
  canal - Adiciona canal ao pool de monitoramento
  status - Métricas do pipeline
  ajuda - Lista todos os comandos
  ```

## Parte 2 — Configurar N8N

### 2.1 Acessar o N8N

Abra `http://localhost:5678` no navegador.

### 2.2 Adicionar credenciais no N8N

Vá em **Credenciais** (ícone de chave) e crie:

#### Telegram API
- Tipo: `Telegram API`
- Access Token: _(seu token do BotFather)_
- Nome: `Telegram Canal de Cortes`

#### MySQL
- Tipo: `MySQL`
- Host: `mysql` (nome do container)
- Port: `3306`
- Database: `clips_automation`
- User: `clips_user`
- Password: _(valor de `CLIPS_DB_PASSWORD` no seu `.env`)_
- Nome: `MySQL Canal de Cortes`

#### HTTP Header Auth (para webhook seguro — opcional)
- Tipo: `Header Auth`
- Name: `X-Bot-Secret`
- Value: _(string aleatória, ex: resultado de `openssl rand -hex 32`)_

### 2.3 Importar os workflows

Para cada arquivo em `telegram-n8n/workflows/`:

1. No N8N, clique em **+ New Workflow**
2. Clique nos três pontos (menu) → **Import from File**
3. Selecione o arquivo `.json`
4. Conecte as credenciais criadas nos nós que pedirem
5. Ative o workflow (toggle no canto superior direito)

**Ordem de importação:**
1. `01-telegram-handler.json` — importar primeiro (outros dependem dele)
2. `02-busca-videos.json`
3. `03-tendencias.json`
4. `04-notificador-fila.json`

## Parte 3 (Phase 6) — Exposição via Cloudflare Tunnel

> **Phase 6 substituiu ngrok/NGINX por Cloudflare Tunnel.** O serviço `cloudflared` foi adicionado ao `docker-compose.yml` raiz no Plan 06-06 e expõe o n8n via Cloudflare Zero Trust — **sem porta aberta no host**, sem reverse proxy custom, sem ngrok.

### 3.1 Criar Tunnel no Cloudflare

1. Acessar [https://one.dash.cloudflare.com](https://one.dash.cloudflare.com) → **Networks** → **Tunnels** → **Create a tunnel**
2. Escolher connector **cloudflared**, dar nome (sugerido: `n8n-canaldecortes`)
3. Cloudflare exibe um token (formato `eyJh...`). Copiar e colar no `.env`:
   ```env
   CLOUDFLARE_TUNNEL_TOKEN=eyJh...
   ```

### 3.2 Configurar Public Hostname

Na mesma tela do Tunnel:
- **Public Hostnames** → **Add a public hostname**
- Subdomain: `n8n`
- Domain: `<seudominio>` (ex.: `canaldecortes.com.br`)
- Service type: `HTTP`
- URL: `n8n:5678` (nome do container — resolvido pela rede docker `internal`)

Salvar.

### 3.3 Atualizar variáveis de ambiente

Adicionar ao `.env` (raiz `/Users/alessandrobm1/develop/server/wordpress/.env`):

```env
N8N_WEBHOOK_URL=https://n8n.<seudominio>
N8N_HOST=n8n.<seudominio>
```

### 3.4 Subir cloudflared + restartar n8n

```bash
cd /Users/alessandrobm1/develop/server/wordpress
docker compose up -d cloudflared
docker compose restart n8n
```

### 3.5 Validar tunnel ativo

```bash
docker logs cloudflared 2>&1 | grep -E "Registered tunnel connection"
curl -I https://n8n.<seudominio>   # deve retornar 200/302 do n8n
```

## Parte 3.5 (Phase 6) — Configurar Telegram setWebhook (com secret)

1. Criar bot via `@BotFather` no Telegram (`/newbot` → seguir prompts).
2. Copiar o token retornado e salvar em `.env`:
   ```env
   TELEGRAM_BOT_TOKEN=123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
3. Gerar secret aleatório:
   ```bash
   openssl rand -hex 32
   ```
   Salvar em `.env`:
   ```env
   TELEGRAM_WEBHOOK_SECRET=<hex>
   ```
4. Confirmar `TELEGRAM_CHAT_ID_ALLOWED` no `.env` (Phase 6 usa allowlist via Telegram Trigger):
   ```env
   TELEGRAM_CHAT_ID_ALLOWED=5760918317
   ```
5. Executar `setWebhook` apontando para o tunnel + secret_token:
   ```bash
   source /Users/alessandrobm1/develop/server/wordpress/.env
   curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
     -H "Content-Type: application/json" \
     -d "{
       \"url\": \"$N8N_WEBHOOK_URL/webhook/telegram-canaldecortes\",
       \"secret_token\": \"$TELEGRAM_WEBHOOK_SECRET\",
       \"allowed_updates\": [\"message\"]
     }"
   ```
6. Verificar:
   ```bash
   curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo" | jq
   ```
   Esperado: `result.url` aponta para o tunnel, `pending_update_count=0`, `last_error_message` ausente.

## Parte 3.6 (Phase 6) — Importar workflows no n8n

Após o Tunnel estar ativo:

1. Acessar `https://n8n.<seudominio>` (login se necessário).
2. **Importar `telegram-n8n/workflows/06-router.json`**:
   - Menu → **Import from File** → upload → **Save** → **Activate**
   - Conferir credenciais "Telegram Canal de Cortes" e "MySQL Canal de Cortes" linkadas.
3. **Importar `telegram-n8n/workflows/06-cron-resumo-diario.json`**:
   - Mesma rotina → **Activate**.
4. Workflow `06-router.json` contém **dois triggers**:
   - **Telegram Trigger** (recebe comandos `/status`, `/clipes`, `/aprovar`, `/rejeitar`, `/processar`, `/ajuda`)
   - **Webhook `/webhook/notify`** (recebe POSTs internos do `clip-processor` com 3 eventos: `upload_published`, `pipeline_failure`, `clip_ttl_warning`). **NÃO** exposto via Cloudflare — só acessível pela rede docker (`http://n8n:5678/webhook/notify`).

> **Nota:** O workflow `01-telegram-handler.json` (Phases 1-5) NÃO é arquivado automaticamente. Operador decide manualmente no n8n UI quando substituir/desativar.

## Parte 3 (deprecated) — Exposição via ngrok / NGINX

> **Esta seção está mantida apenas como referência histórica para Phases 1-5.** Phase 6 substituiu pelo Cloudflare Tunnel (acima). NÃO use ngrok nem NGINX para o setup atual.

<details>
<summary>Mostrar passos antigos (ngrok / NGINX) — não usar</summary>

### Opção A — Exposição via ngrok (desenvolvimento/teste)

```bash
# Instalar ngrok
brew install ngrok

# Expor porta 5678
ngrok http 5678
```

Anote a URL gerada (ex: `https://abc123.ngrok.io`).

### Opção B — Servidor com IP público (produção)

Se o servidor já tem IP público, configure:
- Domínio: `n8n.seudominio.com.br`
- Configure NGINX como proxy reverso para porta 5678
- Configure SSL com Let's Encrypt

### Configurar o webhook no Telegram (legado, sem secret_token)

Substitua `TOKEN` e `N8N_URL`:

```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "<N8N_URL>/webhook/telegram-canaldecortes",
    "allowed_updates": ["message"]
  }'
```

Resposta esperada:
```json
{"ok":true,"result":true,"description":"Webhook was set"}
```

### Verificar configuração

```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

</details>

## Parte 4 — Variáveis de Ambiente Adicionais

Adicione ao seu `.env`:

```env
# Telegram
TELEGRAM_BOT_TOKEN=123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=987654321

# YouTube Data API (para busca de vídeos — diferente do upload OAuth)
YOUTUBE_API_KEY=AIzaSyXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Configurações do agente
MAX_SEARCH_RESULTS=10
CLIP_MIN_DURATION=300
CLIP_MAX_DURATION=7200
```

### Como obter YouTube API Key

1. Acesse [console.cloud.google.com](https://console.cloud.google.com)
2. Selecione o projeto "Canal de Cortes" (ou crie um novo)
3. APIs e Serviços → Ativar APIs → **YouTube Data API v3**
4. Credenciais → Criar credencial → **Chave de API**
5. Restrinja a chave para YouTube Data API v3

## Parte 5 — Teste

### Teste básico

Envie `/ajuda` para o bot no Telegram. Você deve receber a lista de comandos.

### Teste de busca

Envie `/buscar Flamengo gol polêmico`

O bot deve responder com algo como:
```
Buscando vídeos sobre "Flamengo gol polêmico"...
Encontrados 3 vídeos novos. Adicionados à fila de processamento.
```

### Teste de tendências

Envie `/trending`

O bot deve responder com os assuntos em alta no futebol BR.

## Solução de Problemas

### Bot não responde

1. Verifique se o webhook foi configurado: `getWebhookInfo`
2. Verifique se o N8N está rodando: `docker ps | grep n8n`
3. Verifique os logs do N8N: `docker logs n8n --tail 50`
4. Verifique se o workflow está **ativado** no N8N

### Erro de MySQL

1. Verifique as credenciais no N8N
2. Teste a conexão: `docker exec -i mysql mysql -u clips_user -p<senha> clips_automation -e "SELECT 1;"`

### Erro na busca do YouTube

1. Verifique se a `YOUTUBE_API_KEY` está correta
2. Verifique a quota: [console.cloud.google.com/apis/api/youtube.googleapis.com/quotas](https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas)
3. A quota padrão é 10.000 unidades/dia; uma busca custa 100 unidades
