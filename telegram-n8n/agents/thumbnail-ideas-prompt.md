# Prompt — Thumbnail Idea Generator (Gerador de Ideias de Thumbnail)

**Modelo recomendado:** Claude Haiku (para ideias) + DALL-E / Midjourney (para gerar)  
**Custo estimado:** ~$0.001 (ideias) + $0.02–0.04 (geração de imagem, se usar)  
**Quando usar:** Após renderizar o clip, antes do upload

---

## Por que thumbnail importa tanto

Thumbnails são responsáveis por **60–80% do CTR** de um vídeo. Mesmo para Shorts
(onde a thumbnail aparece na grade do canal e no YouTube Search), uma imagem forte
faz enorme diferença na quantidade de cliques.

**Padrão dos canais de cortes que crescem:**
- Expressão facial exagerada (surpresa, choque, raiva)
- Texto grande e contrastante (máximo 5 palavras)
- Cores vibrantes (vermelho, amarelo, laranja — evite azul escuro)
- Seta ou destaque visual apontando para o elemento principal
- Fundo contrastante (não deixe o fundo se misturar ao rosto)

---

## System Prompt

```
Você é um especialista em criação de thumbnails virais para YouTube, com foco em
canais de esportes brasileiros.

Você conhece o padrão de thumbnails que geram mais cliques:
- Rosto com expressão exagerada (preferível ao placar ou ao campo)
- Texto em caixa alta, fundo com contraste alto
- Paleta: vermelho (#FF0000), amarelo (#FFD700), laranja (#FF6B00), branco com outline preto
- Fontes: Impact, Bebas Neue, Anton (grossas e impactantes)
- Evitar: muito texto, fundos sem contraste, imagens desfocadas, cores frias

Para Shorts especificamente:
- Proporção 9:16 (vertical)
- Texto deve ser legível em tela pequena (min. 48pt equivalente)
- O elemento principal deve estar no terço superior-central
```

---

## User Prompt (template)

```
Crie 3 conceitos de thumbnail para este clip de futebol:

TÍTULO DO CLIP: {TITULO}
DURAÇÃO: {DURACAO}s
TIPO DE MOMENTO: {TIPO} (gol / polêmica / declaração / confusão / mico)
TIMES ENVOLVIDOS: {TIMES}
DESCRIÇÃO DO MOMENTO: {DESCRICAO_MOMENTO}

Para CADA conceito, especifique:

1. IMAGEM DE FUNDO
   - Qual frame do vídeo usar (ex: "momento da expulsão, 0:21", "reação do técnico após o gol")
   - Alternativa: descreva uma imagem gerada por IA (para DALL-E/Midjourney)

2. TEXTO PRINCIPAL (grande, no topo ou centro)
   - Máximo 4 palavras
   - Em caixa alta
   - Cor recomendada + cor do contorno

3. TEXTO SECUNDÁRIO (menor, opcional)
   - Máximo 3 palavras
   - Posição na imagem

4. ELEMENTOS VISUAIS
   - Emojis ou ícones sugeridos (máximo 2)
   - Bordas, setas, círculos de destaque?
   - Cor de fundo se não usar foto

5. PALETA DE CORES
   - Cor primária: [hex]
   - Cor secundária: [hex]
   - Cor do texto: [hex]

6. PROMPT DALL-E (se quiser gerar via IA)
   - Descrição em inglês para gerar a thumbnail base

Indique qual dos 3 você recomenda e por quê.
```

---

## Exemplos de Output

### Exemplo: Gol espetacular do Vini Jr

```
CONCEITO 1 — Grito do gol (RECOMENDADO)
Imagem: Frame do Vini Jr com os braços abertos comemorando, expressão de êxtase
Texto principal: "GOL HISTÓRICO" (branco com outline preto, topo da imagem)
Texto secundário: "Vini Jr ✨" (amarelo, canto inferior direito)
Elementos: Confete amarelo no fundo, estrelas ao redor da cabeça
Paleta: Fundo dourado #FFD700 | Texto branco #FFFFFF | Outline preto #000000
Prompt DALL-E: "Brazilian soccer player celebrating goal, arms wide open, extreme joy expression, bright stadium lights, confetti falling, cinematic style, vertical portrait orientation"

---

CONCEITO 2 — Reação da torcida
Imagem: Frame da torcida em êxtase, bandeiras, fogos de artifício
Texto principal: "SEM PALAVRAS" (vermelho com outline branco)
Texto secundário: "VINI JR 🔥"
Elementos: Faixa com as cores do Real Madrid no topo
Paleta: Fundo branco #FFFFFF | Texto vermelho #CC0000 | Destaque dourado #FFD700

---

CONCEITO 3 — Comparação dramática
Imagem: Splitscreen — frame da finalização (esquerda) + placar final (direita)
Texto principal: "INACREDITÁVEL" (laranja com outline preto)
Texto secundário: "Champions 2026"
Elementos: Relâmpago separando os dois lados
Paleta: Fundo preto #000000 | Texto laranja #FF6B00 | Destaque branco #FFFFFF

---

RECOMENDAÇÃO: Conceito 1
O rosto em close com expressão extrema sempre supera outros formatos no CTR.
A expressão do Vini Jr comemorando é reconhecível e cria conexão emocional imediata.
```

---

## Ferramentas para Criar as Thumbnails

### Opção 1: Canva (gratuito, mais fácil)
1. Acesse [canva.com](https://canva.com)
2. Crie projeto "YouTube Thumbnail" → mude para 1080×1920 (Shorts)
3. Use o frame extraído pelo pipeline em `/app/videos/thumbnails/`
4. Adicione o texto com as fontes Impact ou Anton

### Opção 2: DALL-E via ChatGPT Plus
1. Acesse [chatgpt.com](https://chatgpt.com) (GPT-4 com imagens)
2. Cole o Prompt DALL-E do conceito escolhido
3. Baixe a imagem e adicione o texto no Canva

### Opção 3: Automatizado via N8N + DALL-E API
Custo: ~$0.04 por thumbnail (OpenAI API)

```json
{
  "url": "https://api.openai.com/v1/images/generations",
  "method": "POST",
  "body": {
    "model": "dall-e-3",
    "prompt": "<PROMPT_DALL-E do conceito escolhido>",
    "n": 1,
    "size": "1024x1792",
    "quality": "standard"
  }
}
```

### Opção 4: Frame automático do pipeline
O pipeline já extrai uma thumbnail em `/app/videos/thumbnails/`. Use essa imagem
como base e adicione texto no Canva. É a opção mais rápida.

---

## Comando Telegram (futuro)

```
/thumbnail 42

Bot responde:
🖼 Ideias de thumbnail para Clip #42:

CONCEITO 1 (recomendado):
Frame: 0:21 (reação do árbitro)
Texto: "VAR ERROU?"
Cor: vermelho + branco
[Prompt DALL-E aqui]
```
