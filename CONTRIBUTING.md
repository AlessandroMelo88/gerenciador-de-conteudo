# Contribuindo

Guia curto. O detalhe de ferramentas e setup está em [`Docs/DESENVOLVIMENTO.md`](Docs/DESENVOLVIMENTO.md);
o índice de toda a documentação, em [`Docs/README.md`](Docs/README.md).

## Antes de qualquer coisa

1. Leia `Docs/README.md` e `CLAUDE.md` (regras de operação destrutiva — valem para pessoas e agentes).
2. `make setup && make hooks`.

## Branches

- `master` é produção. `develop` é integração. Trabalho em `release/*`, `feat/*`, `fix/*`.
- Nunca `main`.

## Commits

- Conventional Commits em português: `feat:`, `fix:`, `docs:`, `chore:`, `style:`, `refactor:`,
  `test:`, `ci:` — com escopo quando ajuda (`feat(clip-processor): ...`, `fix(painel): ...`).
- Um assunto por commit. Formatação (`style:`) separada de comportamento.
- Sem trailers de autoria de IA (`Co-Authored-By`).
- `make lint` (ou os hooks do pre-commit) verde antes de commitar.

## Changelog

Toda mudança relevante ganha um fragmento em `CHANGELOG.d/<slug>.<tipo>.md`
(`novidade | melhoria | correcao | tecnico`). Não edite `CHANGELOG.md` à mão — `make changelog-release`
faz isso ao fechar a versão. Regras em `CHANGELOG.d/README.md`.

## Versões

`v0.MINOR.PATCH`. Primeira tag será `v0.1.0`. Como fechar: `Docs/DESENVOLVIMENTO.md` §7.

## Documentação

Status mora no documento, não na conversa: bug corrigido → `Docs/BUGS.md`; comportamento de subsistema →
`Docs/SISTEMA-*.md`; decisão de arquitetura → `Docs/ADR/`; dívida → `Docs/TODO-REFATORACAO.md`.
Datas sempre absolutas, referências de código como `arquivo:linha`.
