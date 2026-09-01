# Instruções de trabalho — Canal de Cortes

Comece pelo índice [`Docs/README.md`](Docs/README.md). Para arquitetura, leia
[`ARCHITECTURE.md`](ARCHITECTURE.md). Em caso de divergência, o código executado,
migrations, `docker-compose.yml` e `.env.example` vencem a documentação.

## Regras operacionais

1. Antes de apagar qualquer coisa, liste o alvo, conte itens, calcule tamanho e confirme o escopo.
2. Use caminhos absolutos e valide o resultado depois; apague arquivo antes de atualizar o banco.
3. Ao cruzar banco e disco, filtre pela chave do registro, não apenas pelo nome do arquivo.
4. Nunca use `docker compose down -v`, `docker system prune`,
   `docker image prune`, `git clean`, `git reset --hard` ou
   `FLUSHALL` sem autorização explícita e escopo comprovado.
5. Faça backup antes de `DELETE`, `DROP`, `TRUNCATE` ou limpeza em massa.
6. Trate `selecting`, `pending_cut`, `cutting` e `publishing`
   como trabalho potencialmente ativo; não classifique como lixo sem verificar idade e processo.
7. O raw ainda é necessário enquanto houver clip em `pending_cut` ou `cutting`.
   O banco pode não registrar todos os artefatos auxiliares.

## Operação do runtime

- A fila é PostgreSQL: `source_videos` e `generated_clips`. Redis guarda dedup,
  quota e idempotência de avisos; limpar Redis não limpa a fila.
- Alterar `clip-processor/src` exige rebuild porque o código está embutido na imagem:
  `docker compose build clip-processor && docker compose up -d clip-processor`.
- `PIPELINE_ENABLED=false` pausa ingestão/publicação, mas mantém o sidecar disponível.
- Antes de restart, confira clips em corte/publicação e logs do processador.

Recovery implementado:

| Situação | Ação automática |
|---|---|
| `downloading` preso | volta para `pending` |
| `selecting` antigo/sem arquivo | volta ou falha conforme as evidências |
| `publishing` preso | volta para fila após timeout |
| `cutting` no boot | volta para `pending_cut` |
| `transcribing` | sem recovery automático; avaliar manualmente |

## Documentação e grafo

Documentos atuais estão em `Docs/`. ADRs preservam decisões e planos não são runtime.
Quando `graphify-out/graph.json` existir, consultas sobre arquitetura/código devem começar
por `graphify query`; use o código para confirmar detalhes. Não execute rebuild do grafo
apenas por editar documentação.

## Checklist rápido

~~~bash
git status --short
docker compose ps
docker compose logs --tail=100 clip-processor
~~~

Nunca estenda uma operação destrutiva para outros projetos, volumes ou workspaces.
