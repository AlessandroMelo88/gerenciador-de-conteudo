import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

def generate_aligned_thumbnail(
    base_frame_path: str,
    output_path: str,
    title: str,
    niche: str = 'politica',
    badge_text: str = None,
    watermark_path: str = None,
    include_emblem: bool = True
):
    # 1. Base 1280x720
    if os.path.exists(base_frame_path):
        bg = Image.open(base_frame_path).convert('RGB')
        bg = bg.resize((1280, 720), Image.Resampling.LANCZOS)
    else:
        bg = Image.new('RGB', (1280, 720), (12, 18, 32))

    # Realce profissional de contraste e cores
    bg = ImageEnhance.Contrast(bg).enhance(1.18)
    bg = ImageEnhance.Color(bg).enhance(1.15)
    bg = ImageEnhance.Sharpness(bg).enhance(1.12)

    n = (niche or '').lower()
    is_pol = 'pol' in n or 'debate' in n or 'fatos' in n
    is_fut = 'fut' in n or 'bola' in n or 'gol' in n or 'resenha' in n
    is_mon = 'monetiz' in n or '3g' in n or 'market' in n

    # 2. Fonte Anton (Ultra-Bold Condensed)
    font_path = None
    for cand in [
        'branding/fonts/Anton-Regular.ttf',
        '/System/Library/Fonts/Supplemental/Arial Black.ttf',
        '/System/Library/Fonts/Supplemental/Impact.ttf',
        '/Library/Fonts/Arial Black.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    ]:
        if os.path.exists(cand):
            font_path = cand
            break

    def get_font(size: int):
        if font_path:
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                pass
        return ImageFont.load_default()

    # 3. Processamento do Título em Linha 1 e Linha 2
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
        color_line1 = (255, 255, 255)       # Branco Puro
        color_line2 = (0, 225, 255)         # Ciano Neon (#00E5FF)
        badge_label = badge_text or 'FATOS & DEBATES'
        badge_dot_color = (239, 68, 68)     # Vermelho
        badge_bg = (180, 15, 25, 240)
        glow_color = (0, 210, 255, 160)
        neon_border = (0, 225, 255, 230)
        wm_default = 'branding/watermark-fatos-e-debates.png'
    elif is_fut:
        color_line1 = (255, 255, 255)       # Branco Puro
        color_line2 = (255, 225, 0)         # Amarelo Ouro (#FFE100)
        badge_label = badge_text or 'LANCE DECISIVO'
        badge_dot_color = (34, 197, 94)     # Verde
        badge_bg = (16, 140, 75, 240)
        glow_color = (34, 197, 94, 160)
        neon_border = (34, 197, 94, 230)
        wm_default = 'branding/watermark-futebol-em-cortes.png'
    else:
        color_line1 = (255, 255, 255)       # Branco Puro
        color_line2 = (255, 215, 0)         # Ouro Dourado (#FFD700)
        badge_label = badge_text or 'MONETIZAÇÃO 3G'
        badge_dot_color = (168, 85, 247)
        badge_bg = (109, 40, 217, 240)
        glow_color = (168, 85, 247, 160)
        neon_border = (234, 179, 8, 230)
        wm_default = None

    # 4. SOMBRA PRETA EMBAIXO ESTILO CSS (Sombra de verdade, uniforme, profunda e suave)
    # Como solicitado pelo usuário:
    # "uma sombra preta embaixo, sombra mesmo, dá para fazer isso com CSS. As setas e as linhas são mais escuras."
    # Gradiente linear horizontal em toda a largura (1280px) de y=360 a y=720
    shadow_overlay = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
    d_shadow = ImageDraw.Draw(shadow_overlay)

    grad_start_y = 350
    grad_height = 720 - grad_start_y
    for y in range(grad_start_y, 720):
        t = (y - grad_start_y) / float(grad_height)
        # Sombra profunda estilo CSS: linear-gradient(to top, rgba(0,0,0,0.98) 0%, rgba(0,0,0,0.88) 45%, rgba(0,0,0,0.3) 85%, transparent 100%)
        # Sem cortes verticais — cobre toda a largura de 0 a 1280
        alpha = int(252 * min(1.0, (t * 1.30) ** 1.25))
        d_shadow.line([(0, y), (1280, y)], fill=(0, 0, 0, alpha))

    # Leve desfoque suave para eliminar qualquer bandagem
    shadow_overlay = shadow_overlay.filter(ImageFilter.GaussianBlur(radius=4))
    bg.paste(shadow_overlay, (0, 0), shadow_overlay)

    # 5. Cálculo dinâmico do tamanho das fontes (horizontal, sem diagonal)
    base_x = 60
    available_w = 980 if include_emblem else 1160

    font_size1 = 76
    f1 = get_font(font_size1)
    dummy = ImageDraw.Draw(bg)
    while dummy.textlength(text1, font=f1) > available_w and font_size1 > 38:
        font_size1 -= 2
        f1 = get_font(font_size1)

    font_size2 = 80
    f2 = get_font(font_size2)
    while dummy.textlength(text2, font=f2) > available_w and font_size2 > 38:
        font_size2 -= 2
        f2 = get_font(font_size2)

    # 6. Renderização do Texto PERFEITAMENTE ALINHADO (HORIZONTAL, SEM DIAGONAL)
    draw = ImageDraw.Draw(bg)

    def draw_aligned_text(d, x, y, text, font, fill_color, stroke_w=6, drop_shadow_offset=4):
        # Drop shadow suave projetada para baixo (estilo CSS text-shadow: 0 4px 10px rgba(0,0,0,0.85))
        for s in range(1, drop_shadow_offset + 1):
            d.text((x, y + s + 2), text, font=font, fill=(0, 0, 0, 200))
        # Contorno preto 360° reforçado para contraste absoluto
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

    # 7. Bola / Brasão decorativo com Aura Neon no canto direito inferior
    if include_emblem:
        circle_size = 140
        ball_x = 1085
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

        wm_file = watermark_path or wm_default
        if wm_file and os.path.exists(wm_file):
            try:
                wm = Image.open(wm_file).convert('RGBA')
                wm = wm.resize((circle_size - 24, circle_size - 24), Image.Resampling.LANCZOS)
                emblem_layer.paste(wm, (12, 12), wm)
            except Exception:
                pass

        bg.paste(emblem_layer, (ball_x, ball_y), emblem_layer)

    # 8. Badge Superior Esquerdo com ponto luminoso
    font_badge = get_font(23)
    text_w = draw.textlength(badge_label, font=font_badge)
    badge_w = int(text_w + 58)
    badge_h = 42

    draw.rounded_rectangle([45, 35, 45 + badge_w, 35 + badge_h], radius=10, fill=badge_bg, outline=(255, 255, 255, 200), width=2)
    draw.ellipse([58, 48, 72, 62], fill=badge_dot_color, outline=(255, 255, 255, 240), width=1)
    draw.text((80, 42), badge_label, font=font_badge, fill='white')

    # Moldura dourada elegante de acabamento
    draw.rounded_rectangle([10, 10, 1270, 710], radius=16, outline=(212, 175, 55, 130), width=3)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    bg.save(output_path, 'JPEG', quality=95)
    print(f"Capa gerada: {output_path}")

if __name__ == '__main__':
    # Teste 1: Futebol no frame 736 (lance de campo)
    generate_aligned_thumbnail(
        base_frame_path='videos/thumbnails/736.jpg',
        output_path='/tmp/aligned_futebol_736_v2.jpg',
        title='YURI ALBERTO SALVA CORINTHIANS: GOLAÇO HISTÓRICO!',
        niche='futebol'
    )
    # Teste 2: Debate no frame 874
    generate_aligned_thumbnail(
        base_frame_path='videos/thumbnails/874.jpg',
        output_path='/tmp/aligned_debate_874_v2.jpg',
        title='DEBATE ACALORADO AO VIVO: CLIMA ESQUENTA NO ESTÚDIO!',
        niche='politica'
    )
    # Teste 3: Imagem enviada pelo usuário (Flavio e Lula)
    generate_aligned_thumbnail(
        base_frame_path='/Users/alessandrobm1/.gemini/antigravity/brain/db2709f6-abe0-4bfa-b49a-63ce0578746d/.user_uploaded/media_1789148723089.png',
        output_path='/tmp/aligned_user_sample.jpg',
        title='FLÁVIO TEM 45,4% CONTRA 45% DE LULA: PESQUISA FUTURA!',
        niche='politica'
    )
