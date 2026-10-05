# SPEC-003 — Bot de descoberta e acompanhamento de nicho no YouTube

**Status:** rascunho — não implementado
**Data:** 05/10/2026
**Onde viveria o código:** `niche-scout/` (worker local em Python, irmão do `affiliate-worker`)
**Não toca:** `clip-processor/`, pipeline de clipes, banco de produção.

## 1. Problema e decisão

Hoje a escolha de nicho para canal próprio ("dark", conteúdo gerado por nós, sem recorte de terceiro)
é feita por palpite: olha-se o YouTube na mão, acha-se que "tal assunto está pegando" e abre-se canal.
Não há número nem registro, então erro de nicho só aparece depois de semanas de produção perdida.

**Decisão:** construir um worker local que, a cada rodada, mede um conjunto fixo de nichos candidatos com
dados públicos do YouTube e do Google Trends, calcula sinais comparáveis entre nichos, e devolve
(a) um ranking de nichos e (b) por nicho uma lista de pautas candidatas. O bot **não** publica, não
produz vídeo e não altera o pipeline de clipes — ele só informa a decisão humana de abrir canal.

A primeira versão **não** tem tela no painel. Justificativa em §5.4.

## 2. Fora de escopo, e por quê

- **Raspagem de área autenticada da Hotmart, Monetizze ou Eduzz** (ranking de mais vendidos, blueprint,
  temperatura de produto). Os Termos Gerais de Uso da Hotmart vedam expressamente reproduzir, copiar,
  baixar ou redistribuir material da plataforma, e a Hotmart pode aplicar medidas "a qualquer tempo, com
  ou sem aviso prévio". O risco é bloqueio da conta de afiliado **e das comissões já acumuladas** — custo
  desproporcional para um sinal que o YouTube + Trends já aproximam. Dado de oferta continua entrando à
  mão pelo CSV do `affiliate-worker`.
- Raspagem do HTML do YouTube. Existe API oficial; scraping aqui troca dado estável por fragilidade e
  violação de ToS sem ganho.
- Decidir **sozinho** em qual nicho abrir canal. A saída é ranking, não comando.
- Produção de roteiro, thumbnail ou áudio; e acompanhar os canais **nossos** (isso é a SPEC-001).

## 3. Fontes de dados

### 3.1 YouTube Data API v3 (fonte principal)

Cota padrão por projeto no Google Cloud: **10.000 unidades por dia**, com reset à meia-noite do
Pacífico e **sem acúmulo**. Custos relevantes:

| Chamada | Custo | Uso aqui |
|---|---|---|
| `search.list` | **100 unidades** | descobrir vídeos de um termo (`q`, `publishedAfter`, `order=viewCount` ou `date`, `regionCode=BR`, `relevanceLanguage=pt`) |
| `videos.list` | 1 unidade | `statistics` (viewCount, likeCount, commentCount) e `contentDetails` (duração) — aceita **até 50 ids por chamada** |
| `channels.list` | 1 unidade | `statistics` (subscriberCount, videoCount, viewCount) e `snippet.publishedAt` (data de criação) — também até 50 ids |

Consequência de desenho: `search.list` é 100× mais caro que as outras duas e é o único gargalo real.
Toda a cota diária equivale a **100 buscas**. Portanto:

- `search.list` é a **única** chamada com orçamento controlado; `videos.list` e `channels.list` são
  praticamente grátis e devem ser usadas em lote de 50 para hidratar tudo que a busca retornou.
- Orçamento de uma rodada completa, com 8 nichos × 3 termos = 24 buscas:
  24 × 100 = 2.400 unidades de busca; ~24 unidades de `videos.list` (até 1.200 vídeos em lotes de 50);
  ~24 unidades de `channels.list`. **Total ≈ 2.450 unidades**, ou ~25% da cota gratuita diária.
  Cabe com folga para reexecução no mesmo dia.
- Não usar paginação de `search.list` (`pageToken`): cada página extra custa outras 100 unidades. Uma
  página de 50 resultados por termo é suficiente para medir mediana.
- Aumento de cota só por formulário de auditoria do YouTube, que não vale para este uso. **Não confirmei**
  nenhuma opção de compra de cota.

Chave: `YOUTUBE_API_KEY` (API key simples, sem OAuth — tudo é dado público). Fica no `.env` do worker,
fora do git: o repositório é público.

### 3.2 Google Trends (sinal de tendência)

