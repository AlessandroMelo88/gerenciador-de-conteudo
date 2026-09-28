# Vídeo, FFmpeg e assets

> Tipo: referência as-built · Atualizado: 2026-08-26
> Fontes: `video_processor.py`, `media_composer.py` e
> `media_assets.py`

## Fluxo do clip

`video_processor.process_clip` aceita um clip em `pending_cut`:

~~~text
pending_cut → cutting → render + metadata + thumbnail → pending
                              └─ qualquer exceção → failed
~~~

1. lê raw, transcrição e intervalo;
2. completa bordas para não cortar fala;
3. gera trecho raw;
4. aplica render específico do formato;
5. aplica watermark quando disponível;
6. compõe assets obrigatórios do longo;
7. gera metadata e texto da thumbnail;
8. extrai frame, grava texto na thumbnail e persiste caminhos;
9. muda o clip para `pending`.

Falha em qualquer etapa marca `failed`. O tratamento atual não garante remoção de todos
os intermediários em toda falha; confira `videos/clips` antes de uma limpeza manual.

## Formatos

| Formato | Corte | Legenda | Dimensão/saída |
|---|---|---|---|
| `curto` | janela exata de 30s | render único com quadro vertical, SRT queimado salvo quando a fonte já tem legenda gravada, e watermark opcional | vertical 1080×1920 |
| `longo` | trecho horizontal | SRT gerado depois da composição e enviado como legenda oficial | horizontal, altura 1080 |

### Curto

O vídeo horizontal completo é mantido em primeiro plano. Uma cópia ampliada, desfocada e
escurecida preenche o canvas 9:16. A faixa de áudio recebe fade in/out curto. O SRT usa DejaVu Sans
Bold, fica na região inferior e é aplicado via libass.

#### Fonte que já vem legendada

Antes de queimar, `subtitle_detector.has_burned_subtitles` verifica se o próprio vídeo fonte já
traz legenda gravada no quadro — queimar de novo deixaria dois textos na tela. A verificação lê
a metade inferior de 6 quadros do trecho com OCR (`tesseract -l por`) e cruza as palavras lidas
com a transcrição daquele mesmo segundo. Só decide "já tem legenda" quando pelo menos 3 quadros
batem e eles são 60% ou mais das leituras: placar, lower-third, código na tela e estante ao
fundo não repetem a fala, mas um apresentador que lê a tela em voz alta repete por alguns
segundos. O SRT continua sendo gerado nos dois casos, porque é dele que sai a legenda oficial
do YouTube.

A detecção erra para o lado seguro: quando não consegue decidir (OCR ilegível, tesseract
ausente, FFmpeg com erro) ela devolve "não tem" e o pipeline queima a legenda como sempre fez.
Legenda animada palavra a palavra em fonte estilizada de vídeo 360p escapa do OCR. Para
Para desligar a detecção, use `BURNED_SUBTITLE_DETECTION=false`; o padrão é `true`.

Shorts não recebem intro, encerramento ou música.

### Longo

O trecho é normalizado para canvas horizontal 1920×1080. Intro, conteúdo e encerramento são unidos
com transição curta; a música é misturada nos 15 segundos finais do vídeo composto. O encerramento
pode receber card com thumbnail/título de outro vídeo publicado no mesmo destino.

O longo exige os três tipos `intro`, `outro` e `music`. Se algum faltar,
o clip falha. O SRT é gerado após a composição, com offset calculado para a intro, e o uploader o envia como
legenda oficial `pt-BR`.

## Resolução de assets

Ordem:

1. filesystem canônico por canal: `assets/channels/<slug>`;
2. biblioteca legada em `media_assets` no PostgreSQL.

Arquivos aceitos:

| Tipo | Nomes no filesystem |
|---|---|
| intro | `intro.mp4`, `intro.mov`, `intro.webm`, imagens equivalentes |
| outro | `encerramento.mp4`, `outro.mp4`, imagens equivalentes |
| music | qualquer `.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac` ou `.aac` em `assets/audio` |

Para cada tipo, a resolução prioriza canal + formato, depois prioridade e uma rotação determinística
por ID do clip. Imagens são transformadas em vídeo estático de 3 s quando necessário. A música é
misturada nos 15 segundos finais do vídeo já composto: começa bem baixa, sobe durante 7 segundos e
fica no volume final nos 8 segundos finais. O volume configurado recebe ganho de 20%, limitado a 100%,
e a faixa entra em loop apenas para cobrir esse trecho.

A marca d’água é `/app/branding/watermark-{destination_slug}.png`, no canto superior
direito. Se não existir, o pipeline segue sem watermark.

## Relacionado e thumbnail

- o relacionado prioriza o último clip publicado no canal-destino; se não houver, o código pode
  usar o vídeo fonte conforme o contexto;
- a miniatura do relacionado é baixada para o card quando o YouTube responder;
- a thumbnail do clip é um frame em 1 s do resultado final;
- `generate_thumbnail_text` escolhe a frase literal da transcrição;
- `overlay_thumbnail_text` grava a frase em JPG com FFmpeg;
- sem frase literal válida, o clip falha.

## Artefatos

| Artefato | Local |
|---|---|
| raw fonte | `/app/videos/<youtube_id>.mp4` |
| transcript | `/app/videos/<youtube_id>_transcript.json` |
| raw do clip | `/app/videos/clips/<id>_raw.mp4` |
| SRT | `/app/videos/clips/<id>.srt` |
| intermediário de Shorts | `/app/videos/clips/<id>_subtitled.mp4` |
| final | `/app/videos/clips/<id>.mp4` |
| thumbnail | `/app/videos/thumbnails/<id>.jpg` |

Os caminhos finais ficam em `generated_clips.clip_path` e
`generated_clips.thumbnail_path`. Na finalização da fonte, o publisher remove raw, finals,
SRTs, intermediários e thumbnail, zera os dois caminhos e marca a fonte como publicada.

## Operação segura

Não apague raw se houver clip em `pending_cut` ou `cutting`. Não classifique
`*.srt` ou `*_raw.mp4` como órfão só porque não aparecem em colunas próprias:
filtre pelo ID de `generated_clips` e pelo estado. Consulte [`../CLAUDE.md`](../CLAUDE.md).
