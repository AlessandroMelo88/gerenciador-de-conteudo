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
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from src.telegram_notifier import notify

SAO_PAULO_TZ = ZoneInfo('America/Sao_Paulo')
# Mesma regra do pipeline_runner: 10 vagas por canal destino ativo.
DOWNLOAD_WINDOW_PER_CHANNEL = int(os.environ.get('DOWNLOAD_WINDOW_PER_CHANNEL', 10))
# Fallback se a contagem de canais destino falhar (2 canais hoje).
MAX_WINDOW_SLOTS = 2 * DOWNLOAD_WINDOW_PER_CHANNEL
WINDOW_STUCK_HOURS = 2
APPROVAL_IDLE_HOURS = 6
MIN_FREE_DISK_GB = 5.0
MAX_DISK_PERCENT = 85.0


def _horas_atras(horas: int) -> datetime:
    """Instante de N horas atrás, sem timezone, para comparar com colunas DATETIME/TIMESTAMP.

    Calculado em Python de propósito: `DATE_SUB(NOW(), INTERVAL n HOUR)` existe só no
    MySQL, e o mesmo código roda contra PostgreSQL (ver PLANO-POSTGRES.md).
    """
    return datetime.now() - timedelta(hours=horas)


def _max_window_slots(conn) -> int:
    """Teto total da janela: DOWNLOAD_WINDOW_PER_CHANNEL × canais destino ativos."""
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) AS n FROM destination_channels WHERE active = TRUE')
            row = cur.fetchone() or {}
        return int(row.get('n') or 0) * DOWNLOAD_WINDOW_PER_CHANNEL
    except Exception:
        return MAX_WINDOW_SLOTS


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
    """Identifica e cura clipes que perderam seus arquivos no disco:
    1. Clipes em 'approved' ou 'pending' cujo arquivo de corte (.mp4) não existe mais.
    2. Clipes em 'pending_cut' cujo vídeo fonte original não existe mais no disco.

    Retorna a quantidade de clipes curados.
    """
    curated_count = 0
    with conn.cursor() as cur:
        cur.execute(
            'SELECT gc.id, gc.source_video_id, gc.clip_path, gc.status, gc.title, '
            'sv.title AS source_title, sv.local_path AS source_local_path '
            'FROM generated_clips gc '
            'LEFT JOIN source_videos sv ON sv.id = gc.source_video_id '
            "WHERE gc.status IN ('approved', 'pending', 'pending_cut') "
        )
        clips = cur.fetchall() or []

    for clip in clips:
        clip_id = clip['id']
        source_id = clip['source_video_id']
        clip_path = clip.get('clip_path')
        status = clip.get('status')
        source_local_path = clip.get('source_local_path')

        is_ghost = False
        error_reason = ''

        if status in ('approved', 'pending'):
            # Clip já foi cortado — arquivo final deve existir
            if not clip_path or not os.path.exists(clip_path):
                is_ghost = True
                error_reason = 'Arquivo .mp4 do corte não encontrado no disco (auto-cura watchdog)'
        elif status == 'pending_cut':
            # Clip ainda não foi cortado — arquivo fonte original deve existir para permitir o corte
            if not source_local_path or not os.path.exists(source_local_path):
                is_ghost = True
                error_reason = 'Vídeo fonte original não encontrado no disco para realizar o corte'

        if is_ghost:
            title = clip.get('title') or clip.get('source_title') or f'Clip #{clip_id}'
            _log(f'Auto-cura: Clip fantasma #{clip_id} ("{title}") status={status}. Marcando failed: {error_reason}')
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE generated_clips SET status = 'failed', clip_path = NULL, "
                    "upload_error = %s "
                    "WHERE id = %s",
                    (error_reason, clip_id),
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

    max_slots = _max_window_slots(conn)
    if occupied < max_slots:
        return True  # Janela saudável com vagas livres

    # Janela cheia: verifica se algum vídeo mudou nas últimas WINDOW_STUCK_HOURS horas.
    # O corte é calculado em Python e vai como parâmetro — DATE_SUB é só do MySQL.
    with conn.cursor() as cur:
        cur.execute(
            'SELECT COUNT(*) AS active_recent '
            'FROM source_videos sv '
            'WHERE (sv.local_path IS NOT NULL '
            "       OR sv.status IN ('downloading', 'downloaded', 'transcribing', 'selecting')) "
            'AND sv.updated_at >= %s',
            (_horas_atras(WINDOW_STUCK_HOURS),),
        )
        active_recent = int(cur.fetchone().get('active_recent') or 0)

    if active_recent == 0:
        _log(f'DEADLOCK DETECTADO: Janela de download cheia ({occupied}/{max_slots}) sem atividade há >{WINDOW_STUCK_HOURS}h!')
        notify('watchdog_alert', {
            'type': 'download_window_deadlock',
            'occupied': occupied,
            'max_slots': max_slots,
            'stuck_hours': WINDOW_STUCK_HOURS,
            'message': f'🚨 Alerta Crítico: A Janela de Download está travada em {occupied}/{max_slots} vagas sem progresso há mais de {WINDOW_STUCK_HOURS} horas. O robô está impedido de baixar novos vídeos.',
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

        # Clipes criados nas últimas APPROVAL_IDLE_HOURS horas
        cur.execute(
            'SELECT COUNT(*) AS created_recent FROM generated_clips '
            'WHERE created_at >= %s',
            (_horas_atras(APPROVAL_IDLE_HOURS),),
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
            'SELECT id, name, slug, active FROM destination_channels WHERE active = TRUE'
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
