# Canal de Cortes

> **Status:** as-built · **Atualizado:** 2026-08-27

Pipeline que monitora canais do YouTube, baixa vídeos, transcreve, escolhe trechos com IA, gera
clips, prepara metadata e publica em canais de destino. O fluxo normal é automático; o painel e o
Telegram servem para observar, aprovar e corrigir.

## Fluxo em uma linha

~~~text
RSS → dedup → PostgreSQL/pending → yt-dlp → legenda ou Whisper → seleção IA
→ FFmpeg → metadata/thumbnail → pending ou approved → cota/OAuth → YouTube
~~~

## Componentes

| Componente | Responsabilidade | Fonte principal |
|---|---|---|
| `clip-processor` | sidecar HTTP autenticado do pipeline | `clip-processor/src/sidecar.py` |
| workers `clip-*` | descoberta, download, IA, render, publicação e manutenção em processos separados | `clip-processor/src/worker.py` |
| `painel` | UI, autenticação, configuração, aprovação e controles | `painel/` |
| PostgreSQL 16 | estado, fila, relacionamentos e metadata | `painel/database/migrations/` |
| Redis 7 | dedup, cota diária e idempotência de avisos | `dedup.py`, `quota_manager.py`, `ttl_worker.py` |
| sidecar Flask | ponte autenticada entre painel e processador | `clip-processor/src/internal_api.py` |

O Compose da raiz é isolado deste projeto. PostgreSQL, Redis e o sidecar não têm portas publicadas
no host; a aplicação web fica em `http://localhost:8088` por padrão.

O Compose atual monta `./clip-processor/src:/app/src` no sidecar e em cada worker. Assim,
alterações Python entram nos containers após recriá-los; mudanças no Dockerfile, dependências ou
pacotes do sistema ainda exigem rebuild.

## Funcionamento

1. **Descoberta:** `clip-poller`/`rss_poller.py` consulta canais ativos e não blacklistados. IDs repetidos são
   ignorados; títulos com termos de apostas/cassino são bloqueados.
2. **Classificação:** `curto` quando a fonte tem menos de 420 s; `longo` a partir de 420 s.
3. **Download:** `clip-downloader`/`yt-dlp` baixa até 1080p, com três tentativas, proteção de 2 GB livres e limpeza
   de artefatos incompletos. A janela padrão é 6 vídeos curtos e 4 longos.
4. **Transcrição:** `clip-ai` tenta somente legendas manuais em português do YouTube; sem legenda, usa Groq
   Whisper `whisper-large-v3-turbo`. O resultado fica em `<video_id>_transcript.json`.
5. **Seleção:** a IA escolhe até 3 trechos curtos com 30 s exatos ou 1 trecho longo de 420–1200 s.
   O prompt vem do perfil ativo do canal-fonte; o Python valida bordas, publicidade, duplicidade,
   duração e score mínimo 7.
6. **Pós-produção:** `clip-renderer` gera Shorts em janelas exatas de 30 s, verticais 1080×1920, com legenda e
   marca d’água compostas em um único passe FFmpeg — a menos que o vídeo fonte já traga legenda
   gravada, detectada por OCR cruzado com a transcrição. Longos são
   horizontais, sem legenda queimada, e exigem intro, encerramento e música configurados.
7. **Metadata:** usa o perfil ativo do canal-destino para gerar título, descrição, tags e a chamada
   literal da thumbnail; o sistema valida essa frase contra a transcrição.
8. **Publicação:** `clip-publisher` publica; o clip fica `pending` no modo automático ou `approved` quando a aprovação manual
   está habilitada. O publisher aplica roteamento por perfil/nicho, cota, janela horária e OAuth.
9. **Finalização:** após publicação, envia evento ao Telegram e remove arquivos que não são mais
   necessários quando todos os clips do vídeo terminam.

## Formatos

| Formato | Seleção | Saída |
|---|---|---|
| `curto` | até 3 trechos, 30 s exatos | vertical 9:16 em 1080×1920, legenda oficial e render único |
| `longo` | 1 trecho contínuo, 420–1200 s | horizontal, legenda oficial sem queimar, intro/outro/música obrigatórios |

O nicho continua em `source_channels.target_niche` e `destination_channels.niche`, mas a
seleção editorial é governada por `prompt_profiles`. Cada canal pode apontar para um perfil ativo
compatível com seu nicho. O perfil do canal-fonte controla seleção; o perfil do canal-destino
controla metadata e thumbnail. A publicação só encontra destino com o mesmo perfil quando a fonte
já está configurada. Futebol, Conteúdo de Inteligência e Podcast são semeados pela migration;
novos nichos devem adicionar seu próprio perfil.

