---
phase: quick-1
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - painel/database/migrations/2026_07_30_000000_create_transcription_jobs_table.php
  - painel/app/Models/TranscriptionJob.php
  - painel/app/Services/ClipProcessorClient.php
  - clip-processor/Dockerfile
  - clip-processor/src/transcription_job.py
  - clip-processor/src/internal_api.py
  - clip-processor/tests/test_transcription_job.py
  - painel/app/Http/Controllers/TranscriptionController.php
  - painel/routes/web.php
  - painel/resources/js/pages/TranscricaoLocal.tsx
  - painel/resources/js/components/app-sidebar.tsx
  - painel/resources/js/components/ui/progress.tsx
autonomous: true
requirements: [QUICK-1]
must_haves:
  truths:
    - "Usuário cola uma URL do YouTube no painel e aperta um botão para iniciar a transcrição local"
    - "O processamento (download de áudio + whisper-cpp) roda em background no clip-processor sem travar a requisição HTTP"
    - "O progresso aparece como uma Progress bar (shadcn) no painel e sobrevive a reload/saída da página (persistido no MySQL, não em memória)"
    - "Quando a transcrição termina, o botão de download do .srt fica habilitado e baixa o arquivo correto"
    - "Nenhum job de transcrição local entra na fila de aprovação de clips nem é enviado ao YouTube"
  artifacts:
    - path: "painel/database/migrations/2026_07_30_000000_create_transcription_jobs_table.php"
      provides: "Tabela transcription_jobs (id, youtube_url, status, progress_percent, srt_path, error_message, timestamps)"
    - path: "clip-processor/src/transcription_job.py"
      provides: "start_transcription_job(url) — cria job no banco e dispara thread de background que baixa áudio, roda whisper-cpp e grava o .srt"
    - path: "clip-processor/src/internal_api.py"
      provides: "Endpoint POST /internal/transcribe protegido por X-Internal-Token, chama start_transcription_job"
    - path: "painel/app/Http/Controllers/TranscriptionController.php"
      provides: "index() renderiza a página com jobs recentes; store() chama ClipProcessorClient::transcribe(); download() serve o .srt via disco clips-videos"
    - path: "painel/resources/js/pages/TranscricaoLocal.tsx"
      provides: "Formulário de URL + lista de jobs com Progress bar (shadcn) e botão de download, com polling via router.reload"
  key_links:
    - from: "painel/resources/js/pages/TranscricaoLocal.tsx"
      to: "/painel/transcricoes"
      via: "useForm().post + router.reload({only:['jobs']}) em polling periódico"
      pattern: "post\\('/painel/transcricoes'"
    - from: "painel/app/Services/ClipProcessorClient.php"
      to: "clip-processor:8090/internal/transcribe"
      via: "Http::post com header X-Internal-Token"
      pattern: "internal/transcribe"
    - from: "clip-processor/src/internal_api.py"
      to: "clip-processor/src/transcription_job.py"
      via: "start_transcription_job(url) chamado pela rota Flask"
      pattern: "start_transcription_job"
    - from: "clip-processor/src/transcription_job.py"
      to: "transcription_jobs (MySQL)"
      via: "INSERT/UPDATE via pymysql, mesma tabela que TranscriptionController lê"
      pattern: "transcription_jobs"
---

<objective>
Adicionar uma sessão "Transcrição Local" no painel: o usuário cola uma URL do YouTube e aperta um
botão; o `clip-processor` baixa o áudio, roda `whisper-cpp` localmente (sem custo, sem YouTube,
sem entrar no fluxo de aprovação de clips) em background, e persiste o progresso no MySQL
compartilhado (`transcription_jobs`). O painel mostra uma Progress bar (shadcn) que sobrevive a
reload da página, e libera um botão de download do `.srt` quando o job termina.

Purpose: dar ao operador uma ferramenta rápida de transcrição para vídeos avulsos (ex. conferir
uma fala, gerar legenda de um clipe fora do pipeline automático) sem consumir cota do YouTube nem
tocar na fila de clips.

Output: tabela `transcription_jobs`, endpoint interno `/internal/transcribe` no clip-processor com
worker em thread, whisper-cpp instalado na imagem do clip-processor, página `TranscricaoLocal.tsx`
no painel com formulário + lista de jobs + Progress bar + download.
</objective>

