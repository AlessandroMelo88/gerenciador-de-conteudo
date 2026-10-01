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
from src.prompt_profiles import load_profile_for_source_video
from src.selector import select_moments, insert_selected_moments, MIN_LONGFORM_SECONDS
from src.format_mode import (
    MODE_BOTH, MODE_SHORT_ONLY, clip_format_sql, generated_clips_has_format, get_long_format_mode,
)
from src.video_processor import process_clip
from src.queue_controls import _cleanup_partial


REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))


def _log(msg: str) -> None:
    """Loga mensagem com timestamp para stdout."""
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [ACQU] {msg}')


def _detect_format(video_id: str, mode_resolver=None) -> str:
    """Decide 'curto' ou 'longo' com base na duração real do vídeo fonte.

    mode_resolver: callable opcional que devolve o `long_format_mode` do canal destino do nicho
    (`auto` | `short_only` | `both`). É consultado só quando a fonte é longa; `short_only` rebaixa
    a fonte para 'curto' (gera Shorts, nunca longo). Sem resolver = comportamento histórico (`auto`).

    Vídeos com MIN_LONGFORM_SECONDS ou mais (entrevistas, podcasts, análises longas)
    têm material suficiente pra um corte longo horizontal; o resto continua shorts.
    Falha ao consultar metadados (rede, vídeo indisponível) → assume 'curto' (comportamento
    anterior), sem abortar a ingestão do vídeo por isso.
    """
    try:
        ydl_opts = {
            'quiet': True,
            'no_color': True,
            'skip_download': True,
            'remote_components': ['ejs:github'],
            'extractor_args': {
                'youtube': {
                    'player_client': ['mweb', 'tv', 'ios', 'android']
                }
            },
        }
        cookie_file = '/app/youtube/cookies.txt'
        if os.path.exists(cookie_file):
            ydl_opts['cookiefile'] = cookie_file

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
        duration = info.get('duration') if info else None
        if duration and duration >= MIN_LONGFORM_SECONDS:
            if mode_resolver is not None and mode_resolver() == MODE_SHORT_ONLY:
                return 'curto'
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


def _count_clips_of_format(conn, source_video_id: int, fmt: str) -> int:
    """Clips já existentes da fonte no formato `fmt` (guard de idempotência do modo `both`)."""
    expr = clip_format_sql(conn)
    with conn.cursor() as cur:
        cur.execute(
            'SELECT COUNT(*) AS n FROM generated_clips gc '
            'JOIN source_videos sv ON sv.id = gc.source_video_id '
            f'WHERE gc.source_video_id = %s AND {expr} = %s',
            (source_video_id, fmt),
        )
        row = cur.fetchone()
    try:
        return int((row or {}).get('n') or 0)
    except (TypeError, ValueError, AttributeError):
        return 0


