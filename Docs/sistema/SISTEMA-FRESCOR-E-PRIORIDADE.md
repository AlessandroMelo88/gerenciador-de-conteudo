# Frescor e prioridade por canal-fonte

Cada canal-fonte (tela **Canais Fonte** do painel) passou a ter duas regras próprias: até que
idade um vídeo dele ainda serve para virar corte (**janela de busca**) e quem começa primeiro
quando dois canais disputam a mesma vaga (**prioridade de input**).

Origem: trazido de `origin/release/rico` em 30/09/2026 (Lote 4), adaptado à política da master.
**Atualizado em 01/10/2026:** na `master` e em produção (lotes do `release/rico`, deploy `ace7714` de 30/09/2026).

---

## Para quem opera o painel

| Controle | Onde | Opções | O que faz |
|---|---|---|---|
| Janela de busca | Canais Fonte, coluna "Janela de busca" (ou cartão) | **Hoje e ontem** (padrão) ou **3 dias** | Vídeo mais velho que a janela nunca é baixado; fica `pending` |
| Prioridade de input | Canais Fonte, botões − e + | -10 a +10, começa em 0 | Canal com número maior é atendido primeiro na rodada |

```
Rodada de download (vaga livre na janela do nicho)
   |
   v
vídeos pending do canal  --(mais velhos que a janela do canal?)--> ficam de fora
   |
   v
fila justa: quem tem menos vagas ocupadas vem primeiro
   |
   v   empate de ocupação?
prioridade de input maior vem primeiro
   |
   v
teto por canal continua valendo (prioridade NÃO dá mais vagas)
```

Pontos que costumam surpreender:

- A prioridade só **desempata a ordem**. Ela não aumenta o teto de vagas do canal nem fura a regra
  anti-fome (canal com menos vagas ocupadas continua na frente).
- Não existe opção "1500 dias". A `release/rico` usava 1500 como padrão, o que faria todo backlog
  antigo voltar a baixar; aqui só são aceitos 1 e 3 dias.
- Mudança na janela vale na rodada seguinte; não apaga nada já baixado.
- Aba **Ativos** de Vídeos Fonte não mostra mais os `published` (histórico); eles seguem na aba
  **Todos**.

---

## Referência técnica

### Banco

Migration `2026_09_30_100000_add_freshness_and_input_priority_to_source_channels` (idempotente,
ignora tabela/coluna já existente):

| Coluna em `source_channels` | Tipo | Padrão |
|---|---|---|
| `freshness_days` | smallint unsigned | **1** |
| `input_priority` | smallint | 0 |

Efeito no deploy: **todo canal existente passa a ter `freshness_days = 1`**. O default do código
(`FRESHNESS_DAYS`, variável de ambiente, hoje 3 no `pipeline_runner.py`) fica só como fallback
para vídeo sem canal-fonte; antes desta mudança ele valia para todos os canais. Quem dependia de
3 dias em algum canal precisa marcá-lo na tela.

### Clip-processor

- `pipeline_runner._select_pending_videos`: o corte deixou de ser calculado em Python. O SQL usa
  `DATE(sv.published_at) >= (hoje_SP - COALESCE(sc.freshness_days, FRESHNESS_DAYS))` e devolve
  `COALESCE(sc.input_priority, 0) AS input_priority` em cada candidato.
- `fair_queue.fair_pick`: a ordem das rodadas é `(ocupação, -input_priority, chegada)`. Prioridade
  inválida (texto, `None`) vira 0.

### Painel

- `SourceChannelController@update` valida `freshness_days` em `SourceChannel::FRESHNESS_OPTIONS`
  (1 e 3) e `input_priority` entre `-10` e `10`; `@index` expõe `freshnessDays` e `inputPriority`.
- `SourceVideoController@index`: aba `ativos` exclui `failed` e `published`; `per_page` limitado a
  1..100.

### Testes

`painel/tests/Feature/SourceChannelPriorityTest.php`, `clip-processor/tests/test_fair_queue.py`,
`clip-processor/tests/test_pipeline_runner.py`.
