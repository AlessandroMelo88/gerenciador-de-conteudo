# Telegram + N8N — Canal de Cortes

Automação de descoberta e orquestração do pipeline via Telegram Bot + N8N.

## O que isso faz

Você envia comandos pelo Telegram e o N8N orquestra o pipeline:

```
Você (Telegram) → N8N → [Agentes de IA] → MySQL → clip-processor → YouTube
```

## Comandos disponíveis

| Comando | Descrição |
|---------|-----------|
| `/buscar <tema>` | Busca vídeos recentes no YouTube sobre o tema e adiciona à fila |
| `/trending` | Retorna top 5 assuntos em alta no futebol BR hoje |
| `/fila` | Lista clipes prontos para upload (status `pending`) |
| `/publicar` | Dispara upload do próximo clipe da fila (requer Phase 5) |
| `/canal <URL>` | Adiciona novo canal RSS ao pool de monitoramento |
| `/status` | Exibe métricas: clips gerados, quota usada, próximo upload |
| `/ajuda` | Exibe esta lista de comandos |

## Estrutura

```
telegram-n8n/
├── README.md               # Este arquivo
├── SETUP.md                # Guia passo a passo de configuração
├── workflows/
│   ├── 01-telegram-handler.json     # Webhook handler + roteador
│   ├── 02-busca-videos.json         # Agente de busca por tema
│   ├── 03-tendencias.json           # Agente de tendências diárias
│   └── 04-notificador-fila.json     # Notificação automática de clips prontos
└── agents/
    ├── trend-hunter-prompt.md       # Prompt do agente de tendências
    ├── script-generator-prompt.md   # Prompt gerador de roteiro
    └── seo-optimizer-prompt.md      # Prompt otimizador SEO
```

## Início rápido

1. Leia o [SETUP.md](SETUP.md) completo
2. Importe os workflows em: `http://localhost:5678` (N8N)
3. Configure as credenciais (Telegram, YouTube, MySQL)
4. Teste com `/ajuda` no Telegram

## Custos estimados

| Serviço | Custo |
|---------|-------|
| Telegram Bot API | Grátis |
| N8N (self-hosted) | Grátis (já instalado) |
| YouTube Data API | Grátis (10.000 unidades/dia de quota) |
| Google Trends RSS | Grátis |
| Claude Haiku (agentes) | ~$0.001 por request |
| SerpAPI (SEO) | $50/mês (opcional) |
