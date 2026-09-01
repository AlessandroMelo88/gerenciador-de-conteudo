+# Workflow manual

> **Tipo:** fallback operacional e diagnóstico · **Atualizado:** 2026-08-26

Use estes scripts quando a publicação automática estiver desabilitada, quando for necessário
inspecionar um backlog ou quando um operador precisar publicar um clip manualmente. O fluxo
principal e os estados continuam sendo os do [RUNBOOK](../Docs/RUNBOOK.md).

## Pré-requisitos

- Docker Compose ativo, incluindo `postgres` e `clip-processor`;
- `.env` na raiz com `CLIPS_DB_PASSWORD` e os dados do PostgreSQL;
- acesso ao YouTube Studio do canal destino.

Os scripts leem credenciais de `.env` e executam SQL no serviço `postgres`. Não use
`docker compose down -v`: isso remove os volumes de dados.

## Listar e revisar clips

~~~bash
./manual-workflow/list-pending-clips.sh
./manual-workflow/list-pending-clips.sh --id <CLIP_ID>
./manual-workflow/list-pending-clips.sh --all-status
~~~

A listagem mostra status, score, duração, título, canal de origem e data. O modo detalhado também
exibe descrição, tags e caminhos dos artefatos.

Copie os arquivos usando os caminhos exibidos:

~~~bash
docker compose cp clip-processor:/app/videos/clips/<arquivo>.mp4 ~/Desktop/
docker compose cp clip-processor:/app/videos/thumbnails/<arquivo>.jpg ~/Desktop/
~~~

Antes do upload, verifique corte, sincronismo, legenda, thumbnail, título, descrição e tags.
Formato `curto` é vertical (30–180 s, legenda queimada); `longo` é horizontal (420–1200 s,
sem legenda queimada e com legenda oficial em arquivo quando disponível).

## Publicar manualmente

1. No YouTube Studio, faça upload do `.mp4`.
2. Revise título, descrição, tags, thumbnail, público-alvo e visibilidade.
3. Para `longo`, associe o SRT gerado como legenda oficial `pt-BR` quando ele estiver disponível.
4. Publique no canal correspondente e copie o ID de 11 caracteres da URL.
5. Atualize o banco, confirmando cada alteração:

~~~bash
./manual-workflow/mark-published.sh <CLIP_ID> <YOUTUBE_VIDEO_ID>
~~~

O script valida o ID, pede confirmação, marca o clip como `published` e finaliza o vídeo fonte
quando todos os clips associados estão em estado terminal.

Para retirar um clip do fluxo:

~~~bash
./manual-workflow/mark-failed.sh <CLIP_ID> "motivo objetivo"
~~~

Marcar publicado ou falho altera o banco; não apaga automaticamente arquivos locais.

## Forçar apenas o download

Use quando o RSS já criou registros `source_videos` em `pending`, mas o worker não avançou:

~~~bash
./manual-workflow/force-download.sh
./manual-workflow/force-download.sh --limit 3
~~~

O limite padrão é 10. O script baixa e muda o estado para `downloaded`; transcrição, seleção e
corte continuam sendo responsabilidade do worker. Consulte logs depois da execução:

~~~bash
docker compose logs --tail=100 clip-processor
~~~

## Diagnóstico rápido

- nenhum clip: confira `docker compose ps`, logs do worker e [RUNBOOK.md](../Docs/RUNBOOK.md);
- clip preso: consulte [ESTADOS-E-TRANSICOES.md](../Docs/ESTADOS-E-TRANSICOES.md) e use recovery;
- erro de OAuth ou cota: siga [SISTEMA-PUBLICACAO.md](../Docs/SISTEMA-PUBLICACAO.md);
- disco cheio: interrompa downloads e siga o procedimento de limpeza do runbook.

Os scripts são auxiliares; não substituem o painel, o scheduler, o recovery nem a publicação
idempotente do pipeline.
