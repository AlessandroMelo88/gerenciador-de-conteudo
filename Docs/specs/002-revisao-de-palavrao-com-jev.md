# SPEC-002 — Revisão de palavrão na aprovação, com julgamento tipado (JEV)

**Status:** Rascunho
**Data:** 02/10/2026
**ADRs relacionados:** ADR-0004 (fallback de IA obrigatório)
**Onde vive o código:** `clip-processor/src/` (detecção e cliente) e `painel/` (chave, liga/desliga e tela)

## 1. Objetivo

Dar ao dono, na fila de aprovação, a lista de palavrões de cada clip **com minuto e segundo e a frase
em volta**, para ele decidir caso a caso em vez de um filtro reprovar sozinho. É a etapa 1 do
[`../planos/PLANO-REVISAO-DE-PALAVRAO.md`](../planos/PLANO-REVISAO-DE-PALAVRAO.md): **só detectar e
mostrar**, sem reprocessar áudio e sem bloquear nada.

A detecção usa o TypeSafe/JEV, que devolve **julgamento tipado com probabilidade calibrada** em vez
de texto. Cada ocorrência candidata vira uma pergunta `noul` ("esta palavra, neste contexto, é
palavrão ofensivo?"), e o clip inteiro recebe um `score` de risco de desmonetização. É o caso que a
ferramenta faz bem: muitas perguntas fechadas numa chamada só.

**A integração nasce desligada.** Nada chama a API até o dono ligar no painel. Enquanto estiver
desligada, o pipeline se comporta exatamente como hoje.

## 2. Fora de escopo

- **Censurar áudio** (bip, silêncio, animação) e o render extra que isso exige. É a etapa 2 do plano
  de palavrão e não entra aqui.
- **Bloquear ou reprovar clip automaticamente.** A lista é consultiva. Nenhum caminho novo decide
  publicação; só o dono decide, como hoje.
- Revisar título, descrição e tags (é texto gerado; outro problema).
- Regra por canal destino e alerta de densidade (etapa 3 do plano de palavrão).
- Usar o JEV em qualquer outro ponto do pipeline. O cliente nasce genérico, mas esta spec liga **um**
  consumidor: a revisão de palavrão.

## 3. Regras de negócio

**Liga/desliga e chave**

- **R1.** A integração é controlada por `system_settings` com a chave `jev_enabled`, **padrão
  `false`**. Desligada, nenhuma chamada HTTP é feita e nenhum custo é gerado.
- **R2.** O liga/desliga aparece na tela de Configurações do painel, com o texto dizendo que é um
  serviço pago por uso e que fica desligado por padrão.
- **R3.** A chave da API vive em `TYPESAFE_API_KEY`, no `.env` do servidor, **fora do git** (o
  repositório é público). Sem a chave, a integração se comporta como desligada, mesmo com
  `jev_enabled = true`, e registra isso no log uma vez por ciclo.
- **R4.** Ligar no painel **não** reprocessa clip nenhum retroativamente. Vale do próximo clip em diante.

**Cliente JEV**

- **R5.** O cliente fala `POST https://api.typesafe.ai/v1/systemone`, com `Authorization: Bearer
  <TYPESAFE_API_KEY>`, corpo `{state, model, questions}` e `model = "jev-latest"`.
- **R6.** `429` e `529` são tentados de novo com espera exponencial, no máximo 3 tentativas. Esgotadas,
  é falha comum (ver R7).
- **R7.** **Nenhuma falha do JEV pode derrubar o pipeline nem impedir a publicação.** Erro de rede,
  HTTP, chave inválida ou resposta fora do formato: loga, grava o clip **sem** revisão, e o clip segue
  seu caminho normal.
- **R8.** Fallback obrigatório (ADR-0004): sem JEV disponível, a detecção cai para a lista de palavras
  local, que marca as ocorrências **sem** julgamento de contexto, e a tela diz que a revisão foi feita
  pelo modo simples. O fallback nunca reprova nada.
- **R9.** Teto de gasto: `JEV_MAX_CALLS_PER_DAY` (padrão 100). Atingido o teto, o dia segue no modo
  fallback e o log registra.

**Detecção**

- **R10.** As candidatas saem da transcrição com tempo por palavra que o pipeline já produz. Uma lista
  de palavras local escolhe **o que perguntar**; o JEV decide **o que é**. A lista sozinha nunca marca
  ocorrência como confirmada quando o JEV respondeu.
- **R11.** Cada ocorrência vira uma pergunta `noul`, com a frase em volta como contexto. Todas as
  ocorrências de um clip vão **numa única chamada** — é isso que torna o uso barato.
- **R12.** Uma pergunta `score` por clip estima o risco de desmonetização numa escala ordenada.
- **R13.** Ocorrência com probabilidade abaixo de `JEV_NOUL_THRESHOLD` (padrão 0,5) é guardada como
  **descartada**, não some: a tela pode mostrar "o modelo achou que não era".
- **R14.** O resultado é gravado em `clip_profanity_findings`, uma linha por ocorrência, com
  `start_s`, `end_s`, `word`, `context`, `probability`, `source` (`jev` ou `fallback`).

**Painel**

- **R15.** No modal de aprovação do clip, a lista de ocorrências é clicável: clicar pula o player para
  o segundo da ocorrência e mostra a frase em volta.
- **R16.** A lista mostra a contagem total, a densidade (ocorrências por minuto) e o risco do R12.
- **R17.** Clip sem revisão (integração desligada, falha, ou clip anterior à feature) não mostra seção
  nenhuma — nunca um "0 palavrões" que pareça uma revisão que não houve.

## 4. Contrato

### `system_settings`

| Chave | Padrão | O que faz |
|---|---|---|
| `jev_enabled` | `false` | liga a revisão por JEV (R1) |

### Variáveis de ambiente (`clip-processor`)

| Variável | Padrão | O que faz |
|---|---|---|
| `TYPESAFE_API_KEY` | vazio | chave da API; vazio = comporta-se como desligado (R3) |
| `JEV_MAX_CALLS_PER_DAY` | `100` | teto de chamadas por dia (R9) |
| `JEV_NOUL_THRESHOLD` | `0.5` | acima disso a ocorrência conta como confirmada (R13) |

Precisam entrar no `environment:` do `clip-processor` em `docker-compose.yml`.

### Tabela `clip_profanity_findings`

| Coluna | Tipo | Nota |
|---|---|---|
| `id` | bigint PK | |
| `generated_clip_id` | FK `generated_clips` | `cascadeOnDelete` |
| `start_s` | decimal(8,2) | segundo de início na transcrição |
| `end_s` | decimal(8,2) | |
| `word` | string(64) | a palavra candidata |
| `context` | text | a frase em volta, para o dono ler |
| `probability` | decimal(4,3) nullable | o `noul` do JEV; nulo no fallback |
| `confirmed` | boolean | `probability >= JEV_NOUL_THRESHOLD` (R13) |
| `source` | string(16) | `jev` ou `fallback` (R8) |

Mais, em `generated_clips`: `profanity_risk` (decimal(4,2), nulo) com o `score` do R12 e
`profanity_reviewed_at` (timestamp, nulo) para distinguir "sem palavrão" de "não revisado" (R17).

### Chamada ao JEV

```json
POST https://api.typesafe.ai/v1/systemone
Authorization: Bearer <TYPESAFE_API_KEY>

{
  "model": "jev-latest",
  "state": { "clip": "<título do clip>", "trechos": [ {"id": "o1", "frase": "<frase em volta>"} ] },
  "questions": {
    "o1": {
      "type": "noul",
      "instructions": "A palavra marcada em `trechos.frase` é palavrão ofensivo neste contexto, do tipo que o YouTube desmonetiza?",
      "criteria": {
        "true": "xingamento, obscenidade ou ofensa dirigida",
        "false": "intensificador coloquial, citação, nome próprio ou uso técnico"
      }
    },
    "risco": {
      "type": "score",
      "instructions": "Risco de desmonetização do clip inteiro pela linguagem.",
      "criteria": ["nenhum", "baixo", "médio", "alto", "muito alto"]
    }
  }
}
```

Resposta: `answers.o1.noul` (0–1) por ocorrência e `answers.risco.score` com `confidence`.

## 5. Critérios de pronto

- [ ] Cada regra da §3 tem teste
- [ ] Com `jev_enabled = false`, nenhum teste de integração faz chamada HTTP (provado por mock que falha se chamado)
- [ ] `pytest` dentro da imagem `wordpress-clip-processor` passando
- [ ] `php artisan test` do painel passando contra PostgreSQL; `vendor/bin/pint` limpo
- [ ] Nenhuma chave no git (`git log -p` do `.env` e do `docker-compose.yml` conferido)
- [ ] `Docs/sistema/` e `Docs/PROGRESSO.md` atualizados; `PLANO-REVISAO-DE-PALAVRAO.md` com a etapa 1 marcada
- [ ] Esta spec em **Entregue**

## 6. Riscos e perguntas em aberto

| Item | Dono | Estado |
|---|---|---|
| Preço do JEV não é publicado na documentação; saldo da conta está em US$ 0,00 | Dono | Creditar e medir o custo real do primeiro clip antes de ligar de vez |
| Limite de perguntas por chamada não documentado | Quem implementar | Medir: um clip de 3 min pode ter dezenas de ocorrências. Se houver teto, dividir em lotes |
| Transcrição tem tempo por palavra? | Quem implementar | **Verificar antes da Tarefa 3.** Se o Whisper do projeto devolver só por segmento, a minutagem fica no grão do segmento e a spec R10/R14 muda de precisão |
| Lista de palavras: fixa no código ou editável por canal | Dono | Fixa no código nesta etapa; editável é etapa 3 |
| `queue_controls.py:24` usa crase (sintaxe MySQL) ao ler `system_settings` | Quem implementar | **Bug vivo:** em PostgreSQL falha e o `except` engole, então `allow_local_download` é sempre `false`. Não introduzir o mesmo erro ao ler `jev_enabled`; corrigir em branch própria |
