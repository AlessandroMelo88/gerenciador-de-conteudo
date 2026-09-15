"""
video_processor.py — Corte, legendas, thumbnail e processamento de clips.

Exporta:
  - cut_clip(source_path, start_time, end_time, output_path) -> str
  - generate_srt(transcript, start_time, end_time, srt_path) -> str
  - burn_subtitles(input_clip_path, srt_path, output_path) -> str
  - extract_thumbnail(clip_path, thumbnail_path, at_seconds=None) -> str
  - overlay_watermark(input_path, watermark_path, output_path) -> str
  - process_clip(conn, clip_id, anthropic_client=None) -> bool

Convenções:
  - FFmpeg é chamado via subprocess.run(check=True, capture_output=True)
  - Diretórios são constantes patcháveis em testes
  - conn: quem chama é responsável por fechar
"""
import json
import os
import subprocess
from datetime import datetime

from src.metadata_generator import generate_metadata, update_clip_metadata


VIDEOS_DIR = '/app/videos'
CLIPS_DIR = '/app/videos/clips'
THUMBNAILS_DIR = '/app/videos/thumbnails'
BRANDING_DIR = os.environ.get('BRANDING_DIR', '/app/branding')


def resolve_background_path(slug: str | None = None, niche: str | None = None) -> str | None:
    """Busca a imagem de background 1920x1080 do canal ou nicho."""
    candidates = []
    if slug:
        candidates.append(os.path.join(BRANDING_DIR, f'background-{slug}.png'))
    if niche:
        n = niche.lower()
        if 'fut' in n:
            candidates.append(os.path.join(BRANDING_DIR, 'background-futebol-em-cortes.png'))
        elif 'pol' in n:
            candidates.append(os.path.join(BRANDING_DIR, 'background-fatos-e-debates.png'))
            candidates.append(os.path.join(BRANDING_DIR, 'background-cortes-da-politica.png'))
        elif 'pod' in n:
            candidates.append(os.path.join(BRANDING_DIR, 'background-podcast-cortes.png'))

    # Fallback para execução local no host
    local_branding = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'branding'))
    if slug:
        candidates.append(os.path.join(local_branding, f'background-{slug}.png'))
    if niche:
        n = niche.lower()
        if 'fut' in n:
            candidates.append(os.path.join(local_branding, 'background-futebol-em-cortes.png'))
        elif 'pol' in n:
            candidates.append(os.path.join(local_branding, 'background-fatos-e-debates.png'))
            candidates.append(os.path.join(local_branding, 'background-cortes-da-politica.png'))
        elif 'pod' in n:
            candidates.append(os.path.join(local_branding, 'background-podcast-cortes.png'))

    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def resolve_default_template_config(channel_name: str = '', niche: str = '') -> dict:
    """Gera configuração padrão inteligente de template 9:16 baseada no nicho do canal."""
    n = (niche or '').lower()
    is_politica = 'pol' in n
    is_futebol = 'fut' in n
    return {
        'headerTitle': (channel_name or ('FATOS & DEBATES' if is_politica else 'CANAL DE CORTES')).upper(),
        'headerBadge': '🔴 FATOS & DEBATES' if is_politica else ('⚽ LANCE DECISIVO' if is_futebol else '🎙️ CORTES EXCLUSIVOS'),
        'accentColor': '#0284c7' if is_politica else ('#10B981' if is_futebol else '#8B5CF6'),
        'bgStyle': 'blur_dark',
        'subtitleColor': '#facc15',
        'ctaText': 'INSCREVA-SE NO CANAL',
    }


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [VID] {msg}')


