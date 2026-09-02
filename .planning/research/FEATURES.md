# Features Research: Canal de Cortes v2.0

**Pesquisado:** 2026-06-21
**Domínio:** Laravel/Filament admin panel, multi-channel YouTube OAuth, Telegram bot Laravel, FFmpeg watermark
**Contexto:** Adições ao pipeline Python existente (RSS → download → Whisper → Haiku → FFmpeg → YouTube API v3, mono-canal)

---

## Admin Panel (Laravel/Filament)

**Versão alvo:** Laravel 11 + Filament 3 (Filament 5 requer Livewire 4 — manter v3 para Laravel 11)
**Stack base:** TALL (Tailwind + Alpine.js + Livewire + Laravel)

### Table Stakes
_Sem isso o painel não tem razão de existir._

| Feature | Como faz no Filament 3 | Complexidade |
|---------|------------------------|--------------|
| Listar/adicionar/desativar canais-fonte | `php artisan make:filament-resource SourceChannel --generate` gera tabela + form CRUD completo | Baixa |
| Listar canais-destino com status OAuth | Resource `DestinationChannel` com coluna badge `oauth_status` (authorized/expired/missing) | Baixa |
| Ver status dos vídeos no pipeline | Resource `SourceVideo` com coluna `status` como badge colorido e filtro por status | Baixa |
| Aprovar/rejeitar clips da fila | Table row action com `->requiresConfirmation()` ou modal inline; chama `UPDATE generated_clips SET status='approved'/'rejected'` | Média |
| Dashboard de contadores | `make:filament-widget StatsOverview --stats-overview` com query COUNT por status — polling padrão 5s configurável | Baixa |
| Autenticação básica | `php artisan make:filament-user` cria usuário admin; auth incluída no panel por padrão | Baixa |

### Differentiators
_Adicionam valor real ao operador sem custo de manutenção alto._

| Feature | Detalhe | Valor |
|---------|---------|-------|
| Polling de status em tempo real no dashboard | `protected static ?string $pollingInterval = '10s'` no widget — sem websocket | Alto — operador vê pipeline ao vivo |
| Badge colorido por status do clip | `->badge()->color(fn($state) => match($state) { 'published' => 'success', 'failed' => 'danger', ... })` | Médio — UX mais legível |
| Link direto pro vídeo publicado no YouTube | Coluna `youtube_video_id` como link `https://youtu.be/{id}` | Médio |
| Filtro por canal-destino | Filament SelectFilter em `generated_clips` por `destination_channel_id` | Médio |
| Botão "Forçar pipeline agora" | Header action que faz POST para endpoint do clip-processor | Baixo |

### Anti-features
_Parecem úteis mas adicionam complexidade sem retorno neste contexto._

| Feature | Motivo para evitar |
|---------|-------------------|
| Editor de vídeo inline no painel | Sistema é 100% autônomo; edição manual contradiz o modelo |
| Charts de analytics do YouTube (views/subs) | Exige YouTube Reporting API adicional, cota separada — fora do escopo v2 |
| Multi-tenant / multi-usuário | Um operador; auth simples é suficiente |
| Notificações Filament in-panel (database notifications) | Telegram já cobre notificações; duplicar cria confusão |
| Upload manual de vídeos pelo painel | Torna o pipeline dependente de ação humana para cada vídeo |
| Role/permission system (Spatie) | Overkill para um único operador |

---

## Multi-Channel YouTube Publishing

**Contexto atual:** `uploader.py` usa um único `token.json` (linha 14: `DEFAULT_TOKEN_FILE = '/app/token.json'`). `QuotaManager` usa uma chave Redis global `youtube_uploads:{date}`.

### Table Stakes
_Mínimo necessário para rotear clips a canais distintos._

| Feature | Detalhe | Complexidade |
|---------|---------|--------------|
| Token OAuth por canal armazenado em DB | Tabela `destination_channels` com coluna `token_json TEXT` ou path para arquivo; 1 token por canal Google | Média — setup OAuth manual uma vez por canal |
| Roteamento nicho → canal-destino | `source_channels.niche ENUM('futebol','podcast')` → JOIN com `destination_channels.niche`; roteamento feito antes do upload | Baixa |
| Quota independente por canal no Redis | Chave Redis `youtube_uploads:{channel_id}:{date}` em vez de global; `QuotaManager` recebe `channel_id` | Baixa — 2 linhas de código |
| Upload usando token do canal correto | `YouTubeUploader` recebe `token_path` dinâmico em vez de env var hardcoded | Baixa |
| 3 uploads/dia por canal | `MAX_UPLOADS_PER_DAY=3` por canal; 2 canais = 6 uploads totais = teto da cota gratuita (10.000 / 1.600 ≈ 6) | Já funciona se quota for por canal |

