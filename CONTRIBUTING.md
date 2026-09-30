# Contribuindo

> Guia curto. A documentação completa está em [`Docs/README.md`](Docs/README.md).

## Antes de alterar

1. Leia [`CLAUDE.md`](CLAUDE.md) antes de tocar em dados, Docker, disco ou estados transitórios.
2. Consulte o documento do subsistema em [`Docs/sistema/`](Docs/sistema/README.md).
3. Confirme a fonte de verdade no código, migrations, Compose e `.env.example`.
4. Ambiente local, lint e testes: [`Docs/DESENVOLVIMENTO.md`](Docs/DESENVOLVIMENTO.md).

## Branches e commits

- Produção roda a `master`; não existe `develop`. Toda tarefa sai da `master` atualizada, numa branch
  com prefixo `feature/`, `fix/`, `hotfix/`, `docs/` ou `chore/`, e volta com merge `--no-ff`.
  Regras completas: `.claude/skills/gitflow/SKILL.md`.
- Commits convencionais em português (`feat:`, `fix:`, `docs:`, `test:`, `chore:`...), um assunto
  por commit.
- O repositório é público: nunca commitar `.env`, chave, token ou `client_secret`.

## Verificação

~~~bash
make lint
make test-python
make test-php     # exige o Postgres avulso de scripts/dev-pgvector.sh
~~~

Alterações de comportamento devem incluir teste ou explicar por que não há cobertura.

## Changelog e documentação

Mudança relevante recebe fragmento em `CHANGELOG.d/<slug>.<tipo>.md`; não edite `CHANGELOG.md`
manualmente. Tipos: `novidade`, `melhoria`, `correcao`, `tecnico`.

Atualize o documento do subsistema quando o comportamento mudar, e
[`Docs/sistema/ESTADOS-E-TRANSICOES.md`](Docs/sistema/ESTADOS-E-TRANSICOES.md) quando mudar estado ou
transição. Decisões estruturais novas entram em um ADR novo em [`Docs/adr/`](Docs/adr/README.md).
Use datas absolutas e caminhos reais; não documente planos como se fossem funcionalidades.
