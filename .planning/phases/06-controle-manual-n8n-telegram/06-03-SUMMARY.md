---
phase: 06-controle-manual-n8n-telegram
plan: 03
subsystem: api

tags: [tdd, mysql, rejeitar, telegram, cli, status-machine, phase-6-wave-1]

requires:
  - phase: 06-controle-manual-n8n-telegram
    provides: "Plan 06-01 entregou stub rejeitar(clip_id) + 3 testes RED em test_rejeitar.py + ENUM com 'rejected' (migration 05-controle-manual-migration.sql)"
provides:
  - "rejeitar(clip_id) — função Python que faz SELECT + UPDATE guardado por status + delete MP4 + preserva raw video"
  - "Entrypoint CLI `python -m src.rejeitar <id>` com exit codes documentados (0/1/2) para uso pelo n8n executeCommand"
  - "Pattern: alias `db_connect = get_db_connection` no namespace do módulo para que testes possam patchar via `src.<modulo>.db_connect`"
affects: [06-07-n8n-flows]

tech-stack:
  added: []
  patterns:
    - "Guard de status em UPDATE: `WHERE id=%s AND status IN ('pending','approved')` — proteção atômica contra race com publisher (que move approved→publishing)"
    - "SELECT + check + UPDATE no MESMO cursor antes do commit — evita condition race entre leitura e escrita sem precisar de SELECT ... FOR UPDATE"
    - "CLI entrypoint defensivo: valida len(sys.argv) e int(sys.argv[1]) antes de chamar a função, exit code 2 em argumentos inválidos"

key-files:
  created: []
  modified:
    - clip-processor/src/rejeitar.py

key-decisions:
  - "Dois cur.execute (SELECT + UPDATE) no mesmo cursor: SELECT lê clip_path+status; UPDATE aplica guard `status IN ('pending','approved')` — evita race condicional (leitura→escrita) sem precisar de transação isolada ou SELECT FOR UPDATE. Se publisher mover approved→publishing entre o SELECT e o UPDATE, rowcount=0 e MP4 não é removido."
  - "Exit codes: 0 sucesso, 1 clip não existe, 2 status inválido para rejeição OU argumento CLI inválido — n8n executeCommand propaga para o bot reportar diferenciado ao operador"
  - "Alias `db_connect = get_db_connection` (via `from src.db import get_db_connection as db_connect`) — satisfaz o contrato dos testes que patcheiam `src.rejeitar.db_connect`, sem alterar a API pública de src.db"
  - "Raw video NUNCA é deletado em /rejeitar (decisão explícita de 06-CONTEXT.md). Apenas clip_path da tabela generated_clips. Cleanup de raw fica em rotina dedicada de housekeeping (deferred Phase 6)"
  - "Status 'approved' é rejeitável (não apenas 'pending'): operador pode mudar de ideia entre /aprovar e a janela de upload. Race com publisher resolvida pelo guard atomico no UPDATE"

patterns-established:
  - "Status guard em UPDATE: para qualquer transição de status sensível a race, usar `UPDATE ... SET status='X' WHERE id=%s AND status IN (<estados validos>)` e checar rowcount antes de side-effects (delete de arquivo, notificação externa)"
  - "Testes patcheiam funções importadas pelo nome usado no namespace do módulo, não pelo nome original em src.db — favorecer alias module-level via `from X import Y as Z` quando o teste pré-existe (Wave 0 RED)"

requirements-completed: [CTRL-03]

duration: 5min
completed: 2026-06-19
---

# Phase 6 Plan 03: Rejeitar Summary

**Comando `/rejeitar <id>` do Telegram: rejeitar.py marca clip como rejected via UPDATE guardado por `status IN ('pending','approved')`, remove o MP4 do disco e preserva o raw video do source_videos para recorte futuro.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-06-19T20:18:08Z
- **Completed:** 2026-06-19T20:21:58Z
- **Tasks:** 1 (auto, TDD GREEN)
- **Files modified:** 1

## Accomplishments

- **`rejeitar(clip_id)`** implementada com SELECT clip_path/status, guard de status terminal, UPDATE com filtro atômico em `status IN ('pending','approved')`, delete condicional do MP4 (`os.remove` apenas se `os.path.exists`) e preservação explícita do raw video do source_videos.
- **3 testes RED em GREEN** localmente (`test_marca_rejected`, `test_apaga_mp4_mantem_raw`, `test_clip_nao_existe`) — todos os 3 critérios de sucesso 6-03-01/02/03 satisfeitos.
- **CLI entrypoint** `python -m src.rejeitar <clip_id>` validando argumentos antes de chamar a função (exit code 2 para argv ausente / inválido). Pronto para n8n executeCommand.
- **Suíte completa preservada**: 91 testes pré-existentes continuam GREEN; nenhum regression. Os 13 RED restantes são todos planejados (Plans 06-02, 06-04, 06-05, 06-06).

## Task Commits

1. **Task 1 (TDD GREEN): Implementar rejeitar.py — SELECT + UPDATE guardado + delete MP4 + entrypoint CLI** — `adad56f` (feat)

_Plan metadata commit segue após este SUMMARY._

## Files Created/Modified

### Modificados