<execution_context>
@/Users/alessandrobm1/.claude/get-shit-done/workflows/execute-plan.md
@/Users/alessandrobm1/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@CLAUDE.md

<interfaces>
<!-- Contratos existentes que os executores devem seguir exatamente — nada de explorar o codebase. -->

Padrão de rota interna Flask (clip-processor/src/internal_api.py), auth por header:
```python
INTERNAL_TOKEN = os.environ.get('CLIP_PROCESSOR_INTERNAL_TOKEN')

def _check_auth() -> bool:
    return bool(INTERNAL_TOKEN) and request.headers.get('X-Internal-Token') == INTERNAL_TOKEN

@app.post('/internal/algum-endpoint')
def _route_algum_endpoint():
    if not _check_auth():
        return jsonify(error='unauthorized'), 401
    payload = request.get_json(silent=True) or {}
    ...
    return jsonify(result), 200
```

Padrão de acesso a banco (clip-processor/src/db.py):
```python
from src.db import get_db_connection
conn = get_db_connection()  # pymysql, DictCursor, autocommit=False — quem chama fecha a conexão
with conn.cursor() as cur:
    cur.execute('UPDATE ... WHERE ...', (params,))
conn.commit()
conn.close()
```

Padrão VIDEOS_DIR (clip-processor/src/transcriber.py):
```python
VIDEOS_DIR = '/app/videos'  # constante módulo-level, patchável nos testes
```

Padrão `ClipProcessorClient` (painel/app/Services/ClipProcessorClient.php) — cada método chama
`Http::timeout(N)->withHeader('X-Internal-Token', (string) $this->token)->post($this->baseUrl.'/internal/...', [...])`
e lança `RuntimeException` em erro. `baseUrl`/`token` vêm de `config('services.clip_processor.*')`
(já configurado em `painel/config/services.php`, nenhuma mudança necessária ali).

Disco `clips-videos` (painel/config/filesystems.php) já aponta para
`storage_path('app/clips-videos')`, que é o MESMO host path `./canaldecortes/videos` montado
`rw` em `clip-processor:/app/videos` e `ro` em `php:/var/www/html/painel/storage/app/clips-videos`
(ver `wordpress/docker-compose.yml`, serviços `clip-processor` e `php`). Ou seja: um arquivo escrito
pelo Python em `/app/videos/transcripts/{job_id}.srt` aparece automaticamente para o Laravel em
`Storage::disk('clips-videos')->path("transcripts/{job_id}.srt")` — sem endpoint extra de sync.

Padrão de página Inertia + shadcn (painel/resources/js/pages/ProcessVideo.tsx): usa
`AppSidebar` + `SiteHeader` + `SidebarProvider`/`SidebarInset`, `useForm` do Inertia, `Toaster`
(sonner) para flash messages, `Card`/`CardContent`, `Field`/`FieldLabel`.

Nav lateral (painel/resources/js/components/app-sidebar.tsx) é um array de
`{ title: string; url: string; icon: LucideIcon }` — adicionar uma entrada nesse array.

