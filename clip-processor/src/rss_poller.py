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

from __future__ import annotations

import json
import os
import re
import unicodedata
from datetime import UTC, datetime

import feedparser
import redis
import requests
import yt_dlp

from src.db import (
    fetch_used_moments,
    get_db_connection,
    insert_video,
    reconcile_source_video_status,
    update_status,
)
from src.dedup import is_seen
from src.paths import VIDEOS_DIR, resolve_stored_video_path
from src.prompt_profiles import PROMPT_PROFILE_SQL_COLUMNS, profile_from_row, profile_matches_niche
from src.queue_controls import _cleanup_partial
from src.selector import MIN_LONGFORM_SECONDS, insert_selected_moments, select_moments
from src.topic_segmenter import process_transcript_topics
from src.transcriber import WHISPER_TECH_PROMPT, save_transcript, transcribe_video
from src.video_processor import process_clip

# Bloqueios editoriais globais; políticas por canal ficam em listas separadas abaixo.
_TITLE_BLOCK_KEYWORDS = [
    'aposta',
    'apostas',
    # A checagem é por palavra inteira (antes era substring): flexões precisam constar.
    'apostar',
    'apostou',
    'apostando',
    'apostador',
    'apostadores',
    'bet ',
    'bets ',
    'bet365',
    'betano',
    'betfair',
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

_HACKER_LIBERTARIO_TITLE_BLOCK_KEYWORDS = [
    'fux',
    'dino',
    'moraes',
    'stf',
    'tse',
    'stj',
    'pgr',
    'lula',
    'bolsonaro',
    'haddad',
    'congresso',
    'câmara',
    'camara',
    'senado',
    'planalto',
    'receita federal',
    'imposto de renda',
    'inss',
    'ibge',
    'pib',
    'tráfico',
    'trafico',
    'drogas',
    'eleição',
    'eleicao',
    'eleições',
    'eleicoes',
    'voto',
    'urna',
    'ministro',
    'deputado',
    'senador',
    'governador',
    'prefeito',
    'partido',
    'política',
    'politica',
    'parasita',
    'servidor público',
    'servidor publico',
    'funcionário público',
    'funcionario publico',
    'concurso público',
    'concurso publico',
    'candidatura',
    'candidato',
    'campanha eleitoral',
]


def _normalize_title_terms(value: str) -> str:
    decomposed = unicodedata.normalize('NFKD', value.casefold())
    without_accents = ''.join(char for char in decomposed if not unicodedata.combining(char))
    return ' '.join(re.findall(r'[a-z0-9]+', without_accents))


def _contains_title_keyword(title: str, keywords: list[str]) -> bool:
    normalized_title = f' {_normalize_title_terms(title)} '
    return any(f' {_normalize_title_terms(keyword)} ' in normalized_title for keyword in keywords)


def _is_blocked_title(title: str, prompt_profile_slug: str | None = None) -> bool:
    if _contains_title_keyword(title, _TITLE_BLOCK_KEYWORDS):
        return True

    return prompt_profile_slug == 'conteudo-inteligencia' and _contains_title_keyword(
        title, _HACKER_LIBERTARIO_TITLE_BLOCK_KEYWORDS
    )


REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
SOURCE_FILE_ROOT = os.path.realpath(VIDEOS_DIR)
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

    transcript_path = resolve_stored_video_path(source.get('transcript_path'))
    transcript_archived = not transcript_path or not os.path.isfile(transcript_path)
    if transcript_path and os.path.isfile(transcript_path):
        try:
            with open(transcript_path, encoding='utf-8') as f:
                save_transcript(conn, video_id, json.load(f))
            transcript_archived = True
        except (OSError, ValueError) as exc:
            _log(f'[AI] Transcrição de {video_id} não pôde ser arquivada; arquivo mantido: {exc}')

    paths = [resolve_stored_video_path(source.get('local_path'))]
    if transcript_archived:
        paths.append(transcript_path)
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
            'UPDATE source_videos SET local_path=NULL, '
            'transcript_path=CASE WHEN %s THEN NULL ELSE transcript_path END '
            "WHERE id=%s AND status='failed'",
            (transcript_archived, source['id']),
        )
    conn.commit()
    _log(f'[AI] Arquivos de {video_id} liberados após falha terminal')


