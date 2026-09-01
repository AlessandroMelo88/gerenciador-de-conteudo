+# Painel Canal de Cortes

> **Tipo:** referência as-built · **Atualizado:** 2026-08-27

Aplicação Laravel 13 com Inertia 3, React 19, Tailwind 4 e shadcn/ui. É a interface do operador
para configurar canais, acompanhar o pipeline, revisar clips e controlar a fila. O painel roda no
Compose da raiz; o processador Python continua sendo o dono da execução do pipeline.

## Inicialização

Consulte o [README da raiz](../README.md) para o primeiro boot. Em resumo:

~~~bash
make setup
docker compose up -d --build
docker compose exec php php artisan painel:create-user
~~~

O serviço `panel-init` aguarda o PostgreSQL saudável e executa as migrations Laravel antes de
liberar `php`, `queue`, `scheduler` e `nginx`. O painel fica em
[http://localhost:8088](http://localhost:8088), ou na porta definida por `APP_PORT`.

Para desenvolvimento fora do container, `make setup-panel` instala Composer e npm no diretório
`painel/`. Use `make lint`, `make test-php` e
`make ci` conforme [DESENVOLVIMENTO.md](../Docs/DESENVOLVIMENTO.md).

## Telas e responsabilidades

| Tela | Uso |
|---|---|
| Dashboard | fila, falhas, cota, clips aguardando revisão e ações rápidas |
| Canais fonte | URLs RSS, nicho, perfil de prompt, ativo/blacklist e monitoramento |
| Canais destino | canal YouTube, nicho, perfil de prompt, watermark, OAuth e ativo |
| Vídeos | fonte baixada, status, busca, ordenação, pausa e limpeza segura |
| Processar vídeo | enfileirar uma URL manual no fluxo normal |
| Transcrições | iniciar e acompanhar transcrição local isolada |
| Configurações | assets de pós-produção e senha |
| Documentação | resumo operacional embutido no painel |

A aprovação manual só entra em vigor quando `MANUAL_APPROVAL_REQUIRED=true`. Caso contrário,
clips válidos seguem para publicação conforme cota, horário e OAuth.

## OAuth

Depois de cadastrar um canal destino, coloque `youtube/client_secret.json` conforme
[SISTEMA-PUBLICACAO.md](../Docs/SISTEMA-PUBLICACAO.md) e execute:

~~~bash
docker compose exec clip-processor python -m src.youtube_oauth --channel <slug>
~~~

O comando grava o token em `youtube/token_<slug>.pickle`.

## Contratos importantes

- PostgreSQL é compartilhado pelo painel e pelo processador; Redis é reservado para dedup, cota e
  idempotência de avisos.
- Perfis editoriais ficam em `prompt_profiles`; cada canal deve usar um perfil ativo compatível com
  seu nicho. A migration semeia Futebol, Conteúdo de Inteligência e Podcast.
- A fila do pipeline está nas tabelas `source_videos` e `generated_clips`; a fila Laravel usa a
  tabela `jobs` para tarefas do painel.
- Chamadas do painel ao processador passam pelo sidecar autenticado e seus endpoints estão em
  [SISTEMA-SIDECAR.md](../Docs/SISTEMA-SIDECAR.md).
- Formatos, legendas e aprovação estão descritos em
  [SISTEMA-VIDEO.md](../Docs/SISTEMA-VIDEO.md) e [ESTADOS-E-TRANSICOES.md](../Docs/ESTADOS-E-TRANSICOES.md).
