---
phase: 06-controle-manual-n8n-telegram
plan: 02
subsystem: publisher

tags: [tdd, mysql, publisher, status-machine, race-guard, phase-6-wave-1]

requires:
  - phase: 06-controle-manual-n8n-telegram
    provides: "Plan 06-01 entregou TestPublishApprovedClips (3 testes RED) em test_publisher.py + ENUM com 'approved' na migration 05-controle-manual-migration.sql"
provides:
  - publisher.publish_pending_clips agora seleciona apenas clips status='approved' (não mais 'pending')
  - _transition_approved_to_publishing com guard WHERE id=%s AND status='approved' + rowcount check
  - Defesa contra race condition com /rejeitar concorrente — skip silencioso quando 0 rows afetadas
  - Mensagens de log atualizadas (approved em vez de pending)
affects:
  - 06-03-rejeitar (race scenario coberto): /rejeitar agora pode atuar com segurança em paralelo a publish
  - 06-07-n8n-flows: comando /aprovar passa clip de 'pending' → 'approved'; publisher consome a partir daí

tech-stack:
  added: []
  patterns:
    - "Guard de status no UPDATE com `WHERE id=%s AND status='X'` + verificação de cursor.rowcount: padrão de defesa contra race entre worker e operações manuais (RESEARCH Pitfall 2)"
    - "Skip silencioso (log + continue) quando rowcount=0: clip pulado sem exception; loop processa próximos clips approved normalmente"

key-files:
  created: []
  modified:
    - clip-processor/src/publisher.py
    - clip-processor/tests/test_publisher.py

key-decisions:
  - "SELECT muda de status='pending' para status='approved' (literal único) — pipeline para de publicar automaticamente; requer aprovação humana via /aprovar"
  - "Guard de status no UPDATE approved→publishing usa cursor.rowcount: se 0, clip foi rejeitado em paralelo — log 'Clip {id} pulado: status mudou durante seleção' e continue (sem exception)"
  - "Função dedicada _transition_approved_to_publishing (não reuso _update_clip_status genérico): expressa a intenção de guarded transition e isola o COMMIT mesmo no caso 0 rows"
  - "Fixture make_conn_with_clips ajustada com cursor.rowcount=1 — simula MySQL retornando 1 row no caminho feliz (Rule 3 - blocking: testes legados precisavam de update para suportar nova feature)"
  - "QuotaManager, janela horária 19h-22h America/Sao_Paulo e cleanup do raw video NÃO foram tocados — mudança cirúrgica conforme objetivo do plan"

patterns-established:
  - "Phase 6 race-defense pattern: SELECT WHERE status='X' + UPDATE WHERE id=%s AND status='X' + rowcount check (vai se replicar em /rejeitar Plan 06-03 e /aprovar n8n flow Plan 06-07)"
  - "Logs de transição de status sempre mencionam o status atual: 'mantido approved por quota/janela', 'Próximo clip approved: id={id}', 'pulado: status mudou durante seleção'"

requirements-completed: [CTRL-02]

duration: 8min
completed: 2026-06-19
---

# Phase 6 Plan 02: Publisher Swap pending→approved + Guard de Status

**Swap de 1 literal (`pending` → `approved`) no SELECT do publisher + guard de status no UPDATE para publishing (defesa contra race com `/rejeitar`). Mudança cirúrgica que ativa o gate de aprovação manual (CTRL-02) sem tocar quota, janela horária ou cleanup do raw video.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-06-19T20:16:32Z
- **Completed:** 2026-06-19T20:25:06Z
- **Tasks:** 1 (auto + tdd)
- **Files modified:** 2

## Mudanças Exatas

### `clip-processor/src/publisher.py`

**1. SELECT — `_fetch_pending_clips`:**

Antes:
```python
def _fetch_pending_clips(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            'SELECT '
            'gc.id, gc.source_video_id, gc.clip_path, gc.thumbnail_path, '
            'gc.title, gc.description, gc.tags, sv.local_path AS source_local_path '
            'FROM generated_clips gc '
            'JOIN source_videos sv ON sv.id = gc.source_video_id '
            "WHERE gc.status = 'pending' "
            'AND gc.clip_path IS NOT NULL '
            'AND gc.title IS NOT NULL '
            'ORDER BY gc.created_at ASC'
        )
        return cur.fetchall()
```

