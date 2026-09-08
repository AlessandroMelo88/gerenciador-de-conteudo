"""
watchdog.py — Monitor inteligente de integridade do pipeline e detector de deadlocks.

Executado a cada 30 minutos pelo scheduler do daemon.
Regras de Verificação:
  1. check_download_window_health: Detecta se a janela de download está 7/7 ocupada sem nenhum avanço >2h.
  2. check_ghost_clips: Detecta clipes em 'approved' ou 'pending_cut' sem arquivo .mp4 físico no disco e aplica auto-cura.
  3. check_approval_queue_activity: Detecta fila de aprovação zerada por mais de 6h em horário útil.
  4. check_youtube_tokens: Valida tokens OAuth dos canais destino antes da janela nobre de postagem.
  5. check_disk_space: Monitora uso do SSD em /app/videos (< 5 GB livres ou > 85% de uso).

Exporta:
  - run_watchdog_cycle(conn) -> dict
"""
import os
import shutil
from datetime import datetime, time
from zoneinfo import ZoneInfo

from src.telegram_notifier import notify

SAO_PAULO_TZ = ZoneInfo('America/Sao_Paulo')
MAX_WINDOW_SLOTS = 7
WINDOW_STUCK_HOURS = 2
APPROVAL_IDLE_HOURS = 6
MIN_FREE_DISK_GB = 5.0
MAX_DISK_PERCENT = 85.0


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [WATCHDOG] {msg}', flush=True)


def check_disk_space(path: str = '/app/videos') -> dict | None:
    """Verifica espaço livre em disco no volume de vídeos."""
    target_path = path if os.path.exists(path) else '/'
    try:
        total, used, free = shutil.disk_usage(target_path)
        total_gb = total / (1024 ** 3)
        free_gb = free / (1024 ** 3)
        used_percent = (used / total) * 100 if total > 0 else 0

        if free_gb < MIN_FREE_DISK_GB or used_percent > MAX_DISK_PERCENT:
            _log(f'ALERTA DISCO: {free_gb:.1f} GB livres ({used_percent:.1f}% em uso)')
            return {
                'level': 'warning',
                'free_gb': round(free_gb, 1),
                'total_gb': round(total_gb, 1),
                'used_percent': round(used_percent, 1),
            }
    except Exception as exc:
        _log(f'Aviso ao checar disco: {exc}')
    return None


def check_ghost_clips(conn) -> int:
    """Identifica e cura clipes marcados como 'approved' ou 'pending_cut' sem arquivo .mp4 no disco.

    Retorna a quantidade de clipes curados.
    """
    curated_count = 0
    with conn.cursor() as cur:
        cur.execute(
            'SELECT gc.id, gc.source_video_id, gc.clip_path, gc.status, gc.title '
            'FROM generated_clips gc '
            "WHERE gc.status IN ('approved', 'pending_cut', 'cutting') "
        )
        clips = cur.fetchall() or []

    for clip in clips:
        clip_id = clip['id']
        source_id = clip['source_video_id']
        clip_path = clip.get('clip_path')

        is_ghost = False
        if not clip_path:
            is_ghost = True
        elif not os.path.exists(clip_path):
            is_ghost = True

        if is_ghost:
            _log(f'Auto-cura: Clip fantasma #{clip_id} ("{clip.get("title")}") sem arquivo em disco. Marcando failed.')
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE generated_clips SET status = 'failed', clip_path = NULL, "
                    "upload_error = 'Arquivo .mp4 não encontrado no disco (auto-cura watchdog)' "
                    "WHERE id = %s",
                    (clip_id,),
                )
                # Libera o vídeo fonte se não houver outros clipes válidos
                cur.execute(
                    "SELECT COUNT(*) as c FROM generated_clips "
                    "WHERE source_video_id = %s AND status IN ('pending_cut', 'cutting', 'pending', 'approved')",
                    (source_id,),
                )
                active_remaining = cur.fetchone().get('c', 0)
                if active_remaining == 0:
                    cur.execute(
                        "UPDATE source_videos SET status = 'published', local_path = NULL WHERE id = %s",
                        (source_id,),
                    )
            conn.commit()
            curated_count += 1

    if curated_count > 0:
        _log(f'{curated_count} clipe(s) fantasma(s) corrigido(s) e vagas liberadas.')
        notify('watchdog_alert', {
            'type': 'ghost_clips_healed',
            'count': curated_count,
            'message': f'Auto-cura executada: {curated_count} clipe(s) sem arquivo foram removidos da fila e as vagas de download foram liberadas.',
        })

    return curated_count


