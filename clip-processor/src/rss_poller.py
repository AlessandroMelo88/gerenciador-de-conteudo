"""
rss_poller.py — Monitor de feeds RSS de canais YouTube e inserção de vídeos novos.

Exporta:
  - poll_all_channels(db_conn=None, redis_client=None)
  - _process_ai_pipeline(conn, video_id, local_path, groq_client=None, anthropic_client=None)
  - _process_pending_clips(conn)

Comportamento:
  - Busca canais ativos do PostgreSQL (blacklisted=FALSE filtrado no SELECT — COPY-03)
  - Para cada canal, faz GET no rss_url e parseia com feedparser
  - Para cada entrada: extrai video_id, verifica deduplicação, insere se novo
  - Resiliência por canal: falha em um canal não aborta os demais
  - Nova conexão PostgreSQL por chamada (evita timeout de 6h) — exceto quando db_conn passado (testes)
  - Após RSS polling: processa vídeos com status 'downloaded' via pipeline de IA
  - Após IA: processa clips com status 'pending_cut' via pipeline de vídeo
"""

import os
import re
from datetime import datetime

import feedparser
import redis
import requests
import yt_dlp

# Palavras-chave que bloqueiam ingestão de vídeos — títulos com qualquer uma são ignorados
_TITLE_BLOCK_KEYWORDS = [
    'aposta',
    'apostas',
    'bet ',
    'bets ',
    'betting',
    'odds',
    'cassino',
    'casino',
    'tigrinho',
    'crash game',
    'blaze',
    'esportebet',
    'pixbet',
    'sportingbet',
]


def _is_blocked_title(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in _TITLE_BLOCK_KEYWORDS)


from src.db import (
    fetch_used_moments,
    get_db_connection,
    insert_video,
    reconcile_source_video_status,
    update_status,
)
from src.dedup import is_seen
from src.prompt_profiles import PROMPT_PROFILE_SQL_COLUMNS, profile_from_row, profile_matches_niche
from src.selector import MIN_LONGFORM_SECONDS, insert_selected_moments, select_moments
from src.transcriber import save_transcript, transcribe_video
from src.video_processor import process_clip

REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
SOURCE_FILE_ROOT = os.path.realpath('/app/videos')
CLIP_STATUSES_NEED_RAW = ('pending_cut', 'cutting', 'pending', 'approved', 'publishing')


def _log(msg: str) -> None:
    """Loga mensagem com timestamp para stdout."""
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [ACQU] {msg}')


def _release_failed_source_files(conn, video_id: str) -> None:
    """Remove raw/transcript de uma fonte falha quando nenhum clip os usa.

    Vídeos marcados como ``failed`` pela transcrição ou seleção ainda mantinham
    ``local_path``. A janela de download conta esse caminho mesmo em estado
    terminal, então alguns erros de IA acabavam bloqueando downloads novos.
    Só caminhos dentro de ``/app/videos`` são aceitos e o banco só é limpo
    depois que todos os arquivos existentes forem removidos.
    """
    with conn.cursor() as cur:
        cur.execute(
            'SELECT sv.id, sv.status, sv.local_path, sv.transcript_path, '
            'EXISTS ('
            '  SELECT 1 FROM generated_clips gc '
            '  WHERE gc.source_video_id = sv.id '
            "  AND gc.status IN ('pending_cut', 'cutting', 'pending', 'approved', 'publishing')"
            ') AS has_active_clip '
            'FROM source_videos sv WHERE sv.youtube_video_id = %s',
            (video_id,),
        )
        source = cur.fetchone()

    if not source or source.get('status') != 'failed' or source.get('has_active_clip'):
        return

    paths = [source.get('local_path'), source.get('transcript_path')]
    for raw_path in paths:
        if not raw_path:
            continue
        resolved = os.path.realpath(str(raw_path))
        if not resolved.startswith(f'{SOURCE_FILE_ROOT}{os.sep}'):
            _log(f'[AI] Arquivo fora da pasta de vídeos não será removido: {raw_path}')
            return
        if os.path.exists(resolved):
            try:
                os.remove(resolved)
            except OSError as exc:
                _log(f'[AI] Não foi possível liberar arquivo de {video_id}: {exc}')
                return

    with conn.cursor() as cur:
        cur.execute(
            'UPDATE source_videos SET local_path=NULL, transcript_path=NULL '
            "WHERE id=%s AND status='failed'",
            (source['id'],),
        )
    conn.commit()
    _log(f'[AI] Arquivos de {video_id} liberados após falha terminal')


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


