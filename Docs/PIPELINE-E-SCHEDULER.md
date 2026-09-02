# Pipeline e scheduler

> Tipo: referência as-built · Atualizado: 2026-08-27
> Fonte: `clip-processor/src/main.py` e `pipeline_runner.py`

## Boot

1. cria o scheduler em `America/Sao_Paulo`;
2. executa recovery de downloads, seleção, publicação e cortes interrompidos;
3. inicia o sidecar Flask em `0.0.0.0:8090`;
4. se `PIPELINE_ENABLED=true`, executa `run_pipeline_once` imediatamente;
5. inicia o scheduler.

Com `PIPELINE_ENABLED=false`, o sidecar continua disponível, mas o ciclo inicial e os jobs
de ingestão/publicação saem sem processar.

## Jobs

| ID | Frequência | Função | Executa |
|---|---:|---|---|
| `ingest_cycle` | 20 min | `run_ingest_cycle` | RSS, IA, corte e download |
| `publish_cycle` | 10 min | `run_publish_only` | publicação de clips prontos |
| `clip_pending_ttl` | 1 h | `run_ttl_once` | alerta e rejeição por TTL |
| `state_recovery` | 30 min | `run_recovery_once` | recovery de downloads, seleção e publicação |

Todos usam `coalesce=true`, `max_instances=1` e tolerância de execução atrasada
de 900 s. Cortes em `cutting` só são recuperados no boot.

As travas Redis de ingestão e publicação têm TTL padrão de 7200 s
(`PIPELINE_LOCK_TIMEOUT_SECONDS` e `PUBLISH_LOCK_TIMEOUT_SECONDS`). O valor cobre o
render em `preset=slow` e pode ser aumentado em instalações com vídeos longos ou disco mais lento.

## Ciclo de ingestão

`run_ingest_cycle` abre conexão PostgreSQL e Redis quando necessário e executa:

1. `rss_poller.poll_all_channels`: consulta RSS, faz dedup, insere fontes pendentes,
   transcreve/seleciona fontes `downloaded` e processa clips `pending_cut`;
2. `pipeline_runner._download_pending_videos`: repõe as janelas de download por formato.

A ordem é intencional: primeiro drena trabalho já baixado; depois baixa o déficit da janela.

Apesar do nome, `poll_all_channels` não faz apenas polling. A função concentra descoberta,
transcrição, seleção e chamada do render. Cada canal e cada clip têm tratamento de erro isolado.

## Ciclo de publicação

`run_publish_only` chama somente `publisher.publish_pending_clips`. O publisher:

- busca destinos ativos;
- seleciona `pending` ou `approved`, conforme `MANUAL_APPROVAL_REQUIRED`;
- aplica roteamento por perfil/nicho, round-robin por canal-fonte e quota;
- faz OAuth/upload e registra o resultado.

Separar publicação de ingestão permite drenar a fila quando a quota libera sem repetir RSS, IA ou
download.

## Ciclo completo

`run_pipeline_once` é usado no boot e executa, em ordem:

~~~text
poll_all_channels → _download_pending_videos → publish_pending_clips
~~~

Cada bloco tem `try/except` próprio, loga falhas e envia `pipeline_failure` ao
painel. Uma falha de estágio não deve derrubar o scheduler.

## Recovery

O recovery periódico não toca em `cutting` porque um render legítimo pode durar mais que
30 minutos. A rotina de boot recebe `recover_cutting=true` porque, após reiniciar o
processo, não há FFmpeg antigo válido.

| Estado | Ação |
|---|---|
| fonte `downloading` | volta para `pending` |
| fonte `selecting` com raw | volta para `downloaded` após o limite |
| fonte `selecting` sem raw | vai para `failed` após o limite |
| clip `publishing` sem update por 15 min | volta para `pending` |
| clip `cutting` no boot | volta para `pending_cut` |
| fonte `transcribing` | sem recovery automático |

Falha de conexão no boot é engolida e tentada novamente pelo job de 30 minutos.

## Alteração e deploy

O Dockerfile copia o scheduler e o código do processador, mas o Compose atual monta
`./clip-processor/src:/app/src`. Após mudar Python, reinicie somente o serviço:

~~~bash
docker compose restart clip-processor
~~~

Faça rebuild quando mudar Dockerfile, dependências ou pacotes do sistema:

~~~bash
docker compose up -d --build clip-processor
~~~

Não é necessário reiniciar PostgreSQL ou Redis para uma alteração somente no processador.
