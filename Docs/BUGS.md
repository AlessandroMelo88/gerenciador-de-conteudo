# Backlog de bugs

Status: **FEITO** (corrigido e verificado) · **PARCIAL** (parte corrigida, parte aberta) ·
**ABERTO** (confirmado, não corrigido) · **SUSPEITA** (evidência parcial, falta confirmar).

Numeração é estável — não renumerar ao fechar um item, outros documentos linkam por número.
Última atualização: **13/08/2026**.

| # | Status | Título |
|---|---|---|
| 1 | FEITO | Órfãos de download nunca eram apagados |
| 2 | FEITO | `_raw.mp4` nunca era apagado |
| 3 | SUSPEITA | Thumbnail não aplicada nos vídeos longos no YouTube |
| 4 | PARCIAL | Estados sem recuperação automática seguram arquivo em disco |
| 5 | FEITO | `_subtitled.mp4` órfão |
| 6 | ABERTO | Painel não consegue apagar o backlog de download |
| 7 | ABERTO | 4 testes de `test_pipeline_runner.py` falhando |
| 8 | ABERTO | Docker Desktop travado sob pressão de disco |
| 9 | FEITO | Download falho vazava disco e entupia a janela |
| 10 | ABERTO | 287 clips com `clip_path` apontando para arquivo inexistente |
| 11 | ABERTO | Container não honra SIGTERM — todo `docker stop` vira SIGKILL |

---

## 1. FEITO — Órfãos de download nunca eram apagados

**Corrigido em 11/08/2026** (`clip-processor/src/downloader.py`, `pipeline_runner.py`,
`tests/test_downloader.py`).

Eram dois defeitos somados:

`_cleanup_partial` globava `output_path + '*.part'`, ou seja `<id>.mp4*.part`. O yt-dlp põe o sufixo de
formato **antes** do `.mp4` (`QFDWHS3Oy3E.f298.mp4.part`), então o glob nunca casava com os streams
separados. Também não cobria `.ytdl`, `.temp.mp4`, `.fNNN.webm` nem `.part-FragN.part`.

E mesmo corrigido, `_cleanup_partial` só roda no `except`. Quando o container morre (OOM, MySQL fora,
disco cheio) o `except` nunca executa e o arquivo fica órfão para sempre.