def check_download_window_health(conn) -> bool:
    """Verifica se a janela de 7 vagas está 100% cheia e estagnada há mais de WINDOW_STUCK_HOURS."""
    with conn.cursor() as cur:
        cur.execute(
            'SELECT COUNT(DISTINCT sv.id) AS occupied '
            'FROM source_videos sv '
            'LEFT JOIN generated_clips gc ON gc.source_video_id = sv.id '
            'WHERE sv.local_path IS NOT NULL '
            "OR sv.status IN ('downloading', 'downloaded', 'transcribing', 'selecting', 'cutting', 'publishing') "
            "OR (gc.id IS NOT NULL AND gc.status IN ('pending_cut', 'pending', 'cutting', 'approved'))"
        )
        occupied = int(cur.fetchone().get('occupied') or 0)

    if occupied < MAX_WINDOW_SLOTS:
        return True  # Janela saudável com vagas livres

    # Se a janela está cheia (>= 7), verifica se algum vídeo mudou nos últimos 2h
    with conn.cursor() as cur:
        cur.execute(
            'SELECT COUNT(*) AS active_recent '
            'FROM source_videos sv '
            'WHERE (sv.local_path IS NOT NULL '
            "       OR sv.status IN ('downloading', 'downloaded', 'transcribing', 'selecting')) "
            'AND sv.updated_at >= DATE_SUB(NOW(), INTERVAL %s HOUR)',
            (WINDOW_STUCK_HOURS,),
        )
        active_recent = int(cur.fetchone().get('active_recent') or 0)

    if active_recent == 0:
        _log(f'DEADLOCK DETECTADO: Janela de download cheia ({occupied}/{MAX_WINDOW_SLOTS}) sem atividade há >{WINDOW_STUCK_HOURS}h!')
        notify('watchdog_alert', {
            'type': 'download_window_deadlock',
            'occupied': occupied,
            'max_slots': MAX_WINDOW_SLOTS,
            'stuck_hours': WINDOW_STUCK_HOURS,
            'message': f'🚨 Alerta Crítico: A Janela de Download está travada em {occupied}/{MAX_WINDOW_SLOTS} vagas sem progresso há mais de {WINDOW_STUCK_HOURS} horas. O robô está impedido de baixar novos vídeos.',
        })
        return False

    return True


def check_approval_queue_activity(conn) -> None:
    """Avisa se a fila de aprovação estiver zerada há mais de 6h em horário comercial (08h às 23h)."""
    now = datetime.now(SAO_PAULO_TZ)
    if not (time(8, 0) <= now.time() <= time(23, 0)):
        return

    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS pending_count FROM generated_clips WHERE status = 'pending'"
        )
        pending_count = int(cur.fetchone().get('pending_count') or 0)

        # Clipes criados nas últimas 6h
        cur.execute(
            'SELECT COUNT(*) AS created_recent FROM generated_clips '
            'WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s HOUR)',
            (APPROVAL_IDLE_HOURS,),
        )
        created_recent = int(cur.fetchone().get('created_recent') or 0)

    if pending_count == 0 and created_recent == 0:
        _log(f'Aviso: Fila de aprovação vazia e nenhum corte gerado nas últimas {APPROVAL_IDLE_HOURS}h.')
        notify('watchdog_alert', {
            'type': 'empty_approval_queue',
            'idle_hours': APPROVAL_IDLE_HOURS,
            'message': f'⚠️ Fila de aprovação vazia há mais de {APPROVAL_IDLE_HOURS} horas no horário diurno. Verifique se os canais fonte estão publicando conteúdo novo.',
        })


def check_youtube_tokens(conn, token_dir: str = '/app/youtube') -> list[str]:
    """Verifica se todos os canais destino ativos possuem arquivo de credencial OAuth presente."""
    warnings = []
    with conn.cursor() as cur:
        cur.execute(
            'SELECT id, name, slug, active FROM destination_channels WHERE active = 1'
        )
        channels = cur.fetchall() or []

    for ch in channels:
        slug = ch.get('slug')
        name = ch.get('name')
        token_file = os.path.join(token_dir, f'token-{slug}.json')
        if not os.path.exists(token_file):
            msg = f'Canal ativo "{name}" ({slug}) não possui token OAuth em {token_file}'
            _log(f'Aviso OAuth: {msg}')
            warnings.append(msg)

    if warnings:
        notify('oauth_warning', {
            'type': 'missing_oauth_tokens',
            'warnings': warnings,
            'message': f'🔑 Alerta de OAuth: {len(warnings)} canal(is) ativo(s) sem token de publicação configurado.',
        })

    return warnings


def run_watchdog_cycle(conn) -> dict:
    """Executa o ciclo completo de monitoramento do Watchdog."""
    _log('Iniciando ciclo de verificação de integridade do Watchdog...')
    results = {
        'timestamp': datetime.now(SAO_PAULO_TZ).isoformat(),
        'ghost_clips_healed': 0,
        'window_healthy': True,
        'disk': None,
        'oauth_warnings': [],
    }

    try:
        results['ghost_clips_healed'] = check_ghost_clips(conn)
        results['window_healthy'] = check_download_window_health(conn)
        results['disk'] = check_disk_space()
        results['oauth_warnings'] = check_youtube_tokens(conn)
        check_approval_queue_activity(conn)
        _log('Ciclo do Watchdog concluído com sucesso.')
    except Exception as exc:
        _log(f'Erro durante ciclo do Watchdog: {exc}')

    return results