def cut_clip(
    source_path: str,
    start_time: float,
    end_time: float,
    output_path: str,
    fmt: str = 'curto',
    template_config: dict | None = None,
    background_path: str | None = None,
) -> str:
    """Corta um trecho do vídeo fonte.

    fmt='curto' (padrão): converte pra vertical 1080x1920 (Shorts).
    fmt='longo': se background_path for fornecido, compõe o vídeo 16:9 na janela (1520x855 em x=320, y=72)
    sobre a imagem de background 1920x1080 do canal. Se não houver imagem de fundo, usa o blur vertical 9:16.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cfg = template_config or {}
    bg_style = cfg.get('bgStyle', 'blur_dark')

    duration = max(float(end_time) - float(start_time), 0.1)
    if fmt == 'longo':
        if duration > 1800:
            _log(f'Aviso: duração de corte longo ({duration}s) excede 1800s. Limitando a 1800s.')
            duration = 1800.0
            end_time = float(start_time) + duration
    else:
        if duration > 300:
            _log(f'Aviso: duração de corte curto ({duration}s) excede 300s. Limitando a 300s.')
            duration = 300.0
            end_time = float(start_time) + duration

    if fmt == 'longo':
        if background_path and os.path.exists(background_path):
            video_filter = (
                '[0:v]scale=1520:855:force_original_aspect_ratio=increase,crop=1520:855[fg];'
                '[1:v][fg]overlay=320:72,setsar=1'
            )
            input_args = [
                '-ss', str(start_time),
                '-to', str(end_time),
                '-i', source_path,
                '-loop', '1',
                '-i', background_path,
                '-t', str(duration),
            ]
            filter_args = ['-filter_complex', video_filter]
        else:
            if bg_style == 'blur_intense':
                blur_param = 'boxblur=35:10,eq=brightness=-0.35:contrast=0.90'
            else:
                blur_param = 'boxblur=25:5,eq=brightness=-0.30:contrast=0.95'

            video_filter = (
                f'[0:v]split=2[bg_in][fg_in];'
                f'[bg_in]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,{blur_param}[bg];'
                f'[fg_in]scale=1080:-2[fg];'
                f'[bg][fg]overlay=0:(H-h)/2,setsar=1'
            )
            input_args = [
                '-ss', str(start_time),
                '-to', str(end_time),
                '-i', source_path,
            ]
            filter_args = ['-filter_complex', video_filter]
    else:
        video_filter = (
            'scale=1080:1920:force_original_aspect_ratio=increase,'
            'crop=1080:1920,'
            'setsar=1'
        )
        input_args = [
            '-ss', str(start_time),
            '-to', str(end_time),
            '-i', source_path,
        ]
        filter_args = ['-vf', video_filter]

    subprocess.run(
        [
            'ffmpeg',
            '-threads', '1',
            *input_args,
            *filter_args,
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-crf', '24',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            output_path,
            '-y',
        ],
        check=True,
        capture_output=True,
    )
    return output_path


def generate_srt(transcript: dict, start_time: float, end_time: float, srt_path: str) -> str:
    """Gera arquivo SRT relativo ao início do clip a partir dos segmentos Whisper."""
    os.makedirs(os.path.dirname(srt_path), exist_ok=True)
    cues = []

    for seg in transcript.get('segments', []):
        seg_start = float(seg['start'])
        seg_end = float(seg['end'])
        if seg_end <= start_time or seg_start >= end_time:
            continue

        cue_start = max(seg_start, start_time) - start_time
        cue_end = min(seg_end, end_time) - start_time
        text = str(seg.get('text', '')).strip()
        if not text:
            continue
        cues.append((cue_start, cue_end, text))

    with open(srt_path, 'w', encoding='utf-8') as f:
        for index, (cue_start, cue_end, text) in enumerate(cues, start=1):
            f.write(f'{index}\n')
            f.write(f'{_format_srt_time(cue_start)} --> {_format_srt_time(cue_end)}\n')
            f.write(f'{text}\n\n')

    return srt_path


def burn_subtitles(input_clip_path: str, srt_path: str, output_path: str, fmt: str = 'curto', template_config: dict | None = None) -> str:
    """Queima legendas SRT no clip usando FFmpeg."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cfg = template_config or {}
    color_hex = str(cfg.get('subtitleColor', '#facc15')).lower()
    if color_hex == '#ffffff':
        primary_color = '&H00FFFFFF'
    elif color_hex == '#38bdf8':
        primary_color = '&H00F8BD38'
    else:
        # Padrão amarelo ouro (#facc15 -> BBGGRR: 15CCFA)
        primary_color = '&H0015CCFA'

    if fmt == 'longo':
        subtitle_filter = (
            f"subtitles={srt_path}:"
            "force_style='Fontname=DejaVu Sans,Bold=1,Fontsize=30,"
            "PlayResX=1920,PlayResY=1080,"
            f"PrimaryColour={primary_color},OutlineColour=&H00000000,"
            "BackColour=&H60000000,"
            "BorderStyle=3,Outline=1,Shadow=0,Alignment=2,MarginV=190'"
        )
    else:
        subtitle_filter = (
            f"subtitles={srt_path}:"
            "force_style='Fontname=DejaVu Sans,Bold=1,Fontsize=38,"
            "PlayResX=1080,PlayResY=1920,"
            f"PrimaryColour={primary_color},OutlineColour=&H00000000,"
            "BackColour=&H60000000,"
            "BorderStyle=3,Outline=1,Shadow=0,Alignment=2,MarginV=200'"
        )

    subprocess.run(
        [
            'ffmpeg',
            '-threads', '1',
            '-i', input_clip_path,
            '-vf', subtitle_filter,
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-crf', '24',
            '-c:a', 'copy',
            output_path,
            '-y',
        ],
        check=True,
        capture_output=True,
    )
    return output_path


