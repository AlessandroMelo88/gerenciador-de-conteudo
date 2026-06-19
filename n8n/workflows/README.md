# N8N Workflows — Canal de Cortes

## Workflows disponíveis

| Arquivo | Função |
|---------|--------|
| `canaldecortes-pipeline.json` | Pipeline principal (cron 6h + retry + notificação Telegram) |

## Como importar

1. Acesse o N8N em `http://localhost:5678`
2. Menu lateral → **Workflows** → Botão `+`
3. Três pontos (⋮) → **Import from File**
4. Selecione o arquivo `.json`
5. Configure as credenciais nos nós que exibirem aviso laranja
6. Ative o workflow (toggle no topo)

## Credenciais necessárias

Configure em **Configurações** → **Credenciais**:

| Nome | Tipo | Campos |
|------|------|--------|
| `Telegram Canal de Cortes` | Telegram API | Bot Token |
| `MySQL Canal de Cortes` | MySQL | host=mysql, db=clips_automation, user=clips_user |

## Variáveis de ambiente N8N

Configure em **Configurações** → **Variables**:

| Variável | Valor |
|----------|-------|
| `TELEGRAM_CHAT_ID` | Seu chat ID do Telegram (obtenha com @userinfobot) |

## Pré-requisito para Execute Command

O workflow usa `docker exec clip-processor python -m src.pipeline_runner` a partir do container n8n. Para isso funcionar, o container n8n precisa ter acesso ao Docker host. No `docker-compose.yml` pai, monte o socket Docker e, se necessário, instale/adicione o cliente docker na imagem n8n usada em produção:

```yaml
n8n:
  volumes:
    - ./canaldecortes/n8n/data:/home/node/.n8n
    - /var/run/docker.sock:/var/run/docker.sock
```

Se você não quiser expor o socket Docker ao n8n, deixe o daemon `clip-processor` rodando com APScheduler e use o n8n apenas para monitoramento/notificações.

## Fluxo do pipeline principal

```
Cron 6h
  → docker exec clip-processor python -m src.pipeline_runner
    → poll_all_channels() [RSS + AI + render]
    → publish_pending_clips() [upload YouTube]
  → Retry automático no nó de execução
  → Se ERRO depois dos retries: notifica Telegram com detalhes
  → Se publicou: notifica Telegram com métricas
```

## Primeiro uso recomendado

1. Configure `YOUTUBE_PRIVACY_STATUS=private` no `.env` do clip-processor
2. Configure `MAX_UPLOADS_PER_DAY=1`
3. Importe e ative `canaldecortes-pipeline.json`
4. Execute manualmente uma vez (botão "Execute Workflow")
5. Verifique no YouTube Studio se o vídeo privado apareceu
6. Se OK: mude `YOUTUBE_PRIVACY_STATUS=public` e `MAX_UPLOADS_PER_DAY=2`

## Retry e resiliência

O nó `Executar Pipeline` está configurado com retry automático:

- `retryOnFail: true`
- `maxTries: 3`
- `waitBetweenTries: 900000` (15 minutos)

Mesmo quando um ciclo falha, o próximo agendamento de 6 horas tenta novamente. Para retry imediato, execute o workflow manualmente no N8N.
