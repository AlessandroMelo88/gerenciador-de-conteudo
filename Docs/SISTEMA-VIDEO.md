# Corte e pós-produção de vídeo

Tudo que o FFmpeg faz: cortar, legendar, marcar e gerar thumbnail. Módulo único,
[`video_processor.py`](../clip-processor/src/video_processor.py).

A **escolha** dos trechos é assunto de [`SISTEMA-IA-SELECAO.md`](SISTEMA-IA-SELECAO.md); aqui o
`start_time`/`end_time` já vem decidido no banco.

Verificado no código em **13/08/2026**.

---

## `process_clip` — o orquestrador

[`video_processor.py:188`](../clip-processor/src/video_processor.py#L188). Roda por clip em
`pending_cut`, disparado por `_process_pending_clips`
([`rss_poller.py:158`](../clip-processor/src/rss_poller.py#L158)) — que só pega clips cujo vídeo fonte
tem `paused = 0`.

| # | Etapa | Função | Saída |
|---|---|---|---|
| 0 | marca `cutting` | [`:200`](../clip-processor/src/video_processor.py#L200) | — |
| 1 | corta o trecho | `cut_clip` [`:34`](../clip-processor/src/video_processor.py#L34) | `clips/<id>_raw.mp4` |
| 2 | gera legenda | `generate_srt` [`:72`](../clip-processor/src/video_processor.py#L72) | `clips/<id>.srt` |
| 3 | queima legenda | `burn_subtitles` [`:99`](../clip-processor/src/video_processor.py#L99) | `clips/<id>_subtitled.mp4` |
| 4 | marca d'água | `overlay_watermark` [`:158`](../clip-processor/src/video_processor.py#L158) | `clips/<id>.mp4` |
| 5 | thumbnail | `extract_thumbnail` [`:137`](../clip-processor/src/video_processor.py#L137) | `thumbnails/<id>.jpg` |
| 6 | grava `clip_path`/`thumbnail_path` | [`:235`](../clip-processor/src/video_processor.py#L235) | — |
| 7 | gera título/descrição/tags | `generate_metadata` [`:244`](../clip-processor/src/video_processor.py#L244) | — |
| 8 | marca `pending` | [`:246`](../clip-processor/src/video_processor.py#L246) | — |

Todo o corpo está num `try/except` único ([`:250`](../clip-processor/src/video_processor.py#L250)):
qualquer exceção ⇒ clip vira `failed` e a função retorna `False`. Não há retry, e não há limpeza dos
intermediários nesse caminho.

O transcript é lido do disco em [`:202`](../clip-processor/src/video_processor.py#L202) via
`clip['transcript_path']`; se o arquivo não existir, o clip vai direto para `failed`.

---

## Corte por formato

`cut_clip` ([`:34`](../clip-processor/src/video_processor.py#L34)) muda **só o filtro de vídeo**:

| `fmt` | Filtro | Resultado |
|---|---|---|
| `curto` (default) | `scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1` | vertical 1080x1920 (Shorts) |
| `longo` | `scale=-2:1080,setsar=1` | mantém o horizontal, normaliza a altura em 1080p |

Encode comum aos dois: `-ss/-to` antes do `-i`, `libx264 -preset veryfast -crf 23`, `aac -b:a 128k`,
`-movflags +faststart`.

`-ss` antes do `-i` é seek rápido por keyframe — pode deslocar o início em fração de segundo em
relação ao `start_time` pedido.

---

## Legendas

`generate_srt` ([`:72`](../clip-processor/src/video_processor.py#L72)) recorta os `segments` do
transcript Whisper para a janela do clip e **rebaseia os timestamps em zero**
([`:83-84`](../clip-processor/src/video_processor.py#L83)): segmento que atravessa a borda é
truncado, segmento fora da janela é descartado, texto vazio é ignorado.

`burn_subtitles` ([`:99`](../clip-processor/src/video_processor.py#L99)) queima com o filtro
`subtitles` do libass. Estilo, e o porquê de cada escolha:

| Propriedade | Valor | Motivo (do próprio código) |
|---|---|---|
| `Fontname` | `DejaVu Sans`, `Bold=1` | única família disponível no container (`fc-list`) |
| `Fontsize` | 38 | — |
| `PlayResX/PlayResY` | 1080 / 1920 | `Fontsize` é relativo a isso; sem `PlayRes` explícito o texto sai desproporcionalmente pequeno |
| `BorderStyle=3, BackColour=&H60000000` | caixa fina semi-transparente | imita o closed caption nativo do YouTube em vez de bloco opaco |
| `Alignment=2, MarginV=180` | rodapé-centro, afastado | afasta da barra de interações do player |

`-c:a copy` — o áudio não é re-encodado nesta etapa.

**`PlayResY=1920` é fixo**, inclusive para clips `longo` (que são 1920x1080). Não confirmei o efeito
visual disso no formato horizontal; pelo raciocínio do próprio comentário do código, a escala da
fonte deveria sair diferente do esperado em `longo`. Vale conferir num clip longo real antes de mexer.

---

## Marca d'água

`overlay_watermark` ([`:158`](../clip-processor/src/video_processor.py#L158)):
`-filter_complex overlay=W-w-20:20` — canto superior direito, margem de 20 px.

O PNG vem de `/app/branding/watermark-<slug>.png`, onde `<slug>` é
`destination_channels.slug` ([`:216-218`](../clip-processor/src/video_processor.py#L216)).
O painel faz upload desses arquivos (`POST /painel/canais-destino/.../watermark`); o volume é
montado **read-only** no `clip-processor` e read-write no `php`.

Degradação graciosa em três caminhos ([`:215-230`](../clip-processor/src/video_processor.py#L215)):

| Situação | O que acontece |
|---|---|
| slug existe e o PNG existe | overlay aplicado, `_subtitled.mp4` removido |
| slug existe e o PNG **não** existe | `overlay_watermark` retorna o input sem chamar FFmpeg; `_subtitled.mp4` é **renomeado** para o path final |
| clip sem `destination_channel_id` | renomeia direto, sem overlay |

Nos dois últimos casos o clip sai **sem marca d'água e sem erro** — nada no painel sinaliza isso.

---

## Thumbnail

`extract_thumbnail` ([`:137`](../clip-processor/src/video_processor.py#L137)): um frame, `-q:v 2`,
JPG. O `at_seconds` usado por `process_clip` é `duração / 2`
([`:232-233`](../clip-processor/src/video_processor.py#L232)) — o meio do clip, não o início.

**Não há ramo por formato**: `curto` e `longo` geram thumbnail igual. Isso já foi verificado ao
investigar a suspeita de thumbnail faltando nos longos — o defeito, se existir, está na aplicação via
API do YouTube, não aqui. Ver [`BUGS.md`](BUGS.md) e
[`SISTEMA-PUBLICACAO.md`](SISTEMA-PUBLICACAO.md#thumbnail-sem-trycatch-próprio).

---

## Artefatos em disco

| Padrão | Diretório | Está no banco? | Quem apaga |
|---|---|---|---|
| `<clip_id>.mp4` | `videos/clips/` | `generated_clips.clip_path` | `_maybe_finalize_source_video`; `rejeitar.py` |
| `<clip_id>.jpg` | `videos/thumbnails/` | `generated_clips.thumbnail_path` | `_maybe_finalize_source_video` |
| `<clip_id>_raw.mp4` | `videos/clips/` | **não** | `_maybe_finalize_source_video` (desde 12/08/2026) |
| `<clip_id>_subtitled.mp4` | `videos/clips/` | **não** | caminho feliz de `process_clip`; senão `_maybe_finalize_source_video` |
| `<clip_id>.srt` | `videos/clips/` | **não** | **ninguém** |

`_raw.mp4` e `_subtitled.mp4` passaram a ser apagados na finalização do vídeo fonte
([`publisher.py:345-354`](../clip-processor/src/publisher.py#L345)) — antes ficavam para sempre e eram
o maior consumidor de disco do projeto. O `.srt` continua sem nenhuma rotina de limpeza (arquivo de
texto, KB).

**Nenhum desses auxiliares está em coluna do banco.** Cruzar disco × banco por **nome de arquivo**
classifica `.srt` e `_raw.mp4` como órfãos e apaga arquivo de clip vivo — filtrar pelo **id**
(prefixo numérico antes de `.` ou `_`). Regra 3 do [`../CLAUDE.md`](../CLAUDE.md).

### Buraco que sobra

O `except` de `process_clip` marca `failed` e **não limpa nada**. Um clip que morra entre o passo 1 e
o 4 deixa `_raw.mp4` e possivelmente `_subtitled.mp4` no disco, e `_maybe_finalize_source_video` só
os alcança se algum **outro** clip do mesmo vídeo chegar a publicar. Se nenhum publicar, ficam.

---

## Metadata do clip

`generate_metadata` ([`metadata_generator.py:124`](../clip-processor/src/metadata_generator.py#L124)),
chamado no passo 7. Ordem de tentativa, corrigida em 27/07/2026:

| Ordem | Caminho | Modelo |
|---|---|---|
| 1 | Anthropic | `claude-haiku-4-5` ([`:97`](../clip-processor/src/metadata_generator.py#L97)) |
| 2 | Groq | `llama-3.3-70b-versatile` ([`:112`](../clip-processor/src/metadata_generator.py#L112)) |
| 3 | determinístico | título = título bruto do vídeo original |

**`ANTHROPIC_API_KEY` está vazia na operação normal**, então o caminho 1 sempre levanta e quem gera a
metadata em produção é o **Groq** (caminho 2).

Antes do fallback Groq existir, essa mesma configuração caía **sempre** no caminho 3. Como o seletor tira
até 3 momentos por vídeo, os 3 clips saíam com título idêntico — parecia vídeo duplicado na fila de
aprovação, mas eram trechos diferentes do mesmo vídeo.

Créditos ao canal fonte são anexados **no momento da publicação**, não aqui: `append_credits`
([`:152`](../clip-processor/src/metadata_generator.py#L152)) e `resolve_credit_handle`
([`:164`](../clip-processor/src/metadata_generator.py#L164)) são chamados pelo publisher
([`publisher.py:69-76`](../clip-processor/src/publisher.py#L69)) usando
`destination_channels.credit_template`.

---

## Abortar um corte em andamento

`pause_video` ([`queue_controls.py:34`](../clip-processor/src/queue_controls.py#L34)) mata o ffmpeg do
clip (`pkill -f 'ffmpeg.*clips/<id>'`, [`:200`](../clip-processor/src/queue_controls.py#L200)) e
devolve o clip de `cutting` para `pending_cut` ([`:82`](../clip-processor/src/queue_controls.py#L82)).
Os intermediários do corte abortado **não** são limpos.
