# Download e descoberta

> Tipo: referência as-built · Atualizado: 2026-09-29
> Fontes: `rss_poller.py`, `pipeline_runner.py`, `downloader.py`,
> `dedup.py` e `processar.py`

## Descoberta automática

`rss_poller.poll_all_channels`:

1. busca `source_channels` ativos e não blacklistados;
2. consulta cada `rss_url` com timeout de 30 s;
3. extrai o ID do vídeo;
4. aplica dedup;
5. bloqueia títulos com termos de apostas/cassino;
6. insere uma única fonte com `source_videos.status=pending` e `generate_both_formats=true`.

Não há consulta prévia de duração para escolher um único formato. O worker transcreve a fonte uma vez,
seleciona até três Shorts e tenta também um longo se houver um trecho contínuo elegível de pelo menos
420 s que não cubra a fonte inteira. Fontes curtas continuam elegíveis para Shorts. Falha em um canal
é registrada e não interrompe os demais.

## Deduplicação

A chave primária operacional é `video:<youtube_id>` no Redis, criada com `SET NX`
e TTL de 30 dias. Se Redis falhar, o código consulta `source_videos.youtube_video_id` no
PostgreSQL.

A inserção no banco também é idempotente. Redis limpo não ressuscita uma linha já existente no banco.
A fila continua sendo PostgreSQL.

## Formato e janela

- RSS gera Shorts e, quando a transcrição comporta, também um vídeo longo da mesma fonte;
- o formato de cada saída fica em `generated_clips.format`; `source_videos.format` continua
  atendendo fluxos manuais de formato único e compatibilidade com registros antigos;
- janela de download padrão: 10 fontes por canal de destino ativo do nicho (`DOWNLOAD_WINDOW_PER_CHANNEL`);
- janela de frescor configurada por canal-fonte no painel: 3 ou 1500 dias;
- `FRESHNESS_DAYS=1500` é somente o fallback para registros sem valor de canal;
- registros sem `published_at` usam `created_at` para o filtro e a ordenação da janela;
- ordem: `priority DESC`, `queue_position` e data efetiva (`published_at` ou `created_at`) DESC.

A ocupação considera raw local, estados ativos e clips que ainda precisam do raw. O ciclo baixa apenas
o déficit de cada formato.

Apagar o arquivo bruto libera disco sem apagar a linha em `source_videos`, a transcrição (`transcript_text`
e `transcript_data`) ou os clips e metadados associados. Assim, o assunto continua pesquisável e pode
ser localizado para novos cortes. Uma busca editorial pode combinar referências de fontes e pessoas
diferentes quando tratam do mesmo tema. A busca do painel consulta a transcrição e os metadados dos
clips e apresenta cada fonte separadamente; cada corte continua vinculado à sua origem no banco.

## Download com yt-dlp

`download_video`:

- usa `bestvideo[height<=1080]+bestaudio/best` e mescla em MP4;
- verifica pelo menos 2 GB livres em `VIDEOS_DIR` (no Docker, `/app/videos`);
- tenta até 3 vezes;
- espera 60 s entre tentativas;
- não repete erros identificados como privado, removido, indisponível ou bloqueado por região;
- verifica pause antes e durante o download;
- remove artefatos parciais após falha;
- retorna sucesso somente quando o arquivo final existe.

Artefatos `.part`, `.ytdl`, streams separados e temporários de merge são limpos
quando incompletos. `cleanup_stale_downloads` remove artefatos de trabalho com mais de 1 h
no início de cada ciclo de ingestão; não remove um raw final `<id>.mp4`.

No erro, o pipeline apaga o parcial antes de marcar `failed` e zera `local_path`
quando consegue confirmar a remoção. Se a remoção falhar, preserva o caminho para não esconder a
divergência entre banco e disco.

## URL manual

O comando `python -m src.processar <url>`:

- aceita URLs `watch`, `youtu.be`, `shorts`, `embed` e
  `/v`;
- consulta metadata sem baixar o vídeo;
- cria canal-fonte inativo quando o canal ainda não existe;
- insere a fonte como `pending`;
- não executa download diretamente.

O painel e o Telegram chamam essa mesma entrada por `/internal/process-url`. Depois da
inserção, o scheduler segue o fluxo normal.

## Pause e exclusão

Pause marca `source_videos.paused=true`. Durante download, mata `yt-dlp`, remove
parciais e volta para `pending`. Na transcrição/seleção, a pausa é cooperativa entre etapas.

O raw só deve ser removido quando nenhum clip está em `pending_cut` ou `cutting`.
A exclusão operacional passa pelo sidecar e valida banco, estado e disco. Para limpeza manual, siga
[`../CLAUDE.md`](../CLAUDE.md).
