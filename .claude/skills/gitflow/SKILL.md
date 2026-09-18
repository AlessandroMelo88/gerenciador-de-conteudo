---
name: gitflow
description: Use SEMPRE que qualquer tarefa do Canal de Cortes for começar, ramificar, nomear branch, commitar, abrir correção urgente ou fechar trabalho — "vamos fazer X", "corrige Y", "cria a branch", "faz o commit", "hotfix", "qual branch eu uso". Define o Gitflow obrigatório do projeto: de onde sair, como nomear, onde mesclar e quando apagar a branch.
---

# Gitflow do Canal de Cortes

**Toda tarefa nasce numa branch.** Nunca commitar direto na `master`. Vale para código, documentação,
configuração e script — inclusive mudança de uma linha.

Referência do modelo: [Gitflow (XP Inc.)](https://medium.com/xp-inc/trabalhando-com-o-gitflow-a8ae0e1ddaae).
Aqui ele vem **adaptado**: uma pessoa, deploy contínuo, sem `develop` e sem `release`.

## Branches permanentes

| Branch | Papel |
|---|---|
| `master` | O que está em produção. Só recebe merge, nunca commit direto. Protegida pelo `deploy.sh` |

Não existe `develop` neste projeto: com um desenvolvedor e deploy diário, ela só criaria um desvio a
mais. O papel de "integração" é da própria `master`, que só recebe trabalho testado.

## Branches de trabalho

| Prefixo | Para quê | Sai de | Volta para |
|---|---|---|---|
| `feature/` | funcionalidade nova, tela, canal, integração | `master` | `master` |
| `fix/` | correção de bug do backlog (`Docs/sistema/BUGS.md`) | `master` | `master` |
| `hotfix/` | produção quebrada agora | `master` | `master`, com deploy imediato |
| `docs/` | só documentação, sem efeito em runtime | `master` | `master` |
| `chore/` | dependência, build, CI, limpeza | `master` | `master` |

**Nome:** prefixo + assunto curto em kebab-case, sem acento e sem número solto.
`fix/bug17-finaliza-video-rejeitado`, `feature/canais-mbl`, `hotfix/publisher-token-expirado`.
Se houver bug no backlog, o número entra no nome.

**Branch de longa duração** (hoje nenhuma; `afiliadas-fase2` entrou na master em 18/09/2026): traz a `master` para dentro dela com frequência
(`git merge master`), senão o merge final vira um conflito só. Nunca o contrário.

## Ciclo de uma tarefa

```bash
# 1. sair sempre da master atualizada
git switch master && git pull --ff-only origin master
git switch -c feature/assunto-curto

# 2. trabalhar em commits pequenos, cada um com uma ideia
git add <arquivos>            # nunca `git add -A` às cegas
git commit                    # mensagem no padrão abaixo

# 3. antes de fechar: testes da área alterada (ver skill finalizar-e-deploy)

# 4. fechar
git switch master && git pull --ff-only origin master
git merge --no-ff feature/assunto-curto
git push origin master
./deploy.sh                   # ou --skip-vite se não mexeu no frontend

# 5. apagar a branch já mesclada
git branch -d feature/assunto-curto
```

`--no-ff` no merge de propósito: mantém visível na história o agrupamento de commits daquela tarefa.

## Mensagem de commit

Convencional, em português, no imperativo:

```
tipo(escopo): resumo em uma linha, minúsculo, sem ponto final

Corpo explicando o porquê, não o quê. O diff já diz o quê.
Cita bug do backlog quando houver.
```

Tipos: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `perf`, `security`.
Escopos usados: `painel`, `clip-processor`, `pipeline`, `publisher`, `seletor`, `worker`, `a1`,
`compose`, `deploy`, `bug N`.

Rodapé de autoria conforme as instruções da sessão.

## Regras que não se negociam

1. **Nada de commit direto na `master`.** Se aconteceu por engano e ainda não subiu:
   `git branch fix/assunto && git reset --hard origin/master && git switch fix/assunto`.
2. **Nada de `git push --force` sem tag de backup antes** (`git tag backup/<branch>-AAAAMMDD`).
3. **Segredo nunca entra em commit.** `.env`, chave, token, `client_secret`, cookie. O repositório é
   público; a varredura obrigatória está na skill `finalizar-e-deploy`.
4. **Branch mesclada é apagada.** Branch abandonada ganha tag de backup antes de sumir.
5. **`hotfix/` fura a fila**, mas segue o mesmo caminho: branch, teste, merge, deploy. Nunca direto na
   produção pelo SSH — o servidor não tem git e o próximo deploy sobrescreveria a correção.
6. **Rebase só dentro da própria branch**, nunca em algo que já foi para o GitHub.

## Estado das branches (17/09/2026)

| Branch | Situação |
|---|---|
| `master` | produção, VM A1 com PostgreSQL |
| `afiliadas-fase2` | **mesclada** na master em 18/09/2026; afiliados segue em branches curtas |
| `afiliadas` | **apagada** em 17/09/2026; backup na tag `backup/afiliadas-20260917` |
| `feature/fontes-seguras-futebol`, `fix/pendencias-fontes-e-seletor`, `fix/bug17-…` | locais antigas; conferir se já estão na master e apagar |
