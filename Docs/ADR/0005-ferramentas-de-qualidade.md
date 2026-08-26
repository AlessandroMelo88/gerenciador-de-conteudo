# ADR-0005 — Lint e formatação bloqueantes, baseline para dívida antiga, tipos informativos

**Status:** aceito · **Data:** 25/08/2026

## Contexto

Até 25/08/2026 o repositório não tinha lint, formatter, análise estática nem CI: 122 achados do ruff
(82 auto-corrigíveis), 42 de 44 arquivos Python fora de qualquer formatação consistente, 16 arquivos
PHP fora do padrão Pint, 1 erro de `tsc` que ninguém via porque `vite build` não checa tipos, 87 erros
de PHPStan nível 5, e dumps de banco de 1 MB versionados. Detalhe em `DESENVOLVIMENTO.md`.

## Decisão

1. **Bloqueantes** (pre-commit + CI): `ruff check` + `ruff format` (Python), Pint + PHPStan nível 5
   (PHP), `tsc --noEmit` + oxlint (erros) + Prettier (TS/React), shellcheck, yamllint, hadolint.
2. **Baseline só para a dívida que não cabe corrigir de uma vez**: `phpstan-baseline.neon` (87
   erros). A baseline **só pode encolher**; erro novo nunca entra nela. Para ruff não há baseline —
   as regras foram escolhidas de modo que a base passe limpa após um único commit `style:`.
3. **Informativos**: mypy e avisos do oxlint. Não bloqueiam até a contagem chegar a zero; aí viram
   bloqueantes.
4. **Formatação em commit próprio** (`style:`), separada de mudança de comportamento, para manter
   `git blame` útil.
5. **oxlint em vez de ESLint** enquanto `typescript-eslint` não suportar `typescript@7`.
6. **Ferramentas sem dependência de rede em runtime**: tudo roda no host via `make` e, para o CI,
   em jobs separados por linguagem para falhar rápido e em paralelo.

## Consequências

- `make lint` é o contrato: o que passa nele passa no CI.
- Quem toca os 13 módulos do clip-processor que estavam em migração de banco em 25/08/2026 precisa
  rodar `make format-python` antes de commitar (a formatação deles ficou de fora do commit `style:`).
- Regras rejeitadas de propósito: `SIM105`/`SIM108` (estilo), `E501` (o formatter cuida), `T20`
  (`print` como log é dívida real, mas está em 12 módulos — TODO-REFATORACAO Python #10).

## Alternativas consideradas

- black + isort + flake8 — três ferramentas para o que ruff faz em uma.
- ESLint + typescript-eslint — incompatível com TS 7 hoje.
- Biome — cobriria lint+format em uma ferramenta, mas o plugin Tailwind do Prettier e a convenção
  shadcn pesaram a favor de Prettier.