Migration mais recente como referência de estilo (painel/database/migrations/2026_07_14_010214_create_niches_table.php):
`Schema::create` com `Blueprint`, comentário explicando o "porquê" da tabela.
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Contrato de dados — migration + model Laravel + método ClipProcessorClient::transcribe()</name>
  <files>painel/database/migrations/2026_07_30_000000_create_transcription_jobs_table.php, painel/app/Models/TranscriptionJob.php, painel/app/Services/ClipProcessorClient.php</files>
  <action>
    1. Criar migration `create_transcription_jobs_table`:
       ```php
       Schema::create('transcription_jobs', function (Blueprint $table) {
           $table->id();
           $table->string('youtube_url', 500);
           $table->enum('status', ['pending', 'downloading', 'transcribing', 'done', 'failed'])
               ->default('pending');
           $table->unsignedTinyInteger('progress_percent')->default(0);
           $table->string('srt_path')->nullable();
           $table->text('error_message')->nullable();
           $table->timestamps();
       });
       ```
       Rodar `php artisan migrate` dentro do container `php` (`docker compose exec php php artisan migrate
       --path=... ` ou equivalente já usado no projeto) para aplicar em `clips_automation`.
    2. Criar `App\Models\TranscriptionJob` (Eloquent simples, `$fillable` ou `$guarded = []`, sem
       relations — é uma tabela isolada, não referencia `source_videos`/`generated_clips`).
    3. Adicionar método `transcribe(string $url): array` em `ClipProcessorClient`, seguindo
       exatamente o padrão dos outros métodos da classe (ver `<interfaces>`):
       ```php
       public function transcribe(string $url): array
       {
           $response = Http::timeout(15)
               ->withHeader('X-Internal-Token', (string) $this->token)
               ->post($this->baseUrl.'/internal/transcribe', ['url' => $url]);

           if (! $response->successful()) {
               throw new RuntimeException('Erro ao iniciar transcrição: HTTP '.$response->status());
           }

           return ['job_id' => (int) $response->json('job_id', 0)];
       }
       ```
       Timeout curto (15s) porque o endpoint só cria o job e dispara a thread — não espera o
       whisper terminar.
  </action>
  <verify>
    <automated>cd painel && php artisan migrate:status | grep transcription_jobs</automated>
  </verify>
  <done>Tabela `transcription_jobs` existe em `clips_automation`, model Eloquent criado, e
  `ClipProcessorClient::transcribe()` compila (nenhum erro de sintaxe PHP:
  `php -l app/Services/ClipProcessorClient.php`).</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Worker de transcrição local no clip-processor (whisper-cpp + thread + endpoint)</name>
  <files>clip-processor/Dockerfile, clip-processor/src/transcription_job.py, clip-processor/src/internal_api.py, clip-processor/tests/test_transcription_job.py</files>
  <behavior>
    - `create_transcription_job(conn, youtube_url)` insere linha com status='pending',
      progress_percent=0 e retorna o `id` gerado (mockar `conn.cursor()` e `lastrowid`).
    - `update_job(conn, job_id, status=None, progress_percent=None, srt_path=None, error_message=None)`
      monta um UPDATE só com os campos passados (não sobrescrever colunas não informadas).
    - `process_transcription_job(job_id)` — caminho feliz: abre conexão, marca
      status='downloading'/progress=10, chama `_download_audio` (mockado), marca
      status='transcribing'/progress=50, chama `_run_whisper` (mockado), marca
      status='done'/progress=100/srt_path=caminho final.
    - `process_transcription_job(job_id)` — caminho de erro: se `_download_audio` ou
      `_run_whisper` lançar exceção, marca status='failed' com `error_message` preenchido e
      NÃO propaga a exceção (thread de background não pode matar o processo).
    - `start_transcription_job(youtube_url)` chama `create_transcription_job`, dispara
      `threading.Thread(target=process_transcription_job, args=(job_id,), daemon=True).start()`
      e retorna o `job_id` imediatamente (mockar `threading.Thread` para não rodar de verdade
      no teste).
    - `POST /internal/transcribe` sem header `X-Internal-Token` retorna 401; com header correto
      e `url` no body, retorna 200 com `{"job_id": N}` (mockar `start_transcription_job`).
    - `POST /internal/transcribe` sem `url` no body retorna 400.
  </behavior>
  <action>
    1. Escrever `clip-processor/tests/test_transcription_job.py` cobrindo o `<behavior>` acima,
       seguindo o padrão de mocks de `tests/test_internal_api.py` e `tests/test_transcriber.py`
       (fixtures com `MagicMock`, `patch('src.transcription_job....')`). Rodar e confirmar RED
       (`ModuleNotFoundError` ou `AttributeError` esperado).
    2. Implementar `clip-processor/src/transcription_job.py`:
       - `VIDEOS_DIR = '/app/videos'` (mesma constante padrão do projeto)
       - `TRANSCRIPTS_DIR = os.path.join(VIDEOS_DIR, 'transcripts')`
       - `WHISPER_BIN = os.environ.get('WHISPER_CPP_BIN', '/opt/whisper.cpp/build/bin/whisper-cli')`
       - `WHISPER_MODEL = os.environ.get('WHISPER_MODEL_PATH', '/opt/whisper.cpp/models/ggml-small.bin')`
       - `create_transcription_job(conn, youtube_url) -> int`: INSERT em `transcription_jobs`
         (`youtube_url`, `status='pending'`, `progress_percent=0`, `created_at=NOW()`,
         `updated_at=NOW()`), commit, retorna `cur.lastrowid`.
       - `update_job(conn, job_id, **fields)`: monta SET dinâmico só com os campos não-None
         passados + sempre `updated_at=NOW()`, executa UPDATE, commit.
       - `_download_audio(job_id, youtube_url) -> str`: `subprocess.run(['yt-dlp', '-x',
         '--audio-format', 'wav', '-o', f'{VIDEOS_DIR}/transcripts/{job_id}_audio.%(ext)s',
         youtube_url], check=True, capture_output=True, timeout=600)`, retorna o caminho do wav
         gerado (`f'{VIDEOS_DIR}/transcripts/{job_id}_audio.wav'`). Criar `TRANSCRIPTS_DIR` com
         `os.makedirs(..., exist_ok=True)` antes de baixar.
       - `_run_whisper(job_id, audio_path) -> str`: `subprocess.run([WHISPER_BIN, '-m',
         WHISPER_MODEL, '-f', audio_path, '-l', 'pt', '-osrt', '-of',
         f'{TRANSCRIPTS_DIR}/{job_id}'], check=True, capture_output=True, timeout=1800)`. O
         whisper-cpp com `-osrt -of <prefix>` gera `<prefix>.srt`. Retorna
         `f'{TRANSCRIPTS_DIR}/{job_id}.srt'`.

         LIMITAÇÃO DOCUMENTADA: whisper-cpp não expõe progresso incremental fácil de parsear via
         stdout/stderr entre versões — usar milestones grosseiros de progresso (não % real do
         whisper), conforme instrução do usuário.
       - `process_transcription_job(job_id)`: abre `get_db_connection()`, try/except amplo:
         `update_job(conn, job_id, status='downloading', progress_percent=10)` →
         `audio_path = _download_audio(job_id, youtube_url)` (buscar `youtube_url` com um SELECT
         antes) → `update_job(conn, job_id, status='transcribing', progress_percent=50)` →
         `srt_path = _run_whisper(job_id, audio_path)` → `update_job(conn, job_id, status='done',
         progress_percent=100, srt_path=srt_path)`. Limpar o `.wav` temporário no `finally` (não
         falhar o job se o remove der erro). Em exceção: `update_job(conn, job_id,
         status='failed', error_message=str(e))`, não relançar. Fechar `conn` no `finally` externo.
       - `start_transcription_job(youtube_url) -> int`: abre conexão, `create_transcription_job`,
         fecha a conexão (a thread abre a sua própria via `get_db_connection()` dentro de
         `process_transcription_job` — nunca compartilhar conexão pymysql entre threads), dispara
         `threading.Thread(target=process_transcription_job, args=(job_id,), daemon=True).start()`,
         retorna `job_id`.
    3. Adicionar em `clip-processor/src/internal_api.py`:
       ```python
       from src.transcription_job import start_transcription_job

       @app.post('/internal/transcribe')
       def _route_transcribe():
           if not _check_auth():
               return jsonify(error='unauthorized'), 401
           payload = request.get_json(silent=True) or {}
           url = payload.get('url')
           if not url:
               return jsonify(error='missing url'), 400
           try:
               job_id = start_transcription_job(url)
           except Exception as e:
               return jsonify(error=str(e)), 500
           return jsonify(job_id=job_id), 200
       ```
       Atualizar o docstring do topo do arquivo (lista de endpoints) para incluir
       `POST /internal/transcribe {url} -> {job_id}`.
    4. Atualizar `clip-processor/Dockerfile` para instalar whisper-cpp (build from source) e
       baixar o modelo `small` (multilíngue, funciona com `-l pt`):
       ```dockerfile
       FROM python:3.12-slim

       RUN apt-get update && apt-get install -y \
           ffmpeg \
           git \
           build-essential \
           cmake \
           && rm -rf /var/lib/apt/lists/*

       # whisper-cpp local — Transcrição Local do painel (não usado pelo pipeline principal,
       # que continua na Groq Whisper API via transcriber.py)
       RUN git clone --depth 1 https://github.com/ggerganov/whisper.cpp.git /opt/whisper.cpp \
           && cmake -B /opt/whisper.cpp/build -S /opt/whisper.cpp -DCMAKE_BUILD_TYPE=Release \
           && cmake --build /opt/whisper.cpp/build -j --config Release \
           && bash /opt/whisper.cpp/models/download-ggml-model.sh small /opt/whisper.cpp/models

       ENV WHISPER_CPP_BIN=/opt/whisper.cpp/build/bin/whisper-cli
       ENV WHISPER_MODEL_PATH=/opt/whisper.cpp/models/ggml-small.bin

       WORKDIR /app

       COPY requirements.txt .
       RUN pip install --no-cache-dir -r requirements.txt

       COPY src/ src/

       CMD ["python", "-m", "src.main"]
       ```
       ATENÇÃO: o nome do binário gerado pode variar entre versões do whisper.cpp
       (`build/bin/whisper-cli` nas versões recentes, `build/bin/main` em versões antigas). Após
       o build (`docker compose build clip-processor`), rodar
       `docker compose run --rm clip-processor ls /opt/whisper.cpp/build/bin/` para confirmar o
       nome real do binário e ajustar `WHISPER_CPP_BIN` no Dockerfile se necessário antes de
       seguir para o `up -d`.
    5. Rebuild e restart isolado do serviço (regra do projeto — nunca sobe outros serviços):
       `docker compose build clip-processor && docker compose up -d clip-processor`.
  </action>
  <verify>
    <automated>docker compose exec clip-processor python -m pytest tests/test_transcription_job.py tests/test_internal_api.py -x</automated>
  </verify>
  <done>Testes de `test_transcription_job.py` e `test_internal_api.py` passam; imagem
  `clip-processor` reconstruída com `WHISPER_CPP_BIN` apontando para um binário que existe de
  fato (confirmado via `ls` dentro do container); container `clip-processor` sobe e fica
  `running` (`docker compose ps clip-processor`).</done>
