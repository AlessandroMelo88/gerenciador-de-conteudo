# Deploy automático diário — opções e decisão

**Estado: só desenho. Nada implementado** (decisão do operador em 17/09/2026: "deixa o deploy pra
depois, mas deixe documentado"). Hoje o deploy é manual: `./deploy.sh` a partir do Mac, com a
`master` igual ao GitHub. Ver [`DEPLOY.md`](../../DEPLOY.md) e a skill `finalizar-e-deploy`.

## O que se quer

Deploy do que está na `master` do GitHub, todo dia às **6h (BRT)**, **sem reiniciar o processador no
meio de um corte** ([bug 11](BUGS.md#11-aberto--container-não-honra-sigterm-todo-docker-stop-vira-sigkill)).

## As três opções

```
A)  Mac (launchd 6h) ──rsync──> A1
B)  A1 (cron 6h) ──git pull──> GitHub
C)  GitHub Actions (cron 6h) ──testes──> ssh ──> A1
```

| | A) launchd no Mac | B) cron na A1 puxando do GitHub | C) GitHub Actions + ssh |
|---|---|---|---|
| Depende do Mac ligado e acordado | **sim** | não | não |
| Reusa o `deploy.sh` como está | sim, zero código novo | não: a A1 não tem git nem Node, precisa de um deploy do lado servidor | sim, o runner faz o papel do Mac |
| Roda a suíte antes de subir | não | não | **sim**, em ambiente limpo |
| Segredo novo exposto | nenhum | nenhum | chave SSH de produção como *secret* do GitHub |
| Onde se lê o que aconteceu | log local do launchd | log do cron na VM | histórico do Actions, com diff e teste |
| Custo | zero | zero | zero (repo público) |

**Recomendação: C.** É a única que impede subir código que quebrou o teste, e a única que não depende
de uma máquina pessoal estar acordada às 6h. B é o plano B se não quiser chave de produção no GitHub.
A serve só como muleta temporária.

## A trava obrigatória, em qualquer uma das três

Antes de mexer nos containers:

```sql
SELECT count(*) FROM generated_clips WHERE status IN ('cutting', 'publishing');
```

- resultado `0` → pode deployar;
- maior que zero → espera em laço, conferindo a cada minuto, por até 15 min;
- ainda maior que zero no fim → **aborta o deploy** e deixa para a próxima janela.

Sem essa trava o deploy mata `ffmpeg` no meio do corte, e o clip fica preso para sempre em `cutting`
ou `publishing` — estados que **não têm recuperação automática** (bug 4). `publishing` é o pior caso:
o vídeo pode ter subido no YouTube com o banco registrando outra coisa.

O conserto de verdade do bug 11 (o `BlockingScheduler` não retorna do `shutdown`, então todo
`docker stop` vira `SIGKILL`) é tarefa separada e **deveria vir antes** de ligar qualquer deploy
automático.

## Pendências antes de implementar

- [ ] Corrigir o bug 11 (SIGTERM honrado pelo clip-processor)
- [ ] Decidir entre C e B
- [ ] Se C: gerar uma chave SSH só para o deploy (não reusar a `oracle-a1-2026-09-16.key` pessoal),
      restringir a chave por `command=` no `authorized_keys` da A1
- [ ] Fazer o `deploy.sh` aceitar um modo não interativo com código de saída claro para o CI
