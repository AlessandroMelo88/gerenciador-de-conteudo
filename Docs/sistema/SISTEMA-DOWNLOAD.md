# Download e descoberta

> Tipo: referência as-built · Atualizado: 2026-08-26
> Fontes: `rss_poller.py`, `pipeline_runner.py`, `downloader.py`,
> `dedup.py` e `processar.py`

## Descoberta automática

`rss_poller.poll_all_channels`:

1. busca `source_channels` ativos e não blacklistados;
2. consulta cada `rss_url` com timeout de 30 s;
3. extrai o ID do vídeo;
4. aplica dedup;
5. bloqueia títulos com termos de apostas/cassino;
6. consulta a duração via `yt-dlp`;
7. insere o vídeo como `source_videos.status=pending`.

Falha em um canal é registrada e não interrompe os demais. Se a consulta de duração falhar, o formato
assume `curto`.

## Deduplicação

A chave primária operacional é `video:<youtube_id>` no Redis, criada com `SET NX`
e TTL de 30 dias. Se Redis falhar, o código consulta `source_videos.youtube_video_id` no
PostgreSQL.

A inserção no banco também é idempotente. Redis limpo não ressuscita uma linha já existente no banco.
A fila continua sendo PostgreSQL.

## Formato e janela

- `curto`: duração da fonte menor que 420 s;
- `longo`: duração da fonte igual ou maior que 420 s;
- janela padrão de download: 6 curtos e 4 longos;
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
