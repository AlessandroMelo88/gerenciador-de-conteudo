import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

BRANDING_DIR = 'branding'
os.makedirs(BRANDING_DIR, exist_ok=True)

logo_path = os.path.join(BRANDING_DIR, 'fatos_debates_logo.jpg')
banner_path = os.path.join(BRANDING_DIR, 'fatos_debates_banner.jpg')

# 1. Gerar Watermark circular transparente (256x256 e 512x512)
if os.path.exists(logo_path):
    logo_src = Image.open(logo_path).convert('RGB')
    size = 256
    logo_resized = logo_src.resize((size, size), Image.Resampling.LANCZOS)
    
    # Máscara circular com borda dourada
    mask = Image.new('L', (size, size), 0)
    d_mask = ImageDraw.Draw(mask)
    d_mask.ellipse((4, 4, size - 4, size - 4), fill=255)
    
    watermark = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    watermark.paste(logo_resized, (0, 0), mask)
    
    # Anel dourado
    d_wm = ImageDraw.Draw(watermark)
    d_wm.ellipse((4, 4, size - 4, size - 4), outline=(212, 175, 55, 255), width=4)
    
    wm_out = os.path.join(BRANDING_DIR, 'watermark-fatos-e-debates.png')
    watermark.save(wm_out, 'PNG')
    print('Watermark salva em:', wm_out)

# 2. Gerar Background 1920x1080 oficial para vídeo longo 16:9
bg = Image.new('RGBA', (1920, 1080), (10, 15, 28, 255)) # Azul escuro profundo / Navy elegante

if os.path.exists(banner_path):
    banner = Image.open(banner_path).convert('RGBA')
    banner = banner.resize((1920, 1080), Image.Resampling.LANCZOS)
    banner = ImageEnhance.Brightness(banner).enhance(0.4)
    banner = ImageEnhance.Contrast(banner).enhance(1.2)
    banner = banner.filter(ImageFilter.GaussianBlur(radius=8))
    bg.paste(banner, (0, 0))

draw = ImageDraw.Draw(bg)

# Moldura onde fica a janela do vídeo: x=320, y=72, w=1520, h=855 (mesmas proporções do video_processor)
vx, vy, vw, vh = 320, 72, 1520, 855

# Área interna do vídeo (preto absoluto)
draw.rectangle([vx, vy, vx + vw, vy + vh], fill=(0, 0, 0, 255))
# Moldura dupla elegante: Dourada + Ciano
draw.rectangle([vx - 3, vy - 3, vx + vw + 3, vy + vh + 3], outline=(212, 175, 55, 255), width=3)
draw.rectangle([vx - 6, vy - 6, vx + vw + 6, vy + vh + 6], outline=(0, 220, 255, 120), width=1)

# Barra lateral esquerda (x=0 a x=320)
# Gradiente ou fundo escuro na coluna esquerda
col_overlay = Image.new('RGBA', (320, 1080), (7, 11, 22, 230))
bg.paste(col_overlay, (0, 0), col_overlay)

# Logo oficial na coluna esquerda
if os.path.exists(logo_path):
    logo_col = Image.open(logo_path).convert('RGB').resize((180, 180), Image.Resampling.LANCZOS)
    mask_col = Image.new('L', (180, 180), 0)
    d_m = ImageDraw.Draw(mask_col)
    d_m.ellipse((2, 2, 178, 178), fill=255)
    
    logo_rgba = Image.new('RGBA', (180, 180), (0, 0, 0, 0))
    logo_rgba.paste(logo_col, (0, 0), mask_col)
    
    d_lg = ImageDraw.Draw(logo_rgba)
    d_lg.ellipse((2, 2, 178, 178), outline=(212, 175, 55, 255), width=4)
    d_lg.ellipse((5, 5, 175, 175), outline=(0, 220, 255, 180), width=2)
    
    bg.paste(logo_rgba, (70, 90), logo_rgba)

# Carregar fonte
font_title = None
font_sub = None
font_btn = None
for fp in [
    '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
    '/Library/Fonts/Arial Bold.ttf',
    '/System/Library/Fonts/Helvetica.ttc',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
]:
    if os.path.exists(fp):
        try:
            font_title = ImageFont.truetype(fp, 26)
            font_sub = ImageFont.truetype(fp, 13)
            font_btn = ImageFont.truetype(fp, 16)
            font_footer = ImageFont.truetype(fp, 15)
            break
        except Exception:
            pass

if not font_title:
    font_title = font_sub = font_btn = font_footer = ImageFont.load_default()

# Texto na coluna esquerda: FATOS & DEBATES
draw.text((160, 295), 'FATOS &', font=font_title, fill=(255, 255, 255, 255), anchor='mm')
draw.text((160, 328), 'DEBATES', font=font_title, fill=(212, 175, 55, 255), anchor='mm')
draw.text((160, 360), 'JORNALISMO & POLÍTICA', font=font_sub, fill=(0, 220, 255, 220), anchor='mm')

# Divisor sutil
draw.line([(50, 385), (270, 385)], fill=(212, 175, 55, 100), width=1)

# Badge de Destaque na coluna
draw.rounded_rectangle([45, 410, 275, 442], radius=8, fill=(229, 9, 20, 220))
draw.text((160, 426), '🔴 DEBATE OFICIAL', font=font_sub, fill='white', anchor='mm')

# Botão Inscreva-se na coluna
draw.rounded_rectangle([45, 950, 275, 995], radius=10, fill=(212, 175, 55, 255))
draw.text((160, 972), '▶ INSCREVA-SE', font=font_btn, fill=(10, 15, 28, 255), anchor='mm')

# Rodapé abaixo do vídeo (y=945 a 1040, x=320 a 1840)
draw.text((340, 972), 'FATOS & DEBATES • OS DEBATES E ANÁLISES QUE DEFINEM O BRASIL', font=font_footer, fill=(200, 210, 230, 220))
draw.line([(340, 998), (1700, 998)], fill=(212, 175, 55, 120), width=2)

bg_out = os.path.join(BRANDING_DIR, 'background-fatos-e-debates.png')
bg.save(bg_out, 'PNG')
print('Background salvo em:', bg_out)

# Também sobrescreve background-cortes-da-politica.png para compatibilidade retroativa
bg_legacy = os.path.join(BRANDING_DIR, 'background-cortes-da-politica.png')
bg.save(bg_legacy, 'PNG')
print('Background legado atualizado:', bg_legacy)

# Copiar watermark para watermark-cortes-da-politica.png também
wm_legacy = os.path.join(BRANDING_DIR, 'watermark-cortes-da-politica.png')
watermark.save(wm_legacy, 'PNG')
print('Watermark legado atualizado:', wm_legacy)
