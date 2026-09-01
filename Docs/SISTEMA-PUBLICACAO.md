# Publicação no YouTube

> Tipo: referência as-built · Atualizado: 2026-08-27
> Fontes: `publisher.py`, `quota_manager.py`, `uploader.py` e
> `youtube_oauth.py`

## Elegibilidade

O publisher seleciona somente clips com `clip_path` e `title`:

| Configuração | Status publicável |
|---|---|
| `MANUAL_APPROVAL_REQUIRED=false` (padrão) | `pending` |
| `MANUAL_APPROVAL_REQUIRED=true` | `approved` |

O painel e o Telegram mudam `pending` para `approved`. O publisher usa uma
transição condicional para evitar corrida com rejeição.

## Roteamento e ordem

A seleção resolve `destination_channel_id` pelo casamento entre o perfil ativo do canal-fonte e
`destination_channels.prompt_profile_id`. Para fontes legadas sem perfil, mantém o casamento por
`source_channels.target_niche`/`destination_channels.niche`. O publisher itera somente destinos
ativos e usa um uploader e uma quota por destino.

Dentro de cada destino:

1. ordena por `created_at ASC`;
2. intercala filas por canal-fonte (round-robin);
3. verifica janela e quota;
4. publica um clip por vez.

Se não houver destino ativo, existe caminho legado que usa `YOUTUBE_TOKEN_FILE` ou
`/app/token.json`.

## Quota

A data e a janela usam `America/Sao_Paulo`. Contadores ficam no Redis e expiram à meia-noite:

| Chave | Conteúdo |
|---|---|
| `youtube_uploads:<channel>:<YYYY-MM-DD>` | total do destino |
| `youtube_uploads:<channel>:<YYYY-MM-DD>:longo` | total de longos |

| Regra | Valor |
|---|---:|
| quota padrão total | 2/dia |
| teto absoluto total | 6/dia/destino |
| quota longa padrão no código | 2/dia, limitada pela quota total |
| valor no `.env.example` | `MAX_LONGO_UPLOADS_PER_DAY=1` |
| janela | 19:00 inclusive até 22:00 exclusivo |
| bypass | `UPLOAD_WINDOW_BYPASS=true` |

Quando há um longo elegível aguardando, a quota reserva slots para ele. Shorts usam somente o
saldo que não compromete essa reserva. Redis indisponível interrompe a publicação; não há fallback
de quota para PostgreSQL.

## Upload e finalização

`YouTubeUploader.upload_clip`:

1. valida MP4, título, thumbnail e SRT;
2. reutiliza `youtube_video_id` se houver upload parcial;
3. faz `videos.insert` resumível com categoria `17`;
4. envia/atualiza legenda oficial `pt-BR`, nome
   `Português (Brasil) — Legenda revisada`;
5. aguarda processamento do YouTube quando `YOUTUBE_WAIT_FOR_HD=true`;
6. aplica `YOUTUBE_PRIVACY_STATUS` (padrão `public`);
7. envia a thumbnail.

Quando o destino final não é `private`, o vídeo começa privado se precisar de legenda ou
espera HD e só fica público/unlisted após essas etapas. `selfDeclaredMadeForKids` é
sempre `false`.

Quando a espera HD está ativa, o worker consulta `processingDetails` até o status
`succeeded`. O limite padrão é 900 s (`YOUTUBE_PROCESSING_TIMEOUT_SECONDS`) e o intervalo padrão
é 10 s (`YOUTUBE_PROCESSING_POLL_SECONDS`); timeout, status `failed` ou `terminated` preserva
o ID do YouTube e deixa o clip retomável.

A legenda oficial é usada em curtos e longos. No curto, ela também está queimada no vídeo — exceto
quando a fonte já vinha legendada e a queima foi dispensada. No longo, fica como closed caption
selecionável.

## Erros e idempotência

- SRT ausente ou vazio → `CaptionNotReadyError` → clip volta para `pending_cut`;
- falha após o vídeo ter sido criado, durante legenda ou processamento → `PostUploadError`;
  grava o ID, preserva `pending`/`approved` e retoma sem criar outro vídeo;
- thumbnail com HTTP 403 → aviso; vídeo permanece publicado;
- outro erro de thumbnail ou upload → clip vira `failed`; confira o YouTube antes de
  reprocessar para evitar duplicata;
- refresh OAuth inválido → marca `destination_channels.oauth_expired_flag=true` e
  lança o erro; upload posterior bem-sucedido limpa a flag.

## OAuth

| Item | Valor |
|---|---|
| token por destino | `/app/youtube/token-<slug>.json` |
| client secrets | `YOUTUBE_CLIENT_SECRETS`, padrão do Compose `/app/youtube/client_secret.json` |
| scopes | `youtube.upload` e `youtube.force-ssl` |
| geração | `python -m src.youtube_oauth --channel <slug>` |

Não versione tokens. O segundo scope permite criar/atualizar a faixa de legendas.

## Relacionado e créditos

A descrição recebe um link `Assista também` para o último clip publicado no mesmo
destino; antes de existir histórico, usa o vídeo fonte. O link não é duplicado em retries.

Se o destino tiver `credit_template` e a fonte tiver handle/nome, o publisher acrescenta
crédito ao final da descrição. Sequências `@@` são normalizadas para um único `@`.

## Finalização da fonte

Depois de cada upload, a fonte é finalizada somente quando:

- não há clips em `pending_cut`, `cutting`, `pending`,
  `approved` ou `publishing`;
- existe pelo menos um clip `published`.

Então o código remove raw, MP4s, SRTs, intermediários e thumbnails, zera
`clip_path`/`thumbnail_path` e marca `source_videos.status=published`.
Se nenhum clip publicar, preserva o raw.

## TTL

O job horário rejeita clips `pending` sem ID do YouTube depois de
`CLIP_PENDING_TTL_HOURS` (padrão 48 h) e avisa na janela
`CLIP_PENDING_WARN_HOURS` (padrão 24 h). A chave
`clip_warned:<clip_id>` evita alertas repetidos.

O TTL usa `created_at`, não o tempo desde a última mudança de status.
