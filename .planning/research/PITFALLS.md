# Pitfalls Research: Automated YouTube Clips Channel

## Critical Pitfalls (Matam o Projeto)

### 1. Copyright Strike por Conteúdo Não-Fair Use
- **Risco:** Canal removido permanentemente após 3 strikes
- **Contexto:** Cortes de podcasts/streams são geralmente fair use SE você adiciona valor (comentário, análise, contexto). Cortar e republicar sem modificação é mais arriscado.
- **Sinais de alerta:** Notificações de Content ID nas primeiras semanas
- **Prevenção:**
  - Priorizar canais que já autorizam cortes (muitos podcasters incentivam)
  - Adicionar na descrição: "Corte do canal [NOME] - Siga o original: [link]"
  - Manter clips entre 60s-3min (não republicar conteúdo completo)
  - Evitar cortar canais de TV aberta, ligas esportivas oficiais (direitos caríssimos)
  - Testar com canais que têm licença Creative Commons primeiro
- **Fase:** Fase 5 (antes de publicar qualquer coisa)

### 2. Suspensão de Canal por "Conteúdo Spam"
- **Risco:** YouTube pode suspender canais que postam muita frequência sem engajamento real
- **Sinais de alerta:** Strike de "conteúdo enganoso ou spam" nas primeiras semanas
- **Prevenção:**
  - Começar com 1-2 uploads/dia, não 6
  - Qualidade > quantidade: usar virality_score para filtrar clips abaixo de um threshold
  - Intervalos naturais entre uploads (não todo dia exatamente no mesmo horário)
  - Preencher completamente perfil do canal antes de postar
- **Fase:** Fase 5

### 3. Revogar Acesso OAuth do YouTube
- **Risco:** Google pode revogar tokens OAuth se detectar comportamento automatizado suspeito
- **Sinais de alerta:** Erros 401 no upload API
- **Prevenção:**
  - Implementar refresh token automático
  - Não exceder quotas (monitorar uso diário)
  - Não fazer uploads em sequência rápida (adicionar delay de 10-15min entre uploads)
  - Manter app OAuth em modo "testing" para conta pessoal (sem precisar de verificação Google)
- **Fase:** Fase 5

## Operational Pitfalls (Degradam Qualidade)

### 4. Clips de Baixa Qualidade por Prompt Mal Calibrado
- **Risco:** IA seleciona momentos chatos/irrelevantes; canal não cresce
- **Sinais de alerta:** CTR < 2%, watch time < 30% do clip
- **Prevenção:**
  - Fazer prompt engineering específico para futebol ("identifique: discordâncias acaloradas, revelações exclusivas, opiniões polêmicas, humor")
  - Incluir exemplos no prompt (few-shot) com o tipo de conteúdo que viraliza no nicho
  - Implementar score mínimo de viralidade (não cortar clips com score < 7/10)
  - Revisar manualmente os primeiros 20 clips para calibrar o prompt
- **Fase:** Fase 3

### 5. Transcrição com Baixa Precisão em Português
- **Risco:** Claude recebe texto errado → seleciona momentos errados
- **Sinais de alerta:** Legendas com erros visíveis, clips cortados no lugar errado
- **Prevenção:**
  - Usar modelo `small` do Whisper (melhor que `tiny` para PT-BR)
  - Passar `language="pt"` explicitamente para o Whisper
  - Aceitar gírias e sotaques esportivos: "raiz", "pressão", "mala", etc.
  - Validar primeiros transcritos manualmente
- **Fase:** Fase 3

### 6. Reprocessamento de Vídeos Já Publicados
- **Risco:** Conteúdo duplicado = penalidade do algoritmo + desperdício de cota
- **Prevenção:**
  - UNIQUE constraint em `youtube_video_id` no MySQL
  - Redis SET para deduplicação rápida antes de qualquer processamento
  - Nunca deletar registros de `source_videos` (apenas marcar como processed)
- **Fase:** Fase 2

### 7. Formato Errado para YouTube Shorts
- **Risco:** Vídeos não aparecem como Shorts (sem tráfego orgânico de Shorts)
- **Prevenção:**
  - Duração: máximo 60 segundos para Shorts (vídeos mais longos vão para feed normal)
  - Aspect ratio: 9:16 (1080x1920)
  - FFmpeg resize: `scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920`
  - Incluir `#Shorts` no título ou descrição
