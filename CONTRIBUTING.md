# Contribuindo

> Guia curto. A documentação completa está em [`Docs/README.md`](Docs/README.md).

## Antes de alterar

1. Leia [`CLAUDE.md`](CLAUDE.md) antes de tocar em dados, Docker, disco ou estados transitórios.
2. Consulte o documento do subsistema em [`Docs/`](Docs/README.md).
3. Confirme a fonte de verdade no código, migrations, Compose e `.env.example`.
4. Use `make setup` e `make hooks` no ambiente local.

## Branches e commits

- Produção fica em `master`; integração, quando usada, em `develop`.
- Crie branches de trabalho com prefixo `feat/`, `fix/` ou equivalente.
- Use Conventional Commits: `feat:`, `fix:`, `docs:`, `test:`,
  `chore:`, com escopo quando útil.
- Mantenha um assunto por commit e não adicione trailers de autoria de IA.

## Verificação

~~~bash
make lint
make test-python
make test-php
~~~

Execute o conjunto relevante após cada mudança; alterações de comportamento devem incluir teste ou
explicar por que não há cobertura.

## Changelog e documentação

Mudança relevante recebe fragmento em `CHANGELOG.d/<slug>.<tipo>.md`; não edite
`CHANGELOG.md` manualmente. Use tipos `novidade`, `melhoria`,
`correcao` ou `tecnico`.

Atualize o documento do subsistema quando o comportamento mudar. Atualize
[`Docs/ESTADOS-E-TRANSICOES.md`](Docs/ESTADOS-E-TRANSICOES.md) quando mudar estado ou
transição. Decisões estruturais novas entram em um ADR novo. Use datas absolutas
(`YYYY-MM-DD`) e caminhos reais; não documente planos como se fossem funcionalidades.