Depois:
```python
def _fetch_pending_clips(conn) -> list[dict]:
    # Phase 6: seleciona apenas 'approved' (mudança de pending). Bot Telegram aprova via /aprovar.
    with conn.cursor() as cur:
        cur.execute(
            'SELECT '
            'gc.id, gc.source_video_id, gc.clip_path, gc.thumbnail_path, '
            'gc.title, gc.description, gc.tags, sv.local_path AS source_local_path '
            'FROM generated_clips gc '
            'JOIN source_videos sv ON sv.id = gc.source_video_id '
            "WHERE gc.status = 'approved' "
            'AND gc.clip_path IS NOT NULL '
            'AND gc.title IS NOT NULL '
            'ORDER BY gc.created_at ASC'
        )
        return cur.fetchall()
```

Nome `_fetch_pending_clips` mantido por estabilidade da API interna; semântica passou a ser "fetch approved clips" (refletido no comentário acima da função).

**2. UPDATE — transição approved → publishing (nova função `_transition_approved_to_publishing`):**

Antes (chamada inline no loop):
```python
_update_clip_status(conn, clip_id, 'publishing')  # UPDATE generated_clips SET status=%s WHERE id=%s
```

Depois (função dedicada com guard):
```python
def _transition_approved_to_publishing(conn, clip_id: int) -> bool:
    """Phase 6: move clip approved → publishing com guard de status.

    Retorna True se a transição ocorreu (1 row afetada), False se o clip já
    saiu de approved (race com /rejeitar). Em ambos os casos, faz commit.
    """
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE generated_clips SET status='publishing' "
            "WHERE id=%s AND status='approved'",
            (clip_id,),
        )
        rowcount = cur.rowcount
    conn.commit()
    return rowcount > 0
```

**3. Loop principal `publish_pending_clips`:**

Reescrito para usar a nova função com skip silencioso quando rowcount=0:

```python
for clip in _fetch_pending_clips(conn):
    clip_id = clip['id']

    if not quota_manager.can_upload(now=now):
        _log(f'Clip {clip_id} mantido approved por quota/janela')
        break

    _log(f'Próximo clip approved: id={clip_id}')

    # Phase 6: guard de status — defesa contra race com /rejeitar concorrente.
    # Se 0 rows afetadas, o clip foi rejeitado em paralelo: skip silencioso.
    if not _transition_approved_to_publishing(conn, clip_id):
        _log(f'Clip {clip_id} pulado: status mudou durante seleção')
        continue

    try:
        youtube_video_id = uploader.upload_clip(clip)
        _mark_clip_published(conn, clip_id, youtube_video_id)
        quota_manager.record_upload(now=now)
        _maybe_finalize_source_video(conn, clip['source_video_id'], clip.get('source_local_path'))
        published_count += 1
        _log(f'Clip {clip_id} publicado no YouTube: {youtube_video_id}')
    except Exception as exc:
        _mark_clip_failed(conn, clip_id, str(exc))
        _log(f'Falha ao publicar clip {clip_id}: {exc}')
```

`_update_clip_status` (helper genérico) **foi mantido intacto** para uso futuro com outros status; só a chamada do publisher passou a usar a função guarded.

### `clip-processor/tests/test_publisher.py`

- `make_conn_with_clips`: adicionado `cursor.rowcount = 1` na configuração do mock (simula MySQL retornando 1 row no UPDATE approved→publishing). Também propagado para `conn.cursor.return_value` para consistência.
- `test_raw_file_remains_while_another_clip_is_still_pending`: fixture inline ganhou `cursor.rowcount = 1` pelo mesmo motivo.

Nenhuma mudança em testes legados (`TestPublishPendingClips`) — apenas suporte de infraestrutura para o novo guard.

## Comportamento: Rowcount = 0 no UPDATE

**Cenário:** Operador envia `/rejeitar {clip_id}` no Telegram entre o instante do SELECT (`approved`) e o instante do UPDATE para `publishing`. O `/rejeitar` (Plan 06-03) muda `status='approved'` → `status='rejected'`. Quando o publisher tenta o UPDATE com guard `WHERE id=%s AND status='approved'`, MySQL retorna `rowcount=0`.

**Resposta do publisher:**

1. `_transition_approved_to_publishing` retorna `False`
2. `_log('Clip {id} pulado: status mudou durante seleção')`
3. `continue` no loop — próximo clip approved é processado
4. **Nenhum upload**, **nenhuma exception**, **quota não incrementa**
5. Clip permanece em `rejected` (estado definido por `/rejeitar`)

**Por que skip silencioso e não exception:** é um caso esperado de coordenação humano-máquina, não um erro. Log INFO é suficiente para observability. Exception forçaria `_mark_clip_failed` (status='failed'), o que sobrescreveria o `rejected` — inaceitável.

## O Que NÃO Mudou

