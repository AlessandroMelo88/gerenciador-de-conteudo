# Features Research: Automated YouTube Clips Channel

## Table Stakes (Must Have)

Sem esses, o sistema não funciona:

| Feature | Descrição | Complexidade |
|---------|-----------|--------------|
| Monitor de canais | Verificar periodicamente se há novos vídeos em canais configurados (YouTube RSS ou API) | Simples |
| Download automático | Baixar vídeo completo via yt-dlp quando novo conteúdo detectado | Simples |
| Transcrição automática | Converter áudio em texto com timestamps usando Whisper | Média |
| Seleção de momentos por IA | Analisar transcrição e identificar segmentos de alto impacto (polêmica, humor, informação-chave) | Média |
| Corte de vídeo | Extrair segmentos específicos do vídeo com FFmpeg | Simples |
| Legendas queimadas no vídeo | Burn subtitles para acessibilidade e engajamento (vídeos sem legenda perdem ~80% de views mobile) | Média |
| Metadados gerados por IA | Título, descrição e tags otimizados para SEO do YouTube | Simples |
| Upload automático para YouTube | Publicar clips via YouTube Data API com título/descrição/thumbnail | Média |
| Deduplicação | Não reprocessar vídeos já processados; não publicar conteúdo duplicado | Simples |
| Log de status | Rastrear status de cada job (pending/processing/published/failed) | Simples |

## Differentiators (Competitive Advantage)

Aumentam qualidade ou eficiência sem ser bloqueadores:

| Feature | Descrição | Complexidade | Valor |
|---------|-----------|--------------|-------|
| Thumbnail automática | Extrair frame mais impactante do clip ou gerar com overlay de texto | Média | Alto — afeta CTR diretamente |
| Score de viralidade | IA pontua cada momento antes de cortar (evita desperdício de API quota com clips fracos) | Média | Alto |
| Detecção de momentos por áudio | Identificar picos de volume/emoção além do texto | Alta | Médio |
| Agendamento inteligente | Publicar nos horários de maior audiência do nicho (horário de pico no Brasil: 19-22h) | Simples | Médio |
| Múltiplas durações | Gerar versão 60s (Shorts) e versão 3-5min (vídeo normal) do mesmo momento | Média | Médio |
| Dashboard de métricas | Ver views/likes/subs por clip para feedback loop | Média | Médio |
| Notificação de novo canal-fonte | Alertar quando um canal novo vira fonte frequente de viral | Simples | Baixo |
| A/B de thumbnails | Testar dois títulos/thumbnails e manter o melhor | Alta | Médio |

## Anti-Features (Excluir do v1)

| Feature | Motivo |
|---------|--------|
| Publicação em TikTok/Instagram simultânea | TikTok API é restrita e complexa; aumenta escopo desnecessariamente para v1 |
| Edição manual de clips | Contradiz o objetivo de automação total |
| Geração de vídeo com IA (avatares, voz sintética) | Complexidade alta, custo elevado, foge do modelo de canal de cortes |
| Moderação de comentários | Não impacta crescimento em v1 |
| CMS/painel web para o espectador | O canal é no YouTube; não precisamos de site para o público |
| Multi-conta YouTube | Uma conta por vez para v1; gerenciar OAuth de múltiplas contas é complexo |
| Análise de concorrentes | Útil mais tarde, não é bloqueador |
| Transcrição em múltiplos idiomas | Foco em PT-BR primeiro |

## Feature Dependency Map

```
Monitor de canais
    ↓
Download automático
    ↓
Transcrição automática
    ↓ ↘
Seleção de momentos   Score de viralidade (differentiator)
    ↓
Corte de vídeo
    ↓ ↘
Legendas queimadas    Thumbnail automática (differentiator)
    ↓
Metadados gerados por IA
    ↓
Upload automático
    ↓
Log de status / Deduplicação (transversal)
```

## Complexity Estimates

| Feature | Complexidade | Tempo Estimado |
|---------|--------------|----------------|
| Monitor de canais (RSS) | Simples | 2-4h |
| Download yt-dlp | Simples | 1-2h |
| Transcrição Whisper | Média | 4-8h (setup Docker + integração) |
| Seleção Claude API | Média | 4-8h (prompt engineering + parsing) |
| Corte FFmpeg | Simples | 2-4h |
| Legendas burn | Média | 4-6h (formatação SRT + estilo) |
| Thumbnail automática | Média | 4-6h |
| Metadados IA | Simples | 2h |
| Upload YouTube API | Média | 4-8h (OAuth + quota management) |
| n8n workflow completo | Média | 8-16h (conectar tudo) |
| Deduplicação + logs | Simples | 2-4h |