**Não existe API oficial pública.** O Google anunciou uma *Google Trends API* em alpha em 24/07/2025,
com janela móvel de 5 anos e dado consistentemente escalado, mas o acesso é por candidatura, sem
endpoint self-serve, sem preço e sem tabela de cota publicada. **Não confirmei** disponibilidade nem
limites — tratar como indisponível até alguém da conta ser aceito no alpha.

Opção prática em Python: **`trendspyg`** (`pip install trendspyg`), biblioteca mantida que substituiu o
`pytrends` — este foi arquivado pelos mantenedores em abril de 2025 e não recebe mais correção quando o
Google muda a API interna. `trendspyg` expõe interesse ao longo do tempo com a propriedade de busca
trocada (`gprop`), incluindo **YouTube Search** — que é o recorte que interessa: interesse de busca
dentro do YouTube, não na web.

Riscos certos: é API interna do Google, não contratada — **429 Too Many Requests** aparece depois de
algumas dezenas de consultas seguidas, o bloqueio pode durar horas, e o endpoint pode quebrar sem aviso.

Mitigação obrigatória no desenho: Trends é **sinal opcional**. Uma consulta por termo por rodada, com
pausa de 5 a 10 s entre consultas, resultado em cache de disco por **7 dias**, e backoff exponencial em
429 com no máximo 3 tentativas. Falha após isso ⇒ `trend_ratio = null`, o peso da tendência é
redistribuído proporcionalmente entre os outros sinais, e o relatório marca o nicho como
`trend: indisponível`. O bot **nunca** aborta a rodada por causa do Trends.

### 3.3 VidIQ (citado, não usado pelo bot)

Plano pago a partir de ~US$ 7,50/mês. **Atalho de validação manual**: conferir à mão 2 ou 3 nichos do
topo antes de abrir canal. Não entra no código e nenhuma decisão do bot depende dele.

## 4. Sinais e fórmulas

Para cada nicho, o bot parte de 2 a 4 **termos** (definidos à mão em `niches.yml`) e de um conjunto
`V` de vídeos coletados (`search.list` com `publishedAfter = hoje − 90 dias`, `order=viewCount`) e seus
canais `C`.

Toda agregação usa **mediana**, não média: um vídeo viral de 8 milhões de views distorce a média e faz
nicho saturado parecer aberto.

| # | Sinal | Fórmula | Unidade |
|---|---|---|---|
| S1 | Velocidade de views | `v_i = viewCount_i / max(1, dias(hoje − publishedAt_i))`, e `S1 = mediana(v_i)` sobre `V` | views/dia |
| S2 | Idade mediana dos canais | `a_c = meses(hoje − channel.publishedAt_c)`, e `S2 = mediana(a_c)` sobre `C` (um canal conta uma vez, mesmo com vários vídeos no top) | meses |
| S3 | Razão views/inscritos | `r_i = viewCount_i / max(1, subscriberCount_{canal(i)})`, e `S3 = mediana(r_i)` | adimensional |
| S4 | Tendência do termo | `S4 = média(interesse das últimas 12 semanas) / média(interesse das 12 semanas anteriores)`, série semanal de 52 semanas do Trends com `gprop = youtube`; por nicho, média dos termos | razão |
| S5 | Volume de upload recente | `S5 = (nº de vídeos publicados nos últimos 30 dias pelos canais de C, dentro dos termos do nicho) / |C|` | vídeos/canal/mês |

Leitura de cada sinal:

- **S1 alto** = o assunto entrega views rápido. É o sinal mais direto de demanda.
- **S2 baixo** = canal novo está conseguindo ranquear ⇒ **nicho aberto**. S2 alto (ex.: mediana acima de
  60 meses) significa que só canal velho aparece ⇒ barreira de autoridade, nicho fechado para quem entra
  agora. Este é o sinal que o palpite humano mais erra.
- **S3 alto** (ex.: > 5) = o vídeo alcança muito além da base de inscritos ⇒ a recomendação está
  distribuindo o assunto, e não a audiência fiel do canal. Nicho bom para quem tem 0 inscrito.
- **S4**: `≥ 1,15` subindo, `0,85 – 1,15` estável, `< 0,85` caindo. Faixa deliberadamente larga: a série
  do Trends é relativa e ruidosa, e variação de 10% não é informação.
- **S5 alto** = concorrência produzindo muito ⇒ saturação; para competir é preciso volume igual.

