# ADR-0006 — Gates de qualidade que passam no código atual, com dívida em baseline

**Status:** Aceita · **Data:** 30/09/2026 (adaptada da proposta de 25/08/2026 do Ricardo)

## Contexto

A `master` não tinha lint, análise estática nem CI. A proposta original do Ricardo exigia também
`ruff format`, Prettier e Pint sobre todo o código, o que obrigava a reformatar dezenas de arquivos
de uma vez (medido em 30/09/2026: 48 arquivos Python fora do `ruff format`, 25 arquivos PHP fora do
Pint) e conflitaria com qualquer branch aberta. Também fixava PHP 8.4, mas a produção usa `php:8.3`.

## Decisão

1. **Bloqueantes no CI** (só o que o código atual já respeita): `ruff check` com regras de erro real
   (`E9`, `F63`, `F7`, `F82`), Pint apenas nos arquivos que o PR altera (`--diff=origin/master`),
   PHPStan/Larastan nível 5 com `phpstan-baseline.neon`, oxlint (regras herdadas como aviso),
   shellcheck em severidade `error`, hadolint e yamllint, pytest (piso de cobertura 60 %; medido 66,5 %),
   pest e build do painel.
2. **Informativos** (não reprovam): mypy (23 erros herdados) e `tsc --noEmit` (27 erros herdados).
3. **Dívida só encolhe**: a baseline do PHPStan e os ignores do hadolint não crescem para esconder
   erro novo. Para endurecer uma regra do ruff, limpe os achados e acrescente o prefixo em
   `pyproject.toml`.
4. **Sem reformatação em massa**: formatação é lote `style:` isolado, feito quando não houver
   branch aberta.
5. **CI só valida**: sem segredo, sem deploy (o deploy é `./deploy.sh`, manual).
6. **PHP 8.3** no CI e `config.platform.php = 8.3.0` no `composer.json`, para o `composer.lock` nunca
   resolver pacotes que exijam PHP 8.4.

## Consequências

- `make lint` é o contrato local; o que passa nele passa no CI.
- Prettier, Vitest e Playwright não foram adotados (dependem de código e lockfile fora deste lote).
- Detalhes de uso: [`../DESENVOLVIMENTO.md`](../operacao/DESENVOLVIMENTO.md).

## Alternativas consideradas

- Reformatar tudo num commit `style:` e exigir format — adiado (conflito com branches abertas).
- ESLint em vez de oxlint — `typescript-eslint` não suportava `typescript@7` na proposta original.
