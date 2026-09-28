# Estratégia de Conteúdo, Benchmark e YouTube Analytics

Este documento consolida a metodologia estratégica, as métricas de diagnóstico do **YouTube Studio**, o sistema de **Benchmark de Canais Concorrentes** e a calibração de **Cortes Virais de Política (MBL / Missão)** integrados ao projeto **Canal de Cortes**.

Última atualização: **Setembro/2026**

---

## 1. Como Diagnosticar e Alimentar a IA com Métricas do YouTube Studio

O algoritmo de recomendação do YouTube (tanto para **Shorts** quanto para **Vídeos Longos**) decide o alcance baseado em 4 métricas principais obtidas em `studio.youtube.com` > *Estatísticas (Analytics)*:

| Métrica | O que mede | Benchmark de Sucesso | Impacto no Algoritmo |
|---|---|---|---|
| **Taxa de Cliques (CTR %)** | Atratividade da Thumbnail e Título | **5% a 10%+** | Se for menor que 4%, o YouTube para de gerar impressões externas. |
| **% de Retenção Média** | Capacidade de manter o usuário assistindo | **Longos:** 40% a 55%+<br>**Shorts:** 75% a 90%+ | Retenção alta faz o vídeo furar a bolha dos inscritos e ir para a aba Inicial. |
| **Assistiram vs. Pularam (Swiped Away)** | *Exclusivo de Shorts*: % que não passou reto nos 3s | **70% a 85%+** escolheram assistir | Se mais de 30% pularem nos primeiros 3 segundos, o Short estagna. |
| **Velocidade nas Primeiras 24h-48h** | Volume de consumo inicial | Tração sustentada pós-postagem | Define se o vídeo entra no loop de recomendação contínua. |

### Ferramenta de Diagnóstico no Painel (`/painel/assistente`)
No menu **Assistente IA**, o operador conta com o modal **`📊 Diagnóstico YouTube Studio`**:
1. Preenche o formato (*Shorts* ou *Longo*), nicho (*Política*, *Futebol*, *Podcast*), views, retenção % e CTR %.
2. Descreve o problema observado (ex: *"O vídeo parou de receber impressões após as primeiras 24 horas"*).
3. A IA (LLaMA 3.3 70B via Groq) processa a relação entre CTR e Retenção para apontar se o gargalo foi:
   - **Capa/Título fraco** (Retenção alta + CTR baixo).
   - **Gancho inicial fraco** (CTR alto + Retenção despencando nos primeiros 5 segundos).
   - **Perda de ritmo/narrativa** (Queda acentuada no meio do vídeo).

---

## 2. Benchmark de Concorrentes & Canais de Referência

O operador pode monitorar canais de inspiração e concorrência na tela de [Canais Fonte](file:///Users/alessandrobm1/develop/server/wordpress/canaldecortes/painel/resources/js/pages/SourceChannels.tsx):

- **Cadastro Simples:** Suporta `@handle` (ex: `@mblivre`, `@cortesdomissao`, `@kimkataguiri`), URLs completas do canal ou Channel ID (`UC...`).
- **Nicho Configurável:** Seleção de nicho (*Futebol*, *Política*, *Podcast*, ou novo nicho customizado).
- **Ação `🧠 Analisar IA`:** Em cada canal cadastrado, o botão dispara uma análise do LLaMA 3.3 que destrincha:
  1. Fórmulas dos títulos mais clicados do canal.
  2. Como o canal estrutura o Gancho (Hook) nos primeiros 3 segundos.
  3. Frequência e horários de publicação ideais no Brasil.
  4. Padrões de edição, legendas e enquadramento para modelar.

---

## 3. Modelo dos Cortes Virais de Política (MBL / Missão)

O motor de inteligência artificial em `clip-processor/src/selector.py` foi calibrado especificamente com o `POLITICA_SYSTEM_PROMPT` para selecionar cortes baseados na fórmula dos canais de maior engajamento político:

1. **Gancho Inicial Agressivo (0 a 5 segundos):**
   - O clipe inicia diretamente na pergunta provocativa, na declaração chocante ou no início de uma refutação contundente.
   - **Proibido:** saudações, vinhetas, introduções ou agradecimentos.
2. **Conflito & Refutação ("Jantada"):**
   - Priorização de trechos onde narrativas são desmascaradas, contradições são expostas e argumentos são rebatidos com firmeza e dados.
3. **Raciocínio Fechado & Término no Clímax:**
   - O corte encerra imediatamente após o argumento decisivo (sem enrolação pós-desfecho), estimulando replay e engajamento nos comentários.
4. **Enquadramento 9:16 Otimizado:**
   - Formato vertical com fundo dinâmico desfocado, legendas destacadas em alto contraste e espaço superior para manchete.

---

## 4. Monetização e RPM Médio no YouTube Brasil

Estimativas de mercado integradas no painel em [Links Úteis](file:///Users/alessandrobm1/develop/server/wordpress/canaldecortes/painel/resources/js/pages/UsefulLinks.tsx):

- **YouTube Shorts:** RPM de **\$0.02 a \$0.06** por 1.000 visualizações (R\$ 0,10 a R\$ 0,35).
  - *Função principal:* Crescimento acelerado de inscritos e volume de tráfego.
- **Vídeos Longos (7 a 20 minutos):** RPM de **\$1.50 a \$3.50+** por 1.000 visualizações (R\$ 8,50 a R\$ 20,00+).
  - *Função principal:* Geração de receita publicitária consistente e retenção da comunidade.
- **Google AdSense:** Uma única conta AdSense (ex: `alessandrobm1988@gmail.com`) pode receber o faturamento consolidado de todos os canais de destino gerenciados.