### 4.1 Nota composta

Cada sinal é normalizado para 0–100 pelo **percentil dentro da rodada** (comparação entre os nichos
medidos, não contra escala absoluta inventada). S2 e S5 entram **invertidos** (menor é melhor).
S4 entra por faixa: subindo = 100, estável = 60, caindo = 20.

```
nota = 0,30·n(S1) + 0,25·inv(S2) + 0,20·n(S4) + 0,15·n(S3) + 0,10·inv(S5)
```

Justificativa dos pesos:

- **S1 = 0,30** — demanda medida é o único sinal que não é proxy de nada.
- **S2 = 0,25** — quase empatado com S1 porque é o que decide se *nós* conseguimos entrar; um nicho com
  demanda enorme e só canal de 10 anos no topo é inútil para canal novo.
- **S4 = 0,20** — tendência protege de entrar em assunto em queda, mas vem da fonte menos confiável
  (§3.2) e às vezes é `null`, então não pode pesar mais que os dois primeiros.
- **S3 = 0,15** — bom sinal, mas contaminado: canal pequeno com um vídeo viral infla a razão.
- **S5 = 0,10** — saturação só desempata; nicho com muita gente produzindo também é nicho com demanda.

> **Estes pesos são chute inicial.** Eles não foram calibrados com nenhum dado real deste projeto.
> Devem ser recalibrados depois de pelo menos 2 ciclos reais, comparando a nota prevista com o
> desempenho observado dos canais que de fato abrirmos (§8). Até lá, o ranking vale como ordem de
> investigação, não como veredito. Os pesos ficam em `niches.yml`, não no código.

### 4.2 Pautas candidatas

Cada vídeo coletado é uma pauta candidata, pontuada só por `v_i`, com dois cortes: descartar
`duration < 60 s` (Shorts de recorte, formato diferente) e agrupar títulos de similaridade alta
(normalizar, comparar por token; manter o de maior `v_i`), para o topo não virar 10 variações do mesmo
título. Saem as 10 melhores por nicho, com a idade do canal de origem ao lado — pauta que só canal velho
puxa é pauta ruim para nós, mesmo com views/dia alto.

## 5. Modelo de dados e saída

### 5.1 Entrada — `niches.yml` (versionado, sem segredo)

```yaml
pesos: { s1: 0.30, s2: 0.25, s4: 0.20, s3: 0.15, s5: 0.10 }
janela_dias: 90
nichos:
  - slug: financas-pessoais
    termos: ["como sair das dívidas", "investir pouco dinheiro"]
    idioma: pt
    regiao: BR
```

Campos `null` na saída são permitidos e significam "não medido" — nunca `0` no lugar de ausência.

### 5.2 Saída — `data/report-YYYY-MM-DD.json`

```json
{
  "gerado_em": "2026-10-05T12:00:00-03:00",
  "janela_dias": 90,
  "cota_gasta_unidades": 2451,
  "pesos": { "s1": 0.30, "s2": 0.25, "s4": 0.20, "s3": 0.15, "s5": 0.10 },
  "nichos": [
    {
      "slug": "financas-pessoais",
      "nota": 78.4,
      "sinais": {
        "s1_views_dia_mediana": 1840.0,
        "s2_idade_canal_meses_mediana": 14.0,
        "s3_views_por_inscrito_mediana": 6.2,
        "s4_trend_ratio": 1.31,
        "s4_trend_rotulo": "subindo",
        "s5_uploads_30d_por_canal": 3.1
      },
      "amostra": { "videos": 97, "canais": 54, "termos": 2 },
      "avisos": [],
      "pautas": [
        { "video_id": "xxxxxxxxxxx", "titulo": "...", "views_dia": 24100.0,
          "duracao_s": 742, "canal_idade_meses": 9, "canal_inscritos": 41000 }
      ]
    }
  ]
}
```

### 5.3 Saída legível — `data/report-YYYY-MM-DD.md`

Uma tabela, um nicho por linha (`nicho | nota | views/dia | idade canal | views/inscrito | tendência |
uploads/mês | avisos`), ordenada por nota; depois uma seção por nicho com as 10 pautas. É este arquivo
que se lê para decidir.

### 5.4 Painel: não, por enquanto