def extract_thumbnail(
    clip_path: str,
    thumbnail_path: str,
    at_seconds: float = None,
    title: str | None = None,
    niche: str | None = None,
) -> str:
    """Extrai um frame do clip como thumbnail JPG e aplica tipografia de alto CTR estilo YouTube."""
    os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
    if at_seconds is None:
        at_seconds = 1.0
    subprocess.run(
        [
            'ffmpeg',
            '-ss', str(at_seconds),
            '-i', clip_path,
            '-frames:v', '1',
            '-q:v', '2',
            thumbnail_path,
            '-y',
        ],
        check=True,
        capture_output=True,
    )

    if title:
        try:
            _apply_youtube_thumbnail_graphics(thumbnail_path, title, niche)
        except Exception as err:
            _log(f'[THUMBNAIL] Aviso: Não foi possível aplicar tipografia na thumbnail: {err}')

    return thumbnail_path


def _apply_youtube_thumbnail_graphics(thumbnail_path: str, title: str, niche: str | None = None):
    """Aplica tipografia profissional e efeito de nuvem de sombra de alto CTR estilo YouTube:
    - Efeito de nuvem de sombra suave (sem caixa quadrada rígida)
    - Tipografia de altíssimo impacto (Anton / Bebas Neue / Arial Black)
    - Texto 1 (Branco) + Texto 2 (Ciano Neon para Política / Amarelo Ouro para Futebol) com efeito 3D
    - Círculo no canto direito com aura luminosa neon e brasão oficial do canal
    - Badge de destaque no canto superior esquerdo com ponto luminoso
    """
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
    except ImportError:
        _log('[CAPA] Pillow não disponível — mantendo frame bruto')
        return

    if not os.path.exists(thumbnail_path):
        return

    bg = Image.open(thumbnail_path).convert('RGB')
    bg = bg.resize((1280, 720), Image.Resampling.LANCZOS)

    # 1. Tratamento profissional de imagem (Contraste + Saturação + Nitidez)
    bg = ImageEnhance.Contrast(bg).enhance(1.22)
    bg = ImageEnhance.Color(bg).enhance(1.20)
    bg = ImageEnhance.Sharpness(bg).enhance(1.15)

    n = (niche or '').lower()
    is_pol = 'pol' in n or 'debate' in n or 'fatos' in n or 'mbl' in title.lower() or 'congresso' in title.lower()
    is_fut = 'fut' in n or 'bola' in n or 'golaço' in title.lower() or 'vasco' in title.lower() or 'gol' in title.lower()
    is_mon = 'monetiz' in n or '3g' in n or 'market' in n

    # 2. Carregamento de fontes de alto impacto (Anton / Bebas Neue / Arial Black / Impact)
    local_branding = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'branding'))
    font_path = None
    for cand in [
        os.path.join(BRANDING_DIR, 'fonts', 'Anton-Regular.ttf'),
        os.path.join(local_branding, 'fonts', 'Anton-Regular.ttf'),
        os.path.join(BRANDING_DIR, 'fonts', 'BebasNeue-Regular.ttf'),
        os.path.join(local_branding, 'fonts', 'BebasNeue-Regular.ttf'),
        '/System/Library/Fonts/Supplemental/Arial Black.ttf',
        '/System/Library/Fonts/Supplemental/Impact.ttf',
        '/Library/Fonts/Arial Black.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    ]:
        if os.path.exists(cand):
            font_path = cand
            break

    def _get_font(size: int):
        if font_path:
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                pass
        return ImageFont.load_default()

    # 3. Processamento inteligente das linhas de chamada (Texto 1 e Texto 2)
    clean_title = title.replace('"', '').replace("'", "").strip()
    parts = clean_title.split(':') if ':' in clean_title else clean_title.split(' - ') if ' - ' in clean_title else clean_title.split('! ')
    if len(parts) >= 2:
        text1 = parts[0].strip().upper()
        if not text1.endswith('!') and not text1.endswith('?'):
            text1 += '!'
        text2 = ' '.join(parts[1:]).strip().upper()
    else:
        words = clean_title.strip().split()
        if len(words) <= 4:
            text1 = clean_title.upper()
            text2 = 'DECISÃO URGENTE!' if is_pol else ('GOLAÇO HISTÓRICO!' if is_fut else 'MÉTODO REVELADO!')
        else:
            mid = max(2, len(words) // 2)
            text1 = ' '.join(words[:mid]).upper() + '!'
            text2 = ' '.join(words[mid:]).upper()

    # Cores e Estilos por Nicho
    if is_pol:
        # Fatos & Debates: Branco Puro + Ciano Elétrico Neon (#00E5FF)
        color_line1 = (255, 255, 255)
        color_line2 = (0, 225, 255)
        badge_label = 'FATOS & DEBATES'
        badge_dot_color = (239, 68, 68)
        badge_bg = (180, 15, 25, 240)
        glow_color = (0, 210, 255, 170)
        neon_border = (0, 225, 255, 230)
        slug = 'fatos-e-debates'
    elif is_fut:
        # Futebol em Cortes: Branco Puro + Amarelo Ouro Elétrico (#FFE100)
        color_line1 = (255, 255, 255)
        color_line2 = (255, 225, 0)
        badge_label = 'LANCE DECISIVO'
        badge_dot_color = (34, 197, 94)
        badge_bg = (16, 140, 75, 240)
        glow_color = (34, 197, 94, 170)
        neon_border = (34, 197, 94, 230)
        slug = 'futebol-em-cortes'
    else:
        # Monetização 3G / Geral: Branco Puro + Amarelo Ouro
        color_line1 = (255, 255, 255)
        color_line2 = (255, 215, 0)
        badge_label = 'MONETIZAÇÃO 3G'
        badge_dot_color = (168, 85, 247)
        badge_bg = (109, 40, 217, 240)
        glow_color = (168, 85, 247, 170)
        neon_border = (234, 179, 8, 230)
        slug = None

    # 4. Cálculo dinâmico do tamanho das fontes (horizontal, sem rotação diagonal)
    base_x = 60
    available_w = 980

    font_size1 = 76
    f1 = _get_font(font_size1)
    dummy = ImageDraw.Draw(bg)
    while dummy.textlength(text1, font=f1) > available_w and font_size1 > 38:
        font_size1 -= 2
        f1 = _get_font(font_size1)

    font_size2 = 80
    f2 = _get_font(font_size2)
    while dummy.textlength(text2, font=f2) > available_w and font_size2 > 38:
        font_size2 -= 2
        f2 = _get_font(font_size2)

    # 5. Sombra preta profunda na base estilo CSS linear-gradient (Sombra suave e uniforme, sem cortes)
    # linear-gradient(to top, rgba(0,0,0,0.98) 0%, rgba(0,0,0,0.88) 45%, rgba(0,0,0,0.3) 85%, transparent 100%)
    shadow_overlay = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
    d_shadow = ImageDraw.Draw(shadow_overlay)

    grad_start_y = 350
    grad_height = 720 - grad_start_y
    for y in range(grad_start_y, 720):
        t = (y - grad_start_y) / float(grad_height)
        alpha = int(252 * min(1.0, (t * 1.30) ** 1.25))
        d_shadow.line([(0, y), (1280, y)], fill=(0, 0, 0, alpha))

    shadow_overlay = shadow_overlay.filter(ImageFilter.GaussianBlur(radius=4))
    bg.paste(shadow_overlay, (0, 0), shadow_overlay)

    # 6. Renderização do texto PERFEITAMENTE ALINHADO (HORIZONTAL, sem inclinação)
    draw = ImageDraw.Draw(bg)

    def draw_aligned_text(d, x, y, text, font, fill_color, stroke_w=6, drop_shadow_offset=4):
        # Drop shadow profunda projetada para baixo (estilo CSS text-shadow: 0 4px 10px rgba(0,0,0,0.85))
        for s in range(1, drop_shadow_offset + 1):
            d.text((x, y + s + 2), text, font=font, fill=(0, 0, 0, 200))
        # Contorno reforçado em 360° para legibilidade impecável
        for dx in range(-stroke_w, stroke_w + 1):
            for dy in range(-stroke_w, stroke_w + 1):
                if dx * dx + dy * dy <= stroke_w * stroke_w:
                    d.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0, 255))
        # Texto principal
        d.text((x, y), text, font=font, fill=fill_color)

    bbox1 = f1.getbbox(text1)
    h1 = (bbox1[3] - bbox1[1]) if bbox1 else font_size1
    bbox2 = f2.getbbox(text2)
    h2 = (bbox2[3] - bbox2[1]) if bbox2 else font_size2

    total_text_h = h1 + h2 + 16
    y1 = 720 - total_text_h - 45
    y2 = y1 + h1 + 14

    draw_aligned_text(draw, base_x, y1, text1, f1, color_line1, stroke_w=6)
    draw_aligned_text(draw, base_x, y2, text2, f2, color_line2, stroke_w=7)

    # 7. Efeito da Bola / Brasão com Aura Neon no canto direito
    circle_size = 145
    ball_x = 1075
    ball_y = 515

    ball_glow = Image.new('RGBA', (circle_size + 60, circle_size + 60), (0, 0, 0, 0))
    d_bglow = ImageDraw.Draw(ball_glow)
    d_bglow.ellipse([10, 10, circle_size + 50, circle_size + 50], fill=glow_color)
    ball_glow = ball_glow.filter(ImageFilter.GaussianBlur(radius=20))
    bg.paste(ball_glow, (ball_x - 30, ball_y - 30), ball_glow)

    emblem_layer = Image.new('RGBA', (circle_size, circle_size), (0, 0, 0, 0))
    d_emb = ImageDraw.Draw(emblem_layer)
    d_emb.ellipse([4, 4, circle_size - 4, circle_size - 4], fill=(8, 12, 22, 245), outline=(212, 175, 55, 255), width=4)
    d_emb.ellipse([8, 8, circle_size - 8, circle_size - 8], outline=neon_border, width=3)

    if slug:
        for candidate_wm in [
            os.path.join(BRANDING_DIR, f'watermark-{slug}.png'),
            os.path.join(local_branding, f'watermark-{slug}.png'),
            f'branding/watermark-{slug}.png',
        ]:
            if os.path.exists(candidate_wm):
                try:
                    wm = Image.open(candidate_wm).convert('RGBA')
                    wm = wm.resize((circle_size - 22, circle_size - 22), Image.Resampling.LANCZOS)
                    emblem_layer.paste(wm, (11, 11), wm)
                except Exception:
                    pass
                break

    bg.paste(emblem_layer, (ball_x, ball_y), emblem_layer)

    # 8. Badge Superior Esquerdo com ponto luminoso
    d_final = ImageDraw.Draw(bg)
    font_badge = _get_font(23)
    text_w = d_final.textlength(badge_label, font=font_badge)
    badge_w = int(text_w + 58)
    badge_h = 42

    d_final.rounded_rectangle([45, 35, 45 + badge_w, 35 + badge_h], radius=10, fill=badge_bg, outline=(255, 255, 255, 200), width=2)
    d_final.ellipse([58, 48, 72, 62], fill=badge_dot_color, outline=(255, 255, 255, 240), width=1)
    d_final.text((80, 42), badge_label, font=font_badge, fill='white')

    # Moldura fina dourada de acabamento
    d_final.rounded_rectangle([10, 10, 1270, 710], radius=16, outline=(212, 175, 55, 130), width=3)

    bg.save(thumbnail_path, 'JPEG', quality=95)
    _log(f'[CAPA] Capa customizada de alto CTR gerada com sucesso: {thumbnail_path}')