def _fallback_channel_entries(channel: dict) -> list[dict]:
    """Busca os vídeos recentes pela aba ``videos`` quando o RSS falha.

    O endpoint RSS do YouTube responde 404/500 para alguns canais mesmo com o
    ``channel_id`` válido. O fallback usa a mesma origem oficial via yt-dlp,
    limita a consulta aos vídeos recentes e devolve o formato mínimo aceito
    pelo restante do poller. A deduplicação continua sendo feita por
    ``is_seen`` antes de qualquer INSERT.
    """
    channel_id = channel.get('youtube_channel_id')
    channel_handle = channel.get('channel_handle')
    if channel_id:
        target = f'https://www.youtube.com/channel/{channel_id}/videos'
    elif channel_handle:
        target = f'https://www.youtube.com/{channel_handle}/videos'
    else:
        _log(f'AVISO: canal {channel.get("channel_name")} sem ID/handle para fallback yt-dlp')
        return []

    options = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'extract_flat': True,
        'ignoreerrors': True,
        'playlistend': 15,
    }
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(target, download=False) or {}
    except Exception as exc:
        _log(f'AVISO: fallback yt-dlp falhou para {channel.get("channel_name")}: {exc}')
        return []

    entries: list[dict] = []
    for item in info.get('entries') or []:
        if not item or not item.get('id'):
            continue

        published_at = item.get('timestamp')
        if published_at:
            published_at = datetime.fromtimestamp(published_at, tz=UTC).isoformat()
        else:
            upload_date = str(item.get('upload_date') or '')
            if len(upload_date) == 8 and upload_date.isdigit():
                published_at = (
                    f'{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}T00:00:00+00:00'
                )

        entries.append(
            {
                'yt_videoid': item['id'],
                'title': item.get('title') or item['id'],
                'published': published_at,
            }
        )

    _log(
        f'Fallback yt-dlp para {channel.get("channel_name")}: '
        f'{len(entries)} entrada(s) encontrada(s)'
    )
    return entries


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
        # Carrega o perfil antes do Whisper para não enviesar a transcrição de outros canais.
        with conn.cursor() as cur:
            cur.execute(
                'SELECT sv.id, sv.format, sv.generate_both_formats, '
                'sc.target_niche, sc.prompt_profile_id, ' + PROMPT_PROFILE_SQL_COLUMNS + ' '
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
            update_status(conn, video_id, 'failed')
            _release_failed_source_files(conn, video_id)
            _cleanup_partial(video_id)
            return

        source_video_id = row['id']
        source_format = row.get('format') or 'curto'
        generate_both_formats = bool(row.get('generate_both_formats'))
        niche = row.get('target_niche')
        prompt_profile = profile_from_row(row)
        if prompt_profile and not profile_matches_niche(prompt_profile, niche):
            _log(
                f'[AI] Perfil {prompt_profile.get("slug")} não corresponde ao nicho {niche}; '
                'fallback seguro aplicado'
            )
            prompt_profile = None

        transcription_kwargs = {}
        if prompt_profile and prompt_profile.get('slug') == 'conteudo-inteligencia':
            transcription_kwargs['prompt'] = WHISPER_TECH_PROMPT

        transcript = transcribe_video(
            video_id,
            local_path,
            groq_client=groq_client,
            **transcription_kwargs,
        )
        if transcript is None:
            _log(f'[AI] Transcrição falhou para {video_id} — marcando como failed')
            update_status(conn, video_id, 'failed')
            _release_failed_source_files(conn, video_id)
            _cleanup_partial(video_id)
            return

        if is_paused(conn, youtube_video_id=video_id):
            _log(f'[AI] {video_id} pausado após transcrição — não seleciona')
            update_status(conn, video_id, 'downloaded')
            return

        save_transcript(conn, video_id, transcript)

        if not process_transcript_topics(
            conn,
            source_video_id,
            transcript,
            ai_client=anthropic_client,
        ):
            _log(
                f'[AI] Transcrição de {video_id} arquivada; divisão por assunto falhou '
                'e poderá ser refeita sem retranscrever'
            )

        # Uma transcrição alimenta os dois formatos; cada clip guarda seu
        # formato para renderização, publicação, cota e metadados.
        update_status(conn, video_id, 'selecting')
        transcript_duration = max(
            (float(segment.get('end', 0)) for segment in transcript.get('segments', [])),
            default=0.0,
        )
        output_formats = [source_format]
        if generate_both_formats:
            output_formats = ['curto']
            if transcript_duration > MIN_LONGFORM_SECONDS + 2.0:
                output_formats.append('longo')

        total_inserted = 0
        for output_format in output_formats:
            try:
                used_moments = fetch_used_moments(conn, source_video_id, format=output_format)
                select_kwargs = {'anthropic_client': anthropic_client, 'fmt': output_format}
                if used_moments:
                    select_kwargs['used_moments'] = used_moments
                if niche:
                    select_kwargs['niche'] = niche
                elif not prompt_profile:
                    select_kwargs['niche'] = 'futebol'
                if prompt_profile:
                    select_kwargs['prompt_profile'] = prompt_profile

                moments = select_moments(transcript, **select_kwargs)
                inserted = insert_selected_moments(
                    conn,
                    source_video_id,
                    video_id,
                    moments,
                    format=output_format,
                )
                total_inserted += inserted
                _log(
                    f'[AI] {output_format} concluído para {video_id}: '
                    f'{inserted} momento(s) inserido(s)'
                )
            except Exception as exc:
                _log(f'[AI] ERRO ao gerar formato {output_format} para {video_id}: {exc}')
                try:
                    conn.rollback()
                except Exception:
                    pass

        _log(
            f'[AI] Pipeline concluído para {video_id}: {total_inserted} momento(s) inserido(s) em generated_clips'
        )
        if total_inserted == 0:
            # Sem clip válido o status 'selecting' segurava a janela pra sempre.
            _log(f'[AI] Nenhum momento válido para {video_id} — marcando failed e liberando janela')
            update_status(conn, video_id, 'failed')
            _release_failed_source_files(conn, video_id)
            _cleanup_partial(video_id)

    except Exception as exc:
        _log(f'[AI] ERRO no pipeline de IA para {video_id}: {exc}')
        try:
            update_status(conn, video_id, 'failed')
            _release_failed_source_files(conn, video_id)
            _cleanup_partial(video_id)
        except Exception:
            pass


def _process_downloaded_videos(conn) -> None:
    """Processa vídeos ``downloaded`` com transcrição e seleção por IA.

    A descoberta, a IA e o render eram originalmente executados pelo mesmo
    método. Manter esta etapa como função pública permite que o deployment
    rode um worker de IA separado, sem alterar o comportamento do ciclo legado.
    """
    try:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT sv.youtube_video_id, sv.local_path FROM source_videos sv '
                'LEFT JOIN source_channels sc ON sc.id = sv.channel_id '
                "WHERE sv.status = 'downloaded' AND sv.local_path IS NOT NULL AND sv.paused = FALSE "
                'ORDER BY sv.priority DESC, COALESCE(sc.input_priority, 0) DESC, '
                'sv.queue_position IS NULL, sv.queue_position ASC, sv.published_at DESC'
            )
            downloaded_videos = cur.fetchall()

        for video_row in downloaded_videos:
            vid_id = video_row['youtube_video_id']
            vid_path = resolve_stored_video_path(video_row['local_path'])
            if not vid_path or not os.path.exists(vid_path):
                _log(f'[AI] Arquivo fonte de {vid_id} não está disponível em {vid_path}')
                continue
            _log(f'[AI] Iniciando pipeline de IA para {vid_id}')
            try:
                _process_ai_pipeline(conn, vid_id, vid_path)
            except Exception as exc:
                _log(f'[AI] ERRO no pipeline de {vid_id}: {exc}')
    except Exception as exc:
        _log(f'[AI] ERRO ao buscar vídeos downloaded para processamento: {exc}')