**Recomendação: só arquivo local na v1.** O bot roda no máximo uma vez por dia e a saída é lida por uma
pessoa, algumas vezes por mês, para uma decisão rara. Tela Inertia + migration + endpoint + token custa
~8 h e resolve um problema (compartilhar, historiar) que ninguém tem ainda; e os pesos vão mudar (§4.1),
levando o schema junto. O `affiliate-worker` virou tela porque a oferta precisa ser **aprovada e
publicada** pelo painel; aqui não há nada para aprovar.

Quando virar tela: depois de 2 ciclos reais, se a pergunta "como esse nicho estava há 3 meses?" aparecer
de verdade. O caminho será o do `affiliate-worker` — worker **empurra** por `POST /api/niches/reports`,
nunca o servidor chama o Mac; o JSON de §5.2 já é o corpo desse POST, de propósito.

## 6. CLI e fluxo de execução

Worker local em Python no Mac, padrão `affiliate-worker`: `.venv`, `.env` fora do git, `data/` no
`.gitignore`, uso por `.venv/bin/python -m niche_scout <comando>`.

| Comando | O que faz |
|---|---|
| `coletar [--nicho slug ...] [--dry-run]` | `search.list` + hidratação em lote; grava `data/cache/` e `data/raw-<data>.json`. Imprime a cota gasta. `--dry-run` mostra o plano de chamadas e a cota estimada **sem chamar a API** |
| `trends [--nicho slug ...] [--dry-run]` | série do Trends por termo (`gprop=youtube`) para `data/cache/trends/`; falha vira aviso, não erro |
| `ranquear [--pesos-de niches.yml]` | lê o cache, calcula S1–S5 e a nota, grava os dois relatórios de §5 |
| `pautas --nicho slug [--top 10]` | imprime as pautas de um nicho no terminal |
| `rodar [--dry-run]` | atalho: `coletar` → `trends` → `ranquear` |
| `cota` | unidades estimadas gastas hoje, lidas do log local de chamadas |

Fluxo de uma rodada: `rodar --dry-run` (conferir orçamento) → `rodar` → ler o `.md` → validar 2 ou 3
nichos do topo à mão (VidIQ, §3.3) → decidir.

Garantias de implementação:

- **Cache em disco antes de qualquer chamada.** Chave `(tipo, termo|id, janela, dia)`; TTL de 24 h para
  busca e estatística, 7 dias para Trends. `--sem-cache` existe e avisa quanto de cota vai custar.
- **Teto de cota.** `YOUTUBE_QUOTA_BUDGET` (padrão `5000`) é teto por dia contado localmente. Chamada que
  estouraria o teto não é feita: o comando para, diz quantos nichos ficaram de fora e sai com código 2
  (parcial). O relatório sai com os nichos que coube, marcados.
- **Retry com backoff** em 429 e 5xx: 3 tentativas, espera exponencial (2 s, 8 s, 32 s), respeitando
  `Retry-After` quando vier. Sem retry em 400, 401, 403 `quotaExceeded` (que não passa com espera) e 404.
- **Nenhum segredo em log**: a chave nunca é impressa, nem em URL de erro. Testes com HTTP simulado,
  sem rede real, como no `affiliate-worker`.

## 7. Limites conhecidos e modos de falha

| Situação | O que acontece | O que fazer |
|---|---|---|
| Cota estourada (`403 quotaExceeded`) | o comando para na hora, grava o que já coletou, sai com código 2 | esperar o reset (meia-noite do Pacífico) ou rodar menos nichos; o cache de 24 h evita repagar |
| Trends bloqueado (429 persistente) | `s4 = null`, peso de S4 redistribuído, nicho marcado `trend: indisponível` | rodar `trends` sozinho horas depois; a nota sem S4 ainda ordena |
| `trendspyg` quebra (Google muda o endpoint interno) | mesma degradação acima | sem plano B barato. Aceito: o bot vale 80% sem S4 |
| Termo ambíguo ("corte", "mbl", "flamengo") | a busca mistura assuntos, as medianas viram ruído e a nota mente | o bot imprime os 5 títulos mais frequentes por termo no relatório, para inspeção; termo ruim é corrigido à mão em `niches.yml`. Não há desambiguação automática |
| Nicho em outro idioma | `regionCode`/`relevanceLanguage` são preferência, não filtro: vídeo em inglês entra e infla S1 | o relatório conta quantos vídeos têm `defaultAudioLanguage` fora de `pt`; acima de 30% o nicho sai marcado `amostra contaminada`. Comparar nicho pt-BR com nicho en é inválido |
| `subscriberCount` oculto pelo canal | S3 do vídeo é descartado (não vira 0) | mediana segue com o resto; o relatório diz quantos foram descartados |
| Viés do `order=viewCount` | mede o **topo** do nicho, não a mediana dele; o nicho parece mais rico do que é | aceito: a decisão é "dá para competir no topo?", que é a pergunta certa |
| Amostra pequena (< 20 vídeos ou < 10 canais) | nicho sai marcado `amostra insuficiente` e **fora** do ranking | acrescentar termo ao nicho |

