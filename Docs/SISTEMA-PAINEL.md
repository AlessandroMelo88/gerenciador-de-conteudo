# Painel administrativo

> Tipo: referência as-built · Atualizado: 2026-08-27
> Fontes: `painel/routes/web.php`, `painel/app/Http/Controllers/` e
> `painel/resources/js/pages/`

## Stack e acesso

- Laravel 13 + Inertia Laravel 3;
- React 19 + TypeScript;
- Tailwind CSS 4 + shadcn/ui;
- Nginx + PHP-FPM em Docker;
- autenticação por sessão; páginas operacionais exigem login;
- URL padrão: `http://localhost:8088`;
- `/` redireciona para `/painel` ou `/login`.

O painel lê PostgreSQL, Redis e volumes compartilhados para exibir dados. Ações que alteram fila,
processos ou arquivos passam pelo [`sidecar`](SISTEMA-SIDECAR.md).

## Páginas

| URL | Página | Responsabilidade |
|---|---|---|
| `/painel` | Dashboard | fila, quota, janela ativa, falhas, aprovação e preview |
| `/painel/canais-fonte` | Canais fonte | canais RSS, nicho, perfil de prompt, ativo e blacklist |
| `/painel/canais-destino` | Canais destino | destinos, nicho, perfil de prompt, OAuth, crédito e watermark |
| `/painel/videos` | Vídeos | fontes, status, busca, uso, limpeza e ordenação |
| `/painel/processar-video` | Processar vídeo | enfileira URLs e escolhe `curto`/`longo` |
| `/painel/transcricoes` | Transcrição local | cria jobs `whisper.cpp` e baixa SRT |
| `/painel/configuracoes` | Configurações | senha e biblioteca de mídia |
| `/painel/documentacao` | Documentação | ajuda resumida embutida na UI |

## Dashboard

Exibe:

- quota usada por canal-destino;
- clips `pending` aguardando aprovação;
- clips `approved` aguardando publicação/quota;
- últimas falhas de clips;
- contagem de fontes falhas;
- janela ativa de download, com formato, prioridade, score e possibilidade de apagar;
- preview do MP4 final por volume compartilhado.

A cota mostrada pelo painel lê a chave Redis do destino. O processador é a fonte de decisão para
publicação; o card serve para observação.

Ações de clip:

| Ação | Efeito |
|---|---|
| aprovar | `pending` → `approved` |
| rejeitar | chama sidecar; marca rejeitado e remove MP4 final |
| reprocessar | `failed` → `pending_cut` se não há MP4, ou status publicável se há |
| preview | serve `clip_path` pelo volume; não reprocessa |

## Canais fonte

Adicionar canal:

1. operador informa URL, nicho e perfil de prompt;
2. sidecar resolve ID, nome e handle via yt-dlp;
3. painel grava `source_channels`, `rss_url` e `prompt_profile_id`.

O seletor mostra apenas perfis ativos compatíveis com o nicho. Em “Automático pelo nicho”, o
backend resolve o perfil semeado por `slug`, `niche` ou `niche_aliases`; um perfil incompatível ou
inativo é rejeitado.

Atualizações permitem desativar ou colocar em blacklist. Blacklist afeta novas entradas do RSS; não
remove automaticamente vídeos já inseridos. Canal com vídeos relacionados não pode ser apagado.

## Canais destino

Campos principais: slug, nome, nicho, perfil de prompt, ID do YouTube, template de crédito e ativo.

- nicho define o roteamento da publicação;
- perfil define os prompts do canal: fonte usa seleção, destino usa metadata e thumbnail; deve ser compatível com o nicho;
- ativo controla se o publisher usa o destino;
- watermark é um PNG salvo em `branding/watermark-<slug>.png`;
- OAuth é gerado no terminal, não no navegador do painel;
- canal com clips relacionados não pode ser apagado.

## Vídeos e controles

A página lista `source_videos` com abas `ativos`, `falharam` e
`todos`, além de status, período, busca e filtro seguro para apagar. A aba
`ativos` mostra somente fontes pendentes ou em processamento; fontes concluídas
(`published`) ficam no histórico em `todos`.

Ações de fila: pause, resume, prioritize, reorder. Exclusão de arquivos e purga de antigos chamam
o sidecar, que valida guards no processador. O painel não deve apagar raw diretamente.

A janela exibida usa, por padrão, 6 fontes curtas e 4 longas, mas a seleção real é feita pelo código
Python conforme [`SISTEMA-DOWNLOAD.md`](SISTEMA-DOWNLOAD.md).

## Processar vídeo

Aceita várias URLs, remove duplicatas e exige formato `curto` ou `longo`. Cada
URL é enviada ao sidecar; o endpoint apenas cria/retorna uma fonte `pending`. Download,
transcrição, seleção, corte e publicação continuam no pipeline normal.

## Transcrição local

O formulário envia uma URL ao sidecar e recebe um job assíncrono. O painel lista os últimos 20 jobs,
progresso persistido e erro; somente jobs `done` disponibilizam download do SRT. Esse fluxo
não cria clips.

## Configurações e mídia

A biblioteca do painel aceita:

- `intro` e `outro`: MP4/MOV/WEBM ou imagem;
- `music`: MP3/WAV/M4A/OGG;
- escopo opcional por destino e formato;
- prioridade, ativo, duração de imagem e volume da música.

O volume informado para a música recebe ganho de 20% no render, limitado a 100%; a trilha é aplicada
nos 15 segundos finais do vídeo longo, com fade-in e volume final nos 8 segundos finais.

O longo exige um asset de cada tipo. O processador prefere filesystem canônico por canal e usa a
biblioteca como fallback; detalhes em [`SISTEMA-VIDEO.md`](SISTEMA-VIDEO.md).

A senha exige senha atual e nova senha com pelo menos 10 caracteres.

## Rotas de sessão e integração

- `/login`: GET/POST de autenticação;
- `/logout`: POST autenticado;
- `/telegramcanal`: webhook protegido por segredo do Telegram e allowlist de chat;
- `/internal/pipeline-event`: evento do processador protegido pelo token compartilhado.

A lista completa das rotas de negócio está no arquivo `painel/routes/web.php`; ações internas
estão no [`SISTEMA-SIDECAR.md`](SISTEMA-SIDECAR.md).

## Telegram

Com token e chat configurados, o painel processa:

- `/status`;
- `/clipes`;
- `/aprovar <id>`;
- `/rejeitar <id>`;
- `/processar <url>`;
- `/ajuda`.

O scheduler Laravel executa `painel:daily-summary` às 18:00 no timezone da aplicação e
envia mensagem somente quando há clips `pending`.
