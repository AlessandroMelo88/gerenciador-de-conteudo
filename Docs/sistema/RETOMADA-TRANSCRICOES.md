# Retomada — Transcrições, extensão e estudos (18/09/2026)

Documento de passagem de contexto. Lê este arquivo e o [`SISTEMA-TRANSCRICAO.md`](SISTEMA-TRANSCRICAO.md)
e dá para continuar sem o histórico da conversa.

## Onde as coisas estão agora

| | Commit | Observação |
|---|---|---|
| **Produção (A1)** | `a50db7e` | transcrição multiplataforma no Mac, texto no banco, busca, `.md/.txt/.srt` |
| **`master` (GitHub)** | `9830ec3` | produção **+** pausar/retomar/apagar, barra de %, login de curso, extensão do Chrome, contadores dourados |
| `afiliadas-fase2` | `0a4b94d` | master de 17/09 já trazida; suíte 86/87 nos dois bancos; **merge suspenso** (ver pendência 4) |

**A `master` está à frente de produção de propósito**: o operador pediu para não fazer deploy.
O próximo `./deploy.sh` leva tudo, incluindo a migration `2026_09_18_000000_transcricao_status_pausado`
(testada ida e volta em PostgreSQL e MySQL).

## O que funciona hoje, provado com uso real

- **Extensão "Transcrever esta aula"** (`extensao-chrome/`, carregada sem compactação no Chrome).
  Um clique na aba da aula: pega a sessão **só daquele site**, manda para o worker do Mac em
  `127.0.0.1:8765`, que grava `~/.config/canaldecortes/cookies.txt` (600) e põe o link na fila.
  Provada na Asimov: aula *"02. O que é analisar dados?"*, BunnyCDN, 375 s, 7.338 caracteres
  (job 5 em produção).
- **Sites sem login:** YouTube, Shorts, TikTok. Short de 48 s em 4,8 s, TikTok de 24 s em 3,8 s.
- **Sites com login:** Asimov passou. Hotmart **não foi testado ainda**. Vimeo passou a exigir login.
- **Worker do Mac** (`scripts/local_download_worker.py` via launchd `com.canaldecortes.downloader`)
  roda a transcrição antes do download do pipeline e é acordado na hora pela extensão.

## Aprendizados que custaram caro (não repetir)

| Armadilha | Detalhe |
|---|---|
| `--cookies-from-browser chrome` | abre a caixa do chaveiro do macOS **a cada execução**; em 17/09 empilhou caixas até travar o Mac. Só arquivo `cookies.txt` |
| `--progress-template` do yt-dlp | o `download:` do começo é **seletor de tipo**, não texto; a linha sai sem ele. Marcador literal: `[progresso]` |
| Groq via `urllib` | Cloudflare do Groq recusa o User-Agent `Python-urllib` com `403 error code: 1010` |
| Asimov | Cloudflare anti-bot (`403`) até instalar `curl_cffi` e usar `--extractor-args generic:impersonate` |
| `enum()` do Laravel | vira CHECK no PostgreSQL e ENUM no MySQL; mudar valores exige SQL por driver |
| `php artisan serve` | só repassa ao processo filho uma lista fixa de variáveis; `DB_HOST=... composer dev` **não funciona**. Resolvido com `127.0.0.1 postgres` no `/etc/hosts` do Mac |
| Worker roda o working tree | o launchd aponta para a pasta do projeto: trocar de branch muda o código que o worker carrega no próximo restart |
| yt-dlp do Mac | instalado por `pip --break-system-packages` no `python3.13` do Homebrew; `curl_cffi` também |
| Painel local × produção | o painel local usa o **banco local**; o worker só lê a fila de **produção** (ver próxima tarefa) |

## Próximas tarefas, na ordem pedida pelo operador

### 1. Escolher o destino da transcrição: local, produção ou os dois

**Problema:** o botão Transcrever do painel **local** grava no banco local, e o worker só lê produção —
o job fica em "Na fila do Mac 0%" para sempre (aconteceu em 18/09 com
`hub.asimov.academy/curso/atividade/como-uma-ia-consegue-analisar-dados/`).

**Desenho proposto (não implementado):**

- No worker, um **destino** é um par `run_sql` / `run_sql_stdin`:
  - `producao`: o `ssh` + `docker exec postgres psql` de hoje;
  - `local`: `docker exec -i postgres psql -U clips_user -d clips_automation` direto no Mac.
- O ciclo do worker chama `process_one_job` para cada destino **ativo** — assim o botão do painel
  local também passa a funcionar.
- Na extensão, duas chaves no popup — **Produção** e **Local** —, guardadas em `chrome.storage.local`.
  O `POST /transcrever` passa `destinos: [...]` e a API insere na fila de cada um.