## 8. Critério de sucesso

Avaliação em **30 dias** a partir da primeira rodada real. O bot serviu se, ao fim dos 30 dias:

1. Rodou **pelo menos 4 rodadas** completas sem intervenção manual além de `rodar`, e nenhuma delas
   gastou mais de **5.000 unidades** de cota (metade da gratuita).
2. Produziu ranking de **pelo menos 8 nichos** com amostra suficiente, e **pelo menos 1** nicho entrou no
   top 3 que o dono não teria listado antes de rodar o bot — registrado por escrito **antes** da primeira
   rodada (lista de palpite em `data/palpite-inicial.md`). Zero nichos novos = o bot só confirmou o
   palpite e não pagou o esforço.
3. O nicho escolhido para o primeiro canal próprio saiu do **top 3** do ranking, e o dono registrou em
   uma frase por que aquele e não o primeiro.
4. A ordem do ranking foi **estável** entre rodadas consecutivas: no máximo **2 posições** de troca no
   top 5, sem mudança nos termos. Instabilidade maior = amostra pequena demais ou pesos sensíveis demais;
   corrigir a amostra antes de confiar no ranking.

Falhar 1 ou 4 é problema de desenho (corrigir). Falhar 2 é o bot não ter valor: parar, voltar a decidir
à mão e não manter o worker.

## 9. Esforço estimado

| Etapa | Horas |
|---|---|
| Esqueleto do worker (pacote, `.env`, `.venv`, CLI, `niches.yml`, log de cota) | 3 |
| Cliente da YouTube Data API: `search.list` + hidratação em lote, cache em disco, teto de cota, backoff | 6 |
| Integração `trendspyg` com cache de 7 dias, backoff e degradação para `null` | 3 |
| Cálculo de S1–S5, normalização por percentil e nota composta | 4 |
| Agrupamento de pautas e cortes (duração, similaridade de título) | 3 |
| Relatórios JSON e Markdown | 2 |
| Testes com HTTP simulado (cota, 429, amostra pequena, inscritos ocultos, Trends em falha) | 5 |
| README do worker e primeira rodada real com ajuste de termos | 3 |
| **Total** | **29 h** |

Tela no painel (§5.4), se um dia: **+8 h**. Não está no total.

## 10. Fontes

- https://developers.google.com/youtube/v3/determine_quota_cost — tabela de custo por chamada
- https://developers.google.com/youtube/v3/getting-started — cota padrão de 10.000 unidades/dia e reset
- https://developers.google.com/youtube/v3/docs/search/list — `q`, `publishedAfter`, `order`, `regionCode`, `relevanceLanguage`
- https://developers.google.com/youtube/v3/docs/videos/list — `statistics`, `contentDetails`, lote de 50 ids
- https://developers.google.com/youtube/v3/docs/channels/list — `statistics`, `snippet.publishedAt`
- https://developers.google.com/search/blog/2025/07/trends-api — anúncio da Google Trends API em alpha (24/07/2025)
- https://ppc.land/google-opens-alpha-testing-for-new-trends-api-targeting-developers-and-journalists/ — alpha por candidatura, sem cota publicada
- https://github.com/flack0x/trendspyg — `trendspyg`, interesse ao longo do tempo com `gprop` (YouTube Search)
- https://dev.to/esteban_ortega/pytrends-is-dead-heres-how-to-get-google-trends-data-in-2026-1a18 — `pytrends` arquivado em abril/2025 e alternativas
- https://scrapebadger.com/blog/best-google-trends-scraper-in-2026-every-tool-compared-honestly — 429 e fragilidade do Trends não oficial
- https://www.hotmart.com/pt-br/tos — Termos Gerais de Uso da Hotmart (atualizados em 06/10/2025)
- https://vidiq.com/pricing/ — preço do VidIQ (~US$ 7,50/mês)
