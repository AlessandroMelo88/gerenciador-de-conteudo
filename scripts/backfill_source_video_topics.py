#!/usr/bin/env python3
"""Backfill isolado de transcrições e assuntos do canal Fabio Akita."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CLIP_PROCESSOR_ROOT = REPO_ROOT / 'clip-processor'
if str(CLIP_PROCESSOR_ROOT) not in sys.path:
    sys.path.insert(0, str(CLIP_PROCESSOR_ROOT))

from src.downloader import download_video
from src.db import get_db_connection
from src.paths import VIDEOS_DIR, resolve_stored_video_path
from src.topic_segmenter import process_transcript_topics
from src.transcriber import (
    _download_youtube_transcript,
    save_transcript,
    transcribe_video,
)

FABIO_AKITA_YOUTUBE_CHANNEL_ID = 'UCib793mnUOhWymCh2VJKplQ'


def _decode_transcript_data(value) -> dict | None:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return None
        return decoded if isinstance(decoded, dict) else None
    return None


def _is_complete_transcript(transcript: dict | None) -> bool:
    if not isinstance(transcript, dict) or not str(transcript.get('text') or '').strip():
        return False
    segments = transcript.get('segments')
    return isinstance(segments, list) and bool(segments) and any(
        isinstance(segment, dict) and str(segment.get('text') or '').strip()
        for segment in segments
    )


def _has_canonical_transcript(row: dict) -> bool:
    transcript = _decode_transcript_data(row.get('transcript_data'))
    return (
        _is_complete_transcript(transcript)
        and str(transcript.get('text') or '') == str(row.get('transcript_text') or '')
    )


def _load_stored_transcript(row: dict) -> dict | None:
    transcript = _decode_transcript_data(row.get('transcript_data'))
    if transcript is not None and not str(transcript.get('text') or '').strip():
        transcript['text'] = str(row.get('transcript_text') or '')
    if not _is_complete_transcript(transcript):
        transcript_path = resolve_stored_video_path(row.get('transcript_path'))
        if transcript_path and os.path.isfile(transcript_path):
            try:
                with open(transcript_path, encoding='utf-8') as transcript_file:
                    sidecar = json.load(transcript_file)
                if isinstance(sidecar, dict) and not str(sidecar.get('text') or '').strip():
                    sidecar['text'] = str(row.get('transcript_text') or '')
                if _is_complete_transcript(sidecar):
                    transcript = sidecar
            except (OSError, json.JSONDecodeError):
                pass

    if not _is_complete_transcript(transcript):
        return None

    transcript = dict(transcript)
    transcript.setdefault('video_id', row['youtube_video_id'])
    if not str(transcript.get('text') or '').strip():
        transcript['text'] = str(row.get('transcript_text') or '')
    return transcript


def _source_channel(conn) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            'SELECT id, channel_name FROM source_channels WHERE youtube_channel_id=%s',
            (FABIO_AKITA_YOUTUBE_CHANNEL_ID,),
        )
        return cur.fetchone()


def _source_videos(conn, channel_id: int) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            'SELECT id, youtube_video_id, title, local_path, transcript_path, transcript_data, '
            'transcript_text, topic_segmentation_status '
            'FROM source_videos WHERE channel_id=%s '
            'ORDER BY published_at NULLS LAST, id',
            (channel_id,),
        )
        return cur.fetchall()


def _dry_run_summary(rows: list[dict]) -> None:
    complete_transcripts = sum(_has_canonical_transcript(row) for row in rows)
    sidecar_transcripts = sum(
        not _has_canonical_transcript(row) and _load_stored_transcript(row) is not None
        for row in rows
    )
    completed_topics = sum(row.get('topic_segmentation_status') == 'completed' for row in rows)
    missing_transcripts = len(rows) - complete_transcripts - sidecar_transcripts
    pending_topics = sum(
        row.get('topic_segmentation_status') in ('pending', 'failed', 'processing', 'not_ready')
        for row in rows
    )
    print(
        'DRY-RUN: '
        f'vídeos={len(rows)}, transcrições completas={complete_transcripts}, '
        f'transcrições recuperáveis de sidecar={sidecar_transcripts}, '
        f'transcrições ausentes/incompletas={missing_transcripts}, '
        f'tópicos concluídos={completed_topics}, elegíveis para processamento/retry={pending_topics}. '
        'Nenhuma chamada de IA ou download foi realizado.'
    )


def _set_not_ready(conn, source_video_id: int) -> None:
    with conn.cursor() as cur:
        cur.execute(
            'UPDATE source_videos SET topic_segmentation_status=%s, '
            'topic_segmentation_error=NULL WHERE id=%s',
            ('not_ready', source_video_id),
        )
    conn.commit()


def _transcribe_missing_video(row: dict) -> tuple[dict | None, str | None]:
    video_id = row['youtube_video_id']
    raw_path = os.path.join(VIDEOS_DIR, f'{video_id}_topic_backfill.mp4')
    pending_raw_path = raw_path if os.path.isfile(raw_path) else None

    # Prefer the platform's captions before spending bandwidth on a media download
    # or a Whisper transcription, including when a previous attempt left a raw file.
    transcript = _download_youtube_transcript(video_id)
    if _is_complete_transcript(transcript):
        transcript = dict(transcript)
        transcript.setdefault('video_id', video_id)
        return transcript, pending_raw_path

    existing_raw = resolve_stored_video_path(row.get('local_path'))
    if existing_raw and os.path.isfile(existing_raw):
        transcript = transcribe_video(video_id, existing_raw)
        if _is_complete_transcript(transcript):
            transcript = dict(transcript)
            transcript.setdefault('video_id', video_id)
            return transcript, None
        return None, None

    os.makedirs(VIDEOS_DIR, exist_ok=True)
    if pending_raw_path is None:
        if not download_video(video_id, raw_path):
            return None, None
        pending_raw_path = raw_path

    transcript = transcribe_video(video_id, pending_raw_path)
    if not _is_complete_transcript(transcript):
        # Keep a successfully downloaded raw file so a later --apply can retry transcription.
        return None, pending_raw_path

    transcript = dict(transcript)
    transcript.setdefault('video_id', video_id)
    return transcript, pending_raw_path


def _process_video(conn, row: dict) -> tuple[bool, bool]:
    """Returns (transcript_was_saved, topic_segmentation_succeeded)."""
    source_video_id = int(row['id'])
    video_id = row['youtube_video_id']
    stored_transcript = _decode_transcript_data(row.get('transcript_data'))
    needs_persistence = not _is_complete_transcript(stored_transcript) or (
        str((stored_transcript or {}).get('text') or '')
        != str(row.get('transcript_text') or '')
    )
    transcript = _load_stored_transcript(row)
    raw_candidate = os.path.join(VIDEOS_DIR, f'{video_id}_topic_backfill.mp4')
    raw_path = raw_candidate if os.path.isfile(raw_candidate) else None

    if transcript is None:
        transcript, raw_path = _transcribe_missing_video(row)
        if transcript is None:
            _set_not_ready(conn, source_video_id)
            return False, False

    save_transcript(conn, video_id, transcript)

    topics_saved = process_transcript_topics(conn, source_video_id, transcript)
    if raw_path:
        try:
            os.remove(raw_path)
        except OSError as exc:
            print(f'AVISO: transcrição salva; raw {raw_path} não pôde ser removido: {exc}')

    return needs_persistence, topics_saved


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            'Organiza transcrições do Fabio Akita em assuntos. '
            'Por segurança, grave e baixe somente com --apply.'
        )
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='mostra o escopo sem chamar IA, gravar ou baixar (padrão)',
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='grava os tópicos e tenta obter transcrições que ainda faltam',
    )
    args = parser.parse_args()
    if args.apply and args.dry_run:
        parser.error('use --apply ou --dry-run, não ambos')

    conn = get_db_connection()
    failures = 0
    try:
        channel = _source_channel(conn)
        if channel is None:
            print(
                f'Canal não encontrado: {FABIO_AKITA_YOUTUBE_CHANNEL_ID}',
                file=sys.stderr,
            )
            return 2

        rows = _source_videos(conn, int(channel['id']))
        if not args.apply:
            _dry_run_summary(rows)
            return 0

        counts = {'transcripts_saved': 0, 'topics_saved': 0, 'pending': 0}
        for row in rows:
            transcript = _load_stored_transcript(row)
            if (
                row.get('topic_segmentation_status') == 'completed'
                and _has_canonical_transcript(row)
            ):
                continue

            video_id = row['youtube_video_id']
            print(f'Processando {video_id}: {row.get("title") or video_id}')
            try:
                transcript_saved, topics_saved = _process_video(conn, row)
            except Exception as exc:
                conn.rollback()
                failures += 1
                print(f'ERRO em {video_id}: {exc}', file=sys.stderr)
                continue

            counts['transcripts_saved'] += int(transcript_saved)
            counts['topics_saved'] += int(topics_saved)
            if not topics_saved:
                counts['pending'] += 1
                failures += 1

        print(
            f"Backfill concluído para {channel.get('channel_name')}: "
            f"novas transcrições={counts['transcripts_saved']}, "
            f"segmentações concluídas={counts['topics_saved']}, "
            f"pendentes/erro={counts['pending']}"
        )
        return 1 if failures else 0
    finally:
        conn.close()


if __name__ == '__main__':
    raise SystemExit(main())
