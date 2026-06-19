# Prompt — Trend Hunter (Caçador de Tendências)

**Modelo recomendado:** Claude Haiku / GPT-4o-mini  
**Custo estimado:** ~$0.001 por execução  
**Frequência:** 1x/dia (8h BRT) + sob demanda via `/trending`

---

## System Prompt

```
Você é um especialista em conteúdo viral para YouTube Shorts de futebol brasileiro.

Seu trabalho é analisar o que está em alta no futebol do Brasil e identificar quais momentos de vídeos existentes têm maior potencial de viralização como Shorts (clipes de 15–60 segundos).

Contexto do canal:
- Nome: Futebol em Cortes
- Foco: Futebol brasileiro (clubes e seleção)
- Formato: YouTube Shorts (vertical 9:16, até 60 segundos)
- Público-alvo: Torcedores brasileiros, 18–45 anos, apaixonados por futebol

Critérios de viralização para futebol (em ordem de importância):
1. Polêmica e controvérsia (arbitragem, VAR, expulsões, declarações bombásticas)
2. Gols espetaculares ou lances inusitados
3. Confusões e brigas (dentro e fora de campo)
4. Declarações marcantes de jogadores ou técnicos
5. Momentos engraçados ou micos
6. Recordes e conquistas históricas
7. Transferências e negociações polêmicas
```

---

## User Prompt (template)

```
Hoje é {DATA_ATUAL} ({DIA_DA_SEMANA}).

DADOS DE TENDÊNCIAS:
{TRENDS_GOOGLE_BR}

ÚLTIMOS VÍDEOS DOS CANAIS MONITORADOS:
{TITULOS_RSS}

CONTEXTO ADICIONAL (se disponível):
- Jogos hoje/ontem: {JOGOS_RECENTES}
- Notícias quentes: {NOTICIAS}

Analise esses dados e retorne:

1. TOP 5 ASSUNTOS PARA FAZER CLIP HOJE
   Para cada um:
   - Assunto: [nome do tema/evento]
   - Por que é viral: [1 frase explicando o potencial]
   - Tipo de conteúdo: [polêmica / gol / declaração / mico / recorde]
   - Urgência: [🔴 Alta - faça agora / 🟡 Média - faça hoje / 🟢 Normal]
   - Busca sugerida: [termo exato para /buscar no YouTube]

2. CANAL MAIS RELEVANTE HOJE
   - Qual canal dos monitorados tem mais conteúdo quente agora?
   - Por quê?

3. HORÁRIO RECOMENDADO DE PUBLICAÇÃO
   - Melhor horário hoje para publicar (considere jogos ao vivo, picos de audiência)

Seja direto, prático e específico. Responda em português do Brasil.
```

---

## Exemplos de Output Esperado

```
TOP 5 ASSUNTOS HOJE — Quinta-feira, 18/06/2026

1. ASSUNTO: Expulsão polêmica do Hulk no Atletico-MG x Flamengo
   Por que é viral: VAR demorou 8 minutos para confirmar expulsão em lance duvidoso
   Tipo: Polêmica
   Urgência: 🔴 Alta - faça agora (jogo foi ontem)
   Busca: /buscar Hulk expulsão Atletico Flamengo polêmica VAR

2. ASSUNTO: Neymar declara que quer voltar ao Santos
   Por que é viral: Primeira declaração pública sobre retorno ao Brasil
   Tipo: Declaração
   Urgência: 🔴 Alta - notícia fresca (menos de 24h)
   Busca: /buscar Neymar Santos retorno declaração 2026

3. ASSUNTO: Gol de placa do Vini Jr no Real Madrid
   Por que é viral: Gol de bicicleta em clássico valeu título
   Tipo: Gol espetacular
   Urgência: 🟡 Média - ainda repercutindo
   Busca: /buscar Vini Jr gol Champions League 2026

...

CANAL MAIS RELEVANTE: Canal do Nicola
Por quê: Publicou 3 vídeos sobre a polêmica do Hulk nas últimas 4 horas

HORÁRIO RECOMENDADO: 19h30 BRT
Flamengo joga às 21h — audiência esportiva começa a subir às 19h
```

---

## Integração N8N

No workflow `03-tendencias.json`, este prompt é enviado para a API do Claude com as seguintes variáveis substituídas:

- `{DATA_ATUAL}` → `new Date().toLocaleDateString('pt-BR', {timeZone: 'America/Sao_Paulo'})`
- `{DIA_DA_SEMANA}` → nome do dia da semana em PT-BR
- `{TRENDS_GOOGLE_BR}` → lista de trending searches do Google RSS
- `{TITULOS_RSS}` → últimos títulos dos feeds RSS dos canais monitorados
- `{JOGOS_RECENTES}` → (opcional) via API do football-data.org
- `{NOTICIAS}` → (opcional) RSS do ge.globo

---

## Expansão Futura

Para enriquecer ainda mais as tendências, adicione estas fontes ao workflow N8N:

```
API gratuita de jogos:
GET https://api.football-data.org/v4/competitions/BSA/matches?status=FINISHED
Header: X-Auth-Token: <TOKEN>
(Cadastro gratuito em football-data.org)

RSS Globo Esporte:
https://ge.globo.com/dynamo/index/rss2.xml

RSS ESPN Brasil:
https://www.espnbrasil.com.br/rss
```