def overlay_watermark(input_path: str, watermark_path: str, output_path: str) -> str:
    """Aplica watermark PNG no canto superior direito do clip via FFmpeg.

    Usa -filter_complex overlay=W-w-20:20 com dois inputs (clip + PNG alpha).
    Retorna input_path sem chamar FFmpeg se o watermark não existir (graceful degradation).
    """
    if not os.path.exists(watermark_path):
        _log(f'[WATERMARK] Arquivo não encontrado: {watermark_path} — pulo overlay')
        return input_path

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    subprocess.run(
        [
            'ffmpeg',
            '-i', input_path,        # [0] = clip vídeo
            '-i', watermark_path,    # [1] = PNG watermark
            '-filter_complex', 'overlay=W-w-20:20',  # canto sup direito, margem 20px
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-crf', '23',
            '-c:a', 'copy',
            output_path,
            '-y',
        ],
        check=True,
        capture_output=True,
    )
    return output_path


def process_clip(conn, clip_id: int, anthropic_client=None) -> bool:
    """Processa um registro de generated_clips com status pending_cut.

    Pipeline: cut → generate_srt → burn_subtitles → overlay_watermark → extract_thumbnail
    O arquivo intermediário _subtitled.mp4 é removido após o watermark (ou rename).
    """
    try:
        clip = _fetch_clip(conn, clip_id)
        if clip is None:
            _log(f'Clip {clip_id} não encontrado')
            return False

        _update_clip_status(conn, clip_id, 'cutting')

        with open(clip['transcript_path'], 'r', encoding='utf-8') as f:
            transcript = json.load(f)

        raw_clip_path = os.path.join(CLIPS_DIR, f'{clip_id}_raw.mp4')
        srt_path = os.path.join(CLIPS_DIR, f'{clip_id}.srt')
        subtitled_path = os.path.join(CLIPS_DIR, f'{clip_id}_subtitled.mp4')
        final_clip_path = os.path.join(CLIPS_DIR, f'{clip_id}.mp4')
        thumbnail_path = os.path.join(THUMBNAILS_DIR, f'{clip_id}.jpg')

        defaults = resolve_default_template_config(
            clip.get('destination_channel_name') or '',
            clip.get('destination_channel_niche') or '',
        )
        cfg = clip.get('template_config')
        if isinstance(cfg, str):
            try:
                cfg = json.loads(cfg)
            except Exception:
                cfg = {}
        elif not isinstance(cfg, dict):
            cfg = {}

        merged_cfg = {**defaults, **cfg}

        slug = clip.get('destination_channel_slug')
        niche = clip.get('destination_channel_niche')
        fmt = clip.get('format') or 'curto'

        bg_path = resolve_background_path(slug=slug, niche=niche) if fmt == 'longo' else None

        cut_clip(
            clip['local_path'],
            clip['start_time'],
            clip['end_time'],
            raw_clip_path,
            fmt=fmt,
            template_config=merged_cfg,
            background_path=bg_path,
        )
        generate_srt(transcript, clip['start_time'], clip['end_time'], srt_path)
        burn_subtitles(raw_clip_path, srt_path, subtitled_path, fmt=fmt, template_config=merged_cfg)

        # Aplicar watermark se canal-destino tem slug configurado e formato curto (vídeo longo já tem branding integrado na moldura)
        if slug and fmt != 'longo':
            watermark_path = f'/app/branding/watermark-{slug}.png'
            # overlay_watermark retorna subtitled_path se arquivo de watermark não existir (graceful)
            result_path = overlay_watermark(subtitled_path, watermark_path, final_clip_path)
            if result_path == subtitled_path:
                # Watermark ausente: renomear para path final
                os.rename(subtitled_path, final_clip_path)
            else:
                # Watermark aplicado: remover intermediário
                if os.path.exists(subtitled_path):
                    os.remove(subtitled_path)
        else:
            # Sem canal-destino ou vídeo longo: renomear arquivo legendado para path final
            os.rename(subtitled_path, final_clip_path)

        metadata = generate_metadata(_build_clip_context(clip, transcript), anthropic_client=anthropic_client)
        update_clip_metadata(conn, clip_id, metadata)
        title = (metadata.get('title') or clip.get('title') or clip.get('source_title') or 'CORTES EXCLUSIVOS').strip()

        duration = max(float(clip['end_time']) - float(clip['start_time']), 1.0)
        # Para vídeo longo 16:9, captura o frame limpo do vídeo original para qualidade HD na capa
        thumb_source = clip.get('local_path') if (fmt == 'longo' and clip.get('local_path') and os.path.exists(clip['local_path'])) else final_clip_path
        at_sec = float(clip['start_time']) + min(3.0, duration * 0.25) if thumb_source == clip.get('local_path') else min(2.0, duration * 0.25)

        extract_thumbnail(
            thumb_source,
            thumbnail_path,
            at_seconds=at_sec,
            title=title,
            niche=niche,
        )

        with conn.cursor() as cur:
            cur.execute(
                'UPDATE generated_clips '
                'SET clip_path=%s, thumbnail_path=%s '
                'WHERE id=%s',
                (final_clip_path, thumbnail_path, clip_id),
            )
        conn.commit()

        _update_clip_status(conn, clip_id, 'pending')
        _log(f'Clip {clip_id} processado: {final_clip_path}')
        return True

    except Exception as exc:
        err_msg = f'Falha no corte/processamento: {str(exc)[:400]}'
        _log(f'Erro ao processar clip {clip_id}: {exc}')
        try:
            _update_clip_status(conn, clip_id, 'failed', error_msg=err_msg)
        except Exception:
            pass
        return False


