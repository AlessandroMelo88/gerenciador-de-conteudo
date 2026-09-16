# Backlog de bugs

Status: **FEITO** (corrigido e verificado) · **PARCIAL** (parte corrigida, parte aberta) ·
**ABERTO** (confirmado, não corrigido) · **SUSPEITA** (evidência parcial, falta confirmar).

Numeração é estável — não renumerar ao fechar um item, outros documentos linkam por número.
Última atualização: **15/09/2026**.

| # | Status | Título |
|---|---|---|
| 1 | FEITO | Órfãos de download nunca eram apagados |
| 2 | FEITO | `_raw.mp4` nunca era apagado |
| 3 | FEITO | Thumbnail não aplicada nos vídeos longos no YouTube — hipótese refutada |
| 4 | PARCIAL | Estados sem recuperação automática seguram arquivo em disco |
| 5 | FEITO | `_subtitled.mp4` órfão |
| 6 | ABERTO | Painel não consegue apagar o backlog de download |
| 7 | FEITO | 4 testes de `test_pipeline_runner.py` falhando |
| 8 | ABERTO | Docker Desktop travado sob pressão de disco |
| 9 | FEITO | Download falho vazava disco e entupia a janela |
| 10 | ABERTO | 287 clips com `clip_path` apontando para arquivo inexistente |
| 11 | ABERTO | Container não honra SIGTERM — todo `docker stop` vira SIGKILL |
| 12 | FEITO | Worker local de download ignorava a janela — disco em 100% e painel fora do ar |
| 13 | FEITO | Rejeitar no painel não apagava os arquivos do clip |
| 14 | FEITO | Usuários de teste com senha padrão viviam no banco de produção |
| 15 | FEITO | Groq recusava toda seleção com 429 — `max_tokens` acima do teto do plano |
| 16 | FEITO | Senhas do MySQL publicadas em repositório público — rotacionadas em 16/09/2026 |
| 17 | ABERTO | Vaga da janela presa por clip aguardando aprovação do operador |

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

### Fechado em 15/09/2026 — a hipótese não se sustenta

Duas verificações independentes derrubam o diagnóstico acima:

1. **Nenhum caso em produção.** A prova proposta era `status='failed'` com `youtube_video_id`
   preenchido — upload feito, falha depois. A contagem real é **zero**:

   ```sql
   SELECT COUNT(*) FROM generated_clips
   WHERE status='failed' AND youtube_video_id IS NOT NULL AND youtube_video_id <> '';
   ```