Correção:
- glob passou a partir do prefixo sem extensão, filtrando por `_WORK_ARTIFACT_RE`
  ([`downloader.py:39`](../clip-processor/src/downloader.py#L39));
- nova `cleanup_stale_downloads` ([`downloader.py:72`](../clip-processor/src/downloader.py#L72)) varre
  o primeiro nível de `/app/videos` e remove artefato de trabalho parado; um `<id>.mp4` completo não
  casa com a regex;
- `pipeline_runner.py:152` chama a limpeza no início de `_download_pending_videos`, antes de ocupar
  disco novo — o disk guard de 2 GB mede o disco real, então órfão não limpo virava bloqueio de
  download.

`STALE_AFTER_HOURS` é **1 hora** ([`downloader.py:45`](../clip-processor/src/downloader.py#L45)), não 6
como constava aqui antes.

5 testes novos com os nomes reais tirados do disco de produção. **Resíduo removido à mão:** 7 arquivos,
4.39 GB (crashes de 27/07, 30/07 e 04/08).

---

## 2. FEITO — `_raw.mp4` nunca era apagado

**Corrigido em 12/08/2026** (commit `5009112`, `publisher.py`).

Impacto quando aberto: 8.5 GB em 259 arquivos — o maior item do disco, acima dos vídeos fonte.
`video_processor.py:205` cria `<clip_id>_raw.mp4`, usa como entrada da queima de legenda e não apagava.

`_maybe_finalize_source_video` ([`publisher.py:345-354`](../clip-processor/src/publisher.py#L345))
passou a apagar, para cada clip do vídeo, `clip_path`, `<prefix>_raw.mp4`, `<prefix>_subtitled.mp4` e a
thumbnail — junto com o `.mp4` bruto do vídeo fonte. Só roda quando nenhum clip do vídeo está em estado
não-terminal **e** ao menos um publicou, o que é exatamente o guard necessário: o `_raw` é insumo do
corte enquanto o clip está em `pending_cut`/`cutting`.

**Buraco que sobra** (não é regressão, é escopo não coberto): o `except` de `process_clip`
([`video_processor.py:250`](../clip-processor/src/video_processor.py#L250)) marca o clip `failed` e
**não limpa nada**. Clip que morre no meio deixa `_raw.mp4` para trás, e a limpeza só o alcança se
algum **outro** clip do mesmo vídeo chegar a publicar. Se nenhum publicar, ficam.

**Limpeza retroativa ainda não feita:** o resíduo anterior a 12/08/2026 continua em disco. Classificar
cruzando com `generated_clips.status` — e pelo **id**, nunca pelo nome do arquivo.

---

## 3. SUSPEITA — Thumbnail não aplicada nos vídeos longos no YouTube

**A geração local está correta e isso já foi verificado.** Dos 63 clips finais em disco, 25 eram longos
(1920x1080, 7–15 min) e **todos os 25 tinham `.jpg` válido** em `videos/thumbnails/`, entre 204K e
388K. Não há ramo por formato: `video_processor.py:233` chama `extract_thumbnail` igual para os dois, e
`uploader.py:120` chama `thumbnails().set` para qualquer clip com `thumbnail_path`.

Logo o defeito está **depois da geração**, na aplicação via API.

**Hipótese principal:** `thumbnails().set` retornando 403 — custom thumbnail exige canal verificado no
YouTube. Ela roda **depois** do `videos.insert` e **fora de qualquer `try` local**
([`uploader.py:114-123`](../clip-processor/src/uploader.py#L114)), então o vídeo sobe e a exceção
propaga, marcando o clip como `failed` com o motivo em `upload_error`. Shorts não expõem o sintoma
porque o YouTube ignora thumbnail custom neles.

**Como confirmar:**
```sql
SELECT id, status, youtube_video_id, upload_error FROM generated_clips
WHERE status='failed' ORDER BY id DESC LIMIT 20;
```
`youtube_video_id` preenchido com `status='failed'` é prova: o upload passou e o que falhou foi depois.
Mais `docker compose logs clip-processor | grep -i thumb`.

**Se confirmado:** envolver o `thumbnails().set` em try/except próprio — o vídeo já subiu, falhar a
thumbnail não deveria marcar o clip inteiro como `failed`.

---

## 4. PARCIAL — Estados sem recuperação automática seguram arquivo em disco

**O que foi corrigido em 13/08/2026** (`main.py`, `db.py`):

1. `recover_stuck_selecting` e `recover_stuck_downloads` deixaram de rodar **só no boot**. Agora rodam
   também como job periódico a cada 30 min — `run_recovery_once`
   ([`main.py:51`](../clip-processor/src/main.py#L51)), job id `state_recovery`
   ([`main.py:127`](../clip-processor/src/main.py#L127)). Antes, o que travasse depois do container
   subir ficava preso até o próximo restart — na prática, dias. A cadência de 30 min é menor que
   `SELECTING_STUCK_HOURS = 2` de propósito.
2. Cobre a janela do `Errno 111` (clip-processor sobe antes do MySQL): o recovery de boot morre no
   `except` e antes ninguém tentava de novo.
3. `recover_stuck_selecting` ganhou uma **terceira query**
   ([`db.py:200`](../clip-processor/src/db.py#L200)): `selecting` com `local_path IS NULL` e sem update
   há 2 h vai para `failed`. Esses registros ficavam presos para sempre — a limpeza de disco
   (`delete_source_video_file`, `purge_old_videos`) zera `local_path` sem tocar em `status`, e as duas
   queries anteriores exigem `local_path IS NOT NULL`. Nenhum restart resolvia. Sem raw em disco não há
   seleção para reprocessar, então `failed` é o estado honesto e libera a vaga da janela.

**O que continua ABERTO:** não existe recuperação para `generated_clips.cutting`,
`generated_clips.publishing` nem `source_videos.transcribing`. O que trava nesses três fica preso para
sempre e segura arquivo em disco. Foi a causa do acúmulo que lotou o SSD no incidente de 27/07/2026.

Agrava com o bug 11: o container morre por SIGKILL em todo `docker stop`, ou seja, pode ser morto **no
meio** de um `cutting` ou `publishing`.

**Onde corrigir:** nova query em [`db.py`](../clip-processor/src/db.py) + chamada em `run_recovery_once`.
`publishing` precisa de cuidado extra: devolver a `pending` um clip que **já subiu** republica e
duplica — checar `youtube_video_id` antes.

Destrave manual em [`RUNBOOK.md`](RUNBOOK.md#estado-preso-sem-recuperação-automática).

---

## 5. FEITO — `_subtitled.mp4` órfão

**Corrigido em 12/08/2026**, junto do bug 2 e pela mesma varredura
([`publisher.py:349`](../clip-processor/src/publisher.py#L349)).

Mesma classe do bug 2, escala menor: `video_processor.py:207` cria o intermediário; ele é removido no
caminho feliz, mas se o processo morrer entre a queima de legenda e o watermark o arquivo fica. Herda o
mesmo buraco residual: clip que nunca publica não passa pela finalização.

---

## 6. ABERTO — Painel não consegue apagar o backlog de download

O card "Backlog download" mostrava 1062 vídeos `pending` sem arquivo em disco. Nenhuma ação do painel
apaga essas **linhas**:

- `DashboardController::bulkDeleteVideos` pula `blank($video->local_path)` como *skipped* — só apaga
  arquivo;
- `SourceVideoController::bulkDeleteFiles` idem;
- só `purgeOld` → `internal_api.purge_old_videos` apaga linha, e apenas por data.

Resultado: o operador vê o número no painel e não tem botão que resolva.

**Complicação a considerar antes de "resolver":** `purge_old_videos` também apaga as chaves Redis
`video:<id>` de dedup ([`internal_api.py:220`](../clip-processor/src/internal_api.py#L220)). Os vídeos
purgados deixam de estar "vistos" e voltam a ser inseridos como `pending` no próximo poll RSS. Não
voltam a baixar (`FRESHNESS_DAYS=1` barra publicado antes de ontem), mas o contador reenche. Purgar
trata o sintoma; a causa é o RSS ingerir mais do que a janela consome.

---

## 7. ABERTO — 4 testes de `test_pipeline_runner.py` falhando

Falhas **pré-existentes**, confirmadas em 11/08/2026 rodando a suíte com as mudanças do bug 1 em stash
— mesmas 4 falhas antes e depois.

- `test_scheduler_compatible_coalesce`: `ModuleNotFoundError: No module named 'flask'` — o host não tem
  as dependências do sidecar instaladas;
- os outros 3: `StopIteration` em mock de cursor com `side_effect` esgotado.

Rodar a suíte **dentro do container** resolve o caso do flask. Os mocks precisam de revisão à parte.

> **Não reverificado em 13/08/2026.** A contagem pode ter mudado com as correções dos bugs 9 e 4.

---

## 8. ABERTO — Docker Desktop travado sob pressão de disco

Em 11/08/2026, com o SSD em 85% (2.1 GiB livres), `docker ps` ficou pendurado indefinidamente em três
tentativas seguidas — daemon inacessível, sem MySQL e sem logs. Liberar 4.39 GB não destravou; exigiu
restart do Docker Desktop.

Não é bug do projeto, mas é o modo de falha que **esconde todos os outros**: sem Docker não há banco nem
log, e o diagnóstico do bug 3 depende dos dois.

---

## 9. FEITO — Download falho vazava disco e entupia a janela

**Corrigido em 13/08/2026** (`_discard_failed_download`,
[`pipeline_runner.py:110`](../clip-processor/src/pipeline_runner.py#L110)).

Antes, download que falhava só rodava `update_status(..., 'failed')`: o `.mp4` meio baixado ficava no
disco e `local_path` continuava preenchido. Como a contagem da janela de download considera
`local_path IS NOT NULL`, o vídeo ocupava slot **para sempre**. Com 58 `failed` acumulados segurando
4.1 GB, o déficit virou 0 e **o pipeline parou de baixar qualquer coisa**.

A correção segue a regra 2 de operações destrutivas do [`../CLAUDE.md`](../CLAUDE.md), na ordem:

1. se algum clip está em `pending_cut`/`cutting` (`_clips_need_raw`), só marca `failed` e **preserva** o
   raw — ainda é insumo do corte;
2. senão, apaga o arquivo com **caminho absoluto**;
3. **confere** que o arquivo saiu (`os.path.exists`);
4. só então `update_status(..., 'failed', clear_local_path=True)`.

Se a remoção falhar, `local_path` é mantido de propósito: banco e disco divergentes são pior que uma
vaga presa. `update_status` ganhou o parâmetro `clear_local_path`
([`db.py:57`](../clip-processor/src/db.py#L57)) porque `local_path=None` significava "não mexe na
coluna" nas chamadas antigas — não havia como zerar a coluna.

**Resíduo antigo não tratado:** vídeos `failed` de antes desta correção que ainda têm `local_path`
preenchido. Ver [`RUNBOOK.md`](RUNBOOK.md#o-pipeline-parou-de-baixar).

---

## 10. ABERTO — 287 clips com `clip_path` apontando para arquivo inexistente

**287 registros de `generated_clips` têm `clip_path` preenchido para um arquivo que não existe em
disco.** Origem: limpeza apagou o arquivo sem limpar a coluna.

Há mais de um caminho que produz isso, e nenhum é acidente isolado:

| Caminho | Comportamento |
|---|---|
| `rejeitar.py:87` | `os.remove(clip_path)` e **não** zera a coluna |
| `_maybe_finalize_source_video` | todos os `os.remove` são `try/except OSError: pass`, e o `UPDATE` que zera as colunas roda **de qualquer forma** — mas a ordem inversa (arquivo apagado, `UPDATE` falhando) também é possível |
| limpeza manual de disco | apagou arquivo sem tocar no banco (incidente registrado no `CLAUDE.md`) |

**Impacto real é baixo, mas não nulo.** O uploader valida a existência do arquivo
([`uploader.py:133`](../clip-processor/src/uploader.py#L133)) e levanta `FileNotFoundError`, então o
clip vira `failed` na tentativa de publicar em vez de subir vazio. O dano é o painel mostrar clip com
preview quebrado e a contabilidade de disco mentir.

**Onde corrigir:** `rejeitar.py` deveria zerar `clip_path`/`thumbnail_path` junto do `UPDATE` de status.
Para o resíduo, script de reconciliação que zera a coluna quando o arquivo não existe — **nunca** o
contrário (apagar arquivo por causa da coluna já apagou clip vivo aqui).

Query de medição em [`BANCO-DE-DADOS.md`](BANCO-DE-DADOS.md#divergência-banco--disco-bug-aberto).

---

## 11. ABERTO — Container não honra SIGTERM, todo `docker stop` vira SIGKILL

**Todo `docker stop clip-processor` termina em `Exited (137)`.** O handler está registrado
([`main.py:137-138`](../clip-processor/src/main.py#L137)) e chama `scheduler.shutdown(wait=False)`
([`main.py:80`](../clip-processor/src/main.py#L80)), mas o `BlockingScheduler` **não retorna do
`shutdown`** — o Docker espera o timeout de graça e manda SIGKILL.

**Por que importa:** o processo é morto **no meio do estágio em execução**. Combinado com o bug 4, um
clip em `cutting` ou `publishing` na hora do kill fica preso para sempre. `publishing` é o pior caso: o
upload pode ter completado no YouTube com o banco registrando outra coisa.

Sintoma colateral: o container reinicia "sujo" e a cada restart pode acumular um estado preso novo.

**Onde investigar:** o `shutdown` é chamado de dentro do handler de sinal, que roda na **mesma thread**
que está bloqueada em `scheduler.start()`. O padrão usual é sinalizar um `threading.Event` no handler e
deixar a thread principal sair do `start()` sozinha, em vez de chamar `shutdown` de dentro do sinal.
Não testei essa hipótese.

Mitigação até então: seguir [`RUNBOOK.md`](RUNBOOK.md#reiniciar-o-clip-processor-com-segurança) —
conferir se há `cutting`/`publishing` em trânsito **antes** de parar o container.