</task>

<task type="auto">
  <name>Task 3: Página "Transcrição Local" no painel — formulário, Progress bar, polling e download</name>
  <files>painel/app/Http/Controllers/TranscriptionController.php, painel/routes/web.php, painel/resources/js/pages/TranscricaoLocal.tsx, painel/resources/js/components/app-sidebar.tsx, painel/resources/js/components/ui/progress.tsx</files>
  <action>
    1. Instalar o componente shadcn Progress (ainda não existe no projeto):
       `cd painel && npx shadcn@latest add progress` — gera
       `painel/resources/js/components/ui/progress.tsx`.
    2. Criar `TranscriptionController` (mesmo padrão de `ProcessVideoController`, ver
       `<interfaces>`):
       ```php
       public function index(): Response
       {
           return Inertia::render('TranscricaoLocal', [
               'jobs' => TranscriptionJob::latest()->limit(20)->get(),
           ]);
       }

       public function store(Request $request, ClipProcessorClient $client): RedirectResponse
       {
           $data = $request->validate(['url' => ['required', 'string', 'url']]);
           try {
               $client->transcribe($data['url']);
           } catch (RuntimeException $e) {
               return back()->with('error', $e->getMessage());
           }
           return back()->with('success', 'Transcrição iniciada');
       }

       public function download(TranscriptionJob $job)
       {
           if ($job->status !== 'done' || ! $job->srt_path) {
               abort(404);
           }
           $relative = 'transcripts/'.basename($job->srt_path);
           if (! Storage::disk('clips-videos')->exists($relative)) {
               abort(404);
           }
           return Storage::disk('clips-videos')->download($relative);
       }
       ```
       Nota: `srt_path` gravado pelo Python é o caminho absoluto DENTRO do container
       clip-processor (`/app/videos/transcripts/{id}.srt`); o Laravel nunca deve usar esse
       caminho absoluto diretamente — sempre remontar via `basename()` + disco `clips-videos`,
       porque os dois containers montam o mesmo host path em pontos diferentes.
    3. Rotas em `painel/routes/web.php` (dentro do grupo `['web', 'auth']`, junto das rotas de
       `ProcessVideoController`):
       ```php
       Route::get('/painel/transcricoes', [TranscriptionController::class, 'index'])->name('transcriptions.index');
       Route::post('/painel/transcricoes', [TranscriptionController::class, 'store']);
       Route::get('/painel/transcricoes/{job}/download', [TranscriptionController::class, 'download'])->name('transcriptions.download');
       ```
    4. Criar `painel/resources/js/pages/TranscricaoLocal.tsx` seguindo a estrutura de
       `ProcessVideo.tsx` (AppSidebar/SiteHeader/SidebarProvider/SidebarInset, useForm, Toaster
       para flash), mais:
       - Tipo `Job = { id: number; youtube_url: string; status: 'pending'|'downloading'|
         'transcribing'|'done'|'failed'; progress_percent: number; srt_path: string | null;
         error_message: string | null }`.
       - Prop `jobs: Job[]` recebida via `usePage<PageProps & { jobs: Job[] }>()`.
       - Formulário com um `Input` de URL + `Button` "Transcrever" (post para
         `/painel/transcricoes`, `reset()` no `onSuccess`).
       - Lista/tabela abaixo com uma linha por job: URL truncada, `<Progress value={progress_percent} />`
         (componente shadcn recém-instalado), status como texto, e um `<Button asChild>` com
         `<a href={`/painel/transcricoes/${job.id}/download`}>Baixar .srt</a>` habilitado só
         quando `status === 'done'`; mostrar `error_message` em vermelho quando `status === 'failed'`.
       - Polling: `useEffect` com `setInterval(() => { if (jobs.some(j => ['pending',
         'downloading','transcribing'].includes(j.status))) { router.reload({ only: ['jobs'] }) } },
         3000)`, limpar o interval no cleanup. Importar `router` de `@inertiajs/react`.
    5. Adicionar entrada no array de navegação de `app-sidebar.tsx`:
       `{ title: 'Transcrição Local', url: '/painel/transcricoes', icon: <ícone lucide
       apropriado, ex. AudioLinesIcon ou FileTextIcon> }` (confirmar que o ícone escolhido existe
       em `lucide-react`, senão usar `LinkIcon` já importado no arquivo).
  </action>
  <verify>
    <automated>cd painel && npm run build 2>&1 | tail -30 && php artisan route:list | grep transcricoes</automated>
  </verify>
  <done>`npx shadcn@latest add progress` gerou `progress.tsx`; rotas `/painel/transcricoes` (GET/POST)
  e `/painel/transcricoes/{job}/download` (GET) aparecem em `php artisan route:list`; `npm run build`
  compila sem erros TypeScript; item "Transcrição Local" visível na sidebar; ao colar uma URL e
  clicar em "Transcrever" o job aparece na lista com Progress bar em 0-10%, evolui via polling, e o
  botão de download só liga quando `status === 'done'`.</done>