## IA e prompts

Os perfis específicos ficam no PostgreSQL, em `prompt_profiles`, e são semeados pela migration
[`2026_08_27_000000_create_prompt_profiles_table.php`](painel/database/migrations/2026_08_27_000000_create_prompt_profiles_table.php).
As regras de segurança, fact-check, duração, JSON e pós-validação continuam compartilhadas no
código para não serem alteradas por um perfil editorial.

- [`selector.py`](clip-processor/src/selector.py): resolve `selection_short_prompt` ou
  `selection_long_prompt` do perfil do canal-fonte, com fallback legado seguro.
- [`metadata_generator.py`](clip-processor/src/metadata_generator.py): resolve
  `metadata_short_prompt`, `metadata_long_prompt` e `thumbnail_prompt` do destino, com fallback
  legado seguro.
- [`prompt_profiles.py`](clip-processor/src/prompt_profiles.py): normaliza o perfil retornado pelo
  PostgreSQL e valida compatibilidade com o nicho.
- [`fact_check_prompt.py`](clip-processor/src/fact_check_prompt.py): instrução comum de pesquisa e
  classificação de alegações.

O catálogo completo, os contratos JSON e as regras de cada prompt estão em
[`Docs/SISTEMA-IA-SELECAO.md`](Docs/SISTEMA-IA-SELECAO.md).

Em runtime:

- Claude `claude-haiku-4-5` é tentado quando `ANTHROPIC_API_KEY` está disponível;
- Groq `openai/gpt-oss-20b` é o fallback da seleção e o caminho usual quando a chave Anthropic está vazia;
- transcrição usa Groq Whisper;
- metadata usa o provider escolhido pela configuração; falha de geração marca o clip como failed;
- thumbnail não tem fallback local: sem frase literal válida, o clip falha.

## Painel e Telegram

O painel oferece:

- dashboard de fila, falhas e cota;
- cadastro de canais-fonte e canais-destino;
- aprovação, rejeição, reprocessamento e preview;
- pausa, retomada, priorização e reordenação da fila;
- processamento manual de URL;
- transcrição local isolada com `whisper.cpp`;
- gestão de assets, marca d’água e senha.

O Telegram aceita `/status`, `/clipes`, `/aprovar <id>`, `/rejeitar <id>`,
`/processar <url>` e `/ajuda`. Eventos de publicação, falha e TTL são enviados pelo painel.

## Configuração e primeiro boot

~~~bash
cp .env.example .env
cp painel/.env.example painel/.env
~~~

Preencha, no mínimo, `CLIPS_DB_PASSWORD`, `APP_KEY` no painel e
`CLIP_PROCESSOR_INTERNAL_TOKEN` com o mesmo valor nos dois arquivos. Configure pelo menos
`GROQ_API_KEY`; `ANTHROPIC_API_KEY` é opcional. Mantenha `PIPELINE_ENABLED=false` até
configurar OAuth e os canais de destino.

~~~bash
docker compose up -d --build
docker compose ps
~~~

O `panel-init` aplica as migrations automaticamente. Crie o operador:

~~~bash
docker compose exec php php artisan painel:create-user
~~~

O painel abre em `http://localhost:8088`. Depois de colocar `youtube/client_secret.json` no projeto,
gere o token de cada canal de destino:

~~~bash
docker compose exec clip-processor python -m src.youtube_oauth --channel <slug>
~~~

Só então habilite o pipeline:

~~~bash
sed -i '' 's/^PIPELINE_ENABLED=.*/PIPELINE_ENABLED=true/' .env
docker compose up -d --force-recreate clip-processor clip-poller clip-downloader clip-ai clip-renderer clip-publisher clip-maintenance
~~~

## Comandos úteis

~~~bash
docker compose ps
docker compose logs -f clip-processor
docker compose logs -f clip-poller clip-downloader clip-ai clip-renderer clip-publisher clip-maintenance
docker compose exec php php artisan migrate:status
make setup
make lint
make test-python
make test-php
~~~

Para operação, diagnóstico, backup e restauração, consulte [`Docs/RUNBOOK.md`](Docs/RUNBOOK.md).

## Fonte de verdade da documentação

1. Código executado e migrations em `painel/database/migrations/`.
2. `.env.example`, `docker-compose.yml` e arquivos de configuração.
3. Documentos “as-built” listados em [`Docs/README.md`](Docs/README.md).
4. ADRs, changelog, bugs, TODOs e planos — histórico ou planejamento, não descrição do runtime.

Leia [`Docs/README.md`](Docs/README.md) para o índice completo.
