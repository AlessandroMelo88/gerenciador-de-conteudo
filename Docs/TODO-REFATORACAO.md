# TODO — onde o código pode ser melhor refatorado

Auditoria de **25/08/2026** (branch `release/rico`), feita por leitura integral de
`clip-processor/src` + `tests`, `painel/app|routes|config|database|tests` e `painel/resources/js`.
Toda referência `arquivo:linha` foi conferida no código daquele dia — linhas podem ter deslocado
depois do commit `style:` (ruff/pint/prettier), mas os símbolos e trechos citados continuam válidos.

**Como usar este documento**

- Itens em **Alta** são os que geram bug, perda de dado ou risco operacional; **Média** são
  duplicação e acoplamento que custam a cada mudança; **Baixa** é higiene.
- Ao concluir um item, marque `**FEITO — DD/MM/AAAA, commit abc1234**` no título. **Não renumerar**:
  outros documentos e ADRs linkam por número.
- Itens já em [`BUGS.md`](BUGS.md) ou em `ARCHITECTURE.md §10` aparecem só como cruzamento.
- Legenda de esforço: **P** (< meio dia) · **M** (1–2 dias) · **G** (> 2 dias). Risco = chance de
  regressão de comportamento.

**Transversal (aparece nas três frentes)**

1. **Estados como strings mágicas** — 13 módulos Python, 30+ pontos PHP e mapas duplicados no React.
   Um `states.py` (Python) + `App\Enums\*` (PHP) + `types/pipeline.ts` (TS) espelhando os ENUMs de
   `mysql/init`, com teste de paridade. É a raiz dos itens Python #6, PHP A3/A5 e React #11.