def _process_ai_pipeline(
    conn, video_id: str, local_path: str, groq_client=None, anthropic_client=None
) -> None:
    """Executa transcrição + seleção para um vídeo com status downloaded.

    Args:
        conn: conexão PostgreSQL ativa (quem chama fecha)
        video_id: youtube_video_id
        local_path: caminho do arquivo .mp4 em disco
        groq_client: cliente Groq (None = produção, injetado = testes)
        anthropic_client: cliente Anthropic (None = produção, injetado = testes)
    """
    try:
        from src.queue_controls import is_paused

        if is_paused(conn, youtube_video_id=video_id):
            _log(f'[AI] Pulando {video_id} — pausado')
            return

        # Transcrição
        update_status(conn, video_id, 'transcribing')
        transcript = transcribe_video(video_id, local_path, groq_client=groq_client)
        if transcript is None:
            _log(f'[AI] Transcrição falhou para {video_id} — marcando como failed')
            update_status(conn, video_id, 'failed')
            _release_failed_source_files(conn, video_id)
            return

        if is_paused(conn, youtube_video_id=video_id):
            _log(f'[AI] {video_id} pausado após transcrição — não seleciona')
            update_status(conn, video_id, 'downloaded')
            return

        save_transcript(conn, video_id, transcript)

        # Seleção
        update_status(conn, video_id, 'selecting')

        # Obter source_video_id INT, formato, nicho e perfil para calibrar a IA.
        with conn.cursor() as cur:
            cur.execute(
                'SELECT sv.id, sv.format, sc.target_niche, sc.prompt_profile_id, '
                + PROMPT_PROFILE_SQL_COLUMNS
                + ' '
                'FROM source_videos sv '
                'LEFT JOIN source_channels sc ON sc.id = sv.channel_id '
                'LEFT JOIN prompt_profiles pp '
                'ON pp.id = sc.prompt_profile_id AND pp.active = TRUE '
                'WHERE sv.youtube_video_id = %s',
                (video_id,),
            )
            row = cur.fetchone()
        if row is None:
            _log(f'[AI] AVISO: source_video_id não encontrado para {video_id}')
            return
        source_video_id = row['id']
        fmt = row.get('format') or 'curto'
        niche = row.get('target_niche')
        prompt_profile = profile_from_row(row)
        if prompt_profile and not profile_matches_niche(prompt_profile, niche):
            _log(
                f'[AI] Perfil {prompt_profile.get("slug")} não corresponde ao nicho {niche}; '
                'fallback seguro aplicado'
            )
            prompt_profile = None
        used_moments = fetch_used_moments(conn, source_video_id)

        select_kwargs = {'anthropic_client': anthropic_client, 'fmt': fmt}
        if used_moments:
            select_kwargs['used_moments'] = used_moments
        if niche:
            select_kwargs['niche'] = niche
        if prompt_profile:
            select_kwargs['prompt_profile'] = prompt_profile

        moments = select_moments(transcript, **select_kwargs)
        inserted = insert_selected_moments(conn, source_video_id, video_id, moments)
        _log(
            f'[AI] Pipeline concluído para {video_id}: {inserted} momento(s) inserido(s) em generated_clips'
        )
        if inserted == 0:
            # Sem clip válido o status 'selecting' segurava a janela pra sempre.
            _log(f'[AI] Nenhum momento válido para {video_id} — marcando failed e liberando janela')
            update_status(conn, video_id, 'failed')
            _release_failed_source_files(conn, video_id)

    except Exception as exc:
        _log(f'[AI] ERRO no pipeline de IA para {video_id}: {exc}')
        try:
            update_status(conn, video_id, 'failed')
            _release_failed_source_files(conn, video_id)
        except Exception:
            pass


def _process_pending_clips(conn) -> None:
    """Processa clips com status pending_cut sem abortar o poll por falha isolada."""
    with conn.cursor() as cur:
        cur.execute(
            'SELECT gc.id, gc.source_video_id FROM generated_clips gc '
            'JOIN source_videos sv ON sv.id = gc.source_video_id '
            "WHERE gc.status = 'pending_cut' AND sv.paused = FALSE "
            'AND sv.local_path IS NOT NULL AND sv.transcript_path IS NOT NULL'
        )
        rows = cur.fetchall()

    for row in rows:
        clip_id = row['id']
        _log(f'[VID] Iniciando processamento do clip {clip_id}')
        try:
            process_clip(conn, clip_id)
        except Exception as exc:
            _log(f'[VID] ERRO no processamento do clip {clip_id}: {exc}')
        finally:
            source_video_id = row.get('source_video_id')
            if reconcile_source_video_status(conn, source_video_id):
                with conn.cursor() as cur:
                    cur.execute(
                        'SELECT youtube_video_id FROM source_videos WHERE id=%s',
                        (source_video_id,),
                    )
                    source_row = cur.fetchone()
                if source_row:
                    _release_failed_source_files(conn, source_row['youtube_video_id'])


def poll_all_channels(db_conn=None, redis_client=None) -> None:
    """Monitora feeds RSS de todos os canais ativos e insere vídeos novos.

    Args:
        db_conn: conexão PostgreSQL (opcional — se None, cria nova conexão para produção)
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
                response = requests.get(
                    rss_url,
                    headers={'User-Agent': 'curl/7.88.1', 'Accept': '*/*'},
                    timeout=30,
                )
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
                    'SELECT youtube_video_id, local_path FROM source_videos '
                    "WHERE status = 'downloaded' AND local_path IS NOT NULL AND paused = FALSE "
                    'ORDER BY priority DESC, queue_position IS NULL, queue_position ASC, published_at DESC'
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