def _process_pending_clips(conn) -> None:
    """Processa clips com status pending_cut sem abortar o poll por falha isolada."""
    try:
        conn.commit()
    except Exception:
        pass
    with conn.cursor() as cur:
        cur.execute(
            'SELECT gc.id, gc.source_video_id FROM generated_clips gc '
            'JOIN source_videos sv ON sv.id = gc.source_video_id '
            'LEFT JOIN source_channels sc ON sc.id = sv.channel_id '
            "WHERE gc.status = 'pending_cut' AND sv.paused = FALSE "
            'AND sv.local_path IS NOT NULL AND sv.transcript_path IS NOT NULL '
            'ORDER BY sv.priority DESC, COALESCE(sc.input_priority, 0) DESC, '
            "(COALESCE(gc.format, sv.format) = 'longo') DESC, gc.id ASC"
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


def poll_all_channels(
    db_conn=None,
    redis_client=None,
    *,
    process_ai: bool = True,
    process_cuts: bool = True,
) -> None:
    """Monitora feeds RSS de todos os canais ativos e insere vídeos novos.

    Args:
        db_conn: conexão PostgreSQL (opcional — se None, cria nova conexão para produção)
        redis_client: cliente Redis (opcional — se None, cria nova conexão para produção)
        process_ai: se True, também drena a fila de vídeos downloaded
        process_cuts: se True, também drena a fila de clips pending_cut
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
                _log(
                    'AVISO: Outro ciclo de poll_all_channels já está em execução — pulando para evitar sobrecarga.'
                )
                if _own_db:
                    db_conn.close()
                return
        except Exception as lock_err:
            _log(f'Aviso: falha ao checar lock Redis: {lock_err}')

    try:
        # Buscar canais ativos (canais blacklistados filtrados no SELECT — COPY-03)
        with db_conn.cursor() as cur:
            cur.execute(
                'SELECT sc.id, sc.channel_name, sc.rss_url, sc.target_niche, '
                'sc.channel_handle, sc.youtube_channel_id, pp.slug AS prompt_profile_slug '
                'FROM source_channels sc '
                'LEFT JOIN prompt_profiles pp '
                'ON pp.id = sc.prompt_profile_id AND pp.active = TRUE '
                'WHERE sc.active = TRUE AND sc.blacklisted = FALSE'
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
                    entries = _fallback_channel_entries(channel)
                else:
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

                    if _is_blocked_title(
                        title,
                        prompt_profile_slug=channel.get('prompt_profile_slug'),
                    ):
                        _log(f'Título bloqueado (keyword): {video_id} — {title}')
                        continue

                    insert_video(
                        db_conn,
                        video_id,
                        channel_id,
                        title,
                        published_at,
                        format='curto',
                        generate_both_formats=True,
                    )
                    _log(
                        f'Novo vídeo detectado (Shorts + longo quando elegível): {video_id} — {title}'
                    )
                    total_new += 1

            except Exception as exc:
                _log(f'ERRO ao processar canal {channel_name}: {exc}')
                continue

        _log(f'Poll concluído: {total_new} vídeo(s) novo(s) inserido(s)')

        # Processar vídeos que já estão downloaded (transcrição + seleção)
        if process_ai:
            _process_downloaded_videos(db_conn)

        # Processar clips selecionados pela IA (corte + legenda + thumbnail + metadata)
        if process_cuts:
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


def poll_sources_only(db_conn=None, redis_client=None) -> None:
    """Atualiza apenas a fila de fontes, sem executar IA ou FFmpeg."""
    return poll_all_channels(
        db_conn=db_conn,
        redis_client=redis_client,
        process_ai=False,
        process_cuts=False,
    )


def process_downloaded_videos(conn) -> None:
    """Drena a fila de vídeos baixados (transcrição + seleção)."""
    return _process_downloaded_videos(conn)


def process_pending_clips(conn) -> None:
    """Drena a fila de clips aguardando renderização."""
    return _process_pending_clips(conn)