- `clip-processor/src/rejeitar.py` — Stub Plan 06-01 substituído pela implementação completa: import `os`/`sys`, alias `db_connect`, constante `_REJECTABLE_STATUSES=('pending','approved')`, função `rejeitar(clip_id) -> int` com SELECT + guard + UPDATE + delete condicional, e bloco `if __name__ == '__main__'` validando argumentos CLI.

## Decisions Made

### Decisão técnica: dois `cur.execute` no mesmo cursor

O fluxo é **SELECT clip_path, status → checa se row existe → checa se status é rejeitável → UPDATE com guard atômico → commit → side-effects**. Justificativa:

1. **Por que SELECT antes?** Precisamos do `clip_path` para deletar o MP4 e do `status` para retornar exit code diferenciado (1 vs 2). UPDATE direto não dá essa visibilidade.
2. **Por que UPDATE com guard mesmo após SELECT?** Janela entre SELECT e UPDATE permite race com o publisher (que move `approved → publishing`). Se o publisher venceu, `cur.rowcount=0` e **não removemos o MP4** (publisher precisa dele para upload).
3. **Por que não SELECT FOR UPDATE?** Overhead desnecessário — o guard no UPDATE já garante consistência. Comportamento "publisher venceu = rejeitar silenciosa sem side-effect" é aceitável.

### Exit codes documentados

| Code | Significado                                                | Ação do n8n                                      |
| ---- | ---------------------------------------------------------- | ------------------------------------------------ |
| 0    | sucesso (clip rejeitado, MP4 removido se existia)          | confirmar ao operador `✓ Clip <id> rejeitado`    |
| 1    | clip não existe (id não encontrado em generated_clips)     | `✗ Clip <id> não encontrado`                     |
| 2    | status inválido (terminal: rejected/published/failed/...) OU argumento CLI inválido | `✗ Clip <id> não pode ser rejeitado nesse estado` |

### Como o n8n usará

No workflow `06-router.json` (Plan 06-07), o output `rejeitar` do Switch v2 conecta a um nó `executeCommand` com:

```
docker exec clip-processor python -m src.rejeitar {{ $('Parse Comando').first().json.arg }}
```

O exit code propaga via `$json.exitCode` no nó subsequente — `0` → mensagem de sucesso; `!= 0` → mensagem de erro (stderr/stdout do container já tem o detalhe via `print()`).

### Nota: `/aprovar` NÃO requer módulo Python

`/aprovar <id>` será feito **diretamente pelo n8n MySQL node** com query parametrizada `UPDATE generated_clips SET status='approved' WHERE id=? AND status='pending'` — mais simples que invocar Python via docker exec, e o publisher (Plan 06-02) já cuida do swap pending→approved no lado de leitura. Decisão registrada em Plan 06-07 (n8n flows).

## Deviations from Plan

None - plan executed exactly as written.

Observação: o plano descrevia `from src.db import get_db_connection` direto, mas os testes pré-existentes (Plan 06-01) patcheiam `src.rejeitar.db_connect`. Implementei via alias `from src.db import get_db_connection as db_connect` — **não é deviation** porque o `<context>` do plano explicitamente referenciava o test file e o "Pontos Abertos" do Plan 06-01 já indicava esse contrato (`patch('src.rejeitar.db_connect', ...)`).

## Issues Encountered

None.

## User Setup Required

Nenhum nesta wave. A função pode ser exercitada localmente via:

```bash
docker exec clip-processor python -m src.rejeitar 99999   # exit 1: clip não existe
docker exec clip-processor python -m src.rejeitar abc     # exit 2: argumento inválido
```

Ativação real do comando `/rejeitar` no Telegram acontece em Plan 06-07 (n8n flows).

## Next Phase Readiness

- **Plan 06-07 (n8n flows)** pode conectar o output `rejeitar` do Switch ao nó `executeCommand` com `python -m src.rejeitar {{ arg }}` — contrato CLI estável e exit codes documentados.
- **Plan 06-02 (publisher swap pending→approved)** continua independente desta wave; o guard `status IN ('pending','approved')` aqui já contempla o estado pós-swap.
- **Cleanup de raw video** (housekeeping) permanece deferred conforme 06-CONTEXT.md — Phase 6 não toca em source_videos.local_path em nenhum momento.

## Self-Check: PASSED

Verificações realizadas:

- `clip-processor/src/rejeitar.py` existe (`ls` confirma) e contém implementação completa: imports `os`/`sys`/`db_connect`, função `rejeitar`, entrypoint CLI
- `pytest tests/test_rejeitar.py -v` localmente: 3 PASSED (test_marca_rejected, test_apaga_mp4_mantem_raw, test_clip_nao_existe) — todos os critérios 6-03-01/02/03 satisfeitos
- `python3 -c "from src.rejeitar import rejeitar; assert callable(rejeitar)"` retorna OK
- `grep raw_path|video_path /clip-processor/src/rejeitar.py` retorna apenas matches em comentário/docstring (nenhum `os.remove` ou query SQL aplica a raw)
- Suíte completa: 91 GREEN + 13 RED (todos esperados — Plans 06-02/04/05/06)
- Commit `adad56f` presente em `git log --oneline`

---
*Phase: 06-controle-manual-n8n-telegram*
*Completed: 2026-06-19*