</task>

</tasks>

<verification>
1. Migration aplicada: `php artisan migrate:status` mostra `transcription_jobs` como Ran.
2. Testes Python: `docker compose exec clip-processor python -m pytest tests/test_transcription_job.py tests/test_internal_api.py -x` — GREEN.
3. Rebuild obrigatório após qualquer mudança em `clip-processor/src` ou `Dockerfile` — sempre isolado,
   nunca sobe outros serviços do compose raiz:
   `docker compose build clip-processor && docker compose up -d clip-processor`.
4. `docker compose ps clip-processor` mostra `running` (não `restarting`/`exited`) após o rebuild.
5. Fluxo manual fim-a-fim (checkpoint informal, não bloqueante): colar uma URL curta de YouTube em
   `/painel/transcricoes`, confirmar que o job muda de `pending` → `downloading` → `transcribing` →
   `done` (ou `failed` com `error_message` legível) e que o `.srt` baixado abre e tem conteúdo em
   português.
6. Confirmar que NENHUM registro de `transcription_jobs` aparece em `generated_clips` ou nas telas
   de aprovação de clips (Dashboard) — a feature é isolada por design, tabela própria.
</verification>

<success_criteria>
- Tabela `transcription_jobs` existe e é a única fonte de verdade de status/progresso (nada em
  memória, nada no Redis) — reload da página ou fechar a aba não perde o progresso.
- Endpoint `POST /internal/transcribe` responde em menos de 1s (só cria o job e dispara a thread),
  o trabalho pesado (download + whisper-cpp) roda assíncrono.
- `whisper-cpp` compilado e funcional dentro da imagem `clip-processor`, modelo `small` baixado.
- Painel mostra Progress bar (shadcn) real por job e libera download do `.srt` somente quando
  `status === 'done'`.
- Nenhum código deste plano toca `generated_clips`, fluxo de aprovação, upload para YouTube, ou
  qualquer outro serviço do `docker-compose.yml` raiz além de `clip-processor` e paths sob
  `canaldecortes/`.
</success_criteria>

<output>
After completion, create `.planning/quick/1-adicionar-sess-o-de-transcri-o-local-no-/quick-1-01-SUMMARY.md`
summarizing: tabela criada, endpoint novo, binário whisper-cpp confirmado (nome real do binário
usado), decisões tomadas (ex. modelo escolhido, milestones de progresso), e comando de
rebuild/restart executado.
</output>
