# Transcrição

> Tipo: referência as-built · Atualizado: 2026-08-26

Existem dois fluxos independentes. A transcrição principal alimenta a seleção de clips; a transcrição
local apenas gera um `.srt` para download do operador.

## Comparação

| Fluxo | Entrada | Motor | Saída | Entra na fila de clips? |
|---|---|---|---|---|
| pipeline principal | raw `.mp4` de `source_videos` | legenda manual PT-BR; fallback Groq Whisper | JSON temporizado | sim |
| transcrição local | URL enviada pelo painel | `whisper.cpp` local | `.srt` | não |

## Pipeline principal

`transcriber.transcribe_video`:

1. tenta legendas manuais em português pelo player Innertube;
2. tenta a faixa manual via `yt-dlp`;
3. ignora legendas automáticas/ASR;
4. sem faixa utilizável, envia o arquivo para Groq;
5. usa `whisper-large-v3-turbo`, `verbose_json`, timestamps por segmento,
   idioma `pt` e temperatura 0;
6. para arquivo maior que 24.000.000 bytes, extrai MP3 mono, 16 kHz e 32 kbps;
7. remove o áudio temporário;
8. salva `/app/videos/<video_id>_transcript.json` e atualiza
   `source_videos.transcript_path`.

O JSON tem `video_id`, `text` e `segments`, com `start`,
`end` e `text`. As faixas são normalizadas para remover sobreposição e texto
vazio.

Se todos os caminhos falharem, retorna `None`; o vídeo vai para `failed`. A
seleção só começa depois de `save_transcript` concluir.

## Transcrição local

O painel cria um registro em `transcription_jobs` e chama
`POST /internal/transcribe`. O endpoint retorna o ID imediatamente; o worker roda em
thread daemon separada.

Estados:

~~~text
pending → downloading (10%) → transcribing (50%) → done (100%)
                                      └──────────→ failed
~~~

Etapas:

- baixa somente áudio WAV com `yt-dlp` em `/app/videos/transcripts`;
- mede duração com `ffprobe`;
- até 1.500 s, executa uma passada;
- acima disso, divide em no máximo 3 partes, transcreve cada parte e ajusta timestamps;
- executa `whisper-cli` com modelo `ggml-small.bin`, idioma `pt` e saída
  SRT;
- junta partes, remove WAVs/SRTs intermediários e preserva apenas o SRT final;
- remove o áudio baixado mesmo em erro;
- persiste progresso apenas em marcos 10/50/100, não como percentual real do Whisper.

O download do SRT ocorre pelas rotas autenticadas do painel
`/painel/transcricoes/{job}/download`. Nenhum registro local altera
`source_videos` ou `generated_clips`, e não consome quota da API do YouTube.

## Falhas e operação

- pipeline principal sem transcrição válida → fonte `failed`;
- worker local com qualquer exceção → job `failed` e `error_message`;
- `transcribing` em `source_videos` não tem recovery automático;
- os binários e modelos locais são definidos por `WHISPER_CPP_BIN` e
  `WHISPER_MODEL_PATH`.

Fontes: `clip-processor/src/transcriber.py`, `transcription_job.py`,
`internal_api.py` e `painel/app/Http/Controllers/TranscriptionController.php`.
