# Plano — integração JEV e revisão de palavrão (SPEC-002)

> **Para quem executa:** SUB-SKILL OBRIGATÓRIA: `superpowers:executing-plans` (ou
> `superpowers:subagent-driven-development`). Os passos usam caixa (`- [ ]`).

**Status:** APROVADO, não iniciado (02/10/2026)

**Objetivo:** integrar o TypeSafe/JEV ao projeto **desligado por padrão**, ligável na tela de
Configurações, e usá-lo em um consumidor só: a lista de palavrões com minutagem na fila de aprovação.

**Arquitetura:** um cliente fino do JEV (`jev_client.py`) e um revisor (`profanity_reviewer.py`) no
clip-processor. O revisor pergunta ao banco se `jev_enabled` está ligado; desligado, devolve vazio sem
tocar na rede. Ligado, manda todas as ocorrências de um clip numa chamada só e grava o resultado. O
painel só lê a tabela e mostra.

**Stack:** Python 3.11, `requests`, pytest (pipeline); Laravel 12, Inertia, React 19, Pest (painel);
PostgreSQL 17.

**Spec:** [`../specs/002-revisao-de-palavrao-com-jev.md`](../specs/002-revisao-de-palavrao-com-jev.md)

## Restrições globais

- **Desligado por padrão é a regra mais importante deste plano.** `jev_enabled` nasce `false`. Se, em
  qualquer tarefa, um teste com a integração desligada tocar a rede, a tarefa está errada.
- **Nenhuma falha do JEV propaga.** Rede, HTTP, chave inválida, resposta estranha: loga, segue sem
  revisão, o clip publica normalmente (SPEC R7).
- **Fallback obrigatório** (ADR-0004): sem JEV, a lista de palavras local marca as ocorrências sem
  julgar contexto, e a tela diz que foi o modo simples.
- **A chave nunca entra no git.** O repositório é público. `TYPESAFE_API_KEY` só no `.env` do servidor.
  Nenhum valor real em teste, fixture, doc ou mensagem de commit.
- **Ler `system_settings` sem crase.** `queue_controls.py:24` usa `` `key` `` (MySQL) e falha calado em
  PostgreSQL. Não repetir: a coluna é `key`, escrita sem aspas, ou `"key"` com aspas duplas.
- **SQL portável** entre PostgreSQL e MySQL; placeholder `%s`; migration guardada por `hasTable` /
  `hasColumn` (ADR-0005).
- **Rebuild obrigatório** ao mexer no clip-processor: não há bind mount para `src/`.
- **Mexer apenas** no serviço `clip-processor` e em paths sob `canaldecortes/`.
- **Gitflow:** branch `feature/revisao-palavrao-jev` a partir da `master` atualizada; commits
  convencionais em português; merge `--no-ff`.

## Foco de revisão

1. **Integração desligada ainda assim chamando a API** — o jeito mais fácil de gerar conta sem querer.
   Teste na Tarefa 5 com um cliente que levanta exceção se for chamado.
2. **Chave ausente com `jev_enabled = true`** — estado real enquanto o dono não configurar o servidor.
   Tem que se comportar como desligado, não estourar. Tarefa 3.
3. **Resposta do JEV sem a chave de uma pergunta** — o modelo pode omitir; ler sem checar quebra o
   ciclo. Tarefa 3.
4. **Clip nunca revisado × clip revisado e limpo** — mostrar "0 palavrões" para quem nunca foi revisado
   mente para o dono na hora de aprovar. Tarefas 1 e 7.
5. **Teto diário estourado no meio de um clip** — não pode gravar meio clip como `jev` e meio como
   `fallback` sem dizer qual foi. Tarefa 5.

---

### Tarefa 1: tabelas e colunas

**Arquivos:**
- Criar: `painel/database/migrations/2026_10_03_100000_create_clip_profanity_findings_table.php`
- Criar: `painel/database/migrations/2026_10_03_100100_add_profanity_columns_to_generated_clips.php`
- Teste: `painel/tests/Feature/ProfanitySchemaTest.php`

**Produz:** tabela `clip_profanity_findings` (`generated_clip_id`, `start_s`, `end_s`, `word`,
`context`, `probability`, `confirmed`, `source`) e, em `generated_clips`, `profanity_risk` e
`profanity_reviewed_at`. Todas as tarefas seguintes usam esses nomes.

