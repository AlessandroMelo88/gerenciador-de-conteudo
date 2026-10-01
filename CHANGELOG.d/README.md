# CHANGELOG.d — fragmentos de release notes

Cada mudança relevante ganha **um arquivo aqui**, em vez de editar o `CHANGELOG.md` direto.
Isso evita conflito de merge no changelog e deixa o `[Unreleased]` sempre montável.

## Nome do arquivo

```
CHANGELOG.d/<slug>.<tipo>.md
```

| `tipo`     | Vira a seção     | Use para                                   |
|------------|------------------|--------------------------------------------|
| `novidade` | `### ✨ Novidades` | feature nova — nome em **negrito**, `—`, descrição |
| `melhoria` | `### 🎨 Melhorias` | melhoria em algo que já existia            |
| `correcao` | `### 🐛 Correções` | bug corrigido                              |
| `tecnico`  | `### 🔧 Técnico`   | refatoração, infra, ferramentas, docs      |

`slug` é livre (kebab-case, curto, único). Arquivos começando com `_` são ignorados.

## Conteúdo

Uma linha por item. O prefixo `- [x]` é adicionado automaticamente; escreva-o você mesmo
se quiser marcar um item como pendente (`- [ ]`). Linhas iniciadas por espaço são
continuação do item anterior. Exemplo (`restore-postgres.tecnico.md`):

```
**Restauração guardada do PostgreSQL** — `scripts/restore-postgres.sh` exige `CONFIRM_RESTORE` e confere o SHA-256
```

## Comandos

```bash
make changelog-preview                 # mostra a seção [Unreleased] montada
make changelog-release VERSION=v0.2.0  # move os fragmentos para o CHANGELOG.md e os apaga
```

O `release` cria um cabeçalho de versão com link de comparação logo abaixo de `[Unreleased]`,
usando a versão anterior encontrada no próprio CHANGELOG para montar o link
(`.../releases/tag/vX.Y.Z` quando é a primeira). Ele **não** faz bump de versão nem tag —
o fluxo completo de fechar versão está em `Docs/operacao/DESENVOLVIMENTO.md`.
