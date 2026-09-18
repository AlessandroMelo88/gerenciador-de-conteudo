# affiliate-worker

Worker **local** de afiliados do Canal de Cortes. Roda na sua máquina, quando você quiser:
busca ou importa ofertas, gera copy com IA e **empurra** para o painel via `POST /api/offers`.
O servidor nunca chama o worker. Toda oferta chega no painel como `draft` e só vai ao ar depois
que você aprovar.

Sem dependência do clip-processor nem do banco: só HTTP.

## Instalação

```bash
cd affiliate-worker
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # preencha AFFILIATE_API_URL e AFFILIATE_API_TOKEN
```

| Variável | Obrigatória | Uso |
|---|---|---|
| `AFFILIATE_API_URL` | para `push` | URL base do painel (sem `/api/offers`) |
| `AFFILIATE_API_TOKEN` | para `push` | Bearer token configurado no painel |
| `ANTHROPIC_API_KEY` | não | copy via `claude-haiku-4-5` |
| `GROQ_API_KEY` / `GROQ_MODEL` | não | fallback de copy (default `qwen/qwen3.8-27b`) |
| `MERCADOLIVRE_ACCESS_TOKEN` | não | busca no ML se a busca anônima for recusada |
| `AFFILIATE_DATA_DIR` | não | onde ficam os arquivos locais (default `data/`) |

## Fluxo

```
search (ML) ──► data/candidates.json ──(você cola o affiliate_url)──┐
                                                                     ▼
arquivo CSV/JSON preenchido ──► import ──► data/ready.json ──► copy ──► push ──► painel (draft)
                                                                         └──► data/pushed.jsonl
```

| Comando | O que faz |
|---|---|
| `search --source mercadolivre --query "chuteira society" --niche futebol --limit 20` | Busca candidatos na API oficial do ML e grava `data/candidates.json` **sem** `affiliate_url` |
| `import --file ofertas.csv` (ou `.json`) `[--niche futebol]` | Carrega ofertas em `data/ready.json`, mesclando por `network` + `external_id` |
| `copy [--provider auto\|anthropic\|groq\|template]` | Gera `cta_text`, `copy_short`, `copy_long` para itens com link e sem copy |
| `push [--dry-run] [--force]` | Envia os itens válidos em lotes de até 100; `--dry-run` só imprime o payload |
| `run --file ofertas.csv [--provider ...] [--dry-run]` | Atalho: import + copy + push |

Uso: `.venv/bin/python -m affiliate_worker <comando>`.

### Exemplo rápido

```bash
.venv/bin/python -m affiliate_worker import --file examples/ofertas.csv
.venv/bin/python -m affiliate_worker copy
.venv/bin/python -m affiliate_worker push --dry-run   # confira; depois rode sem --dry-run
```

## Formato do CSV

Cabeçalho na primeira linha, com os nomes de campo do contrato. Separador `,` ou `;` (detectado
pelo cabeçalho). Codificação UTF-8. Célula vazia = campo não enviado.

```csv
network;external_id;niche;title;affiliate_url;product_url;image_url;price;commission_percent;description
hotmart;HP-ORATORIA-01;politica;Curso de Oratória;https://go.hotmart.com/SEU_LINK;;;297,00;40;Curso online de fala em público.
amazon;B0EXEMPLO01;futebol;Camisa Retrô 1970;https://amzn.to/SEU_LINK;https://www.amazon.com.br/dp/B0EXEMPLO01;;189,90;;
```

| Coluna | Obrigatória | Regra |
|---|---|---|
| `network` | sim | `hotmart`, `eduzz`, `kiwify`, `monetizze`, `amazon`, `mercadolivre`, `shopee`, `awin`, `manual` |
| `niche` | sim | slug existente no painel (`futebol`, `politica`…); ou use `--niche` no import |
| `title` | sim | até 255 caracteres |
| `affiliate_url` | sim para push | link **com tracking** copiado da rede, http/https |
| `external_id` | recomendado | id do produto na rede; sem ele o servidor não consegue fazer upsert |
| `price` **ou** `price_cents` | não | `price` em reais (`297,00`, `R$ 1.297,00`, `189.90`) é convertido para centavos |
| `currency` | não | 3 letras, default BRL |
| `commission_percent` | não | número 0–100 (`40` ou `40,5`) |
| `description`, `product_url`, `image_url`, `cta_text`, `copy_short`, `copy_long`, `ai_provider` | não | URLs precisam ser http/https; `copy_short` até 280 |

`status` é ignorado se vier no arquivo: quem define é o servidor.

O JSON aceita uma lista de objetos ou `{"offers": [...]}` com os mesmos campos (o próprio
`data/candidates.json` do `search` pode ser editado e reimportado).

**Hotmart, Eduzz, Kiwify e Monetizze** não têm API pública de catálogo para afiliado: pegue o link
de afiliado no painel da plataforma e cole no CSV.

## Regras que o worker garante

- **Nunca inventa nem monta `affiliate_url`.** Item sem link fica em `ready.json`, mas fora do push, com aviso.
- **Validação local antes de enviar** (network, URL http/https, tamanhos, moeda, comissão): item inválido
  é barrado com a mensagem do problema, em vez de derrubar o lote inteiro com 422.
- **Copy:** Anthropic → Groq → template determinístico. Saída de IA é JSON com parse defensivo; resposta
  inválida cai para o próximo. O template garante que `copy` nunca trava. `copy_short` sai sem link
  (o painel anexa o link rastreável). Prompts proíbem prometer resultado, inventar preço/desconto/escassez
  e afirmar saúde ou renda garantida. Tom: futebol direto de torcedor; política sóbrio e sem partido.
  Copy de template é marcada `ai_provider=manual` (o contrato não tem valor `template`).
  Campos de copy já preenchidos por você não são sobrescritos.
- **Push:** lotes de ≤100; retry com backoff em 429 (respeita `Retry-After`), 5xx, timeout e queda de conexão;
  sem retry em 401 e 422. 401 e 503 persistente interrompem o push. Item enviado com sucesso ganha
  `pushed_at` e não é reenviado (use `--force`, ou reimporte/regere a copy, que zera a marca).
- Token nunca aparece em log. Segredos só via `.env`, que está no `.gitignore` junto com `data/` e `.venv/`.

## Arquivos locais (`data/`)

| Arquivo | Conteúdo |
|---|---|
| `candidates.json` | resultado do último `search` (sobrescrito a cada busca) |
| `ready.json` | ofertas importadas, com copy e marca de envio (`pushed_at`, `server_id`, `server_status`, `tracking_url`) |
| `pushed.jsonl` | uma linha por item a cada push: resultado, código HTTP, erros de validação do servidor |

## Mercado Livre

Usa a API oficial `https://api.mercadolibre.com/sites/MLB/search`, com timeout de 15s. Não faz scraping.
A busca anônima pode ser recusada (401/403): nesse caso o comando explica e sai com código 1, sem
quebrar o resto. Para liberar, crie um app em developers.mercadolivre.com.br e defina
`MERCADOLIVRE_ACCESS_TOKEN` (o token expira em algumas horas). O link de afiliado continua vindo do
gerador do programa Mercado Livre Afiliados.

## Testes

```bash
.venv/bin/pytest -q
```

Sem rede real: HTTP e SDKs de IA são simulados.