- [ ] **Passo 1: teste que falha** — existência das colunas, e que `profanity_reviewed_at` aceita nulo
  (é o que distingue "revisado e limpo" de "nunca revisado", SPEC R17).
- [ ] **Passo 2:** `cd painel && vendor/bin/pest tests/Feature/ProfanitySchemaTest.php` → FALHA.
- [ ] **Passo 3:** as duas migrations, guardadas por `Schema::hasTable` / `Schema::hasColumn`, FK com
  `cascadeOnDelete`, índice em `generated_clip_id`.
- [ ] **Passo 4:** mesmo comando → PASSA.
- [ ] **Passo 5:** commit `feat(palavrao): tabela de ocorrências e colunas de revisão no clip`.

---

### Tarefa 2: liga/desliga no painel

**Arquivos:**
- Modificar: `painel/app/Http/Controllers/SettingsController.php`
- Modificar: `painel/resources/js/pages/Settings.tsx`
- Teste: `painel/tests/Feature/JevToggleTest.php`

**Consome:** `App\Models\SystemSetting::get/set`, que já existe.
**Produz:** a chave `jev_enabled` em `system_settings`.

- [ ] **Passo 1: teste que falha**

```php
it('vem desligado por padrão', function () {
    expect(SystemSetting::get('jev_enabled', false))->toBeFalse();
});

it('liga e desliga pela tela de configurações', function () {
    $this->actingAs(User::first() ?? User::factory()->create())
        ->post('/painel/configuracoes', ['jev_enabled' => true])
        ->assertRedirect();

    expect(SystemSetting::get('jev_enabled'))->toBeTrue();
});
```

- [ ] **Passo 2:** `cd painel && vendor/bin/pest tests/Feature/JevToggleTest.php` → FALHA.
- [ ] **Passo 3:** tratar `jev_enabled` no `SettingsController` no mesmo padrão das chaves que já
  existem, e um switch em `Settings.tsx` com o texto: *"Revisão de palavrão por IA (TypeSafe/JEV).
  Serviço pago por uso — fica desligado por padrão. Ligado, cada clip novo gasta uma chamada."*
- [ ] **Passo 4:** mesmo comando → PASSA.
- [ ] **Passo 5:** commit `feat(palavrao): liga/desliga do JEV nas configurações, desligado por padrão`.

---

### Tarefa 3: cliente do JEV

**Arquivos:**
- Criar: `clip-processor/src/jev_client.py`
- Criar: `clip-processor/tests/test_jev_client.py`

**Produz:** `ask(state: dict, questions: dict, *, session=None) -> dict | None` — devolve o `answers`
da resposta, ou `None` quando não dá para perguntar (sem chave, teto, erro). Nunca levanta exceção.
Mais `api_key() -> str`, `JEV_URL`, `MODEL = 'jev-latest'`.

- [ ] **Passo 1: teste que falha** — cobrir, no mínimo:
  - sem `TYPESAFE_API_KEY`: devolve `None` e **não** chama a sessão HTTP (sessão falsa que levanta se chamada);
  - resposta 200 bem formada: devolve o dicionário `answers`;
  - resposta sem a chave de uma pergunta pedida: devolve o que veio, sem levantar;
  - `429` seguido de 200: tenta de novo e devolve o resultado;
  - `429` três vezes: devolve `None`;
  - erro de rede (`requests.ConnectionError`): devolve `None`;
  - JSON inválido no corpo: devolve `None`.
- [ ] **Passo 2:** `cd clip-processor && pytest tests/test_jev_client.py -v` → FALHA (módulo não existe).
- [ ] **Passo 3:** escrever o cliente. Cabeçalho `Authorization: Bearer <chave>`; corpo
  `{"model": MODEL, "state": state, "questions": questions}`; espera exponencial (1 s, 2 s, 4 s) só
  para 429 e 529; todo o resto é falha comum. Docstring deixando explícito que **nunca** levanta.
- [ ] **Passo 4:** mesmo comando → PASSA.
- [ ] **Passo 5:** commit `feat(jev): cliente que nunca derruba o chamador`.

---

### Tarefa 4: candidatas e lista de palavras (o fallback)

**Arquivos:**
- Criar: `clip-processor/src/profanity_words.py`
- Criar: `clip-processor/tests/test_profanity_words.py`