2. **Apagar arquivos de clip/vídeo está implementado 4× no Python e o guard difere entre Dashboard
   e Vídeos no PHP** (Python #4/#14, PHP A3/M2). Um único `remove_clip_artifacts` no daemon, um único
   `canDeleteFiles()` no painel.
3. **Cascata de IA duplicada** (Python #2) — ver [`ADR/0003`](ADR/0003-fallback-de-ia-obrigatorio.md).
4. **Falta de testes onde mais dói**: `_maybe_finalize_source_video` com cobertura vazia (Python #3),
   `queue_controls` e `main` sem teste, `ClipProcessorClient` sem teste direto (PHP M3), zero testes
   de frontend (React #20).
5. **Configuração lida na importação / fora de `config/`** (Python #11, PHP A6) — cada lado ganha um
   `config` central.

Atalhos: [Python](#parte-1--clip-processor-python) · [PHP](#parte-2--painel-laravel-php) ·
[React](#parte-3--painel-frontend-reacttypescript)

---

# Parte 1 — clip-processor (Python)

22 módulos (~4.5k linhas), 21 arquivos de teste, 186 testes.

## Alta

### 1. **`_abort_if_paused` abre uma conexão MySQL nova a cada callback de progresso do yt-dlp**
- `downloader.py:136-150` (função) e `downloader.py:159` (`'progress_hooks': [_abort_if_paused]`).
- **Problema:** o hook é chamado pelo yt-dlp a cada fragmento baixado (dezenas a centenas de vezes por download). Cada chamada faz `get_db_connection()` → handshake TCP + `_log('Conexão aberta')` (`db.py:53`) → `is_paused` → `close`. Qualquer erro (MySQL fora, timeout) cai em `except Exception: pass` (`149-150`) — inclusive o erro que impediria detectar o pause.
- **Por que importa:** carga desnecessária no MySQL exatamente durante a etapa mais longa do ciclo, log inundado de "Conexão aberta", e falha silenciosa no único mecanismo de abort cooperativo do download.
- **Refatoração:** receber `conn` (ou um callable `is_paused_fn`) como parâmetro de `download_video`; no hook, checar no máximo a cada N segundos (`time.monotonic()` + `PAUSE_CHECK_INTERVAL_S = 5`) e só quando `d['status'] == 'downloading'`; logar a exceção em vez de engolir.
- **Esforço:** P · **Risco:** baixo. **Testar:** hook chamado 200× com mock → ≤ 1 conexão por intervalo; erro no `is_paused` aparece no log e não aborta o download.

### 2. **Cascata Anthropic → Groq duplicada, com semânticas diferentes e ids de modelo espalhados**
- `selector.py:243-269` vs `metadata_generator.py:124-149`; clientes em `selector.py:95-121` e `metadata_generator.py:91-121`.
- **Problema:** duas implementações da mesma cascata que divergem em pontos que importam: o selector checa `ANTHROPIC_API_KEY` antes de tentar (`selector.py:252`), o metadata_generator instancia `anthropic.Anthropic()` às cegas e depende da exceção (`metadata_generator.py:93-94`); com cliente injetado o selector **não** faz fallback (`244-249`) e o metadata **faz** (`132-142`). Os ids de modelo estão hardcoded 4× (`selector.py:98,112`, `metadata_generator.py:97,112`). O comentário de `selector.py:6-10` e `Docs/SISTEMA-CLIP-PROCESSOR.md:61-62` dizem "LLaMA 3.3-70b", mas o código chama `openai/gpt-oss-120b` (`selector.py:112`). Além disso `metadata_generator.SYSTEM_PROMPT` (`18-24`) é específico de Shorts e `generate_metadata` não recebe `fmt` — clips `longo` recebem SEO de Short.
- **Por que importa:** é exatamente a classe de buraco que produziu os títulos duplicados de 27/07 (CLAUDE.md); o próximo caminho de IA vai copiar uma das duas versões.
- **Refatoração:** `ai_client.py` com `complete_json(system: str, user: str, *, max_tokens: int, anthropic_client=None) -> dict` implementando a cascata uma vez (checa key, tenta Anthropic, cai pro Groq, levanta `AIUnavailable` se ambos falharem); ids de modelo em constantes (`ANTHROPIC_MODEL`, `GROQ_MODEL`) em `config.py`; `generate_metadata(clip_context, fmt=...)` com prompt por formato.
- **Esforço:** M · **Risco:** médio (muda o caminho de produção de dois estágios). **Testar:** Anthropic falha → Groq chamado; ambos falham → exceção tipada; cliente injetado se comporta igual nos dois usos; snapshot dos prompts por formato.

### 3. **`_maybe_finalize_source_video` tem cobertura zero — os testes passam por engano**
- `tests/test_publisher.py:58-62` e `:229` devolvem `{'cnt': 0}`/`{'cnt': 1}` no `fetchone`; o código lê `row.get('non_terminal_count')` e `row.get('published_count')` (`publisher.py:326-327`).
- **Problema:** as duas chaves viram `0`, a função retorna no guard `published_count == 0` (`publisher.py:328-329`) e **nunca** chega na remoção de arquivos (`331-360`) nem nos `UPDATE`s (`362-370`). `test_raw_file_remains_while_another_clip_is_still_pending` (`test_publisher.py:222-247`) passa vacuamente. Agrava: `make_conn_with_clips` (`test_publisher.py:38-77`) usa `dest_channels=[]` por padrão, então 11 dos 13 testes exercitam o caminho **legado** (`publisher.py:52-57`), não o loop multi-canal de produção (`60-84`).
- **Por que importa:** essa função é a que apaga raw, `_raw`, `_subtitled` e thumbnails (bugs 2 e 5) e zera colunas (bug 10). Está sem rede de segurança.
- **Refatoração:** corrigir as chaves do mock; adicionar testes com `tmp_path` para (a) finaliza e apaga tudo, (b) OSError num arquivo mantém a coluna daquele arquivo, (c) `non_terminal_count > 0` não toca em nada; mudar o default da fixture para um canal-destino real e deixar o legado como caso explícito.
- **Esforço:** P/M · **Risco:** baixo. **Testar:** os novos testes falharem antes de qualquer mudança em `publisher.py` é o próprio critério.

### 4. **Três cópias de "apagar artefatos do clip", nenhuma respeita a regra arquivo-antes-do-banco**
- `publisher.py:331-371`, `internal_api.py:123-141`, `internal_api.py:243-254`; `rejeitar.py:86-87` (bug 10, já catalogado).
- **Problema:** `publisher._maybe_finalize_source_video` engole `OSError` (`334`, `353`, `359`) e roda o `UPDATE ... = NULL` de qualquer jeito (`362-370`). `internal_api.delete_source_video_file` faz o oposto: sem `try` nos `os.remove` (`128-135`, `147`, `153`), um arquivo travado aborta no meio com parte dos arquivos já apagados e a transação faz rollback; a rota (`322-334`) só captura `RuntimeError`, então o `OSError` vira 500 HTML sem JSON. `purge_old_videos` apaga arquivo e faz `UPDATE` por linha mas commita só no fim (`243-254`). As três derivam o prefixo e a lista `(clip_path, _raw, _subtitled)` à mão (`publisher.py:348-349`, `internal_api.py:126-127`) — e **nenhuma lista o `.srt`** criado em `video_processor.py:206`, que fica em disco para sempre (não consta em BUGS.md).
- **Por que importa:** é a origem direta do bug 10 (287 `clip_path` órfãos) e do resíduo de disco; cada cópia nova vai divergir de novo.
- **Refatoração:** `storage.py` (ou dentro de `video_processor.py`, dono da nomenclatura) com `ClipPaths(clip_id)` (raw, srt, subtitled, final, thumb) e `remove_clip_artifacts(clip_path, thumbnail_path) -> RemovalResult(removed: list, failed: list)`; quem chama só zera coluna de arquivo confirmado removido (`os.path.exists` depois do `remove`), commit por registro. `rejeitar.py` passa a zerar `clip_path`/`thumbnail_path` via o mesmo helper.
- **Esforço:** M · **Risco:** médio (mexe em 4 caminhos destrutivos — fazer com backup e a lista-antes-de-apagar do CLAUDE.md). **Testar:** `tmp_path` com arquivo `chmod 000` → coluna mantida, resto removido; `.srt` incluído na remoção.

### 5. **`poll_all_channels` é o ciclo inteiro dentro de uma função de 115 linhas**
- `rss_poller.py:177-291`: RSS (`200-259`), estágio de IA (`262-281`), estágio de corte (`284-287`).
- **Problema:** um módulo chamado `rss_poller` executa transcrição, seleção e FFmpeg (a doc já chama de "nome enganoso"). Os testes dependem da **ordem** dos `fetchall` (`test_clip_pipeline.py:13-17`, `test_rss_poller.py:140`): adicionar uma query no meio quebra teste sem relação. `_process_ai_pipeline` (`97-155`) faz `from src.queue_controls import is_paused` dentro da função (`108`).
- **Refatoração:** `rss_poller.ingest_rss(conn, redis)`, `ai_stage.run(conn)` (transcrever + selecionar), `cut_stage.run(conn)`; `pipeline_runner.run_ingest_cycle` chama os três com `_run_stage` (item 13). Preservar a ordem atual.
- **Esforço:** M · **Risco:** médio. **Testar:** os testes existentes de `TestAIPipelineIntegration` e `test_clip_pipeline.py` reescritos por estágio; um teste de ordem em `run_ingest_cycle`.

### 6. **Estados como strings mágicas em 13 módulos, com conjuntos divergentes**
- Contagem de literais (`'pending'`, `'cutting'`, `'publishing'`…): `db.py` 29, `pipeline_runner.py` 26, `publisher.py` 15, `rss_poller.py` 12, `queue_controls.py` 11, `internal_api.py` 10, `rejeitar.py` 10, `transcription_job.py` 6, `ttl_worker.py` 5. Conjuntos nomeados: `publisher.NON_TERMINAL_CLIP_STATUSES:18`, `queue_controls._CLIP_STATUSES_NEED_RAW:10`, `internal_api._CLIP_STATUSES_NEED_RAW_FILE:173` (cópia idêntica do anterior), `rejeitar._REJECTABLE_STATUSES:35`; listas inline em `pipeline_runner.py:64-65` (ocupação da janela), `internal_api.py:205,215,234`, `queue_controls.py:158`.
- **Por que importa:** o bug 4 (estados sem recuperação) e o bug 9 (janela ocupada por `failed`) são consequência de ninguém enxergar o conjunto completo de estados num lugar só. `Docs/ESTADOS-E-TRANSICOES.md` existe mas o código não a referencia.
- **Refatoração:** `states.py` com `VideoStatus(StrEnum)`, `ClipStatus(StrEnum)`, `JobStatus(StrEnum)` e conjuntos nomeados (`CLIP_NEEDS_RAW`, `CLIP_NON_TERMINAL`, `CLIP_REJECTABLE`, `VIDEO_OCCUPIES_WINDOW`). `StrEnum` é `str`, então passa direto como parâmetro do driver.
- **Esforço:** M (mecânico) · **Risco:** baixo. **Testar:** suíte existente; um teste que garante que `VIDEO_OCCUPIES_WINDOW ⊆ VideoStatus`.

### 7. **`main.py` faz tudo em tempo de import**
- Scheduler e 4 `add_job` no nível do módulo (`main.py:98-156`), `signal.signal` (`158-159`), import do Flask app (`40`), e um `BlockingScheduler` falso de 30 linhas só para o teste importar sem apscheduler (`7-35`). Único teste de `main` mora em `tests/test_pipeline_runner.py:323-335`.
- **Por que importa:** `import src.main` num teste registra handlers de SIGTERM no processo do pytest; a correção do bug 11 (SIGTERM ignorado, já catalogado) exige justamente reestruturar isso.
- **Refatoração:** `build_scheduler() -> BlockingScheduler`, `install_signal_handlers(stop_event)`, `main()`; o handler só seta um `threading.Event`, e o loop principal sai de `scheduler.start()` (abordagem sugerida no bug 11). Remover o fallback de apscheduler (ver item 20).
- **Esforço:** M · **Risco:** médio (é o entrypoint). **Testar:** `tests/test_main.py` com ids/`coalesce`/`max_instances` dos jobs de `build_scheduler()`; handler seta o evento; `docker stop` termina em `Exited (0)`.

### 8. **`internal_api.py`: app e env em import, auth colada em 10 rotas, mapeamento de erro inconsistente**
- `INTERNAL_TOKEN`/`REDIS_*` em import (`27-29`), `app = Flask(__name__)` (`31`); `if not _check_auth(): return 401` repetido em todas as rotas (`263`, `278`, `293`, `308`, `324`, `339`, `354`, `368`, `382`, `400`); imports tardios em 4 rotas (`356`, `370`, `384`, `402`); `_route_delete_source_video` (`322-334`) é a única sem `except Exception`. `delete_source_video_file` (`86-169`, 84 linhas) e `purge_old_videos` (`176-258`, 83 linhas) são lógica de domínio dentro do módulo HTTP e não têm teste direto (`delete_source_video_file`: zero referências em `tests/`).
- **Refatoração:** `create_app(token: str) -> Flask`; decorator `@require_token`; `_respond(fn)` que mapeia `RuntimeError → 422`, `Exception → 500` uma vez; mover `delete_source_video_file`/`purge_old_videos` para `storage.py`/`queue_controls.py`. Fixture de teste passa a usar `create_app('test-token')` em vez de `monkeypatch.setattr('src.internal_api.INTERNAL_TOKEN', ...)` (`test_internal_api.py:11`, `test_transcription_job.py:25`).
- **Esforço:** M · **Risco:** baixo. **Testar:** 401 em todas as rotas sem token (parametrizado); 422 vs 500 por tipo de exceção; testes de `delete_source_video_file` com `tmp_path` (hoje não há nenhum).

### 9. **Uma conexão de banco segurada durante o ciclo inteiro, sem `ping`/reconnect**
- `pipeline_runner.py:194-244`: a mesma `db_conn` atravessa `poll_all_channels` (transcrição + seleção + FFmpeg de N vídeos) + downloads (com `time.sleep(60)` × 3 por retry, `downloader.py:186`) + publish. `transcription_job.py:231-254`: a conexão é aberta antes do yt-dlp (timeout 600 s) e do whisper (até 3 × 3600 s) e usada depois (`245`, `247`). Não existe `conn.ping(` em `src/` (verificado). O docstring de `rss_poller.py:14` promete "nova conexão por chamada (evita timeout)", o que não acontece quando `db_conn` é injetada pelo runner.
- **Por que importa:** "server has gone away" no `UPDATE` final de um job de 3 h marca nada e deixa o estado preso — é o mesmo mecanismo do bug 4, só que por timeout em vez de crash.
- **Refatoração:** `db.connection()` como context manager e `db.ensure_alive(conn)` chamado na fronteira de cada estágio e antes do `update_job` final; ou abrir conexão curta por estágio (a de `transcription_job` deve ser aberta **depois** do whisper).
- **Esforço:** M · **Risco:** médio. **Testar:** mock com `ping` assertado antes de cada estágio; `process_transcription_job` com `update_job` levantando `OperationalError` na última chamada → reconecta e grava.

## Média

### 10. **`_log()` reimplementado 12×, `flush` inconsistente, tags duplas e nenhum traceback**
- Definições: `db.py:21`, `dedup.py:21`, `downloader.py:48`, `metadata_generator.py:46`, `pipeline_runner.py:26`, `main.py:50`, `queue_controls.py:13`, `publisher.py:29`, `selector.py:67`, `rss_poller.py:49`, `transcriber.py:21`, `video_processor.py:30`. Só 4 usam `flush=True` (`main.py:51`, `queue_controls.py:14`, `pipeline_runner.py:27`, `selector.py:68`) e `PYTHONUNBUFFERED` não está setado no Dockerfile nem no compose (verificado) — no `docker logs` as mensagens dos outros 8 módulos chegam atrasadas e fora de ordem em relação a essas 4. Tags duplas: `[ACQU] [AI]` (`rss_poller.py:51` + `:111`), `[AI] [SELECTOR]` (`selector.py:68` + `:80`), `[PUB] [PUBLISHER]` (`publisher.py:30` + `:54`); `[VID]` é usada por `video_processor.py:31` e `metadata_generator.py:47`. `telegram_notifier`, `ttl_worker`, `rejeitar`, `processar` usam `print` sem timestamp. `uploader.py:172,191` é o único lugar com `logging`. Não há `traceback`/`exc_info`/`logging.exception` em `src/` (verificado): todo `except Exception as exc: _log(f'... {exc}')` joga o stack fora.
- **Refatoração:** `log.py` com `get_logger(tag)` sobre `logging` (StreamHandler em stdout, formatter `%(asctime)s [%(tag)s] %(message)s`), `logger.exception()` nos catches de estágio; `ENV PYTHONUNBUFFERED=1` no Dockerfile.
- **Esforço:** M (mecânico) · **Risco:** baixo. **Testar:** `caplog` em 2–3 módulos; conferir no container que a ordem dos logs bate com a ordem dos estágios.

### 11. **Sem `config.py`: env parseada em import por 7 módulos, com defaults divergentes**
- `REDIS_HOST/PORT` em `internal_api.py:28-29`, `pipeline_runner.py:21-22`, `rss_poller.py:45-46`, `ttl_worker.py:42-43`; `redis.Redis(...)` construído 6× (`internal_api.py:224`, `rss_poller.py:192`, `ttl_worker.py:41`, `pipeline_runner.py:200,260,297`). `CLIP_PROCESSOR_INTERNAL_TOKEN` lida 2× com defaults diferentes (`internal_api.py:27` → `None`, `telegram_notifier.py:34` → `''`). `SAO_PAULO_TZ` em `pipeline_runner.py:23` e `quota_manager.py:12`, e como string em `main.py:98`. `VIDEOS_DIR = '/app/videos'` em `downloader.py:29`, `transcriber.py:18`, `transcription_job.py:25`, `video_processor.py:25` e como default de argumento em `queue_controls.py:172`. Template do token em `uploader.py:78` e `youtube_oauth.py:54`. Leituras em import que obrigam `monkeypatch` de global: `ttl_worker.py:21-22`, `telegram_notifier.py:29-34`, `transcription_job.py:28-29`, `youtube_oauth.py:36-38`, `pipeline_runner.py:35-36`. Drift de `MAX_UPLOADS_PER_DAY` já catalogado (ARCHITECTURE §10 #11).
- **Refatoração:** `config.py` com `@dataclass(frozen=True) Settings` + `Settings.from_env(env=os.environ)` e um acessor `settings()` com cache limpável; `clients.py` com `get_redis(settings)`. Módulos importam funções, não constantes.
- **Esforço:** M · **Risco:** baixo. **Testar:** `Settings.from_env({'REDIS_PORT': '1'})`; testes existentes trocam `monkeypatch.setattr(módulo.CONST)` por `settings` injetado.

### 12. **`publisher.py`: dois loops de publicação quase idênticos e código morto**
- `_publish_clips_for` (`155-200`) e `_publish_one` (`203-235`) repetem literalmente o bloco upload → `_mark_clip_published` → `record_upload` → `_maybe_finalize` → `notify` (`183-198` vs `219-234`), com semântica de cota sutilmente diferente (`has_capacity` no loop legado `167`, `break` externo no multi-canal `83-84`). `_fetch_pending_clips` (`238-253`) é o gêmeo legado de `_fetch_pending_clips_for_channel` (`99-127`) sem o JOIN e sem round-robin. `_ensure_publishable_files` (`256-263`) não é chamada por ninguém (verificado; `uploader._validate_clip:127-135` faz o mesmo). `_update_clip_status` (`266-272`) é byte-a-byte igual a `video_processor._update_clip_status` (`275-281`).
- **Refatoração:** um único `_publish_one`; caminho legado = `_fetch_pending_clips_for_channel(conn, destination_channel_id=None)` com `destination_channel_id IS NULL` — ou remover o legado se `destination_channels` é sempre seedado (ARCHITECTURE §10 #14); apagar `_ensure_publishable_files`; `_update_clip_status` vai para o repositório (item 15).
- **Esforço:** M · **Risco:** médio. **Testar:** `test_publisher.py` inteiro (depois do item 3); teste de `_round_robin_by_source_channel` (hoje sem teste direto).

### 13. **`pipeline_runner.py`: ciclo de vida de conexão e try/except+notify copiados 3×/6×**
- Bloco `own_db/own_redis` em `194-204`, `254-264`, `291-301`; bloco `try: estágio / except: _log + notify('pipeline_failure', {...})` em `209-217`, `219-226`, `228-238`, `266-276`, `304-311`, `313-320`. `run_pipeline_once` (`189-244`) é `run_ingest_cycle` + `run_publish_only`. `from src.uploader import YouTubeUploader` (`18`) não era usado — existia porque 7 testes faziam `patch('src.pipeline_runner.YouTubeUploader')`; **import e patches removidos em 25/08/2026 (commit `style:` do ruff)**.
- **Refatoração:** `@contextmanager _connections(db_conn, redis_client)`; `_run_stage(name, fn, *args)` que loga, notifica e engole; `run_pipeline_once = run_ingest_cycle + run_publish_only`; remover o import e os 7 `patch`.
- **Esforço:** P/M · **Risco:** baixo. **Testar:** suíte existente de `TestRunPipelineOnce`/`TestRunIngestCycle`.

### 14. **Duas funções chamadas `_cleanup_partial` com garantias opostas, importadas como privadas entre módulos**
- `downloader._cleanup_partial` (`53-69`): filtra por `_WORK_ARTIFACT_RE`, **nunca** apaga `<id>.mp4`. `queue_controls._cleanup_partial` (`172-181`): `glob('<id>*')` apaga raw, `<id>_transcript.json` e `<id>_audio.mp3`. `pipeline_runner.py:14` e `internal_api.py:95` importam a versão destrutiva pelo nome privado; `_discard_failed_download` (`pipeline_runner.py:133`) depende dela apagar o raw.
- **Por que importa:** quem lê `_cleanup_partial(...)` no `pause_video` (`queue_controls.py:63`) ou no sidecar (`internal_api.py:158`) assume "limpa temporários" e não "apaga tudo do vídeo" — exatamente o tipo de confusão contra a qual as regras de operação destrutiva do CLAUDE.md foram escritas.
- **Refatoração:** renomear para `remove_video_files(video_id, videos_dir)` (destrutivo, público, em `storage.py`) e `remove_download_artifacts(path)` no downloader; remover `_CLIP_STATUSES_NEED_RAW_FILE` de `internal_api.py:173` em favor do conjunto único (item 6).
- **Esforço:** P · **Risco:** baixo. **Testar:** `tmp_path` com `<id>.mp4`, `<id>_transcript.json`, `<id>.f298.mp4.part`, `<outro>.mp4` → cada função remove exatamente o que promete.

### 15. **Escritas em `generated_clips` espalhadas por 8 módulos; `db.py` só conhece `source_videos`**
- `publisher.py:266-311` (4 helpers), `video_processor.py:235-242,275-281`, `rejeitar.py:76-79`, `ttl_worker.py:50-54`, `queue_controls.py:81-85`, `metadata_generator.py:175-181`, `selector.py:322-329`, `internal_api.py:137-141`. Dois "inserir source_video" com semântica diferente: `db.insert_video:101-124` (`INSERT IGNORE`) e `processar.upsert_source_video:88-152` (SELECT-then-INSERT + pseudo-canal). `db.update_status` monta 3 SQLs para uma coluna opcional (`73-93`) enquanto `transcription_job.update_job` (`56-81`) já tem o padrão de SET dinâmico.
- **Refatoração:** `repo/videos.py`, `repo/clips.py`, `repo/jobs.py` — funções puras sobre `conn`, sem ORM, todo SQL de uma tabela num arquivo; `update_status` reescrito com SET dinâmico; `insert_video` e `upsert_source_video` unificados em `ensure_source_video(conn, ...)`. **Nota (25/08/2026):** a migração de motor de banco em andamento (ADR-0006) é o momento natural para isto — todo SQL vai ser tocado de qualquer jeito.
- **Esforço:** G · **Risco:** médio. **Testar:** testes de repositório com o `FakeCursor` do item 22; módulos de negócio passam a mockar o repo, não o cursor.

### 16. **`select_moments`: filtro de Short curto é código morto e pós-processamento duplicado**
- `_finalize` chama `_filter_shortform_duration(result)` (`selector.py:240`) sem `transcript_duration`, então o ramo `176-177` (permitir < 30 s quando o vídeo inteiro é curto, prometido pelo `SYSTEM_PROMPT:26`) nunca roda em produção — todo momento de um Short < 30 s é descartado em `181-183`. `insert_selected_moments` refaz `_remove_overlaps` (`307`) sobre momentos já finalizados, tem `if inserted >= 3` redundante (`312`), `score < 7` mágico (`318`) e commit por linha (`330`). `MAX_CHARS` (`226`) é constante local em maiúsculas.
- **Refatoração:** `format_transcript(transcript) -> (text, duration)`; passar `transcript_duration` ao filtro (decisão explícita: manter ou não Shorts curtos); `MIN_SCORE = 7`, `MAX_TRANSCRIPT_CHARS = {'curto': 8000, 'longo': 20000}` no topo; um commit ao final de `insert_selected_moments`.
- **Esforço:** P/M · **Risco:** médio (muda o que passa pelo filtro). **Testar:** transcrição de 20 s com momento 0–20 → mantido; `score 6.9` descartado; longo com 1 momento de 300 s → esticado por `_enforce_longform_duration` (hoje sem teste).

### 17. **yt-dlp invocado de 3 jeitos diferentes; duas regex de video id**
- `processar.fetch_metadata:67-85` (API Python, `skip_download`), `rss_poller._detect_format:54-70` (API Python, opções diferentes), `internal_api.resolve_channel:43-78` (`subprocess.run(['yt-dlp', ...])` + `json.loads`). Regex: `processar.YOUTUBE_URL_RE:31-34` e `rss_poller._extract_video_id:90`.
- **Refatoração:** `ytdlp_client.py` com `extract_info(url, *, flat=False, playlist_items=None, timeout=30) -> dict` e `parse_video_id` único (o de `processar`); `resolve_channel` usa a API Python com `extract_flat` em vez de subprocess.
- **Esforço:** M · **Risco:** baixo. **Testar:** os 3 conjuntos de testes existentes passam a mockar um único seam.

### 18. **`purge_old_videos`: mesmo WHERE executado duas vezes e Redis silenciado**
- `internal_api.py:201-209` (SELECT dos ids) e `211-218` (DELETE com o mesmo WHERE): entre um e outro uma linha pode mudar de status, e as chaves Redis apagadas em `225` deixam de corresponder às linhas apagadas. `except redis.RedisError: pass` (`226-227`) esconde exatamente a complicação descrita no bug 6 (já catalogado).
- **Refatoração:** `DELETE FROM source_videos WHERE id IN %s` com os ids do SELECT; logar falha de Redis com a lista de chaves não removidas.
- **Esforço:** P · **Risco:** baixo. **Testar:** `test_purge_old_videos_deletes_rows_and_frees_files` + caso Redis levantando erro → resultado inclui `redis_failed: [...]`.

### 19. **`transcription_job`: falha no `update_job('failed')` mata a thread e o job fica preso; sem recuperação**
- `transcription_job.py:246-247`: se o banco caiu durante 1–3 h de whisper (ver item 9), o `update_job(... 'failed')` levanta dentro do `except`, a thread morre com traceback e o job fica em `transcribing` para sempre. `row = None` (`237`) vira `TypeError` genérico. `run_recovery_once` (`main.py:58-81`) não conhece `transcription_jobs`.
- **Refatoração:** reconectar antes do update final; ramo explícito "job não encontrado"; query de recovery para `transcription_jobs` em `downloading/transcribing` sem update há N horas → `failed`.
- **Esforço:** P · **Risco:** baixo. **Testar:** `update_job` com `side_effect=[None, None, OperationalError]` → nenhuma exceção escapa e o job termina `failed`.

### 20. **Shims de import para rodar testes sem dependências, dentro do código de produção**
- `uploader.py:21-61`: 40 linhas criando `Credentials`, `MediaFileUpload`, `RefreshError` falsos e injetando `googleapiclient.errors` em `sys.modules`. `main.py:7-35`: `BlockingScheduler` falso. `requirements.txt` sem pin e com `pytest`/`pytest-mock` misturados às deps de produção (`requirements-dev.txt` foi criado em 25/08/2026; falta pinar e mover o pytest quando o container deixar de ser o único lugar de rodar a suíte). Causa raiz é o bug 7 (já catalogado).
- **Refatoração:** remover os shims; `requirements.txt` pinado; `pytest` no host via `make test-python` (já funciona) ou no container.
- **Esforço:** P · **Risco:** baixo (só afeta execução no host). **Testar:** suíte no container e no host; `python -c 'import src.uploader'` sem google libs deve falhar rápido e claro.

### 21. **`uploader.py`: helpers gêmeos, conexão própria e duck-typing para mocks**
- `_flag_expired` (`152-173`) e `_clear_expired` (`175-192`) são idênticos exceto `TRUE/FALSE`, cada um abrindo sua própria conexão — o uploader passa a conhecer `destination_channels`. `_execute_resumable` (`210-216`) decide por `hasattr(request, 'next_chunk')` para acomodar mocks. `thumbnails().set` fora de `try` (`114-123`) é o bug 3 (já catalogado); note que `test_uploader.py:140-164` hoje **afirma** a propagação e precisa inverter junto com a correção.
- **Refatoração:** `_set_oauth_flag(value: bool)`; receber `on_oauth_expired`/`on_oauth_ok` callbacks (ou `conn`) do publisher; `_execute_resumable` sempre usa `next_chunk` (é o contrato de `MediaFileUpload(resumable=True)`).
- **Esforço:** P · **Risco:** baixo. **Testar:** `test_uploader_expired.py` + callback chamado com `True`/`False`.

### 22. **Infra de teste acoplada à ordem dos `fetchall`/`fetchone`**
- `conftest.mock_db_conn` (`24-49`) cria um cursor e depois sobrescreve `conn.cursor.return_value` com outro MagicMock; cada teste multi-query enfileira `side_effect` na mão (`test_publisher.py:53-62`, `test_clip_pipeline.py:13-17`, `test_rss_poller.py:140`, `test_pipeline_runner.py:144-150`, `test_ttl_worker.py:41-47`). Os `StopIteration` do bug 7 são isso. `test_pipeline_runner.py:221-239` já teve que inventar um `fetchone` com default para não quebrar.
- **Refatoração:** `tests/fakes.py` com `FakeCursor` que roteia por fragmento de SQL (`{'FROM destination_channels': [...], 'FROM generated_clips gc': [...]}`) com `rowcount`/`lastrowid` configuráveis; alternativa mais forte, para os repositórios do item 15: banco `clips_automation_test` real no container com fixture de truncate.
- **Esforço:** M/G · **Risco:** baixo. Habilita os itens 3, 5, 12 e 15.

### 23. **`ttl_worker.py` carrega código só para satisfazer o mock**
- `ttl_worker.py:56-61`: `cur.fetchall()` dentro de `try/except` depois de um `UPDATE`, com comentário admitindo que existe para "o contrato dos testes". `run_ttl_once` (`26-95`) mistura ciclo de conexão, 2 queries e loop de notificação; `print` sem timestamp em `88` e `91`.
- **Refatoração:** remover o drain e ajustar `test_ttl_worker.py:41-47,60-63` (com `FakeCursor` do item 22 isso some sozinho); separar `expire_pending(conn)` e `warn_expiring(conn, redis)`.
- **Esforço:** P · **Risco:** baixo. **Testar:** existentes + caso `notify` retorna `False` (hoje sem teste).

### 24. **`process_clip`: variável morta, sem limpeza no `except`, paths montados à mão**
- `video_processor.py:232` calculava `duration` e nunca usava (**removido em 25/08/2026 pelo commit `style:` do ruff**). `250-256` marca `failed` sem remover `_raw`/`_subtitled`/`.srt` (residual do bug 2, já catalogado). Os 5 paths (`205-209`) são montados inline e reconstituídos por prefixo em `publisher`/`internal_api` (item 4).
- **Refatoração:** `ClipPaths` (item 4) usado aqui; `except` chama `remove_clip_artifacts(paths)` antes de marcar `failed`.
- **Esforço:** P · **Risco:** baixo. **Testar:** `cut_clip` levantando após criar `_raw.mp4` em `tmp_path` → arquivo removido e status `failed`.

## Baixa

### 25. **`IN (...)` montado de três jeitos**
- Placeholders manuais em `pipeline_runner.py:98`, `queue_controls.py:161`, `internal_api.py:229`; expansão de tupla `IN %s` em `publisher.py:318-322`. Escolher um e, se ficar no explícito, `sql_in(values) -> (fragment, params)` em `db.py`.
- **Esforço:** P · **Risco:** baixo.

### 26. **`pipeline_runner._download_pending_videos` reimplementa `is_paused`**
- `pipeline_runner.py:158-166` e `176-184` fazem `SELECT paused ...` inline; `queue_controls.is_paused` (`21-31`) existe e é usado por `rss_poller` e `downloader`.
- **Esforço:** P · **Risco:** baixo. **Testar:** `test_failed_download_updates_status_to_failed` continua verde.

### 27. **`QuotaManager`: GET duplo no Redis e atributos só para testes**
- `has_capacity` lê o contador (`quota_manager.py:56`) e `can_upload` lê de novo (`71`); `self._max` (`41`) existe para `test_quota_manager.py:71,78`; `UPLOAD_WINDOW_START/END` (`18-19`) são aliases sem uso em `src/`. Envs lidas em `107`, `112`, `123` vão para `config.py`.
- **Esforço:** P · **Risco:** baixo. **Testar:** `test_quota_manager.py` trocando `_max` por `max_uploads_per_day`.

### 28. **`transcriber.transcribe_video`: parâmetro documentado que não faz nada e mágicos**
- `db_conn` (`transcriber.py:51`, docstring `58`) não é referenciado no corpo. `24_000_000` (`72`) → `GROQ_MAX_UPLOAD_BYTES`. `video_path.replace('.mp4', '_audio.mp3')` (`35`) substitui todas as ocorrências.
- **Esforço:** P · **Risco:** baixo.

### 29. **Docstrings e comentários desatualizados; código antes dos imports**
- n8n: `pipeline_runner.py:4`, `processar.py:11-12`, `rejeitar.py:13`. `rss_poller.py:14` ("nova conexão por chamada"). `selector.py:6-10` (LLaMA vs `openai/gpt-oss-120b` em `112`) e `Docs/SISTEMA-CLIP-PROCESSOR.md:61-62`. `rss_poller.py:26-35` tem código antes dos imports — `E402` está ignorado por arquivo em `pyproject.toml` até isto ser resolvido. 17 arquivos de teste ainda trazem "RED state / NotImplementedError" de scaffolding.
- **Esforço:** P · **Risco:** nenhum.

### 30. **Testes no lugar errado / duplicados**
- `test_quota_manager.py:205-209` testa `selector._parse_moments` dentro de `TestLongoReservation`. `test_clip_pipeline.py` é um segundo arquivo de `rss_poller`. `test_uploader_expired.py` cabe em `test_uploader.py`.
- **Esforço:** P · **Risco:** nenhum.

### 31. **Type hints incompletos onde mais importa**
- `db.py:57,101,127,156` (funções públicas sem tipos), `transcription_job.update_job:56`, `main.py:50,54,58`; `conn` sem tipo em todo lugar. Adicionar um alias `Connection` em `db.py`, `-> None` explícitos, e promover `mypy` (hoje informativo, 12 erros) a bloqueante quando zerar.
- **Esforço:** M (mecânico) · **Risco:** baixo.

### 32. **Fuso e timestamps misturados**
- `publisher.py:298` grava `published_at` em UTC (`datetime.now(timezone.utc)`), enquanto cota/janela usam `America/Sao_Paulo` e o resto do banco usa `NOW()` do servidor. Decidir uma convenção e documentar em `BANCO-DE-DADOS.md`.
- **Esforço:** P · **Risco:** baixo (leitura no painel).

### 33. **Suíte leva ~4 minutos por `time.sleep` real**
- `downloader.py:186` (`time.sleep(60)` × 3 no retry) e afins não são mockados nos testes de retry; 186 testes em 244 s no host (25/08/2026). `mocker.patch('time.sleep')` numa fixture `autouse` derruba isso para segundos.
- **Esforço:** P · **Risco:** nenhum.

## Módulo × teste × cobertura percebida

| Módulo (linhas) | Teste | Cobertura | O que falta / observação |
|---|---|---|---|
| `db.py` (223) | `test_db.py` | rasa | asserts por substring de SQL; `OperationalError` em `recover_*` sem teste |
| `dedup.py` (84) | `test_dedup.py` | boa | `mark_failed_redis` testado mas nunca chamado (ARCH §10 #8) |
| `downloader.py` (190) | `test_downloader.py` | boa | `_abort_if_paused` (item 1) sem teste |
| `internal_api.py` (409) | `test_internal_api.py` (+`/transcribe` em `test_transcription_job.py`) | rasa | 5 de 10 rotas; `delete_source_video_file` e as 4 rotas de fila: zero |
| `main.py` (192) | nenhum (1 assert em `test_pipeline_runner.py:323`) | nenhuma | item 7 |
| `metadata_generator.py` (182) | `test_metadata_generator.py` | rasa | só o caminho Anthropic injetado; Groq e fallback final: zero |
| `pipeline_runner.py` (329) | `test_pipeline_runner.py` | boa | os 4 testes do bug 7 passam no host com venv (25/08/2026) |
| `processar.py` (190) | `test_processar.py` | rasa | `main`, `fetch_metadata`, pseudo-canal: zero |
| `publisher.py` (371) | `test_publisher.py` | rasa/média | legado bem coberto; multi-canal 2 testes; `_maybe_finalize` vacuo (item 3); round-robin zero |
| `queue_controls.py` (211) | nenhum | nenhuma | pause/resume/reorder/prioritize/`can_delete_raw`/`_kill_*` |
| `quota_manager.py` (139) | `test_quota_manager.py` | boa | — |
| `rejeitar.py` (108) | `test_rejeitar.py` | rasa | exit code 2 e `affected == 0` sem teste |
| `rss_poller.py` (291) | `test_rss_poller.py` + `test_clip_pipeline.py` | média | tudo mockado por ordem de `fetchall`; `_is_blocked_title` sem teste direto |
| `selector.py` (334) | `test_selector.py` (+1 em `test_quota_manager.py`) | média | modo `longo`, `_enforce_longform_duration`, caminho Groq: zero |
| `telegram_notifier.py` (58) | `test_telegram_notifier.py` | boa | — |
| `transcriber.py` (143) | `test_transcriber.py` | boa | — |
| `transcription_job.py` (271) | `test_transcription_job.py` | média | `_split_audio`/`_shift_srt_timestamps`/`_merge_srt_chunks`/`_run_whisper` (puras, baratas): zero |
| `ttl_worker.py` (95) | `test_ttl_worker.py` | rasa | acoplado à ordem; `notify` falhando sem teste |
| `uploader.py` (237) | `test_uploader.py` + `test_uploader_expired.py` | boa | codifica o comportamento do bug 3 |
| `video_processor.py` (312) | `test_video_processor.py` | boa | limpeza no `except`, filtro `longo` de `cut_clip`: zero |
| `youtube_oauth.py` (112) | nenhum | nenhuma | CLI interativo — aceitável |

## Quick wins Python (< 1 h cada)

1. **Código morto:** apagar `publisher._ensure_publishable_files` (`256-263`). (O import `YouTubeUploader` em `pipeline_runner.py` e os 7 `patch(...)` correspondentes já saíram em 25/08/2026.)
2. **`is_paused` no runner:** trocar os dois `SELECT paused` inline (`pipeline_runner.py:158-166`, `176-184`) por `queue_controls.is_paused(conn, youtube_video_id=...)`.
3. **Conjunto único de "precisa do raw":** remover `internal_api._CLIP_STATUSES_NEED_RAW_FILE` (`173`) e importar `queue_controls._CLIP_STATUSES_NEED_RAW` renomeado para público.
4. **Logs em ordem no Docker:** `ENV PYTHONUNBUFFERED=1` no `Dockerfile` (uma linha) — resolve o `flush` faltante em 8 módulos sem tocar neles.
5. **Mock do publisher honesto:** trocar `'cnt'` por `'non_terminal_count'`/`'published_count'` em `test_publisher.py:58-62,229` — o teste `test_raw_file_remains_while_another_clip_is_still_pending` passa a exercitar o guard de verdade.
6. **`transcriber.transcribe_video`:** remover `db_conn` (`51`) e corrigir docstring (`5`, `10`, `58`); extrair `GROQ_MAX_UPLOAD_BYTES = 24_000_000`.
7. **`time.sleep` mockado por fixture `autouse`** (item 33) — a suíte cai de 4 min para segundos.
8. **Docstrings mentindo:** n8n (`pipeline_runner.py:4`, `processar.py:11-12`, `rejeitar.py:13`), conexão por chamada (`rss_poller.py:14`), nome do modelo Groq (`selector.py:6-10` e `Docs/SISTEMA-CLIP-PROCESSOR.md:61-62` → `openai/gpt-oss-120b`), e mover `rss_poller.py:26-35` para depois dos imports (remove o `E402` do `pyproject.toml`).

---

# Parte 2 — painel Laravel (PHP)

`app/`, `routes/`, `config/`, `database/`, `tests/`. Caminhos relativos a `painel/`.

## Alta

### A1. `/internal/pipeline-event` é fail-open quando o token está vazio (e a comparação não é constant-time)
- `app/Http/Controllers/TelegramWebhookController.php:63-66`; `config/services.php:42`.
- **Problema:** `config('services.clip_processor.token')` vem de `env('CLIP_PROCESSOR_INTERNAL_TOKEN')` sem default → `null` se a var não existir. Sem header, `$request->header('X-Internal-Token')` também é `null`; `null !== null` é `false` e a requisição **passa**. O sidecar Python é fail-closed (ARCHITECTURE §3); o lado Laravel é o oposto. Comparação com `!==` em vez de `hash_equals`.
- **Por que importa:** qualquer um que alcance o nginx (porta 8088) consegue disparar mensagens no Telegram do operador se a env estiver vazia num deploy novo.
- **Refatoração:** middleware `App\Http\Middleware\VerifyInternalToken` — `abort(401)` se `blank($expected) || ! hash_equals($expected, (string) $request->header('X-Internal-Token'))`; alias `internal.token` em `bootstrap/app.php`; aplicar em `routes/web.php:93`; remover o `if` inline.
- **Esforço:** P · **Risco:** baixo.
- **Testar:** `PipelineEventTest` com `config(['services.clip_processor.token' => null])` sem header → 401; token errado → 401; token certo → 200 (já existe).

### A2. `ConnectionException` não é `RuntimeException` — clip-processor fora do ar vira página 500
- `catch (RuntimeException)` em `DashboardController.php:189, 266, 288, 301, 312, 323, 339, 355`; `SourceVideoController.php:186, 207, 224`; `SourceChannelController.php:50`; `ProcessVideoController.php:42`; `TranscriptionController.php:30`; `app/Telegram/Commands/ProcessarCommand.php:26`; `RejeitarCommand.php:26`.
- **Problema:** `Illuminate\Http\Client\ConnectionException extends HttpClientException extends \Exception` (conferido em `vendor/laravel/framework/src/Illuminate/Http/Client/`). Timeout, DNS ou container parado disparam `ConnectionException`, que **nenhum** desses `catch` pega. No painel vira 500; no Telegram o comando morre sem resposta.
- **Por que importa:** SISTEMA-PAINEL diz que "com o clip-processor parado tudo que passa pelo sidecar falha" — mas hoje falha como erro não tratado, não como flash de erro. É o cenário exato do incidente de 27/07.
- **Refatoração:** em `ClipProcessorClient`, um único `private function post(string $path, array $body = [], int $timeout = 15): Response` que captura `ConnectionException` e relança `ClipProcessorUnavailableException extends ClipProcessorException extends RuntimeException`. Controllers e comandos passam a capturar `ClipProcessorException`. Combinar com M3.
- **Esforço:** P–M · **Risco:** baixo.
- **Testar:** unit `Http::fake(fn () => throw new ConnectionException('timeout'))` → exceção própria; feature `POST /painel/clips/{id}/reject` com o mesmo fake → `assertSessionHas('error')`, não 500.

### A3. Guard `canDelete` diverge entre Dashboard e Vídeos, e os docblocks mentem sobre a cascata do sidecar
- `DashboardController.php:72-74, 85` e `:250-255` bloqueiam só clips em `['pending_cut','cutting']`; `SourceVideoController.php:17, 164-165` bloqueia qualquer clip não-terminal (`pending`, `approved`, `publishing` incluídos).
- **Problema:** o sidecar `internal_api.py:86-170` (`delete_source_video_file`) apaga o MP4, `_raw`, `_subtitled` e thumbnail de **todos** os clips do vídeo e zera `clip_path` (`:138-141`); o guard `queue_controls.py:152-169` só recusa `pending_cut`/`cutting`. Logo, "Apagar" no Dashboard num vídeo com clip `approved` aguardando cota apaga o MP4 do clip aprovado → o uploader cai em `FileNotFoundError` → `failed` (mecanismo descrito em BUGS #10). A página Vídeos acerta; o Dashboard não. Os docblocks `DashboardController.php:281-282` ("Não mexe nos clips já cortados") e `ClipProcessorClient.php:82-83` ("Não mexe em status/generated_clips") descrevem um comportamento que não existe mais.
- **Refatoração:** `GeneratedClip::NON_TERMINAL_STATUSES` (ou enum, ver A5) + `SourceVideo::canDeleteFiles(): bool` / scope `deletable()`; Dashboard e Vídeos usam o mesmo método; corrigir os dois docblocks. (Nota: `CLAUDE.md` regra 7 diz que o guard do sidecar só checa `source_videos.status` — já não é verdade, `can_delete_raw` checa `generated_clips` também; atualizar.)
- **Esforço:** P · **Risco:** médio (restringe o que o Dashboard permite — intencional).
- **Testar:** vídeo com clip `approved` → `POST /painel/videos/{id}/delete` → `Http::assertNothingSent()` + flash de erro; prop `activeWindow[].canDelete === false`.

### A4. `tests/Feature/ExampleTest.php` grava usuário com senha `password` no banco real a cada `php artisan test`
- `tests/Feature/ExampleTest.php:8, 24`; `database/factories/UserFactory.php:31`; `phpunit.xml:24-27`.
- **Problema:** é classe PHPUnit que estende `Tests\TestCase` sem `DatabaseTransactions` (o `pest()->extend()->in('Feature')` de `Pest.php:17-19` não aplica trait a classes). `phpunit.xml` aponta para `DB_HOST=mysql` / `clips_automation` — o **mesmo** banco de produção. Cada execução da suíte insere uma linha permanente em `users` com email `*@example.*` e senha `password`.
- **Por que importa:** `users` é a tabela de login do painel. Isso cria contas válidas com senha conhecida.
- **Refatoração:** converter para Pest com `uses(DatabaseTransactions::class)` e fundir em `AuthGuardTest`; apagar `tests/Unit/ExampleTest.php` (residual do skeleton). Depois: `DELETE FROM users WHERE email LIKE '%@example.%'` seguindo as regras de operação destrutiva do `CLAUDE.md`.
- **Esforço:** P · **Risco:** baixo.
- **Testar:** `SELECT COUNT(*) FROM users` antes/depois da suíte deve ser igual.

### A5. Strings mágicas de status em 30+ pontos → Enums PHP
- `DashboardController.php:26, 32, 38, 43, 56, 73, 85, 125, 131, 139-140, 177-178, 208, 213, 217, 231-232, 252, 255`; `SourceVideoController.php:17, 19-29, 46, 48, 57, 61, 136, 142, 158, 164`; `AprovarCommand.php:26-27`; `ClipesCommand.php:16`; `routes/console.php:18`; `TranscriptionController.php:45`; `GeneratedClipFactory.php:28`; `SourceVideoFactory.php:20`.
- **Problema:** três listas diferentes de "em processamento" (`DashboardController:56`, `SourceVideoController:136` e `:142`), rótulos PT-BR hardcoded em `STATUS_LABEL`, e nenhum lugar declara o conjunto válido. O A3 é sintoma direto disso.
- **Refatoração:** `App\Enums\ClipStatus` (`pending_cut, cutting, pending, approved, publishing, published, failed, rejected` — espelho de `mysql/init/05-controle-manual-migration.sql:12`) e `App\Enums\SourceVideoStatus` (espelho de `mysql/init/01-clips-schema.sql:30-40`), string-backed, com `label()`, `isProcessing()`, `needsRawFile()`, `isTerminal()`. `$casts['status' => ClipStatus::class]` nos dois models. Comentar que o ENUM é dono do Python — adicionar teste de paridade contra a lista de `mysql/init`.
- **Esforço:** M · **Risco:** médio (o cast muda `$clip->status` de string para enum; revisar cada `=== 'failed'`; JSON do Inertia serializa o `value` automaticamente).
- **Testar:** suíte atual (ClipApproval, TelegramCommands); teste de paridade enum × `mysql/init`.

### A6. `env()` fora de `config/` **(já catalogado: ARCHITECTURE §10 item 10; SISTEMA-PAINEL "Armadilhas" 1)**
- `DashboardController.php:101, 212`. Só não morde hoje porque `docker/php/bootstrap-panel:23` roda `optimize:clear`, nunca `config:cache`.
- **Refatoração concreta (habilita M12/M13):** criar `config/pipeline.php` com `max_uploads_per_day`, `absolute_max_uploads` (6), `manual_approval_required`, `download_window.curto/longo` (6/4, hoje hardcoded em `SourceVideoController.php:146-150`), `timezone`. Adicionar `MAX_UPLOADS_PER_DAY` e `MANUAL_APPROVAL_REQUIRED` a `painel/.env.example` — estão em `painel/.env` mas não no example (drift não catalogado).
- **Esforço:** P · **Risco:** baixo · **Testar:** `config(['pipeline.max_uploads_per_day' => 9])` → prop `quota[].limit === 6`.

## Média

### M1. `DashboardController::index` faz ~20 queries e mistura leitura de Redis, agregação e apresentação
- `DashboardController.php:19-46` (orquestração), `:54-94` (`activeWindowData`, ordenação em PHP com 6 closures em `:62-70`), `:96-118` (`quotaData`: N `GET` sequenciais no Redis, `:106-110` engole `\Throwable` e mostra `0` — indistinguível de "nada subiu"), `:120-142` (`overviewData`: 4 `count()` com `whereHas`).
- **Refatoração:** `App\ViewModels\DashboardViewModel` (ou `App\Queries\*`): `overviewData` vira 1 query `GeneratedClip::join('source_videos')->selectRaw('source_videos.format, COUNT(*)')->groupBy(...)` + 1 para backlog; `QuotaReader` com `mget` e `null` quando Redis indisponível (UI mostra "indisponível"); `activeWindowData` vira `SourceVideo::scopeInDownloadWindow()` + `sortBy` preservado (≤ 10 linhas, ordenar em PHP é aceitável). Cache não vale a pena — a tela é de observação e precisa ser fresca.
- **Esforço:** M · **Risco:** baixo · **Testar:** `InertiaDashboardTest` com `assertInertia` validando chaves de `quota`, `overview`, `activeWindow`; unit dos query objects com factories.

### M2. Ações de apagar duplicadas em dois controllers e quatro rotas
- `DashboardController::deleteVideo` (`:284-295`) ≡ `SourceVideoController::deleteFile` (`:182-193`); `bulkDeleteVideos` (`:237-278`) vs `bulkDeleteFiles` (`:195-216`) — mesma chamada ao sidecar, guards e mensagens diferentes. Rotas `routes/web.php:35-36` e `:68-69`, todas usadas pelo frontend (`active-window-table.tsx:118, 385`; `SourceVideos.tsx:290, 433`).
- **Refatoração:** `App\Actions\DeleteSourceVideoFiles::handle(Collection $videos): DeleteReport` (freed, failures, skipped) usada pelos dois; idealmente reduzir a 2 rotas (`videos/{video}/files` DELETE e `videos/files/bulk`). Fecha junto com A3.
- **Esforço:** M · **Risco:** baixo · **Testar:** feature das duas rotas com `Http::fake` 200 e 422 em `/internal/delete-source-video`; contagem de skipped/failures na flash.

### M3. `ClipProcessorClient`: 9 métodos repetem o mesmo bloco HTTP com tratamento de erro desigual
- `app/Services/ClipProcessorClient.php:25-27, 49-51, 70-72, 91-93, 120-122, 145-147, 174-176, 192-194` (mesmo `Http::timeout()->withHeader()->post()`); 422 mapeado em `:29, 95, 178, 196` mas não em `rejectClip`, `processUrl`, `purgeOldVideos`, `transcribe`; sem `connectTimeout`; sem retry; retornos `array` sem tipo.
- **Refatoração:** `Http::baseUrl()->withHeaders()->acceptJson()->connectTimeout(3)->timeout($t)` num único `post()`; mapeamento central 422 → `ClipProcessorRejectedException(message: $response->json('error'))`, 5xx → `ClipProcessorException`; `->retry(2, 250)` **só** em `pause/resume/prioritize` (idempotentes — nunca em `reject-clip`/`process-url`/`purge`); DTOs `readonly class ResolvedChannel`, `DeleteResult`, `PurgeResult`. Junta com A2.
- **Esforço:** M · **Risco:** baixo · **Testar:** novo `tests/Unit/ClipProcessorClientTest` com `Http::fake` por endpoint (200/422/500/connection) e `Http::assertSent` conferindo header e URL.

### M4. Nenhum Form Request; validação inline copiada e filtros de listagem sem validação
- `app/Http/Requests/` não existe. `$request->validate` em `DashboardController.php:227, 239-242, 332-335, 348`; `SourceVideoController.php:197, 220`; `DestinationChannelController.php:35-42, 55-62, 71-73`; `SourceChannelController.php:43-46, 71-74`; `ProcessVideoController.php:21-24`; `TranscriptionController.php:26`; `SettingsController.php:22-25`; `NicheController.php:13-16`; `AuthController.php:20-23`.
- **Problemas específicos:** regra `ids` copiada 5× (com `min:1` em 2 e sem em 3, nunca `distinct`/`exists`); `SourceVideoController::index:33-35, 51-52, 66-71` aceita `tab`, `status`, `per_page`, datas sem validar — `per_page=-1` é ignorado por `take()` e **carrega a tabela inteira**; `niche`/`target_niche` (`DestinationChannelController:38, 58`; `SourceChannelController:45`) não valida `exists:niches,slug` embora `niches` seja "a fonte de verdade" (migration `2026_07_14_010214`); `slug` sem `alpha_dash`.
- **Refatoração:** `BulkIdsRequest`, `SourceVideoIndexRequest` (`tab` in, `status` in enum, `per_page` between 10–500, `published_until` `after_or_equal:published_from`), `Store/UpdateDestinationChannelRequest`, `StoreSourceChannelRequest`, `ProcessVideoRequest`, `PipelineEventRequest` (ver M10).
- **Esforço:** M · **Risco:** baixo · **Testar:** 422 para cada entrada inválida; `per_page=-1` → 422.

### M5. Lógica de apresentação dentro dos controllers
- `DashboardController.php:144-171` (`clipPayload`, `formatTrecho`); `SourceVideoController.php:155-180` (`payload`, regra `uso` em `:157-162`); `DestinationChannelController.php:18-28`; `SourceChannelController.php:27-35`.
- **Refatoração:** `JsonResource`s (`GeneratedClipResource`, `SourceVideoResource`, `DestinationChannelResource`, `SourceChannelResource`) ou `App\Presenters`; `formatTrecho` → `Attribute` `GeneratedClip::trecho`; `uso` → `SourceVideo::usageLabel()` usando os enums de A5.
- **Esforço:** M · **Risco:** baixo · **Testar:** `assertInertia` com `->has('pendingClips.0', fn ($p) => $p->hasAll([...]))`.

### M6. `DestinationChannel::oauth_status` faz I/O de filesystem no accessor; `index()` faz 2 syscalls por canal
- `app/Models/DestinationChannel.php:37-47` (`file_exists` a cada acesso; `:43` repete o default de `config/services.php:43`); `DestinationChannelController.php:27` (`Storage::disk('branding')->exists` por canal).
- **Refatoração:** disco `youtube-tokens` em `config/filesystems.php` (igual ao `branding`, `:53-58`) + `App\Services\YouTubeTokenStore::has(string $slug)`; accessor via `Attribute::make(...)->shouldCache()`; no `index()`, ler `Storage::disk(...)->files()` uma vez e testar em memória.
- **Esforço:** P–M · **Risco:** baixo · **Testar:** manter `DestinationChannelOauthStatusTest` trocando `sys_get_temp_dir()` (`:20-24`) por `Storage::fake('youtube-tokens')`.

### M7. Renomear `slug` de canal-destino órfã token OAuth e marca d'água em silêncio
- `DestinationChannelController.php:56, 64` permitem alterar `slug`; token é `token-{slug}.json` (`DestinationChannel.php:44`, ARCHITECTURE §4.3) e marca d'água é `watermark-{slug}.png` (`:75`).
- **Problema:** após rename, badge vira `missing`, o uploader Python perde o token e os clips saem sem watermark — sem nenhum aviso.
- **Refatoração:** tornar `slug` imutável no update (remover da regra ou `'slug' => ['prohibited']`), ou uma action `RenameDestinationChannelSlug` que renomeia os dois arquivos.
- **Esforço:** P · **Risco:** baixo · **Testar:** `PUT` com `slug` novo → 422 / slug inalterado.

### M8. `destroy()` de canais estoura FK e vira 500 sem mensagem
- `DestinationChannelController.php:80-85`; `SourceChannelController.php:81-86`. FKs sem `ON DELETE`: `fk_source_videos_channel` (`mysql/init/01-clips-schema.sql:48-49`) e `fk_generated_clips_destination_channel` (`06-multi-canal-migration.sql:127`). Models não têm as relações inversas (`SourceChannel::sourceVideos()`, `DestinationChannel::generatedClips()`).
- **Refatoração:** adicionar as relações; em `destroy()` checar `->exists()` e devolver `back()->with('error', 'Canal tem N vídeos/clips vinculados')`; opcionalmente oferecer "desativar" no lugar.
- **Esforço:** P · **Risco:** baixo · **Testar:** canal com 1 vídeo → `DELETE` → redirect com erro, linha continua.

### M9. Marca d'água aceita JPEG/GIF/WebP e grava como `.png`
- `DestinationChannelController.php:71-75` — regra `image` + `storeAs(..., "watermark-{slug}.png")`.
- **Problema:** JPEG não tem alpha; o overlay do ffmpeg vira um retângulo opaco sobre o clip.
- **Refatoração:** `'watermark' => ['required', 'mimes:png', 'max:5120', 'dimensions:max_width=1920']`.
- **Esforço:** P · **Risco:** baixo · **Testar:** upload de `.jpg` → 422.

### M10. `pipelineEvent` quebra com payload incompleto e tem branch sem produtor
- `TelegramWebhookController.php:71-77` acessa `$payload['title']`, `['youtube_url']`, `['stage']`, `['error_msg']`, `['clip_id']`, `['expires_in_hours']` sem `??` → chave faltando = `ErrorException` → 500; o notifier Python só loga (`telegram_notifier.py:53`) e o evento se perde. `daily_summary` (`:75`) não tem produtor: `grep daily_summary clip-processor/src` → 0 hits; `telegram_notifier.py:11-14` lista só 3 eventos. `PipelineEventTest.php:55-68` testa esse branch morto.
- **Refatoração:** `PipelineEventRequest` (`event` in:3, `payload.*` por evento) + `App\Telegram\PipelineEventFormatter::format(string $event, array $payload): string` com defaults; remover `daily_summary` (o resumo real é `routes/console.php`, ver B2) ou documentar como reservado.
- **Esforço:** P · **Risco:** baixo · **Testar:** POST `upload_published` sem `title` → 422, não 500; `clip_ttl_warning` (hoje sem teste).

### M11. Webhook do Telegram: sem verificação do secret e allowlist pulável
- `TelegramWebhookController.php:36-40` — `if ($chatId && ...)`: update sem `message.chat.id` (`edited_message`, `callback_query`, `channel_post`) **passa** o allowlist e chega em `Telegram::processCommand` (`:55`). `painel/.env.example` declara `TELEGRAM_WEBHOOK_SECRET`, mas nenhum PHP lê (`grep` → só `scripts/validate-phase6-n8n.py`). O hack de `entities` (`:20-30`) existe só para os testes.
- **Refatoração:** middleware `VerifyTelegramSecret` (`hash_equals` com header `X-Telegram-Bot-Api-Secret-Token`, chave nova `webhook_secret` em `config/telegram.php`); inverter o allowlist para "negar salvo chat_id igual"; mover a montagem de `entities` para o helper `tgCmd()` dos testes.
- **Esforço:** P–M · **Risco:** baixo (exige `setWebhook` com `secret_token`) · **Testar:** sem header → 401; update sem `chat` → `Http::assertNothingSent()`.

### M12. `downloadWindowMetrics` carrega modelos para contar e duplica constantes do Python
- `SourceVideoController.php:133-153`: `get()` + `count()` em PHP (`:135-142`); caps `10/6/4` hardcoded (`:146-150`) espelhando `DOWNLOAD_WINDOW_*` do `pipeline_runner.py`; lista de status em `:136` inclui `cutting`/`publishing`, que `source_videos` nunca recebe (ARCHITECTURE §5); lista "processando" em `:142` difere de `DashboardController:56`.
- **Refatoração:** `SourceVideo::scopeInDownloadWindow()` + `selectRaw('format, COUNT(*)')->groupBy('format')`; caps de `config('pipeline.download_window')` (A6); `isProcessing()` do enum (A5). Nota cross-boundary: `mysql/init` não tem índice em `source_videos.status`/`updated_at` (só `idx_blacklisted`, `06-multi-canal-migration.sql:90`) — cabe ao lado Python.
- **Esforço:** P · **Risco:** baixo · **Testar:** unit do scope com factories (`local_path` null vs preenchido).

### M13. Timezone hardcoded em 3 lugares e `APP_TIMEZONE` do `.env` ignorado
- `DashboardController.php:98, 122` (`Carbon::now('America/Sao_Paulo')`); `routes/console.php:27`; `config/app.php:68` é `'timezone' => 'UTC'` **literal** — não lê `env('APP_TIMEZONE')`, então `APP_TIMEZONE=America/Sao_Paulo` em `painel/.env.example` e `painel/.env` não faz nada.
- **Refatoração:** `config('pipeline.timezone')` como fonte única para o painel. **Não** trocar `app.timezone` sem análise: `overviewData` compara `updated_at` gravado pelo banco/Python; mudar o tz da aplicação desloca o parse desses timestamps.
- **Esforço:** P · **Risco:** baixo (centralizar) / médio (mudar `app.timezone`) · **Testar:** chave de cota às 23:30 SP cai no dia certo.

### M14. Suíte depende de MySQL + Redis reais e tem fontes de flakiness
- `phpunit.xml:24-27` (`DB_HOST=mysql`, banco de produção); `tests/Pest.php:18` (`RefreshDatabase` comentado — motivo em SISTEMA-PAINEL "Banco"); `TelegramWebhookTest.php:35, 50, 59-60` usam Redis real; `TelegramCommandsTest.php:16` gera `update_id` com `random_int` (colisão = dedup silencioso = teste falha sem motivo).
- **Refatoração:** curto prazo — `update_id` via contador estático; `Redis::shouldReceive('set')` ou `Redis::spy()` nos testes de dedup. Médio prazo — extrair `tests/schema/clips_automation.sql` de `mysql/init/01..07`, aplicar num banco `clips_automation_test` (mesmo servidor, outro schema) num `beforeAll`, e religar `RefreshDatabase` — resolve A4 por construção. **O job `php-tests` do CI (25/08/2026) já faz isso num banco descartável** aplicando `mysql/init/*.sql`; falta o equivalente local.
- **Esforço:** G · **Risco:** médio · **Testar:** suíte inteira duas vezes seguidas sem alterar contagens do banco real.

### M15. Lacunas de teste **(parcialmente catalogado: SISTEMA-PAINEL "Testes")**
- Além dos 5 já listados lá (`SettingsController`, `ProcessVideoController`, `SourceVideoController`, `NicheController`, `clips.preview`), não há teste para: `ClipProcessorClient` (direto), `Dashboard::reprocess/bulkApprove/bulkReject/deleteVideo/bulkDeleteVideos/pause/resume/prioritize/reorder`, `TranscriptionController`, `AuthController::login/logout` (só o redirect de guest), `DestinationChannelController::update/uploadWatermark/destroy`, `SourceChannelController::destroy`, o Schedule de `routes/console.php`, e caminhos de erro dos comandos Telegram (`rejeitar` exit 1/2, `processar` com exceção).
- **Ordem sugerida:** ClipProcessorClient (M3) → SourceVideoController index/bulk → Dashboard actions → resto. Ver tabela ao final.
- **Esforço:** G · **Risco:** baixo.

## Baixa

### B1. `clips.preview` como closure em `routes/web.php` e caminho hardcoded
- `routes/web.php:44-52`; `:45` monta `clips/{id}.mp4` em vez de `basename($clip->clip_path)`; `config/filesystems.php:62` referencia um `ClipPreviewController` que não existe; `TranscriptionController.php:49` repete o mesmo remap "caminho do container → disco `clips-videos`".
- **Refatoração:** `ClipPreviewController::__invoke`; helper `App\Support\ClipsVideosDisk::relative(string $containerPath)`; opcional `BinaryFileResponse::trustXSendfileTypeHeader()` + `X-Accel-Redirect` no nginx para não servir MP4 pelo PHP-FPM.
- **Esforço:** P (controller) / M (X-Accel) · **Risco:** baixo · **Testar:** 404 sem arquivo; 200 com `Storage::fake('clips-videos')`.

### B2. Resumo diário é closure no Schedule com `Telegram::sendMessage` dentro
- `routes/console.php:17-27`; comando `inspire` legado em `:9-11`. É o **único** produtor de resumo diário (o Python não tem, ver M10). Roda no serviço `scheduler` (`docker-compose.yml`).
- **Refatoração:** `App\Console\Commands\SendDailySummary` (`painel:daily-summary`) + `Schedule::command(...)`; remover `inspire`.
- **Esforço:** P · **Risco:** baixo · **Testar:** 0 pendentes → `Http::assertNothingSent()`; N → mensagem contém N.

### B3. Higiene de rotas: `web` duplicado, rotas sem nome, Ziggy instalado e não usado
- `routes/web.php:24, 27` aplicam `['web','auth']` — `web` já vem de `withRouting(web:)` (`bootstrap/app.php:11`). Rotas sem `->name()`: `:58-60, 65, 68-70, 73, 76`. `tightenco/ziggy` (`composer.json`) + `@routes` (`resources/views/app.blade.php:11`) + `ziggy-js` (`package.json`) injetam a tabela de rotas inteira em todo HTML, mas `grep "route("` em `resources/js` → 0 usos.
- **Refatoração:** `Route::prefix('painel')->name('painel.')->group(...)` com nomes em tudo, e **ou** usar Ziggy no frontend **ou** remover `@routes` + dependências (ver React #13). Policies/Gates não se justificam hoje (operador único, registro fechado) — registrar a decisão em vez de adicionar cerimônia.
- **Esforço:** P · **Risco:** baixo.

### B4. `shouldRenderJsonWhen` mira `api/*`, que não existe
- `bootstrap/app.php:26-28`. As rotas públicas são `telegramcanal` e `internal/pipeline-event` (`routes/web.php:92-93`); uma exceção ali devolve HTML para o notifier Python.
- **Refatoração:** `fn ($r) => $r->is('internal/*') || $r->is('telegramcanal') || $r->expectsJson()`.
- **Esforço:** P · **Risco:** baixo.

### B5. Models: casts e relações faltando, `$fillable` com `status`
- `SourceChannel.php:14` `$timestamps = false`, mas a tabela tem `created_at` (`01-clips-schema.sql:21`) → `SourceChannelController.php:34` faz `Carbon::parse` na mão; usar `const UPDATED_AT = null` + `$casts['created_at' => 'datetime']`. `TranscriptionJob.php:9` `$guarded = []` sem casts (`progress_percent`, `status`). `GeneratedClip.php:28` e `SourceVideo.php:21` expõem `status` a mass-assignment (todas as escritas atuais usam query builder, então é só risco latente). Relações inversas ausentes (ver M8).
- **Esforço:** P · **Risco:** baixo.

### B6. `ProcessVideoController::store` faz N chamadas síncronas de até 30 s numa única request
- `ProcessVideoController.php:39-54`; timeout em `ClipProcessorClient.php:70`. 10 URLs = até 5 min sob PHP-FPM. O serviço `queue` (`docker-compose.yml`, `QUEUE_CONNECTION=database`) existe, mas não há `app/Jobs`.
- **Refatoração:** opção A — `max` de linhas na validação (ex.: 10) e timeout menor; opção B — `ProcessUrlsJob` com resultado em tabela/flash posterior (perde o feedback imediato por URL, que hoje é útil).
- **Esforço:** P (A) / M (B) · **Risco:** baixo.

### B7. Regra de senha inconsistente **(já catalogado: ARCHITECTURE §10 item 13)**
- `SettingsController.php:24` (`min(8)`) vs `CreatePainelUser.php:48` / `ResetPainelPassword.php:45` (`>= 10`).
- **Refatoração:** `Password::defaults(fn () => Password::min(10))` em `AppServiceProvider::boot`; controller usa `Password::defaults()`; comandos validam com `Validator::make` na mesma regra.
- **Esforço:** P · **Risco:** baixo.

### B8. `TelegramHttpClientHandler` ignora `connectTimeOut`; config do SDK confunde
- `TelegramHttpClientHandler.php:24` guarda `connectTimeOut`, `:33` nunca chama `->connectTimeout()`. `config/telegram.php:23` diz `'http_client_handler' => null`, mas `AppServiceProvider.php:32-37` sobrescreve — o SDK exige instância de `HttpClientInterface` (`vendor/.../Api.php:75`), então o `extend` é necessário; documentar isso no config. `config/telegram.php:7-8` têm domínio e chat_id pessoais como default hardcoded — mover para `.env.example`.
- **Esforço:** P · **Risco:** baixo.

### B9. Resíduos e documentação desatualizada dentro de `painel/`
- **Filament:** `grep -ri filament painel/` (fora de `vendor/`, `*.lock`) → **0 hits**; `app/Filament/Pages/Dashboard.php` foi apagado em `5da905e` — SISTEMA-PAINEL ("Sobrou um órfão") e ARCHITECTURE §10 item 4 estão desatualizados. `painel/README.md` ainda descreve o setup no compose compartilhado de `wordpress/` e "canaldecortes.local" (ARCHITECTURE §2: `localhost:8088`) e diz "NÃO embute player HTML5" (contradito por `clips.preview`). `HandleInertiaRequests.php:24-27` override vazio de `version()`. `tests/Pest.php:40-58` boilerplate (`toBeOne`, `something()`). Nomes de teste "Resource" **(já catalogado: ARCHITECTURE §10 item 9)**.
- **Esforço:** P · **Risco:** nenhum.

### B10. `NicheController` sem feedback e sem ciclo de vida
- `NicheController.php:11-21` — `back()` sem flash; `slug` sem `alpha_dash`/lowercase; não há update/delete de nicho (uma vez criado, é permanente e aparece em todos os selects e tabs).
- **Refatoração:** flash de sucesso; regra `alpha_dash`; `destroy` que recusa se houver canal usando o slug.
- **Esforço:** P · **Risco:** baixo.

## Cobertura percebida por classe

| Classe / arquivo | Teste existente | Cobertura |
|---|---|---|
| `AuthController` | `AuthGuardTest` (guest redirect), `ExampleTest` (raiz) | rasa — sem login OK/falha, sem logout |
| `DashboardController::index` | `InertiaDashboardTest` | rasa — só `component('Dashboard')`, nenhuma prop |
| `DashboardController::approve/reject` | `ClipApprovalActionTest` | boa |
| `DashboardController` demais ações (reprocess, bulk*, videos/*) | — | nenhuma |
| `SourceVideoController` | — | nenhuma |
| `DestinationChannelController` | `DestinationChannelResourceTest` (store, badge) | rasa — sem update/watermark/destroy |
| `SourceChannelController` | `SourceChannelResourceTest` (store ok/422, toggle) | boa (parcial: sem index/destroy) |
| `NicheController` / `ProcessVideoController` / `TranscriptionController` / `SettingsController` / `DocumentationController` | — | nenhuma |
| `TelegramWebhookController::handle` | `TelegramWebhookTest` (allowlist, dedup) | boa |
| `TelegramWebhookController::pipelineEvent` | `PipelineEventTest` (401 + 3 eventos) | boa, mas testa branch morto `daily_summary` e não testa `clip_ttl_warning` nem payload incompleto |
| `app/Telegram/Commands/*` (6) | `TelegramCommandsTest` (7) | boa no caminho feliz; sem erros (`rejeitar` exit 1/2, `processar` exceção) |
| `ClipProcessorClient` | indireto (ClipApproval, SourceChannel, TelegramCommands) | rasa — sem teste direto, sem 5xx/connection |
| `TelegramHttpClientHandler` / `AppServiceProvider` | indireto (todo `Http::fake` de Telegram) | rasa |
| `DestinationChannel::oauth_status` | `DestinationChannelOauthStatusTest` | boa |
| `GeneratedClip`, `SourceVideo`, `SourceChannel`, `Niche`, `TranscriptionJob`, `User` | só via factories | nenhuma (sem unit) |
| `CreatePainelUser` / `ResetPainelPassword` | testes de comando | boa |
| `routes/console.php` (Schedule) | — | nenhuma |
| `clips.preview` (closure) | — | nenhuma |
| `HandleInertiaRequests` (flash/auth props) | indireto | rasa |

Contagem real: 38 testes em 13 arquivos (SISTEMA-PAINEL diz 35).

## Quick wins PHP (< 1 h cada)

1. **Middleware `VerifyInternalToken`** com `hash_equals` e fail-closed, aplicado em `routes/web.php:93` (A1).
2. **Apagar `tests/Unit/ExampleTest.php` e converter `tests/Feature/ExampleTest.php` para Pest com `DatabaseTransactions`** (A4) — depois limpar as linhas `*@example.*` de `users`.
3. **`'mimes:png'` na marca d'água** em `DestinationChannelController.php:72` (M9).
4. **Remover `slug` das regras de `update`** em `DestinationChannelController.php:56` (M7).
5. **`exists:niches,slug`** em `DestinationChannelController.php:38, 58` e `SourceChannelController.php:45` (M4).
6. **`Password::defaults(min 10)`** em `AppServiceProvider` + `SettingsController.php:24` (B7).
7. **Corrigir docblocks errados** em `DashboardController.php:281-282`, `ClipProcessorClient.php:82-83`, `config/filesystems.php:62`, e a regra 7 do `CLAUDE.md` (A3/B1).
8. **`shouldRenderJsonWhen` para `internal/*` e `telegramcanal`** em `bootstrap/app.php:26-28` (B4) + remover `'web'` redundante em `routes/web.php:24, 27` (B3).

---

# Parte 3 — painel frontend (React/TypeScript)

`painel/resources/js` — `pages/`, `components/` (exceto `ui/`, shadcn gerado), `layouts/`, `hooks/`,
`lib/`, `types/`, `app.tsx` e `resources/css/app.css`. Caminhos relativos a `painel/`.

**Sobre a stack anunciada:** de `@tanstack/react-table`, `recharts`, `zod`, `ziggy-js` e `vaul`
(`package.json`), **nenhum é importado por código da aplicação** — `recharts` só via `ui/chart.tsx` e
`vaul` só via `ui/drawer.tsx`, ambos sem importadores. O único dos "extras" realmente em uso é
`dnd-kit`. Vários itens abaixo partem disso.

## Alta

### 1. **Unificar o wrapper de `router.post`** — *o erro de `tsc` foi corrigido em 25/08/2026 (commit `24ead85`); a duplicação continua*
- Onde: `components/active-window-table.tsx` (`postAction`) e `components/clip-queue-tabs.tsx` (`post`, mesma função com `Record<string, FormDataConvertible | number[]>`).
- Problema: são a mesma função copiada em dois arquivos; uma delas usava `Record<string, unknown>`, que não é atribuível a `RequestPayload` (`@inertiajs/core`). A outra "consertou" com um tipo redundante (`number[]` já está dentro de `FormDataConvertible`).
- Refatoração: mover para `lib/inertia.ts` como `postAction(url: string, data?: RequestPayload)`; apagar as duas cópias. (Ver também item 2, que pode absorver o `onSuccess` desse wrapper.) `npm run typecheck` já existe e roda no CI.
- Esforço: P · Risco: baixo

### 2. **Flash → toast: seis implementações com três semânticas diferentes, e três páginas sem feedback nenhum**
- Onde: `pages/Dashboard.tsx` (deps `[]`, roda só no mount), `pages/Settings.tsx`, `pages/ProcessVideo.tsx`, `pages/TranscricaoLocal.tsx` (deps `[flash?.success, flash?.error]`), `components/active-window-table.tsx` e `components/clip-queue-tabs.tsx` (no `onSuccess` da visita). `pages/DestinationChannels.tsx`, `pages/SourceChannels.tsx` e `pages/SourceVideos.tsx` **não mostram flash** — embora os controllers setem (`DestinationChannelController.php:50,66,77,84`, `SourceChannelController.php:66,85`, `SourceVideoController.php:187-230`). `DestinationChannels.tsx` até declara `flash` no tipo e nunca lê.
- Problema: com deps por mensagem, duas ações seguidas com o mesmo texto ("Vídeo #12 pausado" duas vezes) só toastam uma; com deps `[]`, um flash que chega sem remount some. E o operador que apaga um canal-destino ou executa "Limpar vídeos antigos" (ação lenta, via sidecar) não recebe confirmação alguma.
- Por que importa: é a única forma de o painel dizer "deu certo / deu erro" para ações destrutivas.
- Refatoração: usar o canal de flash nativo do Inertia 3, que é **por resposta** (não fica mesclado em `props` como o `flash` compartilhado em `HandleInertiaRequests.php:46-49` — esse persiste entre partial reloads e re-toastaria a cada poll de 20 s). Servidor: `Inertia::flash('toast', ['type' => 'success', 'message' => ...])`. Cliente: **um** `router.on('flash', ...)` em `app.tsx`, tipado via `InertiaConfig.flashDataType`. Apagar os quatro `useEffect`, os dois `onSuccess` e os quatro comentários `eslint-disable` mortos. Enquanto o servidor não migrar, o mínimo é um `hooks/use-flash-toast.ts` único chamado no `AppShell`.
- Esforço: M · Risco: médio (se sobrar um dos efeitos antigos, toast duplica — remover todos na mesma mudança)

### 3. **Tipar as props compartilhadas uma vez, via augmentação do Inertia**
- Onde: `auth: { user: { name: string; email: string } | null }` redeclarado em `pages/Settings.tsx`, `pages/Documentation.tsx`, `pages/ProcessVideo.tsx`, `pages/TranscricaoLocal.tsx`, `pages/SourceVideos.tsx`, `pages/SourceChannels.tsx`, `pages/DestinationChannels.tsx`, `types/dashboard.ts`, `layouts/app-shell.tsx`, `components/app-sidebar.tsx`, `components/nav-user.tsx`. `flash` idem em 5 lugares.
- Problema: 11 cópias de um tipo que o servidor define em um único lugar (`HandleInertiaRequests.php:40-49`). Mudar o shape do usuário exige tocar 11 arquivos.
- Refatoração: criar `types/inertia.d.ts` com `declare module '@inertiajs/core' { interface InertiaConfig { sharedPageProps: { auth: { user: AuthUser | null } }; flashDataType: { toast?: {...} } } }`; exportar `AuthUser` de `types/auth.ts`; remover `auth`/`flash` de todos os `PageProps` locais e de `DashboardPageProps`. Manter os `PageProps` de página como `type` (não `interface`) — `usePage<T extends PageProps>` exige index signature implícita.
- Esforço: P/M · Risco: baixo

### 4. **Decompor `pages/SourceVideos.tsx` (476 linhas) e corrigir o "selecionar todos"**
- Onde: `PurgeOldDialog`; barra de filtros; barra de ações em massa; tabela de 11 colunas; paginação; tipos locais; seleção.
- Problema: uma página com diálogo de purge, filtros por query string, seleção, tabela e paginação no mesmo componente. Bug concreto: `toggleAll` seleciona **todos** os `videos.data`, inclusive linhas que não renderizam checkbox (só mostra se `canDelete ?? hasLocalFile`); o texto de confirmação infla a contagem e o operador não consegue desmarcar essas linhas individualmente. Compare com `active-window-table.tsx` (`deletableIds`), que faz certo. Além disso `canDelete?: boolean` é opcional com fallback `?? hasLocalFile`, mas o controller sempre envia (`SourceVideoController.php:175`).
- Por que importa: é a página de limpeza de disco — a que mais toca ação destrutiva do painel.
- Refatoração: `components/purge-old-dialog.tsx`, `components/source-video-filters.tsx`, `components/source-video-table.tsx`, `components/pagination.tsx` (reutilizável); `types/source-videos.ts` com `SourceVideoRow` (`canDelete` obrigatório). Seleção via `useSelection` com `selectableIds` (item 5).
- Esforço: M · Risco: baixo

### 5. **`useSelection` triplicado**
- Onde: `components/active-window-table.tsx` e `components/clip-queue-tabs.tsx` (idênticos, linha a linha); `pages/SourceVideos.tsx` (reimplementado inline).
- Problema: três cópias de um hook de 12 linhas; `number[]` com `includes` em toda linha da tabela.
- Refatoração: `hooks/use-selection.ts` com `Set<number>`, `isSelected(id)`, `toggle`, `toggleAll(selectableIds)`, `clear`, `count`. Substituir nos três lugares.
- Esforço: P · Risco: baixo

### 6. **Mutações sem estado de carregamento nem tratamento de erro**
- Onde: `components/active-window-table.tsx` (pausar/retomar/priorizar), `pages/DestinationChannels.tsx` e `pages/SourceChannels.tsx` (`Switch` → `router.put`; `router.delete` sem `preserveScroll`), `pages/SourceVideos.tsx` (`purge-old`: só `onSuccess` fecha o diálogo; em erro ele fica aberto e mudo, e nada desabilita durante a requisição — a purga passa pelo sidecar e demora), `components/confirm-button.tsx` (sem `pending`, botão de confirmação sempre `default` mesmo em ação destrutiva, título fixo "Tem certeza?").
- Problema: nenhuma ação fora de `useForm` mostra que está rodando; clique duplo dispara duas vezes; falhas do sidecar só aparecem se o flash for exibido (item 2).
- Refatoração: `hooks/use-inertia-action.ts` → `{ run(url, data?, opts?), pending }` embrulhando `router.visit` com `onStart/onFinish`; `ConfirmButton` ganha `pending`, `confirmLabel`, `title?` e aplica `variant="destructive"` no `AlertDialogAction` quando o gatilho é destrutivo; `Switch` desabilitado enquanto `pending`.
- Esforço: M · Risco: baixo

### 7. **"Baixar .srt" clicável para job não concluído**
- Onde: `pages/TranscricaoLocal.tsx` — `<Button asChild size="sm" disabled={job.status !== 'done'}><a href=...>`.
- Problema: `disabled` não existe em `<a>`; com `asChild` o `Slot` repassa a prop para a âncora, que continua navegável (e as classes `disabled:` do `ui/button.tsx` não disparam). Usuário clica em job `pending` e cai no download de um arquivo inexistente.
- Refatoração: renderizar `<Button disabled>` sem `asChild` quando não for `done`; ou `aria-disabled` + `pointer-events-none` + `tabIndex={-1}`. No mesmo arquivo, `Job` é snake_case porque `TranscriptionController.php:20` envia o model cru (`$guarded = []` em `app/Models/TranscriptionJob.php:9`) — mapear para DTO camelCase no controller e mover o tipo para `types/transcription.ts`.
- Esforço: P · Risco: baixo

## Média

### 8. **Polling manual em dois lugares; Inertia 3 já tem `usePoll`**
- Onde: `components/active-window-table.tsx` (20 s, deps `[videos.length]`) e `pages/TranscricaoLocal.tsx` (3 s, deps `[jobs]` — o array muda a cada resposta, então o intervalo é destruído e recriado a cada poll).
- Refatoração: `usePoll(20000, { only: ['activeWindow', 'overview', 'quota'] })` e `usePoll(3000, { only: ['jobs'] }, { autoStart: hasPendingJob })`. Ganha pausa automática com aba oculta.
- Esforço: P · Risco: baixo

### 9. **`VideoTable` espelha props em estado** — *é o `react/set-state-in-effect` que o oxlint aponta (rebaixado a aviso até isto ser feito)*
- Onde: `components/active-window-table.tsx` — `useState(videos)` + `useEffect(() => setItems(videos), [videos])`.
- Problema: padrão "state mirror": cada poll renderiza um frame com a lista antiga e depois outro com a nova; um reload de 20 s no meio de um arrasto descarta a ordem em andamento. O `SortableContext` e o `handleDragEnd` dependem desse `items`.
- Refatoração: derivar de `videos`; manter só `pendingOrder: number[] | null` otimista, setado no `handleDragEnd` e limpo no `onFinish` do `persistReorder`. Alternativa: `useOptimistic` (React 19). Ao concluir, voltar `react/set-state-in-effect` para `error` em `.oxlintrc.json`.
- Esforço: M · Risco: médio (dnd)

### 10. **`Tabs key={defaultTab}` remonta as abas e perde a aba escolhida**
- Onde: `components/active-window-table.tsx`.
- Problema: quando `processing.length` cruza zero durante o poll, a `key` muda, o `Tabs` remonta e a aba volta para o default enquanto o operador está lendo a lista ociosa.
- Refatoração: `const [tab, setTab] = useState(defaultTab)` controlado, sem `key`.
- Esforço: P · Risco: baixo

### 11. **Mapas de status/label/cor duplicados entre cliente e servidor, indexados por texto de exibição**
- Onde: `components/active-window-table.tsx` (`STATUS_LABEL`) é cópia de `SourceVideoController.php:19-29` (que já vai para o cliente como `statusOptions` e `statusLabel` por linha). `pages/SourceVideos.tsx` (`STATUS_BADGE`, `USO_BADGE`) indexa cor **pela string em português** (`'Falhou — pode apagar'`) e precisa de `as never` para compilar. `status: string` em `types/dashboard.ts` e `SourceVideos.tsx`. `pages/DestinationChannels.tsx` (`OAUTH_LABEL`) e ternários aninhados, `components/video-summary-cards.tsx`.
- Problema: mudar o texto de "uso" no controller apaga a cor do badge em silêncio; `as never` esconde que o índice pode dar `undefined`.
- Refatoração: `types/pipeline.ts` com `SourceVideoStatus` (union) e `OAuthStatus`; `lib/status.ts` com `Record<SourceVideoStatus, { label, badge: BadgeVariant }>` onde `BadgeVariant = VariantProps<typeof badgeVariants>['variant']`; servidor envia `usoTone: 'danger' | 'ok' | 'neutral'` em vez de o cliente inferir pela frase.
- Esforço: M · Risco: baixo

### 12. **Constantes da janela de download hardcoded no cliente enquanto o servidor já as envia**
- Onde: `components/overview-cards.tsx` (`WINDOW_CURTO = 6`, `WINDOW_LONGO = 4`; recomputa "processando" com lista de status fixa, embora `ActiveWindowVideo.processing` venha calculado em `DashboardController.php:56,84`); `components/active-window-table.tsx` reconta curto/longo. Enquanto isso `SourceVideoController::downloadWindowMetrics` já manda `curtoCap/longoCap/processingCount` (`components/video-summary-cards.tsx`).
- Problema: duas fontes de verdade para o teto 6+4 (também citado em `Docs/SISTEMA-PAINEL.md`); se o Python mudar o teto, o Dashboard mente.
- Refatoração: `DashboardController` envia `downloadWindow` no mesmo shape; `OverviewCards` consome; usar `v.processing`; apagar as constantes.
- Esforço: P/M · Risco: baixo

### 13. **~30 URLs literais `/painel/...`, `ziggy-js` instalado e `@routes` injetado sem uso**
- Onde: strings em `active-window-table.tsx`, `clip-queue-tabs.tsx`, `SourceVideos.tsx`, `DestinationChannels.tsx`, `SourceChannels.tsx`, `niche-combobox.tsx`, `nav-user.tsx`, `app-sidebar.tsx`, `TranscricaoLocal.tsx`, `ProcessVideo.tsx`, `Settings.tsx`, `login-form.tsx`. `resources/views/app.blade.php` tem `@routes`, mas `route(` não aparece em nenhum `.tsx`. Rotas sem `->name()`: `routes/web.php:58-60,65,68-70,73,76`.
- Problema: `@routes` embute a tabela inteira de rotas em todo HTML (incluindo `/internal/pipeline-event` e `/telegramcanal`) para nada; renomear uma rota exige grep em 12 arquivos.
- Refatoração (decisão): (a) nomear todas as rotas e adotar `route()` com tipos do Ziggy; ou (b) remover `ziggy-js` + `tightenco/ziggy` + `@routes` e centralizar em `lib/routes.ts` (`routes.videos.deleteFile(id)`). Recomendação: (b) — menos dependência, tipagem trivial. Inclui unificar `SourceChannels.tsx` (tab via `router.get` sem `preserveScroll`/`replace`) com `applyFilters` de `SourceVideos.tsx` num `hooks/use-query-filters.ts`.
- Esforço: M · Risco: baixo

### 14. **`clip-queue-tabs.tsx`: duas tabelas 80 % iguais e quatro barras de ação em massa iguais**
- Onde: `PendingTable` vs `QueuedTable` (células idênticas); barras em `clip-queue-tabs.tsx` (2×), `active-window-table.tsx`, `SourceVideos.tsx`.
- Problema: uma coluna nova em clips = editar dois blocos de 60 linhas. `@tanstack/react-table` está no `package.json` sem uso.
- Refatoração: primeiro o barato — `components/clip-row-cells.tsx` (com `showPosition`/`showApprovedAt`) e `components/bulk-actions-bar.tsx` (contagem, marcar todos, `children`). Só adotar react-table se surgir ordenação/filtro por coluna; senão, remover a dependência.
- Esforço: M · Risco: baixo

### 15. **`ChannelDialog` em `DestinationChannels.tsx`: um `useForm` por linha, valores iniciais congelados, upload encadeado sem feedback**
- Onde: `pages/DestinationChannels.tsx` — instância por linha; `useForm`; `reset()`; upload da marca d'água; `channel!.`; template padrão hardcoded.
- Problema: cada linha monta um diálogo fechado com seu próprio `useForm`; depois de um `router.put` pelo `Switch` as props da linha mudam mas o form guarda os valores iniciais do mount — `reset()` volta ao estado antigo. O upload é um segundo `router.post` disparado dentro do `onSuccess`, sem `onError`, sem `forceFormData`, sem toast. `isEdit` como boolean não estreita `channel`, daí os `!`.
- Refatoração: estado `editing: DestinationChannel | null` na página, **um** `ChannelDialog` com `key={editing?.id ?? 'new'}` montado só quando aberto; separar `CreateChannelForm`/`EditChannelForm` (ou estreitar com `channel ? … : …`); enviar marca d'água no mesmo submit multipart ou com `onError`; o template padrão vem do servidor.
- Esforço: M · Risco: médio

### 16. **Copiar para a área de transferência: três implementações e duas células clicáveis inacessíveis**
- Onde: `pages/SourceVideos.tsx`, `pages/DestinationChannels.tsx` (`CopyCommand` e inline); células `<TableCell onClick>` nos dois.
- Problema: célula clicável não recebe foco, não responde a Enter/Espaço e não tem `aria-label`; erro de clipboard engolido com `.catch(() => {})` em todos.
- Refatoração: `lib/clipboard.ts` (`copyText(text): Promise<boolean>`) + `components/copy-button.tsx` (botão `ghost`/`icon-xs` com estado "Copiado!", `aria-label`).
- Esforço: P · Risco: baixo

### 17. **Acessibilidade de formulários e controles**
- Onde: `Switch` sem rótulo em `DestinationChannels.tsx`, `SourceChannels.tsx`, `SourceVideos.tsx` (texto ao lado sem `htmlFor`/`aria-label`); checkboxes sem rótulo em `SourceVideos.tsx`, `clip-queue-tabs.tsx`, `active-window-table.tsx`; erro de campo como `<p className="text-sm text-destructive">` em `DestinationChannels.tsx`, `SourceChannels.tsx`, `Settings.tsx`, `login-form.tsx` enquanto `ui/field.tsx` exporta `FieldError` e `FieldDescription`.
- Refatoração: `aria-label` nos toggles/checkboxes; trocar os `<p>` por `FieldError`/`FieldDescription` (ganha `aria-invalid`/`aria-describedby` do shadcn). O oxlint com `jsx-a11y` já aponta parte disto.
- Esforço: P/M · Risco: baixo

### 18. **Datas em UTC no diálogo de purga**
- Onde: `pages/SourceVideos.tsx` — `new Date(...).toISOString().slice(0, 10)` (3 pontos).
- Problema: `toISOString` é UTC; entre 21h e 0h no horário de Brasília "hoje" e "há N dias" caem um dia à frente do calendário local, e o `max` do input também.
- Refatoração: `lib/dates.ts` com `toLocalIsoDate(d)` e `daysAgo(n)`; usar nos três pontos. Nenhuma outra formatação de data/duração/bytes existe no cliente hoje (tudo vem formatado do controller) — manter assim e concentrar o pouco que há em `lib/`.
- Esforço: P · Risco: baixo

### 19. **Layout persistente do Inertia em vez de `<AppShell>` inline em cada página**
- Onde: todas as 8 páginas; `layouts/app-shell.tsx` (`withToaster`); `Documentation.tsx` (`withToaster={false}`).
- Problema: sidebar, header e `Toaster` remontam a cada navegação (o cookie `sidebar_state` restaura o colapso, mas o DOM é reconstruído e toasts em voo somem). `Docs/SISTEMA-PAINEL.md` ainda descreve "cada página compõe `AppSidebar` + `SiteHeader`" e `page-header.tsx` — está desatualizado, o `AppShell` já centraliza.
- Refatoração: `createInertiaApp({ layout: (name, page) => … })` ou `Page.layout = (page) => <AppShell …>{page}</AppShell>`; título/descrição/ações via `layoutProps`; `Toaster` sobe para `app.tsx` ao lado do `TooltipProvider` e `withToaster` some. Atualizar `SISTEMA-PAINEL.md`.
- Esforço: M · Risco: médio

### 20. **Ferramental** — *parcialmente FEITO em 25/08/2026: `typecheck`, `lint` (oxlint), `format` (Prettier) e CI existem; falta Vitest e apertar o `tsconfig`*
- Onde: comentários `eslint-disable-next-line react-hooks/exhaustive-deps` sem efeito (o oxlint usa `oxlint-disable`) em `Dashboard.tsx`, `Settings.tsx`, `ProcessVideo.tsx`, `TranscricaoLocal.tsx`; `tsconfig.json` sem `noUnusedLocals`, `noUnusedParameters`, `noUncheckedIndexedAccess`, `verbatimModuleSyntax`; `vite.config.js` fora do `include`. `Docs/SISTEMA-PAINEL.md` já registra "nenhum teste de frontend".
- Refatoração: `test` (Vitest + Testing Library — começar por `use-selection`, `lib/dates`, `lib/status`). `noUncheckedIndexedAccess` vai apontar exatamente o hack de `SourceVideos.tsx` (item 11). Adicionar `vite.config.js` a um `tsconfig.node.json`.
- Esforço: M · Risco: baixo

### 21. **Dependências e arquivos mortos**
- Onde: `zod`, `recharts`, `@tanstack/react-table`, `ziggy-js`, `vaul` (`package.json`) — zero imports fora de `ui/`; 10 arquivos shadcn sem importador (`ui/breadcrumb`, `chart`, `collapsible`, `drawer`, `input-group`, `scroll-area`, `sheet`, `skeleton`, `toggle`, `toggle-group`); `components/page-header.tsx` sem importador; `NavItem.external` (`components/app-sidebar.tsx`) nunca setado, ramo morto.
- Problema: quem chega lê "stack com zod/recharts/react-table" e procura onde está — não está. `npm audit`/upgrades cuidando de pacotes que ninguém usa.
- Refatoração: remover deps, arquivos e ramo; se `zod` for ficar, usá-lo de verdade para validar `usePage().props` em dev (uma `parsePageProps(schema)` em `lib/`) — senão remover.
- Esforço: P · Risco: baixo

## Baixa

### 22. **`Documentation.tsx`: conteúdo estático como JSX repetido, duplicando textos das páginas**
- Onde: `pages/Documentation.tsx` (cinco `AccordionItem` com a mesma estrutura); frases idênticas às de `SourceVideos.tsx` e `DestinationChannels.tsx`.
- Refatoração: array `DOCS: { value, title, intro, items }[]` mapeado, ou Markdown (o plugin typography já está carregado em `app.css`); `lib/copy.ts` para frases compartilhadas entre página e documentação.
- Esforço: P · Risco: baixo

### 23. **Item ativo da sidebar via `window.location`**
- Onde: `components/app-sidebar.tsx`.
- Refatoração: `usePage().url` (reativo e seguro em SSR); vira necessário no item 19, quando a sidebar deixar de remontar.
- Esforço: P · Risco: baixo

### 24. **Bootstrap `app.tsx` sem `title` nem `progress`**
- Onde: `app.tsx`. `Head title="Vídeos"` mostra só "Vídeos" na aba.
- Refatoração: `title: (t) => (t ? `${t} — Canal de Cortes` : 'Canal de Cortes')` e `progress: { color: … }`; `Toaster` aqui (item 19).
- Esforço: P · Risco: baixo

### 25. **CSS: fonte baixada e nunca usada; `@source` irrelevante**
- Onde: `resources/css/app.css` define `--font-sans: 'Instrument Sans'` e depois sobrescreve com `'Geist Variable'` (vence); `vite.config.js` baixa Instrument Sans via Bunny e `app.blade.php` injeta `@fonts` — peso morto. `app.css` manda o Tailwind varrer views de paginação do Laravel e o cache de views compiladas, que um app só-Inertia não usa.
- Refatoração: escolher uma fonte; remover `bunny(...)`, `@fonts` e os dois `@source`.
- Esforço: P · Risco: baixo

### 26. **Espaçamentos duplicados com o `AppShell`**
- Onde: `components/clip-queue-tabs.tsx` (`px-4 lg:px-6` por cima do mesmo padding de `layouts/app-shell.tsx` — as abas de clips ficam mais recuadas que o resto do Dashboard); `components/video-summary-cards.tsx` (`mb-6` por cima do `gap` do shell).
- Refatoração: remover o wrapper e o `mb-6`.
- Esforço: P · Risco: baixo

### 27. **Cards de métrica duplicados**
- Onde: `components/overview-cards.tsx` e `components/video-summary-cards.tsx` (mesma className de 150 caracteres para o gradiente); card de cota vs. card de disco (descrição + badge + número grande + `Progress` com cor por tom).
- Refatoração: `components/metric-card.tsx` (`label`, `badge`, `value`, `suffix`, `progress?`, `tone`) e `MetricCardGrid`.
- Esforço: M · Risco: baixo

### 28. **Detalhes de tipagem e legibilidade**
- Onde: `components/niche-combobox.tsx` — regex com caracteres combinantes literais invisíveis; `React.FormEvent`/`React.ReactNode` pelo namespace global UMD, sem import, em várias páginas — enquanto `app-shell.tsx`, `site-header.tsx`, `page-header.tsx` fazem `import type { ReactNode }`; `clip-queue-tabs.tsx` e `active-window-table.tsx` importam de `@inertiajs/core`, que não está em `package.json` (dependência transitiva).
- Refatoração: `/[̀-ͯ]/g`; padronizar `import type { FormEvent, ReactNode } from 'react'` (`verbatimModuleSyntax` do item 20 força); declarar `@inertiajs/core` explicitamente já que os tipos são importados dele.
- Esforço: P · Risco: baixo

### 29. **Resíduos de UI**
- Onde: `pages/Settings.tsx` — abas "Perfil" e "Redes" renderizam "em construção" em produção; `pages/TranscricaoLocal.tsx` é o único nome de página em português (`Inertia::render('TranscricaoLocal')`) entre `SourceVideos`, `ProcessVideo`, etc.; `components/active-window-table.tsx` botão desabilitado com `title` como único meio de explicar (tooltip do shadcn está disponível, `TooltipProvider` já em `app.tsx`).
- Refatoração: esconder abas até existirem; renomear página + controller; `Tooltip` no botão desabilitado.
- Esforço: P · Risco: baixo

### 30. **`NicheCombobox`: cinco `useState`, flag `creating` manual e erros de validação descartados**
- Onde: `components/niche-combobox.tsx` (estado e `router.post('/painel/niches')` sem `onError`).
- Problema: se `NicheController::store` rejeitar (slug duplicado, por exemplo), o diálogo fica aberto sem dizer por quê; `creating` reimplementa o `processing` do `useForm`.
- Refatoração: `useForm({ label, slug })` — `processing`, `errors` e `reset()` de graça; `FieldError` nos dois campos (item 17); `slugify` para `lib/strings.ts`.
- Esforço: P · Risco: baixo

## Quick wins React (< 1 h cada)

1. **`usePoll`** no lugar dos dois `setInterval` (`active-window-table.tsx`, `TranscricaoLocal.tsx`) (item 8).
2. **`hooks/use-selection.ts`** e apagar as três cópias (item 5) — inclui corrigir `toggleAll` de `SourceVideos.tsx` para usar só ids selecionáveis.
3. **"Baixar .srt"** deixar de ser clicável em job não concluído (`TranscricaoLocal.tsx`) (item 7).
4. **Apagar código morto**: `components/page-header.tsx`, `NavItem.external` + ramo em `app-sidebar.tsx`, os 10 arquivos de `ui/` sem importador (item 21).
5. **Espaçamento**: remover o wrapper `px-4 lg:px-6` de `clip-queue-tabs.tsx` e o `mb-6` de `video-summary-cards.tsx` (item 26).
6. **`app.tsx`**: `title` callback + `progress` + mover o `Toaster` para lá e remover `withToaster` (itens 19/24).
7. **`lib/dates.ts`** com data local para o `PurgeOldDialog` (`SourceVideos.tsx`) (item 18).
8. **`lib/inertia.ts`** com o `postAction` único e apagar as duas cópias (item 1).
