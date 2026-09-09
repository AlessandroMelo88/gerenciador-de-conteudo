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
        f"docker exec canaldecortes-db-1 mysql -uroot -prootpassword canaldecortes --default-character-set=utf8mb4 -s -N -e {subprocess.list2cmdline([query])}"
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


def fetch_pending_videos():
    """Busca até 20 vídeos recentes (máx 2 dias) com status 'pending' (10 futebol, 10 política)."""
    # Auto-expurgo de vídeos com mais de 2 dias (notícia velha)
    run_remote_mysql("UPDATE source_videos SET status = 'failed' WHERE status = 'pending' AND published_at < NOW() - INTERVAL 2 DAY;")

    query = """
    (
      SELECT sv.id, sv.youtube_video_id, sv.title, sv.format
      FROM source_videos sv
      LEFT JOIN source_channels sc ON sv.channel_id = sc.id
      WHERE sv.status = 'pending'
        AND (sv.local_path IS NULL OR sv.local_path = '')
        AND sv.published_at >= NOW() - INTERVAL 2 DAY
        AND (sc.target_niche = 'futebol' OR sc.target_niche IS NULL)
      ORDER BY
        CASE WHEN sv.title LIKE '%#shorts%' OR sv.title LIKE '%#short%' THEN 1 ELSE 0 END ASC,
        sv.id DESC
      LIMIT 10
    )
    UNION ALL
    (
      SELECT sv.id, sv.youtube_video_id, sv.title, sv.format
      FROM source_videos sv
      LEFT JOIN source_channels sc ON sv.channel_id = sc.id
      WHERE sv.status = 'pending'
        AND (sv.local_path IS NULL OR sv.local_path = '')
        AND sv.published_at >= NOW() - INTERVAL 2 DAY
        AND sc.target_niche = 'politica'
      ORDER BY
        CASE WHEN sv.title LIKE '%#shorts%' OR sv.title LIKE '%#short%' THEN 1 ELSE 0 END ASC,
        sv.id DESC
      LIMIT 10
    );
    """
    output = run_remote_mysql(query)
    if not output:
        return []

    videos = []
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
    _log(f'Vídeo {vid_id} salvo com sucesso no servidor como {fmt}!')

    # 6. Notifica o servidor para rodar o pipeline de IA imediatamente (em background)
    _log(f'Acionando IA (Whisper + LLaMA + FFmpeg) no servidor...')
    run_remote_cmd("docker exec -d clip-processor python -c 'from src.rss_poller import poll_all_channels; poll_all_channels()'")


def run_cycle():
    videos = fetch_pending_videos()
    if not videos:
        return 0

    _log(f'Encontrados {len(videos)} vídeo(s) pendente(s) de download.')
    for v in videos:
        process_single_video(v)
        time.sleep(5)
    return len(videos)


def main():
    lock_file = acquire_pid_lock()
    _log('=== LOCAL DOWNLOAD WORKER INICIADO ===')
    _log(f'Diretório temporário: {TEMP_DOWNLOAD_DIR}')
    _log(f'Destino remoto: {SSH_HOST}:{REMOTE_VIDEOS_DIR}')
    
    while True:
        try:
            count = run_cycle()
            if count == 0:
                time.sleep(30)
            else:
                time.sleep(5)
        except KeyboardInterrupt:
            _log('Worker encerrado pelo usuário.')
            break
        except Exception as e:
            _log(f'Erro no loop principal: {e}')
            time.sleep(30)


if __name__ == '__main__':
    main()
