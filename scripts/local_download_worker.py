#!/usr/bin/env python3
"""
local_download_worker.py — Worker de Download Local com IP Residencial.

Fluxo:
1. Consulta vídeos pendentes de download no PostgreSQL do servidor via SSH.
2. Baixa o vídeo com yt-dlp usando a conexão residencial do Mac (zero bloqueio).
3. Transfere o arquivo .mp4 para o servidor na pasta /mnt/videos/videos/.
4. Atualiza o banco no servidor para status='downloaded' e local_path='/app/videos/<video_id>.mp4'.
5. Deleta o arquivo temporário do Mac imediatamente (zero espaço ocupado).
6. Notifica o servidor para rodar transcrição Whisper + IA + cortes.
"""

import json
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Garante acesso aos binários do Homebrew (yt-dlp, deno, rsync) em background
os.environ['PATH'] = f"/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:{os.environ.get('PATH', '')}"

import fcntl
import importlib.util

# Regra de justiça por canal compartilhada com o clip-processor. O diretório tem
# hífen no nome, então não dá para importar pelo caminho normal de módulo.
_fair_spec = importlib.util.spec_from_file_location(
    'fair_queue',
    Path(__file__).resolve().parent.parent / 'clip-processor' / 'src' / 'fair_queue.py',
)
_fair = importlib.util.module_from_spec(_fair_spec)
_fair_spec.loader.exec_module(_fair)
channel_cap = _fair.channel_cap
fair_pick = _fair.fair_pick

# Transcrição multiplataforma (painel → transcription_jobs → este worker).
_tw_spec = importlib.util.spec_from_file_location(
    'transcription_worker', Path(__file__).resolve().parent / 'transcription_worker.py',
)
transcription_worker = importlib.util.module_from_spec(_tw_spec)
_tw_spec.loader.exec_module(transcription_worker)

# VM A1 (Ashburn) desde 17/09/2026 — antes era a E2.1.Micro em São Paulo com MySQL.
SSH_KEY = os.path.expanduser('~/.ssh/oracle-a1-2026-09-16.key')
SSH_HOST = 'ubuntu@129.80.236.185'
# Block volume de 150 GB; o clip-processor enxerga como /app/videos.
REMOTE_VIDEOS_DIR = '/mnt/videos/videos'
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


# Caminho do .env no servidor — é lá que a senha do banco vive, e só lá.
REMOTE_ENV = '/home/ubuntu/canaldecortes/.env'


def run_remote_sql(query: str) -> str:
    """Executa query SQL no PostgreSQL do servidor via SSH e devolve linhas separadas por tab.

    A senha é resolvida **dentro do servidor**, lendo o `.env` no próprio comando remoto.
    Até 16/09/2026 ela estava escrita neste arquivo, que é versionado num repositório público
    (bug 16 em Docs/sistema/BUGS.md). Resolver no destino é melhor do que só tirar daqui: o
    segredo não trafega, não fica em memória do cliente e não aparece em `ps` na máquina local.
    """
    remote = (
        "P=$(grep -m1 '^POSTGRES_PASSWORD=' " + REMOTE_ENV + " | cut -d= -f2- | tr -d '\"'); "
        'docker exec -e PGPASSWORD="$P" postgres psql -U clips_user -d clips_automation '
        "-q -At -F $'\\t' -c " + shlex.quote(query)
    )
    cmd = [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10', '-i', SSH_KEY,
        SSH_HOST,
        remote,
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, errors='replace', timeout=30)
        return res.stdout.strip()
    except subprocess.TimeoutExpired:
        _log('Timeout ao executar query SQL remota')
        return ''


def run_remote_sql_stdin(sql: str) -> bool:
    """Executa SQL mandado pelo stdin do ssh, não como argumento.

    Para gravação de texto grande (transcrição de 1 h passa de 100 KB): argumento
    único no Linux trava em 128 KB. Mesma resolução de senha no servidor que
    `run_remote_sql`. ON_ERROR_STOP faz erro de SQL virar código de saída.
    """
    remote = (
        "P=$(grep -m1 '^POSTGRES_PASSWORD=' " + REMOTE_ENV + " | cut -d= -f2- | tr -d '\"'); "
        'docker exec -i -e PGPASSWORD="$P" postgres psql -U clips_user -d clips_automation '
        '-q -v ON_ERROR_STOP=1 -f -'
    )
    cmd = ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10', '-i', SSH_KEY,
           SSH_HOST, remote]
    try:
        res = subprocess.run(cmd, input=sql, capture_output=True, text=True, errors='replace', timeout=120)
    except subprocess.TimeoutExpired:
        _log('Timeout ao gravar SQL remoto pelo stdin')
        return False
    if res.returncode != 0:
        _log(f'Falha ao gravar SQL remoto: {res.stderr.strip()[:300]}')
        return False
    return True


