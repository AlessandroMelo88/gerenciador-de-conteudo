# Retomada — Transcrições, extensão e estudos (18/09/2026)

Documento de passagem de contexto. Lê este arquivo e o [`SISTEMA-TRANSCRICAO.md`](SISTEMA-TRANSCRICAO.md)
e dá para continuar sem o histórico da conversa.

## Onde as coisas estão agora

| | Commit | Observação |
|---|---|---|
| **Produção (A1)** = **`master`** | ver `REVISION` | 18/09/2026: afiliadas fase 2 mesclada, manutenção no deploy, token do pipeline-event fail-closed, arquivo da aula apagado após transcrever |
| `afiliadas-fase2` | — | **mesclada na master** em 18/09/2026; afiliados segue em branches curtas |

Teste ponta a ponta em produção (18/09): job 6, short de 19 s, `done` com `aulas/6.mp4` (475.990 bytes)
no Mac e na A1; rota sem login → 302, com login → 200 `me-at-the-zoo.mp4`. O job 6 pode ser apagado
pelo painel (apaga o arquivo na A1 junto).

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

### 1. ~~Destino local/produção~~ → só produção, com botão "Baixar aula" (feito em 18/09/2026)

O operador decidiu: a transcrição **só precisa funcionar em produção** — o seletor local/produção
foi descartado. O botão Transcrever do painel **local** continua sem worker (o job fica na fila).
No lugar, entrou o download do arquivo da aula — e, na mesma noite, o operador decidiu que o
arquivo é **apagado depois da transcrição** (só o texto fica); guardar virou opção
`TRANSCRICAO_GUARDAR_AULA=1`, desligada. Ver
[`SISTEMA-TRANSCRICAO.md`](SISTEMA-TRANSCRICAO.md). Material de curso agora mora em
`painel/storage/app/private/conteudo-cursos/`, mesma árvore no Mac e na A1
(`/mnt/videos/conteudo-cursos`).

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
- Materiais da aula (datasets, código): o exemplo do operador foi movido em 18/09 de
  `painel/public/conteudo-cursos/` para `painel/storage/app/private/conteudo-cursos/` (fora do git,
  fora da raiz web). Os arquivos das aulas ficam em `conteudo-cursos/aulas/`; materiais podem ganhar
  pasta irmã quando a Fase 3 existir.

### 3. Hotmart

Testar `hotmart.com/pt-BR/club/formula-youtube/products/8093188/content/V4VKj9GVe2` pela extensão.
**Não confirmado:** se o player do Hotmart usa DRM. Se usar, nem com login o `yt-dlp` baixa.

## Pendências do operador (fora das tarefas acima)

1. **Trocar a senha da conta da Asimov** — passou em texto puro pelo chat em 17/09. A extensão não
   depende dela. A conta está no nome de outra pessoa: conferir consentimento e termos de uso.
2. ~~Deploy~~ feito em 18/09/2026. Transcrições 1–4, 6 e 7 (falhas e testes) apagadas; backup em
   `/mnt/videos/backups/manual/transcription_jobs-20260918.sql`. Fica só a 5 (aula da Asimov).
3. **Cloudflare:** registro A de `toolscut` → `129.80.236.185` (o tráfego ainda passa pela Micro).
4. ~~Correção de segurança do `/internal/pipeline-event`~~ feita em 18/09/2026 (falha fechado sem
   token, `hash_equals`); destravou o merge da `afiliadas-fase2`.
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