- **QuotaManager**: lógica de quota (max 2/dia, configurável até 6) intocada. Quota bloqueada com clip approved → permanece approved.
- **Janela horária 19h-22h America/Sao_Paulo**: validação dentro de `QuotaManager.can_upload` intocada. Fora da janela com clip approved → permanece approved.
- **Cleanup do raw video após published**: `_maybe_finalize_source_video` (PUB-04 Phase 5) intocado. Source video só deleta o arquivo bruto quando todos clips do mesmo source são terminais e ao menos 1 está published.
- **`_mark_clip_published`, `_mark_clip_failed`**: assinaturas e comportamento idênticos.
- **`_update_clip_status` genérico**: mantido (sem callers no publisher, mas público para reuso).
- **Imports, env vars, fixtures externos**: nada adicionado.

## Verificação Realizada

```
docker exec clip-processor pytest tests/test_publisher.py::TestPublishApprovedClips -x
  → 3 passed (test_seleciona_apenas_approved, test_quota_blocked_leaves_clip_as_approved, test_fora_da_janela_horaria)

docker exec clip-processor pytest tests/test_publisher.py -v
  → 10 passed (3 novos + 7 legados — sem regressão)

docker exec clip-processor pytest tests/ --tb=line
  → 99 passed, 5 failed (5 failures são Wave 0 RED esperados em test_telegram_notifier
    e test_ttl_worker — aguardam Plans 06-05 e 06-06; nenhuma regressão Phase 1-5)

grep -E "status\s*=\s*'approved'" clip-processor/src/publisher.py
  → 2 matches: SELECT e UPDATE com guard

grep -E "status\s*=\s*'pending'" clip-processor/src/publisher.py
  → 0 matches (na lógica de publicação)
```

## Success Criteria (Validation Strategy 6-02-01/02/03)

- **6-02-01**: `test_seleciona_apenas_approved` GREEN ✅
- **6-02-02**: `test_quota_blocked_leaves_clip_as_approved` GREEN ✅
- **6-02-03**: `test_fora_da_janela_horaria` GREEN ✅

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixture mock precisava de `cursor.rowcount=1`**

- **Found during:** Task 1, após primeira execução de pytest
- **Issue:** O novo `_transition_approved_to_publishing` lê `cursor.rowcount` (int) e compara com `0`. O fixture `make_conn_with_clips` original deixava `rowcount` como MagicMock attribute, causando `TypeError: '>' not supported between instances of 'MagicMock' and 'int'` em **TODOS os testes** do publisher (legados e novos).
- **Fix:** Adicionado `cursor.rowcount = 1` em `make_conn_with_clips` e no fixture inline de `test_raw_file_remains_while_another_clip_is_still_pending`. Simula o caminho feliz de MySQL retornando 1 row no UPDATE.
- **Files modified:** `clip-processor/tests/test_publisher.py` (2 fixtures)
- **Commit:** b0ab1f3 (mesmo commit da Task 1)
- **Por que Rule 3 (blocking, não 1 ou 2):** sem isso, nem os 3 testes novos do plan rodavam (impedia a Task 1 de virar GREEN). Mock infra precisava acompanhar a feature.

### Auth Gates

Nenhum.

## Backlog Operacional (Não Implementado Neste Plan)

**Backlog de clips em `pending` no momento do deploy:** Plans 06-01 a 06-02 mudaram o filtro para `approved`, mas quaisquer clips com `status='pending'` gerados antes do deploy ficarão eternamente sem publicar até serem aprovados manualmente (`/aprovar {id}`) ou movidos via SQL ad-hoc.

**Recomendação para checkpoint operacional (após Phase 6 completa):**
- Helper opcional `mysql/manual-workflow/approve-backlog.sql` (não criado neste plan): `UPDATE generated_clips SET status='approved' WHERE status='pending' AND clip_path IS NOT NULL;`
- Ou aprovar via Telegram um por um conforme o operador validar
- Decisão fica a cargo do operador no momento do deploy

## Files Created / Modified

**Modified:**
- `/Users/alessandrobm1/develop/server/wordpress/canaldecortes/clip-processor/src/publisher.py` — SELECT approved + função `_transition_approved_to_publishing` + loop com skip silencioso
- `/Users/alessandrobm1/develop/server/wordpress/canaldecortes/clip-processor/tests/test_publisher.py` — `cursor.rowcount=1` em 2 fixtures

**Created:** none

## Commits

- `b0ab1f3` — feat(06-02): publisher seleciona approved e adiciona guard de status

## Self-Check: PASSED

- `clip-processor/src/publisher.py`: FOUND (contains both `status = 'approved'` SELECT and `AND status='approved'` UPDATE guard)
- `clip-processor/tests/test_publisher.py`: FOUND (contains `cursor.rowcount = 1` in fixture)
- Commit `b0ab1f3`: FOUND in git log
- All 3 TestPublishApprovedClips: GREEN
- All 7 TestPublishPendingClips: GREEN (no regression)