def _plan_selection_runs(conn, source_video_id: int, fmt: str, niche: str) -> list[dict]:
    """Decide quais seleções rodar para a fonte, conforme `long_format_mode` do canal destino do nicho.

    - fonte curta, ou modo `auto`: uma seleção no formato da fonte, chamada IDÊNTICA à histórica.
    - fonte longa + `short_only`: uma seleção de Shorts (amostrando janelas) e `source_videos.format`
      passa a 'curto', para o render/cota tratarem o clip como Short.
    - fonte longa + `both`: Shorts primeiro, depois um longo estrito (sem esticar trecho curto), cada
      clip gravado com `generated_clips.format` próprio; `source_videos.format` continua 'longo'.
      Sem a coluna `generated_clips.format` (migration pendente) degrada para `short_only`: melhor
      não gerar o longo do que gerar um clip que o render não saberia distinguir.
    """
    plain = [{'fmt': fmt, 'select_kwargs': {}, 'insert_kwargs': {}, 'guard': False}]
    if fmt != 'longo':
        return plain
    mode = get_long_format_mode(conn, niche)
    if mode == MODE_BOTH and not generated_clips_has_format(conn):
        _log(f'[AI] AVISO: modo both pedido, mas generated_clips.format não existe — gerando só Shorts')
        mode = MODE_SHORT_ONLY
    if mode == MODE_SHORT_ONLY:
        with conn.cursor() as cur:
            cur.execute("UPDATE source_videos SET format = 'curto' WHERE id = %s", (source_video_id,))
        conn.commit()
        return [{'fmt': 'curto', 'select_kwargs': {'sample_windows': True}, 'insert_kwargs': {}, 'guard': False}]
    if mode == MODE_BOTH:
        return [
            {'fmt': 'curto', 'select_kwargs': {'sample_windows': True},
             'insert_kwargs': {'clip_format': 'curto'}, 'guard': True},
            {'fmt': 'longo', 'select_kwargs': {'strict_long': True},
             'insert_kwargs': {'clip_format': 'longo'}, 'guard': True},
        ]
    return plain


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
        from src.queue_controls import is_paused

        if is_paused(conn, youtube_video_id=video_id):
            _log(f'[AI] Pulando {video_id} — pausado')
            return

        # Transcrição
        update_status(conn, video_id, 'transcribing')
        transcript = transcribe_video(video_id, local_path, groq_client=groq_client)
        if transcript is None:
            _log(f'[AI] Transcrição falhou para {video_id} — marcando como failed')
            update_status(conn, video_id, 'failed', clear_local_path=True)
            _cleanup_partial(video_id)
            return

        if is_paused(conn, youtube_video_id=video_id):
            _log(f'[AI] {video_id} pausado após transcrição — não seleciona')
            update_status(conn, video_id, 'downloaded')
            return

        save_transcript(conn, video_id, transcript)

        # Seleção
        update_status(conn, video_id, 'selecting')

        # Obter source_video_id INT + formato (curto/longo) + nicho para FK em generated_clips
        with conn.cursor() as cur:
            cur.execute("""
                SELECT sv.id, sv.format, sc.target_niche
                FROM source_videos sv
                LEFT JOIN source_channels sc ON sv.channel_id = sc.id
                WHERE sv.youtube_video_id = %s
            """, (video_id,))
            row = cur.fetchone()
        if row is None:
            _log(f'[AI] AVISO: source_video_id não encontrado para {video_id}')
            return
        source_video_id = row['id']
        fmt = row.get('format') or 'curto'
        niche = row.get('target_niche') or 'futebol'

        profile_kwargs = {}
        prompt_profile = load_profile_for_source_video(conn, source_video_id)
        if prompt_profile:  # sem perfil: chamada idêntica à de antes dos perfis
            profile_kwargs['prompt_profile'] = prompt_profile
        runs = _plan_selection_runs(conn, source_video_id, fmt, niche)
        inserted = 0
        for run in runs:
            if run['guard'] and _count_clips_of_format(conn, source_video_id, run['fmt']) > 0:
                # reprocessamento: esse formato já tem clip — não duplica
                _log(f'[AI] {video_id}: já existem clips {run["fmt"]} — pulando seleção desse formato')
                inserted += 1
                continue
            moments = select_moments(transcript, anthropic_client=anthropic_client, fmt=run['fmt'], niche=niche,
                                     **run['select_kwargs'], **profile_kwargs)
            inserted += insert_selected_moments(conn, source_video_id, video_id, moments,
                                                **run['insert_kwargs'])
        _log(f'[AI] Pipeline concluído para {video_id}: {inserted} momento(s) inserido(s) em generated_clips')
        if inserted == 0:
            # Sem clip válido o status 'selecting' segurava a janela pra sempre.
            _log(f'[AI] Nenhum momento válido para {video_id} — marcando failed e liberando janela')
            update_status(conn, video_id, 'failed', clear_local_path=True)
            _cleanup_partial(video_id)

    except Exception as exc:
        _log(f'[AI] ERRO no pipeline de IA para {video_id}: {exc}')
        try:
            update_status(conn, video_id, 'failed', clear_local_path=True)
            _cleanup_partial(video_id)
        except Exception:
            pass


def _process_pending_clips(conn) -> None:
    """Processa clips com status pending_cut sem abortar o poll por falha isolada."""
    try:
        conn.commit()
    except Exception:
        pass
    with conn.cursor() as cur:
        cur.execute(
            "SELECT gc.id FROM generated_clips gc "
            "JOIN source_videos sv ON sv.id = gc.source_video_id "
            "WHERE gc.status = 'pending_cut' AND sv.paused = FALSE "
            "ORDER BY gc.id ASC LIMIT 2"
        )
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
        )
    lock_acquired = False
    lock_key = 'lock:poll_all_channels'
    if redis_client:
        try:
            lock_acquired = bool(redis_client.set(lock_key, '1', ex=600, nx=True))
            if not lock_acquired:
                _log('AVISO: Outro ciclo de poll_all_channels já está em execução — pulando para evitar sobrecarga.')
                if _own_db:
                    db_conn.close()
                return
        except Exception as lock_err:
            _log(f'Aviso: falha ao checar lock Redis: {lock_err}')

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

                    fmt = _detect_format(
                        video_id,
                        mode_resolver=lambda: get_long_format_mode(db_conn, channel.get('target_niche')),
                    )
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
                    "SELECT sv.youtube_video_id, sv.local_path FROM source_videos sv "
                    "LEFT JOIN source_channels sc ON sc.id = sv.channel_id "
                    "WHERE sv.status = 'downloaded' AND sv.local_path IS NOT NULL AND sv.paused = FALSE "
                    "ORDER BY sv.priority DESC, "
                    "CASE WHEN LOWER(COALESCE(sc.target_niche, '')) = 'futebol' THEN 0 ELSE 1 END, "
                    "sv.queue_position IS NULL, sv.queue_position ASC, sv.published_at DESC "
                    "LIMIT 2"
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
        if lock_acquired and redis_client:
            try:
                redis_client.delete(lock_key)
            except Exception:
                pass
        if _own_db:
            db_conn.close()