### Differentiators

| Feature | Detalhe | Valor |
|---------|---------|-------|
| Flow OAuth via Laravel no painel | Rota `/oauth/youtube/{channel}` no Laravel inicia handshake; armazena token no DB automaticamente | Alto — sem rodar script Python manual |
| Refresh token automático no PHP | Google Client Library para PHP faz refresh se token expirado; fallback: notificar no Telegram se falhar | Alto |
| Dashboard por canal no painel | Widget separado por `destination_channel_id` mostrando uploads hoje / quota restante | Médio |

### Anti-features

| Feature | Motivo |
|---------|--------|
| Múltiplos Google Cloud Projects | Um projeto basta; a diferenciação ocorre nos tokens OAuth, não no projeto |
| Fila de upload global com lock | Race condition só existe se rodar 2 workers paralelos — pipeline atual é single-process |
| Agendamento granular por canal (horário diferente por nicho) | Desnecessário em v2; todos publicam na mesma janela 19h-22h BRT |

**Aviso crítico (MEDIUM confidence, verificado via Google Developer forum):** Tokens OAuth de apps em modo "Testing" expiram a cada 7 dias. Para tokens permanentes, submeter app para verificação de Produção no Google Cloud Console. Isso é um requisito operacional, não opcional.

---

## Telegram Bot in Laravel

**Contexto atual:** `telegram_notifier.py` faz POST para n8n webhook interno. Bot Telegram atual roda separado (n8n + Cloudflare Tunnel). v2 elimina n8n e Cloudflare para o bot.

**Pacote definido:** `irazasyed/telegram-bot-sdk` (já decisão do projeto)

### Table Stakes
_Bot funcional mínimo no Laravel._

| Feature | Como implementar | Complexidade |
|---------|-----------------|--------------|
| Instalar SDK e configurar token | `composer require irazasyed/telegram-bot-sdk`; `.env TELEGRAM_BOT_TOKEN=`; `config/telegram.php` | Baixa |
| Webhook via rota Laravel | Rota POST `/telegram/{token}/webhook`; excluir de CSRF em `VerifyCsrfToken.php`; `Telegram::getWebhookUpdates()` | Baixa |
| Registrar webhook na API Telegram | `php artisan telegram:webhook:setup` (comando incluído no SDK) ou `Telegram::setWebhook(['url' => $url])` | Baixa |
| Receber comandos: /status, /clipes, /aprovar ID, /rejeitar ID | Classes Command com `$name`, `handle()` e `Telegram::addCommands([...])` | Média |
| Enviar notificação de upload publicado | `Telegram::sendMessage(['chat_id' => $chatId, 'text' => ...])` chamado do publisher Python via HTTP endpoint Laravel ou diretamente | Baixa |
| Substituir n8n notifier no Python | `telegram_notifier.py` aponta `N8N_NOTIFY_URL` para endpoint Laravel em vez de n8n (mudança de 1 env var) | Baixíssima |

### Differentiators

| Feature | Detalhe | Valor |
|---------|---------|-------|
| Mensagens formatadas com Markdown | `parse_mode: Markdown` — negrito para título, link clicável para `https://youtu.be/{id}` | Médio |
| Resumo diário automático | Laravel Scheduler (`schedule->command('bot:daily-summary')->dailyAt('22:00')`) | Médio |
| Comando /pipeline que retorna status atual | Query em `source_videos` e `generated_clips` formatada em tabela ASCII no Telegram | Médio |
| Botões inline (InlineKeyboardMarkup) para aprovar/rejeitar | `sendMessage` com `reply_markup` botões; callback_query handler no webhook | Alto esforço — perde valor se painel web já tem a função |

### Anti-features

