#!/usr/bin/env python3
"""
local_download_worker.py — Worker de Download Local com IP Residencial.

Fluxo:
1. Consulta vídeos pendentes de download no banco MySQL do servidor via SSH.
2. Baixa o vídeo com yt-dlp usando a conexão residencial do Mac (zero bloqueio).
3. Transfere o arquivo .mp4 para o servidor na pasta /home/ubuntu/canaldecortes/videos/.
4. Atualiza o banco no servidor para status='downloaded' e local_path='/app/videos/<video_id>.mp4'.
5. Deleta o arquivo temporário do Mac imediatamente (zero espaço ocupado).
6. Notifica o servidor para rodar transcrição Whisper + IA + cortes.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Garante acesso aos binários do Homebrew (yt-dlp, deno, rsync) em background
os.environ['PATH'] = f"/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:{os.environ.get('PATH', '')}"

import fcntl

SSH_KEY = os.path.expanduser('~/.ssh/oracle-ssh-key-2026-08-27.key')
SSH_HOST = 'ubuntu@147.15.124.191'
REMOTE_VIDEOS_DIR = '/home/ubuntu/canaldecortes/videos'
TEMP_DOWNLOAD_DIR = Path('/tmp/gdc_downloads')
TEMP_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
PID_FILE = Path('/tmp/local_download_worker.pid')

# Teto de vídeos ocupando o servidor: 10 por canal destino ativo do nicho — mesma
# regra do clip-processor (pipeline_runner._niche_windows). Dois canais destino =
# 20 no total; cada canal novo soma 10. Sem esse teto o worker baixava 16 vídeos a
# cada ciclo de 5–30 s: em 15/09/2026 foram 306 downloads num dia, 377 vídeos
# parados na janela e o disco do servidor em 100%.
DOWNLOAD_WINDOW_PER_CHANNEL = int(os.environ.get('DOWNLOAD_WINDOW_PER_CHANNEL', 10))


def _log(msg: str):
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [LOCAL-WORKER] {msg}', flush=True)


def acquire_pid_lock():
    """Garante que apenas uma instância do worker local esteja ativa."""
    try:
        f = open(PID_FILE, 'w')
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        f.write(str(os.getpid()))
        f.flush()
        return f
    except (IOError, BlockingIOError):
        _log('AVISO: Outra instância do local_download_worker já está em execução. Encerrando.')
        sys.exit(0)


def run_remote_mysql(query: str) -> str:
    """Executa query SQL no MySQL do servidor via SSH."""
    cmd = [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10', '-i', SSH_KEY,
        SSH_HOST,
        f"docker exec mysql mysql -uroot -prootpassword clips_automation --default-character-set=utf8mb4 -s -N -e {subprocess.list2cmdline([query])}"
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, errors='replace', timeout=30)
        return res.stdout.strip()
    except subprocess.TimeoutExpired:
        _log('Timeout ao executar query MySQL remota')
        return ''


def run_remote_cmd(cmd_str: str) -> bool:
    """Executa comando bash no servidor via SSH."""
    cmd = [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10', '-i', SSH_KEY,
        SSH_HOST,
        cmd_str
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        return res.returncode == 0
    except subprocess.TimeoutExpired:
        _log(f'Timeout ao executar comando remoto: {cmd_str[:50]}...')
        return False


def get_video_duration(file_path: Path) -> float:
    """Obtém a duração real do vídeo em segundos via ffprobe."""
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(file_path)
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        return float(res.stdout.strip())
    except Exception:
        return 0.0


def _niche_filter(niche: str) -> str:
    """Filtro SQL do nicho; futebol também absorve canal sem nicho (igual ao pipeline_runner)."""
    if niche == 'futebol':
        return "(sc.target_niche = 'futebol' OR sc.target_niche IS NULL OR sc.target_niche = '')"
    # niche vem de destination_channels; só slug simples entra na query.
    if not niche.replace('_', '').replace('-', '').isalnum():
        raise ValueError(f'nicho inválido: {niche!r}')
    return f"sc.target_niche = '{niche}'"


def niche_windows() -> dict:
    """Teto por nicho = DOWNLOAD_WINDOW_PER_CHANNEL × canais destino ativos.

    Futebol primeiro. Falha na consulta devolve {} — sem download (fail-closed).
    """
    output = run_remote_mysql(
        "SELECT LOWER(TRIM(niche)), COUNT(*) FROM destination_channels "
        "WHERE active = 1 GROUP BY LOWER(TRIM(niche));"
    )
    windows = {}
    for line in output.splitlines():
        parts = line.split('\t')
        if len(parts) == 2 and parts[0] and parts[1].strip().isdigit():
            windows[parts[0]] = int(parts[1]) * DOWNLOAD_WINDOW_PER_CHANNEL
    if not windows:
        _log('Nenhum canal destino ativo lido — sem download neste ciclo')
    return dict(sorted(windows.items(), key=lambda w: (w[0] != 'futebol', w[0])))


def window_deficit(occupied: int, window: int) -> int:
    """Quantas vagas faltam na janela do nicho. Nunca negativo."""
    return max(0, window - occupied)


def count_window_occupancy(niche: str) -> int | None:
    """Conta vídeos do nicho que já ocupam o servidor.

    Mesmo critério de `_select_pending_videos` no pipeline_runner: arquivo em disco,
    status em processamento ou clip ainda sendo trabalhado. Retorna None se a
    consulta falhar — quem chama não deve baixar nada nesse caso (fail-closed).
    """
    query = (
        "SELECT COUNT(DISTINCT sv.id) FROM source_videos sv "
        "LEFT JOIN source_channels sc ON sc.id = sv.channel_id "
        "LEFT JOIN generated_clips gc ON gc.source_video_id = sv.id "
        f"WHERE {_niche_filter(niche)} AND ("
        "  (sv.local_path IS NOT NULL AND sv.local_path <> '') "
        "  OR sv.status IN ('downloading', 'downloaded', 'transcribing', 'selecting', 'cutting', 'publishing') "
        "  OR (gc.id IS NOT NULL AND gc.status IN ('pending_cut', 'pending', 'cutting', 'approved'))"
        ");"
    )
    output = run_remote_mysql(query)
    try:
        return int(output.strip().splitlines()[-1])
    except (ValueError, IndexError):
        _log(f'Não consegui contar a janela de {niche} (saída: {output[:80]!r}) — sem download neste ciclo')
        return None


def fetch_pending_videos():
    """Busca vídeos 'pending' recentes (máx 2 dias) só até completar a janela de cada nicho."""
    # Auto-expurgo de vídeos com mais de 2 dias (notícia velha)
    run_remote_mysql("UPDATE source_videos SET status = 'failed' WHERE status = 'pending' AND published_at < NOW() - INTERVAL 2 DAY;")

    videos = []
    for niche, window in niche_windows().items():
        occupied = count_window_occupancy(niche)
        if occupied is None:
            continue
        deficit = window_deficit(occupied, window)
        if deficit == 0:
            continue
        _log(f'Janela {niche}: {occupied}/{window} ocupada — buscando até {deficit} vídeo(s)')

        query = f"""
        SELECT sv.id, sv.youtube_video_id, sv.title, sv.format
        FROM source_videos sv
        LEFT JOIN source_channels sc ON sv.channel_id = sc.id
        WHERE sv.status = 'pending'
          AND sv.paused = 0
          AND (sv.local_path IS NULL OR sv.local_path = '')
          AND sv.published_at >= NOW() - INTERVAL 2 DAY
          AND {_niche_filter(niche)}
        ORDER BY
          CASE WHEN sv.title LIKE '%#shorts%' OR sv.title LIKE '%#short%' THEN 1 ELSE 0 END ASC,
          sv.priority DESC,
          sv.id DESC
        LIMIT {deficit};
        """
        output = run_remote_mysql(query)
        if not output:
            continue

        for line in output.split('\n'):
            parts = line.split('\t')
            if len(parts) >= 4:
                videos.append({
                    'id': int(parts[0]),
                    'youtube_video_id': parts[1],
                    'title': parts[2],
                    'format': parts[3]
                })
    return videos


def download_video_locally(video_id: str, temp_path: Path) -> bool:
    """Baixa o vídeo localmente usando yt-dlp residencial com desafio JS resolvido."""
    url = f'https://www.youtube.com/watch?v={video_id}'
    cmd = [
        'yt-dlp',
        '--remote-components', 'ejs:github',
        '--extractor-args', 'youtube:player_client=tv,mweb,ios',
        '-f', 'bestvideo[height<=720]+bestaudio/best[height<=720]/best',
        '--merge-output-format', 'mp4',
        '--no-color',
        '--quiet',
        '--no-warnings',
        '-o', str(temp_path),
        url
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if res.returncode == 0 and temp_path.exists() and temp_path.stat().st_size > 1000:
            return True
        else:
            _log(f'Erro yt-dlp para {video_id}: {res.stderr.strip()[:200]}')
            return False
    except Exception as e:
        _log(f'Exceção no download de {video_id}: {e}')
        return False


def upload_to_server(temp_path: Path, video_id: str) -> bool:
    """Envia o arquivo .mp4 para o servidor via rsync."""
    remote_target = f'{SSH_HOST}:{REMOTE_VIDEOS_DIR}/{video_id}.mp4'
    cmd = [
        'rsync',
        '-e', f'ssh -o StrictHostKeyChecking=no -i {SSH_KEY}',
        '-az',
        '--partial',
        str(temp_path),
        remote_target
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode == 0


def process_single_video(video: dict):
    vid_id = video['youtube_video_id']
    db_id = video['id']
    title = video['title']
    _log(f'Iniciando processamento do vídeo #{db_id} ({vid_id}): "{title[:40]}..."')

    # 1. Marca como downloading no servidor
    run_remote_mysql(f"UPDATE source_videos SET status = 'downloading' WHERE id = {db_id};")

    temp_file = TEMP_DOWNLOAD_DIR / f'{vid_id}.mp4'

    # 2. Baixa localmente no Mac
    _log(f'Baixando via IP residencial do Mac: {vid_id}')
    success = download_video_locally(vid_id, temp_file)

    if not success:
        _log(f'Download falhou para {vid_id} — marcando como failed no servidor')
        run_remote_mysql(f"UPDATE source_videos SET status = 'failed' WHERE id = {db_id};")
        if temp_file.exists():
            temp_file.unlink()
        return

    duration = get_video_duration(temp_file)
    fmt = 'longo' if duration >= 180 else 'curto'
    file_size_mb = temp_file.stat().st_size / (1024 * 1024)
    _log(f'Download concluído ({file_size_mb:.1f} MB, {duration:.0f}s, formato: {fmt}). Enviando para o servidor Oracle...')

    # 3. Transfere para o servidor
    upload_ok = upload_to_server(temp_file, vid_id)

    # 4. Deleta do Mac imediatamente (libera espaço!)
    if temp_file.exists():
        temp_file.unlink()
        _log(f'Arquivo local deletado do Mac (0 espaço retido).')

    if not upload_ok:
        _log(f'Falha ao enviar {vid_id}.mp4 para o servidor!')
        run_remote_mysql(f"UPDATE source_videos SET status = 'failed' WHERE id = {db_id};")
        return

    # 5. Atualiza no MySQL do servidor para 'downloaded' e define local_path e format real
    remote_path = f'/app/videos/{vid_id}.mp4'
    run_remote_mysql(f"UPDATE source_videos SET status = 'downloaded', local_path = '{remote_path}', format = '{fmt}' WHERE id = {db_id};")
    _log(f'Vídeo {vid_id} salvo com sucesso no servidor como {fmt}! O daemon do servidor irá processar na fila.')


def run_cycle():
    videos = fetch_pending_videos()
    if not videos:
        return 0

    _log(f'Encontrados {len(videos)} vídeo(s) pendente(s) de download.')
    # Só o primeiro: a janela é recontada no próximo ciclo, depois que ele entrou.
    process_single_video(videos[0])
    return 1


def main():
    lock_file = acquire_pid_lock()
    _log('=== LOCAL DOWNLOAD WORKER INICIADO ===')
    _log(f'Diretório temporário: {TEMP_DOWNLOAD_DIR}')
    _log(f'Destino remoto: {SSH_HOST}:{REMOTE_VIDEOS_DIR}')
    
    while True:
        try:
            count = run_cycle()
            # Janela cheia ou nada pendente: espera mais antes de recontar.
            time.sleep(60 if count == 0 else 5)
        except KeyboardInterrupt:
            _log('Worker encerrado pelo usuário.')
            break
        except Exception as e:
            _log(f'Erro no loop principal: {e}')
            time.sleep(30)


if __name__ == '__main__':
    main()