- **Decidir antes de codar:** com os dois ligados, transcrever **uma vez** e gravar nos dois bancos
  (economiza Groq, mas o job passa a ter dois donos) ou deixar cada banco com seu job (simples,
  gasta o dobro de Groq e de download). Recomendação: uma vez só — a extensão cria o job em um
  destino "principal" e o worker, ao terminar, copia o resultado para o outro.

### 2. Contexto para estudo: título, curso, seção, do que a aula trata

O objetivo final do operador é **base de conhecimento para estudar**: rever o conteúdo, montar slides
e, depois, testes para si mesmo. Hoje a transcrição guarda só título do vídeo, plataforma, duração e
texto. Falta:

- **Onde a aula mora:** curso → trilha/seção → aula. A extensão já está na página e pode ler o
  título da aba, o `h1` e o breadcrumb (`Curso › Módulo › Aula`). Isso alimenta a hierarquia da
  Fase 3 **automaticamente**, sem o operador criar rotas à mão.
  Cuidado: seletor de página quebra quando o site muda. Heurística genérica (breadcrumb, `h1`,
  `og:title`) + um adaptador pequeno por plataforma (Asimov, Hotmart).
  Uma aula pode estar em **várias trilhas** (a Asimov mostra "Esta aula está em 4 trilhas") → relação
  N:N aula × trilha.
- **Do que a aula trata:** depois de transcrever, uma chamada ao LLM (Groq, o mesmo `llama-3.3-70b`
  que o projeto já usa, com a mesma regra de fallback do `selector.py`) gera **resumo, tópicos e
  conceitos-chave**, que entram no `.md`. Testes e slides ficam de fora por decisão do operador —
  ele gera depois, colando o `.md` em outra IA.
- Materiais da aula (datasets, código): o operador guardou um exemplo em
  `painel/public/conteudo-cursos/` (**fora do git e do deploy** desde 17/09, porque é material pago
  e ficaria público na raiz web). Destino definitivo: `storage/app/private/cursos/`, servido por
  rota autenticada. A pasta de exemplo pode ser apagada depois que a Fase 3 estiver de pé.

### 3. Hotmart

Testar `hotmart.com/pt-BR/club/formula-youtube/products/8093188/content/V4VKj9GVe2` pela extensão.
**Não confirmado:** se o player do Hotmart usa DRM. Se usar, nem com login o `yt-dlp` baixa.

## Pendências do operador (fora das tarefas acima)

1. **Trocar a senha da conta da Asimov** — passou em texto puro pelo chat em 17/09. A extensão não
   depende dela. A conta está no nome de outra pessoa: conferir consentimento e termos de uso.
2. **Deploy** da `master` quando quiser: leva pausar/apagar, a extensão e os contadores dourados.
   Depois do deploy, apagar pelo painel as transcrições 1, 2 e 4 (falhas antigas) e a 3 (teste).
3. **Cloudflare:** registro A de `toolscut` → `129.80.236.185` (o tráfego ainda passa pela Micro).
4. **Correção de segurança** `fix/pipeline-event-token-fail-closed`: `/internal/pipeline-event`
   aceita requisição sem token quando `CLIP_PROCESSOR_INTERNAL_TOKEN` está vazio (`null === null`).
   Em produção o token existe. É a falha única da suíte da `afiliadas-fase2` e destrava o merge
   dela. A sessão de afiliados combinou não abrir a branch sem liberação do operador.
5. Os contadores da barra lateral (`9`, `3`, `32`, `2620`) são **números fixos no código**
   (`app-sidebar.tsx`), não contagens reais. Decidir se passam a contar de verdade.

## Feito em 17/09/2026 (outras frentes, já em produção)

- Justiça por canal na fila de download (`clip-processor/src/fair_queue.py`) e teto fixo de
  **2 vídeos por canal de origem** (`DOWNLOAD_MAX_PER_SOURCE_CHANNEL=2`, servidor e worker).
- Carência do canal novo no expurgo de notícia velha.
- Vagas de política liberadas (canais legados CNN/UOL/JP/Band), com backup em
  `/mnt/videos/backups/manual/`.
- CI/CD **só desenhado** em [`CI-CD.md`](CI-CD.md), com a trava do bug 11 (não reiniciar com clip
  em `cutting`/`publishing`) — usada na mão em todos os deploys de 17/09.
- Diagnóstico de política: os canais MBL paravam no download; títulos nossos giram em torno de
  instituição (STF, Moraes), os de Felino Missionário e Missão Avança em torno de uma pessoa
  (Renan Santos) com verbo de ação e caixa alta.
