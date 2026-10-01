# Estado do sistema em agosto/2026 (arquivado)

**Status:** OBSOLETO · retrato de 12-13/08/2026, retirado do índice de `Docs/sistema/` em 01/10/2026.
Não descreve a produção de hoje: o banco agora é PostgreSQL 17 na VM A1, a migração para a Oracle já
foi feita, e os bugs 4 e 11 foram corrigidos e estão no ar. Estado vigente: [`../ESTADO-DO-PROJETO.md`](../ESTADO-DO-PROJETO.md)
e [`../PROGRESSO.md`](../PROGRESSO.md). Texto preservado como estava.

---

## Estado atual em uma tela

**Stack do painel:** Laravel 13 + Inertia 3 + **React 19** + shadcn/ui + Tailwind 4 + Vite 8 +
TypeScript, desde o commit `dca6e44`. **O Filament foi removido por completo** — qualquer menção a ele
em README, nome de arquivo ou teste é resíduo, não estado atual.

**Infra:** roda 100% local em Docker, no `docker-compose.yml` da raiz `wordpress/` **compartilhado com
outros projetos** (kelnab, feeb, placebeads, riodelux, gringo). Mexer apenas no serviço
`clip-processor` e nos paths sob `canaldecortes/`. Migração para Oracle **não iniciada** — os
pré-requisitos de código (fase 1) estão em andamento.

**Problema que motivou a migração:** SSD de 228 GB chegou a 85% de uso e derrubou o Docker. Parte era
volume real, parte era vazamento de arquivo.

**Prazo externo em aberto:** a Oracle cortou o Always Free de 4 OCPU/24 GB para 2 OCPU/12 GB e desliga
instâncias fora do novo limite a partir de **18/08/2026**. Se já existe instância na conta, conferir o
shape antes dessa data — e **redimensionar, nunca terminar**.

**Bugs:** 4 corrigidos, 1 parcial, 5 abertos, 1 suspeita. Detalhe e prioridade em
[`BUGS.md`](../operacao/BUGS.md).

### Corrigido em 12–13/08/2026

| O quê | Onde |
|---|---|
| `_raw.mp4` e `_subtitled.mp4` passaram a ser apagados na finalização do vídeo fonte | `publisher.py` (commit `5009112`) |
| Download falho apaga o arquivo e zera `local_path` — antes vazava disco e entupia a janela para sempre (58 vídeos, 4.1 GB, pipeline parado) | `_discard_failed_download` em `pipeline_runner.py` |
| Recovery de estado preso virou job periódico de 30 min, não só no boot | `main.py`, job `state_recovery` |
| `selecting` com `local_path IS NULL` sem update há 2 h agora vai para `failed` — antes ficava preso para sempre | terceira query de `recover_stuck_selecting` em `db.py` |
| `MIN_SHORTFORM_SECONDS` subiu de 15 s para **30 s** e o prompt do modo curto foi reescrito | `selector.py` |

### Os dois que mais doem hoje

1. **Nada em `cutting`, `publishing` ou `transcribing` tem recuperação automática** — o que travar ali
   fica preso para sempre e segura arquivo em disco (bug 4).
2. **O container não honra SIGTERM:** todo `docker stop` termina em `Exited (137)` / SIGKILL porque o
   `BlockingScheduler` não retorna do `shutdown` (bug 11). Junto com o item 1, cada restart pode criar
   um estado preso novo. Por isso o [`RUNBOOK.md`](../operacao/RUNBOOK.md#reiniciar-o-clip-processor-com-segurança)
   manda conferir o que está em trânsito antes de parar o container.

---
