"""
rss_poller.py — Monitor de feeds RSS de canais YouTube e inserção de vídeos novos.

Exporta:
  - poll_all_channels(db_conn=None, redis_client=None)
  - _process_ai_pipeline(conn, video_id, local_path, groq_client=None, anthropic_client=None)
  - _process_pending_clips(conn)

Comportamento:
  - Busca canais ativos do MySQL (blacklisted=FALSE filtrado no SELECT — COPY-03)
  - Para cada canal, faz GET no rss_url e parseia com feedparser
  - Para cada entrada: extrai video_id, verifica deduplicação, insere se novo
  - Resiliência por canal: falha em um canal não aborta os demais
  - Nova conexão MySQL por chamada (evita timeout de 6h) — exceto quando db_conn passado (testes)
  - Após RSS polling: processa vídeos com status 'downloaded' via pipeline de IA
  - Após IA: processa clips com status 'pending_cut' via pipeline de vídeo
"""
import os
import re
import requests
import feedparser
import redis
import yt_dlp
from datetime import datetime

# Palavras-chave que bloqueiam ingestão de vídeos — títulos com qualquer uma são ignorados
_TITLE_BLOCK_KEYWORDS = [
    'aposta', 'apostas', 'bet ', 'bets ', 'betting', 'odds', 'cassino', 'casino',
    'tigrinho', 'crash game', 'blaze', 'esportebet', 'pixbet', 'sportingbet',
]


def _is_blocked_title(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in _TITLE_BLOCK_KEYWORDS)


from src.db import get_db_connection, insert_video, update_status
from src.dedup import is_seen
from src.transcriber import transcribe_video, save_transcript
from src.selector import select_moments, insert_selected_moments, MIN_LONGFORM_SECONDS
from src.video_processor import process_clip


REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))


def _log(msg: str) -> None:
    """Loga mensagem com timestamp para stdout."""
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [ACQU] {msg}')


def _detect_format(video_id: str) -> str:
    """Decide 'curto' ou 'longo' com base na duração real do vídeo fonte.

    Vídeos com MIN_LONGFORM_SECONDS ou mais (entrevistas, podcasts, análises longas)
    têm material suficiente pra um corte longo horizontal; o resto continua shorts.
    Falha ao consultar metadados (rede, vídeo indisponível) → assume 'curto' (comportamento
    anterior), sem abortar a ingestão do vídeo por isso.
    """
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'no_color': True, 'skip_download': True}) as ydl:
            info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
        duration = info.get('duration') if info else None
        if duration and duration >= MIN_LONGFORM_SECONDS:
            return 'longo'
    except Exception as exc:
        _log(f'AVISO: falha ao obter duração de {video_id} para detecção de formato: {exc}')
    return 'curto'


def _extract_video_id(entry) -> str | None:
    """Extrai o video_id de uma entrada de feed RSS.

    Tenta yt_videoid primeiro (namespace YouTube), com fallback para regex no link.

    Args:
        entry: entrada do feedparser

    Returns:
        video_id (11 chars) ou None se não encontrado
    """
    video_id = entry.get('yt_videoid')
    if video_id:
        return video_id

    # Fallback: extrair da URL do link
    link = entry.get('link', '')
    match = re.search(r'v=([A-Za-z0-9_-]{11})', link)
    if match:
        return match.group(1)

    return None


def _process_ai_pipeline(conn, video_id: str, local_path: str, groq_client=None, anthropic_client=None) -> None:
    """Executa transcrição + seleção para um vídeo com status downloaded.

    Args:
        conn: conexão pymysql ativa (quem chama fecha)
        video_id: youtube_video_id
        local_path: caminho do arquivo .mp4 em disco
        groq_client: cliente Groq (None = produção, injetado = testes)
        anthropic_client: cliente Anthropic (None = produção, injetado = testes)
    """
    try:
        # Transcrição
        update_status(conn, video_id, 'transcribing')
        transcript = transcribe_video(video_id, local_path, groq_client=groq_client)
        if transcript is None:
            _log(f'[AI] Transcrição falhou para {video_id} — marcando como failed')
            update_status(conn, video_id, 'failed')
            return

        save_transcript(conn, video_id, transcript)

        # Seleção
        update_status(conn, video_id, 'selecting')

        # Obter source_video_id INT + formato (curto/longo) para FK em generated_clips
        with conn.cursor() as cur:
            cur.execute('SELECT id, format FROM source_videos WHERE youtube_video_id = %s', (video_id,))
            row = cur.fetchone()
        if row is None:
            _log(f'[AI] AVISO: source_video_id não encontrado para {video_id}')
            return
        source_video_id = row['id']
        fmt = row.get('format') or 'curto'

        moments = select_moments(transcript, anthropic_client=anthropic_client, fmt=fmt)
        inserted = insert_selected_moments(conn, source_video_id, video_id, moments)
        _log(f'[AI] Pipeline concluído para {video_id}: {inserted} momento(s) inserido(s) em generated_clips')

    except Exception as exc:
        _log(f'[AI] ERRO no pipeline de IA para {video_id}: {exc}')
        try:
            update_status(conn, video_id, 'failed')
        except Exception:
            pass


