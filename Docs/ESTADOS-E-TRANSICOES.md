# Estados e transições

> Tipo: referência as-built · Atualizado: 2026-08-26

A fila está no PostgreSQL, nas colunas `source_videos.status` e
`generated_clips.status`. Redis não é fila.

## Vídeo fonte: `source_videos.status`

Valores da migration `2026_08_26_000001_create_source_videos_table.php`:

~~~text
pending → downloading → downloaded → transcribing → selecting
                                                        │
                                                        ├─ clips gerados → (aguarda clips)
                                                        ├─ 0 clips válidos → failed
                                                        └─ clips terminais + ≥1 published → published
~~~

| Estado | Quem escreve | Significado |
|---|---|---|
| `pending` | RSS, URL manual, pause/recovery | aguardando janela de download |
| `downloading` | `pipeline_runner.py` | download em andamento |
| `downloaded` | download concluído ou pause após transcrição | raw disponível |
| `transcribing` | `rss_poller.py` | transcrição em andamento |
| `selecting` | `rss_poller.py` | seleção IA em andamento ou clips aguardando corte/publicação |
| `published` | `publisher.py` | fonte finalizada; raw e clips foram limpos |
| `failed` | download, transcrição, seleção ou processamento | etapa sem recuperação automática |

Os valores `cutting` e `publishing` existem no enum por compatibilidade, mas o
código atual não os escreve em `source_videos`. O status do corte e do upload fica no clip.

## Clip: `generated_clips.status`

Valores da migration `2026_08_26_000003_create_generated_clips_table.php`:

~~~text
pending_cut → cutting → pending ──┐
                       └→ failed  │
pending ──────────────────────────┼→ publishing → published
approved ─────────────────────────┘
pending/approved → rejected
~~~

| De | Para | Quem escreve | Condição |
|---|---|---|---|
| — | `pending_cut` | seleção IA | momento com score ≥ 7 |
| `pending_cut` | `cutting` | `video_processor.process_clip` | início do render |
| `cutting` | `pending` | `video_processor.py` | corte, metadata e thumbnail concluídos |
| `cutting` | `failed` | `video_processor.py` | qualquer exceção |
| `pending` | `approved` | painel ou Telegram | aprovação manual |
| `pending` | `publishing` | `publisher.py` | `MANUAL_APPROVAL_REQUIRED=false` |
| `approved` | `publishing` | `publisher.py` | aprovação manual concluída |
| `publishing` | `published` | `publisher.py` | upload e thumbnail concluídos |
| `publishing` | `pending`/`approved` | `publisher.py` | upload parcial; preserva ID para retomada |
| `publishing` | `pending` | recovery | status sem update há mais de 15 min |
| `pending`/`approved` | `rejected` | painel, Telegram ou rejeição interna | remove MP4 final; preserva raw |
| `failed` | `pending_cut` ou publicável | painel | reprocessamento; depende de `clip_path` |

A geração de clips limita-se a 3 por vídeo curto e 1 por vídeo longo. A inserção remove overlaps e
repetições antes de gravar os registros.

## Recovery

| Situação | Frequência | Ação |
|---|---|---|
| `source_videos.downloading` | boot + a cada 30 min | volta para `pending` |
| `source_videos.selecting` com raw e sem progresso por 2 h | a cada 30 min | volta para `downloaded` |
| `source_videos.selecting` sem raw por 2 h | a cada 30 min | vai para `failed` |
| `source_videos.selecting` sem clips e com raw | a cada 30 min | volta para `downloaded` |
| `generated_clips.publishing` sem update por 15 min | a cada 30 min | volta para `pending` |
| `generated_clips.cutting` | somente no boot | volta para `pending_cut` |
| `source_videos.transcribing` | — | não há recovery automático |

O corte não é recuperado no job periódico porque pode durar mais que 30 minutos. Durante pause, o
pipeline mata `yt-dlp`/FFmpeg quando possível e devolve o trabalho ao estado apropriado.

## Janela, pausa e limpeza

- A janela de download conta fontes com raw local ou status ativo e clips em
  `pending_cut`, `cutting`, `pending` e `approved`.
- `pause` marca `source_videos.paused=true`. Download é abortado e volta a
  `pending`; transcrição/seleção cooperam entre etapas; cortes em andamento voltam a
  `pending_cut`.
- O raw só pode ser removido quando nenhum clip da fonte precisa dele.
- O publisher finaliza a fonte apenas com zero clips não terminais e pelo menos um clip publicado.
  Então remove raw, MP4s, SRTs, intermediários e thumbnails, zera caminhos e marca a fonte como
  `published`.
- Sempre confira status e caminho real antes de apagar. O guard de `source_videos.status`
  sozinho não detecta todos os casos de clip em uso; consulte também `generated_clips.status`.

## Fontes de verdade

- estados permitidos: migrations em `painel/database/migrations/`;
- transições: `clip-processor/src/db.py`, `pipeline_runner.py`,
  `rss_poller.py`, `video_processor.py`, `publisher.py` e
  `queue_controls.py`;
- operação segura: [`../CLAUDE.md`](../CLAUDE.md).
