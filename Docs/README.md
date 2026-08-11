# Docs — Canal de Cortes

Índice da documentação. **Comece por aqui em toda conversa nova.**

Última atualização: **11/08/2026**

---

## Onde está cada coisa

| Documento | Para quê | Quando ler |
|---|---|---|
| [`../ARCHITECTURE.md`](../ARCHITECTURE.md) | Arquitetura as-built: o que o sistema faz, fronteira painel ↔ pipeline, máquina de estados, schema, dívida técnica | Primeira leitura de quem chega agora |
| [`BUGS.md`](BUGS.md) | Backlog de bugs com status ABERTO/FEITO, evidência e onde corrigir | Antes de mexer em qualquer coisa |
| [`PLANO-ORACLE.md`](PLANO-ORACLE.md) | Migração para servidor Oracle Cloud, com checklist por fase e as regras que garantem custo zero | Trabalho de infra |
| [`SISTEMA-CLIP-PROCESSOR.md`](SISTEMA-CLIP-PROCESSOR.md) | Referência módulo a módulo do daemon Python | Mexer no pipeline |
| [`SISTEMA-PAINEL.md`](SISTEMA-PAINEL.md) | Referência de rotas, controllers e páginas do Laravel/Inertia | Mexer no painel |
| [`../CLAUDE.md`](../CLAUDE.md) | Regras de operação destrutiva e incidentes já vividos | Antes de apagar qualquer coisa |

`.planning/` é do fluxo GSD (roadmap por fase) e **não** é fonte de verdade do estado atual. `.planning/research/ARCHITECTURE.md` é pesquisa de junho/2026 e descreve um futuro que não aconteceu — ignorar.

---

## Estado atual em uma tela

**Infra:** roda 100% local em Docker, no `docker-compose.yml` da raiz `wordpress/` compartilhado com outros projetos (kelnab, feeb, placebeads, riodelux, gringo). Migração para Oracle **não iniciada** — ver [`PLANO-ORACLE.md`](PLANO-ORACLE.md).

**Problema que motivou a migração:** SSD de 228GB chegou a 85% de uso e derrubou o Docker. Parte era volume real, parte era vazamento de arquivo (ver BUGS 1 e 2).

**Prazo externo em aberto:** a Oracle cortou o Always Free de 4 OCPU/24GB para 2 OCPU/12GB e desliga instâncias fora do novo limite a partir de **18/08/2026**. Se já existe instância na conta, conferir o shape antes dessa data.

**Bugs:** 1 corrigido, 7 abertos. Detalhe e prioridade em [`BUGS.md`](BUGS.md).

---

## Como atualizar estes documentos

Regra única: **status mora no documento, não na cabeça de ninguém.**

- Corrigiu um bug → muda o status em `BUGS.md` para FEITO, com data e commit.
- Concluiu uma fase da migração → marca o checkbox em `PLANO-ORACLE.md`.
- Mudou comportamento do sistema → atualiza `SISTEMA-*.md` e, se for estrutural, `ARCHITECTURE.md`.
- Descobriu incidente novo de operação destrutiva → `CLAUDE.md`, não aqui.

Datas sempre absolutas (`11/08/2026`), nunca relativas ("semana passada") — estes arquivos são lidos meses depois.