def _process_pending_clips(conn) -> None:
    """Processa clips com status pending_cut sem abortar o poll por falha isolada."""
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM generated_clips WHERE status = 'pending_cut'")
        rows = cur.fetchall()

    for row in rows:
        clip_id = row['id']
        _log(f'[VID] Iniciando processamento do clip {clip_id}')
        try:
            process_clip(conn, clip_id)
        except Exception as exc:
            _log(f'[VID] ERRO no processamento do clip {clip_id}: {exc}')


def poll_all_channels(db_conn=None, redis_client=None) -> None:
    """Monitora feeds RSS de todos os canais ativos e insere vídeos novos.

    Args:
        db_conn: conexão pymysql (opcional — se None, cria nova conexão para produção)
        redis_client: cliente Redis (opcional — se None, cria nova conexão para produção)
    """
    # Gerenciar conexões: nova por chamada em produção, injetada em testes
    _own_db = db_conn is None
    _own_redis = redis_client is None

    if _own_db:
        db_conn = get_db_connection()

    if _own_redis:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,
        )

    try:
        # Buscar canais ativos (canais blacklistados filtrados no SELECT — COPY-03)
        with db_conn.cursor() as cur:
            cur.execute(
                'SELECT id, channel_name, rss_url, target_niche, channel_handle '
                'FROM source_channels '
                'WHERE active = TRUE AND blacklisted = FALSE'
            )
            channels = cur.fetchall()

        total_new = 0

        for channel in channels:
            # Guard de segurança: ignora canais blacklistados mesmo que apareçam no resultado
            # (em produção, filtrado no SELECT; guard garante correctness nos mocks — COPY-03)
            if channel.get('blacklisted'):
                continue

            channel_id = channel['id']
            channel_name = channel['channel_name']
            rss_url = channel['rss_url']

            try:
                # Buscar feed RSS via HTTP e parsear com feedparser
                response = requests.get(rss_url, timeout=30)
                if response.status_code != 200:
                    _log(f'AVISO: canal {channel_name} retornou HTTP {response.status_code}')
                    continue

                feed = feedparser.parse(response.text)
                entries = feed.entries if hasattr(feed, 'entries') else []

                _log(f'Canal {channel_name}: {len(entries)} entradas no feed')

                for entry in entries:
                    video_id = _extract_video_id(entry)

                    if video_id is None:
                        _log(f'AVISO: entrada sem video_id no canal {channel_name} — pulando')
                        continue

                    if is_seen(video_id, redis_client, db_conn):
                        continue

                    # Vídeo novo — extrair metadados e inserir
                    title = entry.get('title', video_id)
                    published_at = entry.get('published', None)

                    if _is_blocked_title(title):
                        _log(f'Título bloqueado (keyword): {video_id} — {title}')
                        continue

                    fmt = _detect_format(video_id)
                    insert_video(db_conn, video_id, channel_id, title, published_at, format=fmt)
                    _log(f'Novo vídeo detectado ({fmt}): {video_id} — {title}')
                    total_new += 1

            except Exception as exc:
                _log(f'ERRO ao processar canal {channel_name}: {exc}')
                continue

        _log(f'Poll concluído: {total_new} vídeo(s) novo(s) inserido(s)')

        # Processar vídeos que já estão downloaded (transcrição + seleção)
        try:
            with db_conn.cursor() as cur:
                cur.execute(
                    "SELECT youtube_video_id, local_path FROM source_videos "
                    "WHERE status = 'downloaded' AND local_path IS NOT NULL"
                )
                downloaded_videos = cur.fetchall()

            for video_row in downloaded_videos:
                vid_id = video_row['youtube_video_id']
                vid_path = video_row['local_path']
                _log(f'[AI] Iniciando pipeline de IA para {vid_id}')
                try:
                    _process_ai_pipeline(db_conn, vid_id, vid_path)
                except Exception as exc:
                    _log(f'[AI] ERRO no pipeline de {vid_id}: {exc}')

        except Exception as exc:
            _log(f'[AI] ERRO ao buscar vídeos downloaded para processamento: {exc}')

        # Processar clips selecionados pela IA (corte + legenda + thumbnail + metadata)
        try:
            _process_pending_clips(db_conn)
        except Exception as exc:
            _log(f'[VID] ERRO ao buscar clips pending_cut para processamento: {exc}')

    finally:
        if _own_db:
            db_conn.close()