**Produz:** `candidatas(transcricao: dict) -> list[dict]`, cada item com `start_s`, `end_s`, `word`,
`context`. É o que alimenta tanto o JEV quanto o fallback.

- [ ] **Passo 0 — verificar antes de escrever:** confirmar se a transcrição do projeto tem **tempo por
  palavra** ou só por segmento. Rodar
  `grep -rn "words\|word_timestamps\|segments" clip-processor/src/transcriber.py` e olhar um JSON real
  em disco. Se só houver segmento, `start_s`/`end_s` passam a ser os do segmento — anotar isso na spec
  (§6 já registra o risco) antes de seguir.
- [ ] **Passo 1: teste que falha** — palavra da lista encontrada devolve a ocorrência com o tempo certo;
  palavra que só contém a sequência dentro de outra maior não conta; `context` traz a frase em volta,
  não a palavra solta; transcrição vazia devolve lista vazia.
- [ ] **Passo 2:** `pytest tests/test_profanity_words.py -v` → FALHA.
- [ ] **Passo 3:** lista de palavras no código (comentada como ponto de partida, não como verdade), casamento
  por limite de palavra e sem diferenciar maiúscula/acento.
- [ ] **Passo 4:** mesmo comando → PASSA.
- [ ] **Passo 5:** commit `feat(palavrao): extrai ocorrências candidatas da transcrição`.

---

### Tarefa 5: o revisor

**Arquivos:**
- Criar: `clip-processor/src/profanity_reviewer.py`
- Criar: `clip-processor/tests/test_profanity_reviewer.py`

**Consome:** `jev_client.ask` (Tarefa 3) e `profanity_words.candidatas` (Tarefa 4).
**Produz:** `review_clip(conn, clip_id: int, transcricao: dict, *, client=None, now=None) -> int` —
devolve quantas ocorrências gravou. Nunca levanta exceção.

- [ ] **Passo 1: teste que falha** — os cinco itens do Foco de revisão têm teste aqui:
  - **`jev_enabled = false`:** devolve 0, grava nada, e o cliente falso **levanta se for chamado**
    (é assim que o teste prova que a rede não foi tocada);
  - **ligado, sem chave:** cai no fallback, grava com `source = 'fallback'`, `probability` nula;
  - **ligado e respondendo:** grava `source = 'jev'`, `confirmed` conforme o limiar, e
    `generated_clips.profanity_risk` com o `score`;
  - **probabilidade abaixo do limiar:** grava com `confirmed = false`, **não** descarta a linha (SPEC R13);
  - **teto diário estourado:** o clip inteiro vai para fallback — nunca metade `jev` e metade
    `fallback`;
  - **uma chamada só por clip:** com 12 ocorrências, o cliente é chamado exatamente uma vez (SPEC R11);
  - **sempre marca `profanity_reviewed_at`,** inclusive quando não achou nada, para a tela distinguir
    limpo de não revisado;
  - **exceção do cliente:** devolve 0 sem propagar.
- [ ] **Passo 2:** `pytest tests/test_profanity_reviewer.py -v` → FALHA.
- [ ] **Passo 3:** escrever o revisor. Ler `jev_enabled` de `system_settings` **sem crase**. Montar uma
  pergunta `noul` por ocorrência mais a `score` do clip, conforme o JSON da §4 da spec. Gravar em
  `clip_profanity_findings` e atualizar as duas colunas do clip.
- [ ] **Passo 4:** mesmo comando → PASSA.
- [ ] **Passo 5:** commit `feat(palavrao): revisor com liga/desliga, teto e fallback`.

---

### Tarefa 6: engate no pipeline

**Arquivos:**
- Modificar: o ponto onde o clip fica pronto e vai para aprovação
- Modificar: `docker-compose.yml` (serviço `clip-processor`)
- Modificar: `clip-processor/tests/test_profanity_reviewer.py`

- [ ] **Passo 0 — localizar o ponto exato:** rodar
  `graphify query "onde o clip gerado entra na fila de aprovação, status pending_approval"` e confirmar
  com `grep -rn "pending_approval" clip-processor/src/`. O engate vai **depois** de o clip e a
  transcrição existirem e **antes** de o clip aparecer para aprovação. Anotar `arquivo:linha` no commit.