def _fetch_clip(conn, clip_id: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            'SELECT '
            'gc.id, gc.source_video_id, gc.start_time, gc.end_time, gc.score, gc.reason, '
            'sv.youtube_video_id, sv.title AS source_title, sv.local_path, sv.transcript_path, sv.format, '
            'dc.slug AS destination_channel_slug, dc.name AS destination_channel_name, dc.niche AS destination_channel_niche, dc.template_config '
            'FROM generated_clips gc '
            'JOIN source_videos sv ON sv.id = gc.source_video_id '
            'LEFT JOIN destination_channels dc ON dc.id = gc.destination_channel_id '
            'WHERE gc.id = %s',
            (clip_id,),
        )
        return cur.fetchone()


def _update_clip_status(conn, clip_id: int, status: str, error_msg: str | None = None) -> None:
    with conn.cursor() as cur:
        if error_msg is not None:
            cur.execute(
                'UPDATE generated_clips SET status=%s, upload_error=%s WHERE id=%s',
                (status, error_msg, clip_id),
            )
        else:
            cur.execute(
                'UPDATE generated_clips SET status=%s WHERE id=%s',
                (status, clip_id),
            )
    conn.commit()


def _build_clip_context(clip: dict, transcript: dict) -> dict:
    start_time = float(clip['start_time'])
    end_time = float(clip['end_time'])
    excerpt_lines = []
    for seg in transcript.get('segments', []):
        seg_start = float(seg['start'])
        seg_end = float(seg['end'])
        if seg_end > start_time and seg_start < end_time:
            excerpt_lines.append(str(seg.get('text', '')).strip())

    return {
        'source_title': clip.get('source_title') or '',
        'reason': clip.get('reason') or '',
        'score': clip.get('score'),
        'start_time': start_time,
        'end_time': end_time,
        'niche': clip.get('destination_channel_niche') or 'futebol',
        'format': clip.get('format') or 'curto',
        'transcript_excerpt': ' '.join(line for line in excerpt_lines if line),
    }


def _format_srt_time(seconds: float) -> str:
    milliseconds_total = int(round(seconds * 1000))
    hours = milliseconds_total // 3_600_000
    remainder = milliseconds_total % 3_600_000
    minutes = remainder // 60_000
    remainder %= 60_000
    secs = remainder // 1000
    millis = remainder % 1000
    return f'{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}'
