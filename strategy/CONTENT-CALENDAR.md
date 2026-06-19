# Calendário de Conteúdo — Futebol em Cortes

## Princípios de Publicação

### Horários de pico para futebol BR
- **19h–22h BRT:** Pico máximo. Torcedores chegam em casa, assistem jogos.
- **12h–13h BRT:** Almoço — segundo pico, especialmente em dias de jogo.
- **7h–8h BRT:** Manhã — torcedores buscam resultado de jogos do dia anterior.

### Regra do timing com eventos ao vivo
- Clip de jogo de **ontem à noite** → publicar às **7h–8h** do dia seguinte
- Clip de **jogo ao vivo** → publicar nos **30 minutos** após o apito final
- Clip de **declaração/entrevista** → publicar em até **4 horas** (tendência esquenta e esfria rápido)
- Clip de **polêmica perene** (arbitragem, confusão) → publicar às **19h** sempre

---

## Calendário Tipo — Rodada do Brasileirão

O Brasileirão tem rodadas semanais (geralmente quarta, sábado e domingo). Use este template:

### Segunda-feira (pós-rodada)
- **7h:** Clip do gol mais bonito do final de semana
- **12h:** Clip da polêmica mais comentada (VAR, expulsão)
- **19h:** Clip da declaração mais quente do técnico/jogador

### Terça-feira (semana normal)
- **19h:** Clip de treino + bastidores (buscar em canais oficiais dos clubes)
- **21h:** Clip de análise pré-jogo (entrevistas coletivas)

### Quarta-feira (dia de jogo Copa/Libertadores)
- **12h:** Clip histórico do clube que joga hoje
- **19h30:** Publicar nos 30min após o apito final

### Quinta-feira (pós-jogo semana)
- **7h:** Clip da grande jogada do jogo de ontem
- **19h:** Clip da reação do técnico/torcida

### Sexta-feira (pré-fim de semana)
- **12h:** "Top 3 momentos da semana" (compilação)
- **19h:** Clip de bastidores/treino preparatório

### Sábado (dia de jogo)
- **12h:** Clip de confronto histórico entre os times que jogam hoje
- Após jogo: Clip do lance mais marcante

### Domingo (dia de jogo)
- **12h:** Clip de polêmica/resultado da semana
- Após jogo: Clip do gol ou lance do jogo

---

## Calendário Tipo — Semana de Copa do Brasil/Libertadores

Semanas com Copa do Brasil ou Libertadores têm **audiência 30–50% maior** para clips de futebol BR.

Estratégia:
- Dobre a frequência de publicação nas 24h pós-jogo
- Foque nos clubes brasileiros na Libertadores (maior audiência global)
- Use hashtags da competição: #Libertadores #CopaDoBrasil

---

## Tipos de Conteúdo por Performance

Baseado no comportamento geral de canais de clips esportivos, ordenados por performance:

| Tipo | CTR Esperado | Retenção | Compartilhamento |
|------|-------------|----------|-----------------|
| 1. Polêmica/VAR/Expulsão | ⭐⭐⭐⭐⭐ | Alta | Muito alto |
| 2. Gol espetacular | ⭐⭐⭐⭐⭐ | Alta | Alto |
| 3. Declaração bombástica | ⭐⭐⭐⭐ | Média | Alto |
| 4. Confusão/Briga | ⭐⭐⭐⭐ | Alta | Muito alto |
| 5. Mico/Erro bizarro | ⭐⭐⭐⭐ | Alta | Alto |
| 6. Recorde/Conquista | ⭐⭐⭐ | Média | Médio |
| 7. Treino/Bastidores | ⭐⭐⭐ | Baixa | Baixo |
| 8. Entrevista comum | ⭐⭐ | Baixa | Baixo |

**Regra prática:** Priorize sempre tipos 1–5. Só publique tipo 7–8 quando não tiver nada melhor.

---

## Templates de Título por Tipo

### Polêmica (máximo impacto)
- `[NOME] EXPULSO em lance que PAROU o estádio | [Time] x [Time]`
- `VAR demorou [X] minutos e a decisão foi ESSA | Polêmica no [Campeonato]`
- `O árbitro que fez [Time] PERDER o título | Você vai se INDIGNAR`

### Gol espetacular
- `[JOGADOR] marcou o gol da [Competição] que você vai assistir 100 vezes`
- `Talvez o gol mais bonito de [ANO] | [JOGADOR] para a [Competição]`
- `[X] metros! O golaço que EXPLODIU a internet`

### Declaração polêmica
- `[NOME] disse o que NINGUÉM esperava sobre [assunto]`
- `A declaração de [NOME] que está DIVIDINDO opiniões`
- `[NOME] REVELOU o que aconteceu nos bastidores`

### Confusão/Briga
- `O que aconteceu entre [Time1] e [Time2] que o campo foi LIBERADO tarde`
- `A confusão BIZARRA que você não viu na TV`
- `[X] expulsões em [X] minutos | O jogo que virou BAGUNÇA`

### Mico/Erro
- `O mico de [NOME] que os torcedores não vão esquecer cedo`
- `Esse erro de [NOME] foi tão grave que [CONSEQUÊNCIA]`
- `O golaço... que foi ANULADO de forma ABSURDA`

---

## Integração com o Pipeline Automatizado

### Como o calendário se conecta com o sistema

```
Google Trends RSS (8h BRT)
         ↓
Agente de Tendências (Claude Haiku)
         ↓
Sugestão de temas via Telegram
         ↓
Você decide: /buscar <tema> ou aguarda RSS automático
         ↓
clip-processor baixa, transcreve, seleciona, renderiza
         ↓
Notificação Telegram às 18h BRT: "X clips prontos"
         ↓
Você revisa e publica às 19h no YouTube Studio
```

### Automação do calendário (fase futura)

Quando o Phase 5 estiver completo:
1. N8N verifica tipo de dia (rodada, Copa, normal)
2. Ajusta horário de upload conforme calendário
3. Publica automaticamente sem intervenção manual
4. Envia relatório diário via Telegram às 22h

---

## Acompanhamento Semanal

Toda segunda-feira, revise estes dados no YouTube Studio:

```
Semana: _______________

Clips publicados: ___
Views totais: ___
Inscritos ganhos: ___
Clip mais visto: _______________ (_____ views)
CTR médio: ___%
Retenção média: ___%

Melhor tipo de conteúdo: _______________
Pior tipo de conteúdo: _______________
Horário que mais performou: ___h BRT

Ações para a próxima semana:
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________
```

---

## Datas Importantes do Futebol BR em 2026

Marque esses períodos para **dobrar** a produção de clips:

- **Copa do Mundo 2026** (junho-julho): O maior evento. Prepare clips de brasileiros atuando
- **Brasileirão Série A**: Março–Dezembro (rodadas todas as semanas)
- **Libertadores da América**: Março–Novembro (fase de grupos a final)
- **Copa do Brasil**: Março–Setembro
- **Recesso olímpico** (agosto): Menor competição, audiência cai — reduza frequência
- **Clássicos estaduais** (fevereiro): Fla-Flu, Derby, Choque-Rei — muito cliques
- **Janeiro (mercado de transferências)**: Foco em declarações e negociações