| Feature | Motivo |
|---------|--------|
| Bot com persistência de conversa (estados) | Canal de cortes não tem fluxo conversacional; comandos são stateless |
| Integração com grupos Telegram | Chat privado com operador é suficiente e mais seguro |
| Bot como interface primária de configuração | Painel Filament é o lugar certo; bot é para alertas e ações rápidas |
| Polling (getUpdates loop) | Webhook é mais eficiente e já está planejado via nginx em `alessandromelo.com.br/telegramcanal` |
| Múltiplos bots (um por canal) | Um bot único que notifica sobre todos os canais é suficiente |

---

## Copyright Protection

**Contexto legal:** Clips transformados (9:16, legendas, corte, watermark) + créditos + duração ≤ 60s = Fair Use defensável no Brasil e EUA. Emissoras grandes (Globo, SBT, Band, ESPN) têm histórico de Content ID agressivo.

### Table Stakes
_Proteção mínima defensável._

| Feature | Como implementar | Complexidade |
|---------|-----------------|--------------|
| Watermark/logo queimado no clip via FFmpeg | Filtro `-filter_complex "[1:v]format=rgba,colorchannelmixer=aa=0.5[logo];[0:v][logo]overlay=W-w-20:H-h-20"` — adicionar ao `video_processor.py` antes de gravar clip final | Baixa |
| Créditos na descrição | `metadata_generator.py` inclui `channel_name` e URL original no template da descrição Claude Haiku — já gerado, só formalizar no prompt | Baixíssima |
| Blacklist de canais-fonte | Coluna `blacklisted BOOLEAN DEFAULT FALSE` em `source_channels` + `active=TRUE AND blacklisted=FALSE` nas queries do pipeline | Baixa |
| Pré-popular blacklist com emissoras conhecidas | `source_channels` seed com Globo, SBT, Band, ESPN Brasil, Record, CazéTV marcados como `blacklisted=TRUE` | Baixa |

### Differentiators

| Feature | Detalhe | Valor |
|---------|---------|-------|
| Logo com posição configurável por canal-destino | `destination_channels.watermark_position ENUM('bottom-right','bottom-left','top-right')` | Baixo — bottom-right é padrão universal |
| Logo com transparência ajustável | `colorchannelmixer=aa={opacity}` onde opacity vem de config; 0.4–0.6 é a faixa ideal (visível sem obstruir) | Baixo |
| Gerenciar blacklist pelo painel Filament | Resource `SourceChannel` com toggle `blacklisted` — operador adiciona novos sem SQL | Médio |
| Notificação no Telegram quando canal monitorado entra na lista | Evento ao setar `blacklisted=TRUE` via painel; aviso de que clips existentes não serão afetados | Baixo |

### Anti-features

| Feature | Motivo para evitar |
|---------|-------------------|
| Detecção automática de copyright via Content ID API | API não disponível para contas comuns; só parceiros YouTube certificados têm acesso |
| Alterar áudio (pitch shift, speed) para evitar fingerprint | Degrada qualidade perceptível; clips de futebol com voz distorcida ficam ruins |
| Marca d'água de texto com nome do canal no vídeo | Texto fixo parece spam; logo gráfico é mais profissional e aceitável |
| Sistema de DMCA strikes tracker | Complexidade alta; responder manualmente ao primeiro strike é suficiente em v2 |
| Delay artificial entre clips do mesmo canal-fonte | Não reduz risco de DMCA; Content ID é automático e não considera frequência |

---

## Feature Dependencies

### Mudanças necessárias no schema MySQL existente

```sql
-- 1. Adicionar nicho e blacklist em source_channels
ALTER TABLE source_channels
  ADD COLUMN niche ENUM('futebol', 'podcast') NOT NULL DEFAULT 'futebol' AFTER channel_name,
  ADD COLUMN blacklisted BOOLEAN DEFAULT FALSE AFTER active;

-- 2. Nova tabela: canais de destino YouTube
CREATE TABLE destination_channels (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  youtube_channel_id VARCHAR(64) NOT NULL UNIQUE,
  niche ENUM('futebol', 'podcast') NOT NULL,
  token_path VARCHAR(512),          -- path para token.json deste canal
  oauth_status ENUM('authorized', 'expired', 'missing') DEFAULT 'missing',
  uploads_today INT DEFAULT 0,      -- denormalizado para dashboard rápido
  active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 3. Ligar clips ao canal de destino onde foram publicados
ALTER TABLE generated_clips
  ADD COLUMN destination_channel_id INT NULL AFTER source_video_id,
  ADD CONSTRAINT fk_clips_dest_channel
    FOREIGN KEY (destination_channel_id) REFERENCES destination_channels(id);
```

