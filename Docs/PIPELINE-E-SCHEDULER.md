# Pipeline e scheduler

Como o daemon decide *quando* fazer as coisas, e qual função roda qual etapa.
Referência módulo a módulo em [`SISTEMA-CLIP-PROCESSOR.md`](SISTEMA-CLIP-PROCESSOR.md);
estados e transições em [`ESTADOS-E-TRANSICOES.md`](ESTADOS-E-TRANSICOES.md).

Verificado no código em **13/08/2026**.

---

## Entrypoint

`CMD ["python", "-m", "src.main"]` ([`clip-processor/Dockerfile:29`](../clip-processor/Dockerfile#L29)).
Sequência do boot, em ordem, em [`main.py:140-167`](../clip-processor/src/main.py#L140):

1. Loga env vars relevantes (`MYSQL_HOST`, `REDIS_HOST`, `YOUTUBE_PRIVACY_STATUS`, `MAX_UPLOADS_PER_DAY`).
2. `run_recovery_once()` — recovery de estado preso ([`main.py:153`](../clip-processor/src/main.py#L153)).
3. Sobe o sidecar Flask numa thread daemon ([`main.py:159`](../clip-processor/src/main.py#L159)).
   Vem **antes** do ciclo inicial de propósito: o ciclo pode levar minutos e o painel precisa do
   sidecar disponível logo.
4. `run_pipeline_once()` — um ciclo completo síncrono ([`main.py:164`](../clip-processor/src/main.py#L164)).
5. `scheduler.start()` — entrega o processo ao `BlockingScheduler`.

`BlockingScheduler` com timezone `America/Sao_Paulo` ([`main.py:77`](../clip-processor/src/main.py#L77)).
Há um fallback no-op de `BlockingScheduler` em [`main.py:16`](../clip-processor/src/main.py#L16) para
rodar os testes sem APScheduler instalado — não é usado em produção.

---

## Jobs agendados

| Job id | Função | Intervalo | O que faz |
|---|---|---|---|
| `ingest_cycle` | `run_ingest_cycle` ([`pipeline_runner.py:282`](../clip-processor/src/pipeline_runner.py#L282)) | 20 min | RSS + IA + corte + download. **Sem** publicação |
| `publish_cycle` | `run_publish_only` ([`pipeline_runner.py:247`](../clip-processor/src/pipeline_runner.py#L247)) | 20 min | só publicação |
| `clip_pending_ttl` | `run_ttl_once` ([`ttl_worker.py:26`](../clip-processor/src/ttl_worker.py#L26)) | 1 h | auto-rejeita clip `pending` velho |
| `state_recovery` | `run_recovery_once` ([`main.py:51`](../clip-processor/src/main.py#L51)) | 30 min | destrava `downloading` e `selecting` |

Todos com `coalesce=True, max_instances=1, misfire_grace_time=900`. `max_instances=1` é o que impede
dois ciclos concorrentes disputando o mesmo vídeo.

`clip_pending_ttl` omite `next_run_time` de propósito ([`main.py:112`](../clip-processor/src/main.py#L112)):
a primeira execução é em `now + 1h`, para não rodar TTL antes do banco estar quente após o boot.

**Ingestão e publicação são jobs separados.** O ciclo completo (`run_pipeline_once`,
[`pipeline_runner.py:189`](../clip-processor/src/pipeline_runner.py#L189)) só roda no boot; não está
agendado. Motivo: uma vaga aberta na janela de download — porque um vídeo foi excluído no painel ou
uma publicação concluiu — é reposta em ~20 min em vez de esperar o ciclo antigo de 6 h.

---

## O que cada ciclo executa

### `run_ingest_cycle` (20 min)

Duas chamadas, cada uma em `try/except` isolado que loga e dispara
`notify('pipeline_failure', ...)` — falha de estágio não derruba o scheduler:

1. `poll_all_channels` ([`rss_poller.py:177`](../clip-processor/src/rss_poller.py#L177))
2. `_download_pending_videos` ([`pipeline_runner.py:147`](../clip-processor/src/pipeline_runner.py#L147))

> ⚠️ **`rss_poller.py` não faz só polling.** `poll_all_channels` executa, em sequência, dentro da
> mesma função:
>
> | Bloco | Linhas | Etapa |
> |---|---|---|
> | varre o RSS de cada canal ativo | [`:210-257`](../clip-processor/src/rss_poller.py#L210) | descoberta |
> | processa vídeos `downloaded` | [`:262-281`](../clip-processor/src/rss_poller.py#L262) | transcrição + seleção IA |
> | processa clips `pending_cut` | [`:284-287`](../clip-processor/src/rss_poller.py#L284) | corte / legenda / thumbnail / metadata |
>
> O `pipeline_runner` só cuida de **descoberta de vaga e download**. Quem procura o estágio de IA no
> `pipeline_runner` não acha.

Ordem dentro do ciclo importa: o poll processa o que já está `downloaded` **antes** de baixar
material novo. Ou seja, a cada tick o pipeline primeiro esvazia a janela, depois a reenche.

### `run_publish_only` (20 min)

Só `publish_pending_clips` ([`publisher.py:33`](../clip-processor/src/publisher.py#L33)).
Existe para drenar a fila de publicáveis com frequência alta — quando a cota diária reseta à
meia-noite, os aprovados não ficam represados esperando um ciclo completo.

### `run_pipeline_once` (só no boot)

`poll_all_channels` → `_download_pending_videos` → `publish_pending_clips`, cada um com o mesmo
`try/except` + `notify`.

---

## Conexões

Cada `run_*` abre a própria conexão MySQL e o próprio cliente Redis quando chamado sem argumentos,
e fecha o MySQL no `finally` (`own_db` / `own_redis`, ex.
[`pipeline_runner.py:194-204`](../clip-processor/src/pipeline_runner.py#L194)). Os parâmetros
existem para injeção em teste. `poll_all_channels` faz o mesmo
([`rss_poller.py:185`](../clip-processor/src/rss_poller.py#L185)) — conexão nova por chamada, para
evitar o timeout de conexão longa.

O cliente Redis **não** é fechado explicitamente em nenhum dos ciclos.

---

## Shutdown: o container não honra SIGTERM (bug aberto)

`main.py:137-138` registra `SIGTERM` e `SIGINT` em `shutdown`
([`main.py:80`](../clip-processor/src/main.py#L80)), que chama `scheduler.shutdown(wait=False)`.

**Na prática todo `docker stop` termina em `Exited (137)` / SIGKILL**: o `BlockingScheduler` não
retorna do `shutdown` e o Docker mata o processo depois do timeout de graça. Registrado como bug
aberto em [`BUGS.md`](BUGS.md).

Consequência operacional: o processo pode ser morto **no meio de um estágio**. Um clip em `cutting`
ou `publishing` na hora do kill fica preso — e nenhum dos dois tem recuperação automática
(ver [`ESTADOS-E-TRANSICOES.md`](ESTADOS-E-TRANSICOES.md#recuperação-automática-o-que-tem-e-o-que-não-tem)).
Antes de reiniciar, seguir [`RUNBOOK.md`](RUNBOOK.md#reiniciar-o-clip-processor-com-segurança).

---

## Armadilha recorrente: editar código não muda nada sem rebuild

**Não há bind mount para `clip-processor/src/`.** O `Dockerfile` faz `COPY src/ src/`
([`clip-processor/Dockerfile:27`](../clip-processor/Dockerfile#L27)) — a imagem embute o código no
build. Editar no host e reiniciar o container **não** aplica a mudança: o container continua rodando
o código do último build.

Isso já morreu na prática: em 13/08/2026 o container estava executando código de 01/08 enquanto o
host tinha commits de 12/08, e o comportamento observado não correspondia a nenhuma versão do código
que se estava lendo. Diagnosticar bug de pipeline contra o código do host, sem conferir a data da
imagem, é perda de tempo garantida.

```bash
# aplicar mudança de código (isolado — não sobe mysql/redis nem outros projetos)
docker compose build clip-processor && docker compose up -d clip-processor
```

Como conferir se a imagem está velha: [`RUNBOOK.md`](RUNBOOK.md#o-container-está-rodando-código-velho).

---

## Onde mexer

| Quero mudar | Vou em |
|---|---|
| cadência dos jobs | [`main.py:89-135`](../clip-processor/src/main.py#L89) |
| o que cada ciclo executa | `run_ingest_cycle` / `run_publish_only` em [`pipeline_runner.py`](../clip-processor/src/pipeline_runner.py) |
| ordem das etapas dentro do poll | [`rss_poller.py:198-287`](../clip-processor/src/rss_poller.py#L198) |
| limiar do recovery de `selecting` | `SELECTING_STUCK_HOURS` em [`db.py:153`](../clip-processor/src/db.py#L153) |
| adicionar recovery para `cutting`/`publishing` | nova query em [`db.py`](../clip-processor/src/db.py) + chamada em `run_recovery_once` |
