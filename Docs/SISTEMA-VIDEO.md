# Corte e pós-produção de vídeo

Tudo que o FFmpeg faz: cortar, legendar Shorts, aplicar a identidade configurável, marcar e gerar
thumbnail. O orquestrador está em [`video_processor.py`](../clip-processor/src/video_processor.py),
com a seleção de assets em [`media_assets.py`](../clip-processor/src/media_assets.py) e a composição
em [`media_composer.py`](../clip-processor/src/media_composer.py).

A **escolha** dos trechos é assunto de [`SISTEMA-IA-SELECAO.md`](SISTEMA-IA-SELECAO.md); aqui o
`start_time`/`end_time` já vem decidido no banco.

Verificado no código em **26/08/2026**.

---

## `process_clip` — o orquestrador

[`video_processor.py:251`](../clip-processor/src/video_processor.py#L251). Roda por clip em
`pending_cut`, disparado por `_process_pending_clips`
([`rss_poller.py:158`](../clip-processor/src/rss_poller.py#L158)) — que só pega clips cujo vídeo fonte
tem `paused = 0`.

| # | Etapa | Função | Saída |
|---|---|---|---|
| 0 | marca `cutting` | [`:264`](../clip-processor/src/video_processor.py#L264) | — |
| 1 | corta o trecho | `cut_clip` [`:46`](../clip-processor/src/video_processor.py#L46) | `clips/<id>_raw.mp4` |
| 2 | (curto) gera legenda | `generate_srt` [`:108`](../clip-processor/src/video_processor.py#L108) | `clips/<id>.srt` |
| 3 | (curto) queima legenda | `burn_subtitles` [`:137`](../clip-processor/src/video_processor.py#L137) | `clips/<id>_subtitled.mp4` |
| 4 | marca d'água | `overlay_watermark` [`:214`](../clip-processor/src/video_processor.py#L214) | `clips/<id>.mp4` |
| 5 | intro, encerramento e música | `resolve_media_assets` + `compose_media` | `clips/<id>.mp4` atualizado |
| 6 | gera metadata SEO | `generate_metadata` | title/description/tags em memória |
| 7 | escolhe a chamada da thumbnail | `generate_thumbnail_text` | `thumbnail_text` em memória |
| 8 | extrai o frame | `extract_thumbnail` | `thumbnails/<id>.jpg` |
| 9 | sobrepõe a chamada | `overlay_thumbnail_text` | `thumbnails/<id>.jpg` enriquecida |
| 10 | grava `clip_path`/`thumbnail_path` | [`:472`](../clip-processor/src/video_processor.py#L472) | — |
| 11 | persiste título/descrição/tags | `update_clip_metadata` | — |
| 12 | marca `pending` | [`:478`](../clip-processor/src/video_processor.py#L478) | — |

Todo o corpo está num `try/except` único ([`:250`](../clip-processor/src/video_processor.py#L250)):
qualquer exceção ⇒ clip vira `failed` e a função retorna `False`. Não há retry, e não há limpeza dos
intermediários nesse caminho.

O transcript é lido do disco em [`:202`](../clip-processor/src/video_processor.py#L202) via
`clip['transcript_path']`; se o arquivo não existir, o clip vai direto para `failed`.

Em `format='longo'`, as etapas 2 e 3 são puladas: o arquivo `_raw.mp4` segue direto para a etapa
de marca d'água (se houver) e depois é promovido ao `<id>.mp4`. Assim, vídeos longos permanecem
horizontais e não recebem legenda queimada.

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

`burn_subtitles` ([`:137`](../clip-processor/src/video_processor.py#L137)) queima com o filtro
`subtitles` do libass **somente quando `fmt='curto'`**. A própria função rejeita chamadas com
`fmt='longo'`, e `process_clip` nem gera o SRT nesse formato. Estilo, e o porquê de cada escolha:

| Propriedade | Valor | Motivo (do próprio código) |
|---|---|---|
| `Fontname` | `DejaVu Sans`, `Bold=1` | única família disponível no container (`fc-list`) |
| `Fontsize` | 38 | — |
| `PlayResX/PlayResY` | 1080 / 1920 | `Fontsize` é relativo a isso; sem `PlayRes` explícito o texto sai desproporcionalmente pequeno |
| `BorderStyle=3, BackColour=&H60000000` | caixa fina semi-transparente | imita o closed caption nativo do YouTube em vez de bloco opaco |
| `Alignment=2, MarginV=180` | rodapé-centro, afastado | afasta da barra de interações do player |

`-c:a copy` — o áudio não é re-encodado nesta etapa.

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
| slug existe e o PNG existe | overlay aplicado; o intermediário (`_subtitled.mp4` no curto ou `_raw.mp4` no longo) é removido |
| slug existe e o PNG **não** existe | `overlay_watermark` retorna o input sem chamar FFmpeg; o intermediário é **renomeado** para o path final |
| clip sem `destination_channel_id` | renomeia direto, sem overlay |

Nos dois últimos casos o clip sai **sem marca d'água e sem erro** — nada no painel sinaliza isso.

---

## Biblioteca de assets

A fonte de verdade agora é a pasta [`assets/`](../assets/), montada no worker como `/app/assets`:

```text
assets/
├── channels/<slug-do-canal>/
│   ├── intro.jpg
│   ├── intro.mp4
│   ├── encerramento.jpg
│   └── encerramento.mp4
└── audio/
    ├── faixa_completa.wav
    └── faixa_completa.txt   # letra, quando existir
```

Para intro e encerramento, o vídeo é preferido e a imagem é fallback. A seleção da faixa em `audio/`
é determinística pelo id do clip. A tabela `media_assets` e o disk `branding` continuam aceitos como
fallback para instalações antigas ou assets cadastrados pelo painel.

Em `format='longo'`, intro, encerramento e música são obrigatórios. Se algum dos três não existir,
o clip é marcado como `failed` e não pode seguir para publicação sem identidade completa. A sequência
final é `intro → conteúdo → encerramento`; um trecho da faixa é misturado somente no encerramento,
em volume 0,12 por padrão, preservando a fala do conteúdo principal. Entre as cenas, o compositor
aplica um crossfade curto de vídeo e áudio, calculado a partir da duração real de cada segmento; assim,
uma imagem/intro curta nunca recebe uma transição longa demais. Imagens recebem 3 segundos por padrão;
vídeos respeitam sua duração.

Quando existe um encerramento, a etapa de composição pode preencher a área reservada com a miniatura e
o título de um vídeo relacionado. A escolha prioriza o último clip publicado no mesmo canal-destino e
usa o vídeo fonte como fallback no primeiro clip. A publicação também acrescenta o link desse destino
no final da descrição. A tela final clicável do YouTube continua sendo uma configuração do Studio e
não é exposta pelo `videos.insert` da Data API; o card renderizado e o link garantem o destino mesmo
no fluxo autônomo.

---

## Thumbnail

`extract_thumbnail` ([`:194`](../clip-processor/src/video_processor.py#L194)): um frame, `-q:v 2`,
JPG. O `at_seconds` usado por `process_clip` é 1 segundo, para obter uma imagem após o início do
trecho.

Depois do frame, `overlay_thumbnail_text` ([`:234`](../clip-processor/src/video_processor.py#L234))
usa `drawtext` para colocar no alto da imagem uma frase curta, em branco, com contorno e caixa preta
semitransparente. A frase vem de `generate_thumbnail_text`, que usa um prompt exclusivo para
selecionar a fala mais polêmica, surpreendente ou contundente do trecho, literal e contínua, sem o
contexto explicativo da thumbnail. A resposta só é aceita quando é uma sequência presente na
transcrição e respeita os limites de legibilidade.

O texto é gravado em arquivo temporário UTF-8 (`textfile`) para que aspas, acentos e pontuação não
quebrem o parser do FFmpeg. Se a IA não retornar uma chamada válida ou o `drawtext` falhar, a exceção
marca o clip como `failed`; não há fallback para uma frase local nem para uma thumbnail sem texto.

---

## Artefatos em disco

| Padrão | Diretório | Está no banco? | Quem apaga |
|---|---|---|---|
| `<clip_id>.mp4` | `videos/clips/` | `generated_clips.clip_path` | `_maybe_finalize_source_video`; `rejeitar.py` |
| `<clip_id>.jpg` | `videos/thumbnails/` | `generated_clips.thumbnail_path` | `_maybe_finalize_source_video` |
| `<clip_id>_raw.mp4` | `videos/clips/` | **não** | `_maybe_finalize_source_video` (desde 12/08/2026) |
| `<clip_id>_subtitled.mp4` | `videos/clips/` | **não** | caminho feliz de `process_clip` para `curto`; senão `_maybe_finalize_source_video` |
| `<clip_id>.srt` | `videos/clips/` | **não** | gerado somente para `curto`; **ninguém** limpa o arquivo |

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

`generate_metadata` ([`metadata_generator.py:404`](../clip-processor/src/metadata_generator.py#L404)),
chamado antes da extração da thumbnail, gera apenas os campos persistidos. A chamada textual é uma
etapa separada em `generate_thumbnail_text`, com prompt e schema próprios. O provider é escolhido
pela configuração:

| Configuração | Provider | Modelo |
|---|---|---|
| `ANTHROPIC_API_KEY` preenchida | Anthropic | `claude-haiku-4-5` |
| `ANTHROPIC_API_KEY` ausente | Groq | `openai/gpt-oss-120b` |

**`ANTHROPIC_API_KEY` está vazia na operação normal**, então o provider selecionado para metadata e
thumbnail em produção é o **Groq**.

`generate_thumbnail_text` usa o provider definido pela configuração (`ANTHROPIC_API_KEY` para Claude;
sem ela, Groq), mas só aceita uma resposta que seja uma sequência literal da transcrição. Se o
provider não entregar metadata completa ou uma chamada válida, o clip é marcado como `failed`; não há
conteúdo determinístico ou outro provider substituindo o prompt dedicado.

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