**O que NÃO muda:** `source_videos`, `generated_clips` (exceto coluna acima), ENUM de status, Redis quota keys (só mudará de string para incluir channel_id).

### Mudanças mínimas no código Python existente

| Arquivo | O que muda | Impacto |
|---------|-----------|---------|
| `uploader.py` | `token_file` passa a ser argumento dinâmico (já suportado via `__init__`); recebe `token_path` do canal-destino | Mudança de 1 linha no chamador |
| `publisher.py` | `_fetch_pending_clips` faz JOIN com `destination_channels` para obter `token_path`; passa para `YouTubeUploader` | ~10 linhas |
| `quota_manager.py` | Chave Redis muda de `youtube_uploads:{date}` para `youtube_uploads:{channel_id}:{date}`; `__init__` recebe `channel_id` | ~5 linhas |
| `video_processor.py` | Adicionar filtro watermark ao comando FFmpeg de corte; path do logo como variável de env `WATERMARK_PATH` | ~5 linhas no comando FFmpeg |
| `telegram_notifier.py` | Mudar `N8N_NOTIFY_URL` para apontar para endpoint Laravel; zero mudança de lógica | 1 env var |
| `metadata_generator.py` | Incluir `channel_name` e URL do vídeo original no template passado ao Claude Haiku | 1-2 linhas no prompt |

**Nenhuma mudança estrutural no pipeline Python.** O core (RSS → download → Whisper → Haiku → FFmpeg → YouTube) permanece intacto. As adições são pontuais e backward-compatible.

### Ordem de implementação recomendada por dependência

```
1. Schema migration (destination_channels, niche, blacklisted)
   ↓
2. Blacklist + niche em source_channels (sem risco de quebrar pipeline existente)
   ↓
3. Laravel/Filament install + recursos básicos (SourceChannel, SourceVideo, GeneratedClip)
   ↓
4. OAuth multi-canal + tabela destination_channels
   ↓ (depende de destination_channels existir)
5. Roteamento nicho→canal + quota por canal no Python
   ↓
6. Watermark FFmpeg (independente, pode ser paralelo ao passo 3)
   ↓
7. Telegram bot no Laravel (substitui n8n notifier; depende de Laravel estar rodando)
```

---

## Fontes

- [Filament 3 Installation](https://filamentphp.com/docs/3.x/panels/installation) — HIGH confidence
- [Filament 3 Resources Getting Started](https://filamentphp.com/docs/3.x/panels/resources/getting-started) — HIGH confidence
- [Filament 3 Stats Overview Widgets](https://filamentphp.com/docs/3.x/widgets/stats-overview) — HIGH confidence
- [Filament 3 Actions & Modals](https://filamentphp.com/docs/3.x/actions/modals) — HIGH confidence
- [irazasyed/telegram-bot-sdk Webhook & Updates](https://irazasyed.github.io/telegram-bot-sdk/usage/webhook-updates/) — HIGH confidence
- [telegram-bot-sdk.com Webhook Guide](https://telegram-bot-sdk.com/docs/guides/webhook-updates/) — HIGH confidence
- [YouTube OAuth 2.0 Server-Side](https://developers.google.com/youtube/v3/guides/auth/server-side-web-apps) — HIGH confidence
- [YouTube OAuth Refresh Token Expiry (Google Dev Forum)](https://discuss.google.dev/t/oauth2-refresh-token-expiration-and-youtube-api-v3/160874) — MEDIUM confidence (forum, verificado com doc oficial)
- [FFmpeg Watermark/Overlay Guide (Mux)](https://www.mux.com/articles/add-watermarks-to-a-video-with-ffmpeg) — HIGH confidence
- [FFmpeg colorchannelmixer opacity](https://wiki.tonytascioglu.com/scripts/ffmpeg/overlay_transparent_logo_over_video) — MEDIUM confidence (verificado com Mux)
- [Setup Telegram Bot SDK with webhook in Laravel](https://www.xibel-it.eu/setup-telegram-bot-sdk-with-webhook-in-laravel/) — MEDIUM confidence