- [ ] **Passo 1: teste que falha** — o ciclo que gera clip chama `review_clip` uma vez por clip; e com
  `review_clip` levantando exceção, o clip ainda assim chega a `pending_approval` (SPEC R7).
- [ ] **Passo 2:** rodar → FALHA.
- [ ] **Passo 3:** chamar o revisor no ponto localizado, dentro de `try/except` que só loga. No
  `docker-compose.yml`, no `environment:` do **`clip-processor`** e em nenhum outro serviço:

```yaml
      TYPESAFE_API_KEY: ${TYPESAFE_API_KEY:-}
      JEV_MAX_CALLS_PER_DAY: ${JEV_MAX_CALLS_PER_DAY:-100}
      JEV_NOUL_THRESHOLD: ${JEV_NOUL_THRESHOLD:-0.5}
```

- [ ] **Passo 4:** `pytest` inteiro do clip-processor → PASSA. Conferir com `git diff docker-compose.yml`
  que nenhum outro projeto foi tocado.
- [ ] **Passo 5:** commit `feat(palavrao): revisa o clip antes da fila de aprovação`.

---

### Tarefa 7: a lista na tela de aprovação

**Arquivos:**
- Modificar: o controller que monta a fila de aprovação e o componente do modal do clip
- Teste: `painel/tests/Feature/ProfanityNaAprovacaoTest.php`

- [ ] **Passo 0 — localizar:** `graphify query "modal de aprovação do clip, preview com player"` e
  confirmar o componente em `painel/resources/js/components/`.
- [ ] **Passo 1: teste que falha** — clip revisado com 2 ocorrências entrega as duas às props, com
  `startS` e `context`; clip **nunca revisado** (`profanity_reviewed_at` nulo) entrega
  `profanity: null`, e não uma lista vazia (SPEC R17).
- [ ] **Passo 2:** rodar → FALHA.
- [ ] **Passo 3:** carregar as ocorrências junto do clip e, no modal: contagem, densidade por minuto,
  risco, e a lista clicável que posiciona o player no segundo (`playerRef.current.currentTime =
  startS`). Ocorrência com `confirmed = false` aparece esmaecida, com o rótulo "o modelo achou que não
  era". Quando `source = 'fallback'`, uma linha dizendo que a revisão foi pelo modo simples, sem
  julgamento de contexto. Clip não revisado: seção ausente.
- [ ] **Passo 4:** `vendor/bin/pest && npm run build` → PASSA. Validação visual pela skill
  `validacao-visual` nos três estados (revisado com ocorrências, revisado limpo, não revisado).
- [ ] **Passo 5:** commit `feat(palavrao): lista clicável de ocorrências na aprovação`.

---

### Tarefa 8: documentação e fechamento

- [ ] **Passo 1:** `Docs/sistema/SISTEMA-CLIP-PROCESSOR.md` ganha a seção do revisor; criar, na pasta
  `Docs/sistema/`, um documento novo chamado SISTEMA-JEV (arquivo `SISTEMA-JEV.md`) com o que é o JEV,
  o que custa, como ligar e como desligar.
- [ ] **Passo 2:** `PLANO-REVISAO-DE-PALAVRAO.md` passa a etapa 1 para FEITO e aponta para a SPEC-002;
  a spec vai para **Entregue** com os critérios marcados.
- [ ] **Passo 3:** `python3 scripts/check-doc-links.py` → `quebrados: 0`.
- [ ] **Passo 4:** verificação inteira: `pytest` no clip-processor (dentro da imagem),
  `vendor/bin/pest` e `vendor/bin/pint --test` no painel, `graphify update .`.
- [ ] **Passo 5:** commit `docs(palavrao): documenta a revisão e o liga/desliga do JEV`.

---

## Depois do plano, com o dono

1. Merge e deploy. **Nada muda em produção**: `jev_enabled` nasce `false`.
2. O dono credita a conta no console do TypeSafe e põe `TYPESAFE_API_KEY` no `.env` do servidor.
3. Recriar o container para a variável chegar:
   `docker compose up -d --force-recreate --no-deps clip-processor` (só com `publishing = 0`), e
   `docker exec nginx nginx -s reload` se o `php` também for recriado.
4. Ligar `jev_enabled` na tela de Configurações e acompanhar o custo do primeiro dia no console.
5. Desligar é um clique: volta ao comportamento de hoje na hora.
