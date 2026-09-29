## Operação por canal e agendamento nativo

- A janela de busca passa a ser escolhida por canal-fonte (3 ou 1500 dias), com `FRESHNESS_DAYS=1500` como fallback. Quando `published_at` falta, a fila usa `created_at`.
- A limpeza automática libera arquivos locais e preserva no banco os vídeos, transcrições e vínculos com clips para pesquisa posterior.
- Shorts usam 30–45 segundos por padrão, com teto configurável para testes mais longos. O render mantém qualidade máxima por padrão; modos mais rápidos são opcionais.
- A biblioteca de mídia e as trilhas ficam limitadas ao canal de destino; a trilha é aplicada apenas a vídeos longos.
- O agendamento padrão prevê três vídeos longos por dia, separados por oito horas, e Shorts nas janelas de pico. Workers também podem ser instalados no Linux/macOS via cron, sem Docker.
- Groq com `openai/gpt-oss-20b` passa a ser o padrão de IA; outro provider só é usado quando configurado explicitamente.