- **Fase:** Fase 4

## Technical Pitfalls (Quebram o Pipeline)

### 8. Espaço em Disco Esgotado
- **Risco:** Vídeos de 1h em 1080p ocupam 3-8GB cada; sem limpeza automática, disco enche rápido
- **Prevenção:**
  - Deletar vídeo bruto imediatamente após processamento bem-sucedido
  - Monitorar espaço disponível antes de cada download (n8n check)
  - Baixar em 720p em vez de 1080p (economia de 50% de espaço; qualidade suficiente para cortes)
  - Alertar via n8n quando disco < 10GB livres
- **Fase:** Fase 2

### 9. Whisper Timeout em Vídeos Longos
- **Risco:** Transcrições de 3h+ podem demorar 30-60min no CPU; n8n timeout
- **Prevenção:**
  - Configurar timeout generoso no n8n (ex: 3600s)
  - Processar somente áudio (extrair com FFmpeg antes de enviar ao Whisper — muito mais rápido)
  - Limitar a vídeos de até 2h de fonte (configurar no canal-fonte)
  - Processar em chunks de 30min se necessário
- **Fase:** Fase 3

### 10. YouTube Rate Limiting no Download
- **Risco:** yt-dlp bloqueado por IP após muitos downloads
- **Prevenção:**
  - Adicionar delay entre downloads (60-120s)
  - Usar cookies autenticados do YouTube (reduz chance de bloqueio)
  - Limitar a 10-15 downloads/dia por canal-fonte
  - Implementar retry com backoff exponencial
- **Fase:** Fase 2

### 11. Claude API Context Window Excedida
- **Risco:** Transcrições longas (3h de podcast) excedem o contexto do modelo
- **Prevenção:**
  - Chunkar transcrição em blocos de 30min, processar cada um separadamente
  - Usar modelo com contexto grande (claude-haiku tem 200k tokens — suficiente para ~8h de transcrição)
  - Resumir/comprimir transcrição antes de enviar se necessário
- **Fase:** Fase 3

## Monetization Pitfalls (Atrasam a Receita)

### 12. Canal Não Atingir Critérios de Monetização
- **Risco:** 1k subs + 4k horas pode demorar 6-12 meses sem estratégia
- **Prevenção:**
  - Postar consistentemente (1-2 clips/dia, todo dia)
  - Focar nos primeiros 30 dias nos canais-fonte com maior audiência (mais chance de viral)
  - Usar Shorts E vídeos normais (Shorts paga menos por view mas acelera crescimento de subs)
  - Adicionar cards e end screens para aumentar watch time
  - Nome do canal + banner profissional antes de postar (first impression)
- **Fase:** Fase 5 + ongoing

### 13. Demonetização por Conteúdo "Sensível"
- **Risco:** Conteúdo de futebol raramente tem esse problema, mas palavrões e violência podem causar limited ads
- **Prevenção:**
  - Não cortar cenas de brigas físicas
  - Palavrões: adicionar bip automático ou evitar clips com excesso
  - Marcar conteúdo adequadamente na hora do upload
- **Fase:** Fase 5

### 14. Não Pedir Verificação de Canal Cedo
- **Risco:** Sem verificação, não pode fazer upload de vídeos > 15min, sem thumbnail customizada
- **Prevenção:**
  - Verificar conta do Google/YouTube com número de telefone no dia 1
  - Preencher todas as informações do canal (sobre, links, localização)
- **Fase:** Fase 1 (antes de qualquer upload)

## Prevention Checklist por Fase

| Fase | Ação Preventiva |
|------|----------------|
| Fase 1 | Verificar conta YouTube, criar canal, preencher perfil completo |
| Fase 2 | Implementar deduplicação, delay entre downloads, monitor de espaço em disco |
| Fase 3 | Passar `language="pt"` no Whisper, revisar primeiros 10 transcritos, calibrar prompt Claude |
| Fase 4 | Validar output FFmpeg (aspect ratio 9:16, duração ≤60s para Shorts) |
| Fase 5 | Começar com 1 upload/dia, incluir crédito ao canal original, testar OAuth refresh |
| Ongoing | Monitorar copyright strikes, revisar analytics semanalmente, ajustar threshold de virality_score |
