"""
subtitle_detector.py — Detecta legenda já queimada no vídeo-fonte.

Exporta:
  - has_burned_subtitles(video_path, transcript, start_time, end_time) -> bool

Muitos canais publicam o vídeo com a legenda gravada no quadro. Quando o trecho
extraído já traz esse texto, queimar o nosso SRT por cima deixa duas legendas na
tela do Short.

Só a presença de texto no rodapé não decide nada: placar, lower-third de
transmissão, gravação de tela e estante ao fundo também acendem qualquer
heurística de pixel. O que separa legenda de todo o resto é ela **repetir o que
está sendo falado**. Então a detecção lê o rodapé com OCR (tesseract, idioma
`por`) em alguns instantes do trecho e cruza as palavras lidas com a
transcrição daquele mesmo segundo. Banner de patrocinador e código na tela não
acompanham a fala; legenda queimada acompanha.

Qualquer falha (arquivo ausente, tesseract indisponível, FFmpeg com erro)
devolve False: na dúvida o pipeline mantém o comportamento antigo e queima a
legenda.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import unicodedata
from datetime import datetime

# Faixa inferior lida pelo OCR, em fração da altura do quadro. Generosa de
# propósito: há canal que sobe a legenda para perto do meio do quadro. O filtro
# de verdade é o cruzamento com a transcrição, não o recorte.
BOTTOM_BAND_RATIO = 0.50
OCR_WIDTH = 1600  # tesseract erra menos com o recorte ampliado
OCR_LANGUAGE = 'por'
OCR_PAGE_SEGMENTATION = '6'  # bloco único de texto, que é o formato de uma legenda

SAMPLE_COUNT = 6
# A legenda mostra o que acabou de ser dito; a folga cobre o atraso de quem
# legenda na mão e o adiantamento de quem quebra a frase antes.
SPEECH_LEAD_SECONDS = 2.5
SPEECH_LAG_SECONDS = 1.0

MIN_WORD_LENGTH = 4  # "que", "não", "de" aparecem em qualquer lugar
MIN_MATCHED_WORDS = 3

# O casamento precisa valer para quase todo o trecho, não para um instante. Há
# apresentador que compartilha a tela e lê o texto em voz alta: ali o OCR bate
# com a transcrição por alguns segundos sem existir legenda nenhuma. Legenda
# queimada, ao contrário, acompanha a fala do começo ao fim do clip.
MIN_MATCHING_FRAMES = 3
MIN_MATCHING_RATIO = 0.60

FFMPEG_TIMEOUT_SECONDS = 60
TESSERACT_TIMEOUT_SECONDS = 60

_WORD_RE = re.compile(r'[a-z0-9]+')


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [SUB] {msg}')


def detection_enabled() -> bool:
    """Permite desligar a detecção sem rebuild, via BURNED_SUBTITLE_DETECTION."""
    return os.environ.get('BURNED_SUBTITLE_DETECTION', 'true').strip().lower() in {
        'true',
        '1',
        'yes',
        'on',
    }


def has_burned_subtitles(
    video_path: str,
    transcript: dict,
    start_time: float = 0.0,
    end_time: float | None = None,
) -> bool:
    """Diz se o trecho `[start_time, end_time]` já traz legenda gravada no quadro."""
    if not detection_enabled():
        return False
    if not video_path or not os.path.isfile(video_path):
        return False
    if shutil.which('tesseract') is None:
        _log('tesseract indisponível — sigo queimando a legenda')
        return False

    start = max(float(start_time), 0.0)
    duration = 0.0 if end_time is None else float(end_time) - start
    if duration <= 0:
        return False

    matched = 0
    read = 0
    with tempfile.TemporaryDirectory(prefix='subdetect-') as workdir:
        for index in range(SAMPLE_COUNT):
            moment = start + duration * (index + 0.5) / SAMPLE_COUNT
            spoken = _spoken_words(transcript, moment)
            if len(spoken) < MIN_MATCHED_WORDS:
                continue

            frame_text = _read_bottom_band(
                video_path, moment, os.path.join(workdir, f'{index}.png')
            )
            if frame_text is None:
                continue

            read += 1
            hits = _significant_words(frame_text) & spoken
            if len(hits) >= MIN_MATCHED_WORDS:
                matched += 1

    if read < MIN_MATCHING_FRAMES or matched < MIN_MATCHING_FRAMES:
        return False
    if matched / read < MIN_MATCHING_RATIO:
        return False

    _log(
        f'Legenda queimada detectada em {os.path.basename(video_path)}: '
        f'{matched}/{read} quadros com o rodapé repetindo a fala'
    )
    return True


def _read_bottom_band(video_path: str, moment: float, frame_path: str) -> str | None:
    """Extrai o rodapé do quadro em `moment` e devolve o texto lido pelo OCR."""
    try:
        subprocess.run(
            [
                'ffmpeg',
                '-hide_banner',
                '-loglevel',
                'error',
                '-ss',
                f'{moment:.3f}',
                '-i',
                video_path,
                '-frames:v',
                '1',
                '-vf',
                (
                    f'crop=iw:ih*{BOTTOM_BAND_RATIO}:0:ih*{1 - BOTTOM_BAND_RATIO:g},'
                    f'scale={OCR_WIDTH}:-2,format=gray'
                ),
                frame_path,
                '-y',
            ],
            check=True,
            capture_output=True,
            timeout=FFMPEG_TIMEOUT_SECONDS,
        )
        result = subprocess.run(
            [
                'tesseract',
                frame_path,
                'stdout',
                '-l',
                OCR_LANGUAGE,
                '--psm',
                OCR_PAGE_SEGMENTATION,
            ],
            check=True,
            capture_output=True,
            timeout=TESSERACT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        _log(f'Timeout lendo o rodapé de {os.path.basename(video_path)} em {moment:.1f}s')
        return None
    except (subprocess.CalledProcessError, OSError) as exc:
        _log(f'Falha ao ler o rodapé de {os.path.basename(video_path)}: {exc}')
        return None

    return result.stdout.decode('utf-8', errors='replace')


def _spoken_words(transcript: dict, moment: float) -> set[str]:
    """Palavras da transcrição faladas em torno de `moment`."""
    window_start = moment - SPEECH_LEAD_SECONDS
    window_end = moment + SPEECH_LAG_SECONDS
    spoken = []
    for segment in (transcript or {}).get('segments', []):
        try:
            segment_start = float(segment['start'])
            segment_end = float(segment['end'])
        except (KeyError, TypeError, ValueError):
            continue
        if segment_end < window_start or segment_start > window_end:
            continue
        spoken.append(str(segment.get('text', '')))
    return _significant_words(' '.join(spoken))


def _significant_words(text: str) -> set[str]:
    """Normaliza o texto e devolve as palavras longas o bastante para comparar."""
    stripped = unicodedata.normalize('NFKD', text or '')
    ascii_text = ''.join(char for char in stripped if not unicodedata.combining(char)).lower()
    return {word for word in _WORD_RE.findall(ascii_text) if len(word) >= MIN_WORD_LENGTH}