2. **A correção proposta já estava no código.** `thumbnails().set` **já roda dentro de try/except
   próprio** ([`uploader.py:116-129`](../clip-processor/src/uploader.py#L116)); a falha vira um aviso
   em `stderr` e `upload_video` devolve o `video_id` normalmente. Não há caminho em que a thumbnail
   marque o clip como `failed`.

O texto acima ficou desatualizado em relação ao código. Se o sintoma reaparecer (vídeo longo no ar
sem a thumbnail custom), a investigação recomeça **do lado da API**, não do estado do clip: conferir
o aviso no log (`docker compose logs clip-processor | grep -i thumb`) e se o canal destino está
verificado no YouTube — thumbnail custom exige verificação.

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

## 7. FEITO — testes do `clip-processor` verdes

**Fechado em 15/09/2026.** A suíte inteira passa: **222 testes, 0 falhas**, rodando dentro da imagem
do `clip-processor` (é assim que o `flask` do sidecar está disponível — no host ele não existe, que era
a causa de uma das falhas):

```bash
C=$PWD/clip-processor
docker run --rm --network none -v "$C/src:/app/src" -v "$C/tests:/app/tests" \
  -w /app --entrypoint python wordpress-clip-processor -m pytest tests/ -q
```

As falhas restantes eram **testes desatualizados**, não defeito de código: `test_rss_poller` esperava
`select_moments` sem o argumento `niche`, e `test_selector` esperava descarte de um momento de 20 s que
o código estica até 30 s (ver decisão em [`SISTEMA-IA-SELECAO.md`](SISTEMA-IA-SELECAO.md)).

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

---

## 12. FEITO — Worker local de download ignorava a janela

**Incidente 15/09/2026.** Better Stack: `Timeout (no headers received)` em `/painel` por mais de 1 h.
Cadeia: disco 100% → MySQL `Disk is full writing './binlog.000012' ... Waiting for someone to free
space` → requisições do PHP presas → `server reached pm.max_children setting (5)` → nginx sem resposta.

Causa: `scripts/local_download_worker.py` (launchd `com.canaldecortes.downloader`) buscava 10 vídeos de
futebol + 6 de política **a cada ciclo de 5–30 s**, sem contar quantos já ocupavam o servidor. O teto
só existia no `pipeline_runner`, que com `ALLOW_LOCAL_DOWNLOAD=true` não baixa. 306 downloads num dia,
325 vídeos de política parados em `downloaded` (a VM de 1 GB não transcreve nesse ritmo), 377 na janela.

**Correção:** regra única nos dois lados — **10 vídeos por canal destino ativo** (`_niche_windows` no
servidor, `niche_windows` no worker; watchdog usa o mesmo teto). Worker baixa um vídeo por ciclo, reconta
a ocupação e não baixa nada se a contagem falhar.

**Destrave feito:** worker parado, `clip-processor` congelado com `docker pause`, cache de build e journal
limpos (3,5 G) e 1.980 arquivos órfãos apagados após listagem por id (20,5 G): `_raw` de clip encerrado,
vídeo/áudio/transcrição sem registro, `.mp4` final de clip apagado do banco e artefatos de clips rejeitados.
Disco de 100% para 57%.

---

## 13. FEITO — Rejeitar no painel não apagava os arquivos do clip

`DashboardController::reject`/`bulkReject` apagavam com `Storage::disk('clips-videos')`, mas o volume de
vídeos é montado **read-only** no container `php` (`docker-compose.yml`) e os arquivos são do root do
`clip-processor`. Com `'throw' => false` a falha era silenciosa: o clip virava `rejected` e o `.mp4`, o
`_raw` e a thumbnail continuavam no disco (33 clips, 4 G em 15/09/2026). O caminho do sidecar
(`rejeitar.py`) apagava só o `.mp4` final.

**Correção:** o painel chama `POST /internal/reject-clip`; `rejeitar.py` apaga todos os artefatos pelo id
(`<id>.mp4`, `<id>_raw.mp4`, `<id>_subtitled.mp4`, `<id>.srt`, `thumbnails/<id>.jpg`) e preserva o vídeo-fonte.
Sidecar fora do ar → painel mostra erro e o clip continua `pending`. O Redis não participa da rejeição.

---

## 14. FEITO — Usuários de teste com senha padrão no banco de produção

**Encontrado e corrigido em 15/09/2026.** A tabela `users` da produção tinha, além do operador, três
contas criadas por `User::factory()`:

| id | e-mail | criado em |
|---|---|---|
| 599 | bode.will@example.org | 15/07/2026 |
| 613 | lenore82@example.org | 10/08/2026 |
| 627 | idell.botsford@example.net | 10/08/2026 |

As três aceitavam a senha padrão da factory do Laravel (`password`) — confirmado com `Hash::check`.
Qualquer pessoa com a URL do painel entrava com uma delas. As contas foram apagadas; sobrou só o
operador.

**Causa:** o `phpunit.xml` apontava para `DB_HOST=mysql` / `clips_automation`, o mesmo banco da
produção. Rodar a suíte dentro do servidor gravava dados de teste ali — os testes usam
`DatabaseTransactions`, mas qualquer execução interrompida no meio deixa resíduo.

**Nota de 16/09/2026:** ver também o bug 16 — o repositório público carrega a senha de root do
MySQL de produção. É a mesma classe de problema (credencial conhecida em lugar errado), mas de
alcance maior.

**Prevenção:** desde 15/09/2026 o `phpunit.xml` aponta para o Postgres local
([`PLANO-POSTGRES.md`](PLANO-POSTGRES.md)), fora da produção. Nunca rodar a suíte contra o banco de
produção. A senha do operador foi trocada na mesma data.

**Resíduo ainda aberto (apurado em 15/09/2026):** a *fábrica* que produz essas contas continua no
caminho padrão. `database/seeders/DatabaseSeeder.php` tem, no `run()`, um
`User::factory()->create(['email' => 'test@example.com'])` — e a factory do Laravel usa a senha
padrão `password`. Qualquer `php artisan db:seed` sem `--class` recria uma conta de senha conhecida,
inclusive se rodado contra a produção.

Confirmação de que o problema não é teórico: o Postgres **local** tem hoje duas contas de factory
vivas (`stroman.talon@example.org`, `rosella.zboncak@example.org`). A produção está limpa — só o
operador (verificado em 15/09/2026).

Por isso os seeders de dado deste projeto (`BaselineSeeder`, `SourceChannelsSeeder`) são **avulsos**,
rodados com `--class=`, e nenhum deles cria usuário. Conta de painel se cria só com
`php artisan painel:create-user`, que exige senha.

**Resolvido em 16/09/2026:** o `run()` do `DatabaseSeeder` foi esvaziado, com a explicação no próprio
arquivo. As duas contas de factory que ainda viviam no Postgres **local**
(`stroman.talon@example.org`, `rosella.zboncak@example.org`) foram apagadas. A produção já estava
limpa — só o operador.

---

## 15. FEITO — Groq recusava toda seleção com 429

**Encontrado e corrigido em 16/09/2026.** O log da produção repetia, a cada vídeo:

```
Error code: 429 - Request too large for model `qwen/qwen3.8-27b` ... on output tokens per minute
(OTPM): Limit 1000, Requested 2048
```

A recusa é pelo **`max_tokens` pedido**, não pelo consumido: pedir 2048 devolve 429 sem sequer
chamar o modelo. Como `ANTHROPIC_API_KEY` está vazia por configuração normal de operação, o Groq é o
único caminho — então **toda** seleção falhava, cada vídeo caía em "Nenhum momento válido" e virava
`failed`, liberando a janela sem gerar clip nenhum.

Dois pontos pediam correção, os dois acima do teto de 1000:

| Onde | Antes | Depois |
|---|---|---|
| `selector.py` `_select_via_groq` | 2048 | `GROQ_MAX_OUTPUT_TOKENS` (1000) |
| `metadata_generator.py` `_generate_via_groq` | 1024 | `GROQ_MAX_OUTPUT_TOKENS` (1000) |

O payload real cabe com folga: no máximo 3 momentos, e a justificativa está limitada a
`MAX_REASON_CHARS` (300). Ambos leem `GROQ_MAX_OUTPUT_TOKENS` do ambiente, para quem migrar de plano.

O caminho Anthropic segue em 2048 — o limite é do free tier do Groq, não da Anthropic.

---

## 16. ABERTO — Senha de root do MySQL publicada em repositório público

**Encontrado em 16/09/2026. Não corrigido — depende de rotação acompanhada pelo operador.**

`scripts/local_download_worker.py` monta o comando do banco com a senha escrita no código:

```python
f"docker exec mysql mysql -uroot -p<SENHA_LITERAL> clips_automation ..."
```

Confirmado por comparação de hash: **o literal publicado é a senha ativa da produção**.

Alcance apurado:

| Item | Número |
|---|---|
| Arquivos versionados com o literal | 7 (inclui `scripts/validate-infra.sh` e `.planning/**`) |
| Commits no histórico | 14 |
| Já em `origin/master` público | sim |

**Atenuante real, apurado no servidor:** o MySQL **não está exposto na internet**. O container não
publica porta no host (`3306/tcp` sem binding), nada escuta em `0.0.0.0:3306` e o `iptables` tem
`INPUT policy DROP`. Quem tiver a senha ainda precisa de acesso ao host antes. Não é exploração
remota direta — mas é credencial ativa em repositório público.

**Correção pendente, nesta ordem:**

1. Rotacionar a senha no MySQL de produção e no `.env` do servidor.
2. Tirar o literal do código: o worker deve ler a senha do `.env` do servidor via SSH, como já é
   feito manualmente, em vez de carregar segredo no cliente.
3. Limpar `scripts/validate-infra.sh` e os `.planning/**`.
4. **Decisão separada:** reescrever o histórico (`git filter-repo`) ou aceitar que o valor antigo
   fica no histórico público. Rotacionar já torna o valor antigo inútil; reescrever histórico exige
   force push e quebra clones.

### Resolvido em 16/09/2026 — as duas senhas foram rotacionadas

Executado com o operador acompanhando. Ordem: backup dos `.env` → `ALTER USER` → atualização dos
`.env` → restart → verificação.

| Verificação | Resultado |
|---|---|
| `root` com a senha nova | conecta |
| `clips_user` com a senha nova | conecta (consulta real em `source_channels`) |
| Senha **antiga** | recusada pelo MySQL |
| `.env` e `painel/.env` | hashes batem com as senhas geradas |
| Worker local (máquina do operador) | segue funcionando, **sem alteração** |
| `clip-processor` | zero erros de banco no log após o restart |

O worker continuar funcionando sem tocar em nada é consequência direta da correção anterior: ele
resolve a senha lendo o `.env` **dentro do servidor**, então a rotação foi transparente para ele.

**Armadilha encontrada na execução:** o `docker compose up -d` reiniciou também o container `mysql`
(o compose havia mudado), e a verificação rodou antes de o banco aceitar conexões — os dois testes
deram falso negativo. Não era falha de rotação, era espera curta demais. Em rotação futura, esperar
o MySQL responder antes de validar, não um `sleep` fixo.

**O que continua verdade:** os valores antigos permanecem no histórico público do Git. Eles estão
mortos (o MySQL os recusa), então o risco é nulo para acesso — mas quem clonar o repositório ainda
os verá. Reescrever o histórico segue como decisão em aberto, agora sem urgência.

`.env.bak-<data>` e `painel/.env.bak-<data>` ficaram no servidor como rollback. Apagar depois de
alguns dias de operação normal.

---

## 17. ABERTO — Vaga da janela presa por clip aguardando aprovação

**Apurado em 16/09/2026.** A janela de futebol ficou em **10/10 ocupada** com 145 vídeos frescos
esperando, e nenhum download novo começava.

Causa: os 10 vídeos ocupantes estavam em `selecting` e **já tinham gerado clips**, todos em
`pending`. A ocupação é calculada em `pipeline_runner.py` por três condições em `OR`:

```
sv.local_path IS NOT NULL
OR sv.status IN ('downloading','downloaded','transcribing','selecting','cutting','publishing')
OR (gc.status IN ('pending_cut','pending','cutting','approved'))
```

A terceira sozinha segura a vaga. E `recover_stuck_selecting` **não** alcança esses registros, por
desenho: ele exige `NOT EXISTS (SELECT 1 FROM generated_clips ...)` justamente para não reprocessar
vídeo que já tem clip e duplicar corte ([`db.py:308`](../clip-processor/src/db.py#L308)).

**Não é bug de código, é bug de fluxo.** O sistema está esperando decisão humana: enquanto o
operador não aprovar nem rejeitar, a vaga fica retida — e como o teto é por canal destino ativo,
10 clips parados na aprovação param a ingestão inteira do nicho.

`_maybe_finalize_source_video` só libera o vídeo quando **todos** os clips chegam a estado terminal
e ao menos um publicou, então nada se resolve sozinho.

**Caminhos possíveis, nenhum aplicado:**

- aprovar ou rejeitar os clips pendentes (resolve o caso, não a classe);
- não contar `pending` na ocupação, já que clip pendente não consome download;
- teto separado para "aguardando aprovação", distinto do teto de download;
- alerta no painel quando a janela estiver cheia só por clip pendente — hoje o operador não tem
  como saber que a fila parou por causa dele.

