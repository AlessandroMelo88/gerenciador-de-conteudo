import os
import sys
import shutil
from PIL import Image

sys.path.insert(0, os.path.abspath('clip-processor'))
from src.video_processor import _apply_youtube_thumbnail_graphics

os.makedirs('videos/thumbnails', exist_ok=True)

# 1. Prepara base limpa de debate político (Flavio & Lula da imagem enviada pelo usuário)
user_img_path = '/Users/alessandrobm1/.gemini/antigravity/brain/db2709f6-abe0-4bfa-b49a-63ce0578746d/.user_uploaded/media_1789148723089.png'
base_debate_political = '/tmp/base_debate_political.jpg'
if os.path.exists(user_img_path):
    img = Image.open(user_img_path)
    crop1 = img.crop((105, 96, 858, 388)).convert('RGB')
    crop1 = crop1.resize((1280, 720), Image.Resampling.LANCZOS)
    crop1.save(base_debate_political, quality=95)
else:
    shutil.copyfile('videos/thumbnails/874.jpg', base_debate_political)

# 2. Base limpa de debate de estúdio
base_debate_studio = 'videos/thumbnails/874.jpg'

# 3. Base limpa de futebol (campo e jogada)
base_futebol = 'videos/thumbnails/736.jpg'

# Mapeamento de todos os clipes do banco
clips_config = [
    # FATOS & DEBATES (POLÍTICA)
    (1, base_debate_political, 'TOFFOLI SUSPENDE CAMPANHA: DECISÃO URGENTE NO STF!', 'politica'),
    (3, base_debate_studio, 'CURY SOBE 9 PONTOS: EMBARALHA ELEIÇÃO!', 'politica'),
    (4, base_debate_political, 'TOFFOLI CONTROLA REDES: MAIOR DESEQUILÍBRIO!', 'politica'),
    (5, base_debate_studio, '51 MIL PRESOS VOLTAM À CADEIA: CRISE TOTAL!', 'politica'),
    (6, base_debate_political, 'RENAN SANTOS ACUSA TSE: CAÇA ÀS BRUXAS!', 'politica'),
    (104, base_debate_studio, 'MORAES NÃO É O STF: DEBATE SOBRE PODERES!', 'politica'),
    (105, base_debate_political, 'FACHIN CITA GRAVIDADE: AUTORIDADE EM XEQUE!', 'politica'),
    (107, base_debate_studio, 'FACHIN PROMETE MEDIDAS: RESPOSTA IMEDIATA!', 'politica'),

    # FUTEBOL EM CORTES
    (2, base_futebol, 'GOLAÇO DE LAMINE YAMAL! O CAMISA 10 RESOLVE!', 'futebol'),
    (7, base_futebol, 'BERARDI DECIDE TUDO! SASSUOLO VENCE!', 'futebol'),
    (8, base_futebol, 'MESSI SE APOSENTA? A CARTA QUE EMOCIONOU O MUNDO!', 'futebol'),
    (9, base_futebol, 'PALMEIRAS SEM CRIATIVIDADE? JEAN ODDI CRITICA!', 'futebol'),
    (10, base_futebol, 'NEYMAR E MEMPHIS: A AMIZADE QUE PAROU O BRASIL!', 'futebol'),
    (106, base_futebol, 'YURI ALBERTO SALVA O CORINTHIANS: GOLAÇO HISTÓRICO!', 'futebol'),
    (108, base_debate_studio, 'REFORMA TRIBUTÁRIA: IMPACTO GIGANTE NO VAREJO!', 'politica'),
]

for clip_id, base_img, title, niche in clips_config:
    target_path = f'videos/thumbnails/{clip_id}.jpg'
    if os.path.exists(base_img):
        shutil.copyfile(base_img, target_path)
        _apply_youtube_thumbnail_graphics(target_path, title, niche=niche)
        print(f"Capa do clipe #{clip_id} ({niche}) gerada com sucesso: {target_path}")

print("\n--- TODAS AS CAPAS FORAM ATUALIZADAS COM SUCESSO! ---")