def process_transcription() -> bool:
    """Um job de transcrição, se houver. Nunca derruba o ciclo de download."""
    try:
        return transcription_worker.process_one_job(
            run_sql=run_remote_sql, run_sql_stdin=run_remote_sql_stdin,
        )
    except Exception as e:
        _log(f'Erro na transcrição: {e}')
        return False


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


FRESHNESS_DAYS = int(os.environ.get('WORKER_FRESHNESS_DAYS', 2))

# Teto de vagas por canal de origem; vazio = janela do nicho ÷ canais ativos.
DOWNLOAD_MAX_PER_SOURCE_CHANNEL = os.environ.get('DOWNLOAD_MAX_PER_SOURCE_CHANNEL') or None

# Candidatos buscados por vaga livre — o round-robin precisa de mais de um canal
# na mão para intercalar.
CANDIDATES_PER_SLOT = int(os.environ.get('CANDIDATES_PER_SLOT', 5))

# Carência do canal recém-cadastrado: enquanto ele nunca baixou nada, o expurgo de
# notícia velha não apaga a fila dele. Canal novo entra com backlog de dias e
# perdia tudo antes de ter a primeira chance (foi o que aconteceu com os canais
# do MBL em 17/09/2026).


def _corte_frescor() -> str:
    """Data/hora limite de frescor, formatada — portável entre MySQL e PostgreSQL."""
    return (datetime.now() - timedelta(days=FRESHNESS_DAYS)).strftime('%Y-%m-%d %H:%M:%S')


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
    output = run_remote_sql(
        "SELECT LOWER(TRIM(niche)), COUNT(*) FROM destination_channels "
        "WHERE active = TRUE GROUP BY LOWER(TRIM(niche));"
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


def count_window_occupancy(niche: str) -> dict | None:
    """Ocupação atual do nicho, por canal de origem: {channel_id: vagas}.

    Mesmo critério de `_select_pending_videos` no pipeline_runner: arquivo em disco,
    status em processamento ou clip ainda sendo trabalhado. Retorna None se a
    consulta falhar — quem chama não deve baixar nada nesse caso (fail-closed).
    """
    query = (
        "SELECT sv.channel_id, COUNT(DISTINCT sv.id) FROM source_videos sv "
        "LEFT JOIN source_channels sc ON sc.id = sv.channel_id "
        "LEFT JOIN generated_clips gc ON gc.source_video_id = sv.id "
        f"WHERE {_niche_filter(niche)} AND ("
        "  (sv.local_path IS NOT NULL AND sv.local_path <> '') "
        "  OR sv.status IN ('downloading', 'downloaded', 'transcribing', 'selecting', 'cutting', 'publishing') "
        "  OR (gc.id IS NOT NULL AND gc.status IN ('pending_cut', 'pending', 'cutting', 'approved'))"
        ") GROUP BY sv.channel_id;"
    )
    output = run_remote_sql(query)
    if output is None:
        return None
    ocupacao = {}
    for line in output.strip().splitlines():
        if not line.strip():
            continue
        parts = line.split('\t')
        if len(parts) != 2 or not parts[1].strip().isdigit():
            _log(f'Não consegui contar a janela de {niche} (saída: {output[:80]!r}) — sem download neste ciclo')
            return None
        ocupacao[parts[0].strip()] = int(parts[1])
    return ocupacao


def active_source_channels(niche: str) -> int:
    """Canais de origem ativos do nicho — base do teto por canal."""
    output = run_remote_sql(
        "SELECT COUNT(*) FROM source_channels sc "
        f"WHERE sc.active = TRUE AND sc.blacklisted = FALSE AND {_niche_filter(niche)};"
    )
    try:
        return int(output.strip().splitlines()[-1])
    except (ValueError, IndexError, AttributeError):
        return 0


def fetch_pending_videos():
    """Busca vídeos 'pending' recentes só até completar a janela, com justiça por canal."""
    # Auto-expurgo de vídeos com mais de 2 dias (notícia velha). O corte vai calculado
    # em Python: `INTERVAL 2 DAY` é sintaxe do MySQL e não roda no PostgreSQL.
    # Canal que ainda não baixou nenhum vídeo fica de fora do expurgo: ele acabou de
    # ser cadastrado, e apagar a fila dele aqui é apagá-lo antes da primeira chance.
    corte = _corte_frescor()
    run_remote_sql(
        "UPDATE source_videos SET status = 'failed' "
        f"WHERE status = 'pending' AND published_at < '{corte}' "
        "AND channel_id IN ("
        "  SELECT channel_id FROM source_videos "
        "  WHERE status IN ('downloaded', 'transcribing', 'selecting', 'cutting', 'publishing', 'published') "
        "     OR local_path IS NOT NULL"
        ");"
    )

    videos = []
    for niche, window in niche_windows().items():
        ocupacao = count_window_occupancy(niche)
        if ocupacao is None:
            continue
        occupied = sum(ocupacao.values())
        deficit = window_deficit(occupied, window)
        if deficit == 0:
            continue

        cap = channel_cap(
            window=window,
            active_channels=active_source_channels(niche),
            override=DOWNLOAD_MAX_PER_SOURCE_CHANNEL,
        )
        _log(f'Janela {niche}: {occupied}/{window} ocupada — até {deficit} vídeo(s), teto {cap}/canal')

        query = f"""
        SELECT sv.id, sv.youtube_video_id, sv.title, sv.format, sv.channel_id
        FROM source_videos sv
        LEFT JOIN source_channels sc ON sv.channel_id = sc.id
        WHERE sv.status = 'pending'
          AND sv.paused = FALSE
          AND (sv.local_path IS NULL OR sv.local_path = '')
          AND sv.published_at >= '{corte}'
          AND {_niche_filter(niche)}
        ORDER BY
          CASE WHEN LOWER(sv.title) LIKE '%#short%' THEN 1 ELSE 0 END ASC,
          sv.priority DESC,
          sv.id DESC
        LIMIT {deficit * CANDIDATES_PER_SLOT};
        """
        output = run_remote_sql(query)
        if not output:
            continue

        candidatos = []
        for line in output.split('\n'):
            parts = line.split('\t')
            if len(parts) >= 5:
                candidatos.append({
                    'id': int(parts[0]),
                    'youtube_video_id': parts[1],
                    'title': parts[2],
                    'format': parts[3],
                    'channel_id': parts[4].strip(),
                })

        videos.extend(fair_pick(candidatos, occupancy=ocupacao, deficit=deficit, cap=cap))
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
    run_remote_sql(f"UPDATE source_videos SET status = 'downloading' WHERE id = {db_id};")

    temp_file = TEMP_DOWNLOAD_DIR / f'{vid_id}.mp4'

    # 2. Baixa localmente no Mac
    _log(f'Baixando via IP residencial do Mac: {vid_id}')
    success = download_video_locally(vid_id, temp_file)

    if not success:
        _log(f'Download falhou para {vid_id} — marcando como failed no servidor')
        run_remote_sql(f"UPDATE source_videos SET status = 'failed' WHERE id = {db_id};")
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
        run_remote_sql(f"UPDATE source_videos SET status = 'failed' WHERE id = {db_id};")
        return

    # 5. Atualiza no banco do servidor para 'downloaded' e define local_path e format real
    remote_path = f'/app/videos/{vid_id}.mp4'
    run_remote_sql(f"UPDATE source_videos SET status = 'downloaded', local_path = '{remote_path}', format = '{fmt}' WHERE id = {db_id};")
    _log(f'Vídeo {vid_id} salvo com sucesso no servidor como {fmt}! O daemon do servidor irá processar na fila.')


def run_cycle():
    # Transcrição primeiro: é pedido seu, com você esperando na tela. O download
    # do pipeline é de fundo e aguenta um ciclo de atraso.
    transcreveu = process_transcription()

    videos = fetch_pending_videos()
    if not videos:
        return 1 if transcreveu else 0

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
