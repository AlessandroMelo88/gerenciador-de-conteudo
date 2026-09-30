# Benchmark e Engenharia Reversa: PlaySquad (playsquad.com)

**Data do teste:** 29 de setembro de 2026  
**Ambiente de teste:** Web Browser Subagent (Chrome DevTools Protocol) + Análise de Bundles Vite/React + Mapeamento de API REST (`https://api.playsquad.com/api/v1`)  
**Vídeos testados:**
- `https://www.youtube.com/watch?v=-cBJgAaWimo` (Claude Sonnet 5.5 vs GPT-6, vídeo do projeto com 6 shorts gerados)
- `https://www.youtube.com/watch?v=1uLEHYzUGRs` (Vídeo de economia/política do pipeline do projeto)

---

## 1. Resumo Executivo

O **PlaySquad** (`playsquad.com`) é uma plataforma all-in-one para criadores de conteúdo que combina:
1. **Clips AI:** Extração automatizada de cortes virais a partir de URLs do YouTube ou upload direto, com auto-reframe (9:16, 1:1, 4:5, 16:9), detecção de orador ativo e legendas queimadas dinâmicas.
2. **Video Editor (Web NLE):** Editor não-linear completo no navegador renderizado via HTML5 Canvas/Konva, com timeline multi-pistas (vídeo, áudio, legendas, imagens, música), armazenamento local de sessões em `IndexedDB` (`tubeonix-editor`) para latência zero, e **decupagem automática de silêncio via Web Worker VAD**.
3. **Engine de Legendas Cinéticas:** 13 presets visuais de legenda com sincronização temporal palavra por palavra (incluindo estilos icônicos como *Alex Hormozi*, *Karaokê*, *Word by Word*, *Glitch* e *Shake*).
4. **Audio Lab:** Síntese de voz com múltiplos provedores (Kokoro TTS ultra-rápido, Fish Audio para clonagem de voz zero-shot e High-End Studio TTS), diálogos multi-voz e tags de emoção/tom/efeitos (`[whispering]`, `[laughing]`, `[excited]`, `[break]`).
5. **Ferramentas de Inteligência e Radar:** *Trend Scanner* (Google Trends em 5 verticais: Web, YouTube, Images, News, Shopping), *Outlier Detector* (vídeos que rompem a média do canal concorrente por 3x–10x), *Viral Finder* e *Thumb Analyzer* com *Hook Score*.

---

## 2. Teste Prático com Vídeos do Projeto

### 2.1. Comportamento do Fluxo Público
Ao submeter o vídeo do projeto `https://www.youtube.com/watch?v=-cBJgAaWimo` no formulário público da landing page (`#url-input`):
1. **Validação da URL:** O cliente valida a sintaxe do YouTube (`youtu.be` ou `watch?v=`).
2. **Redirecionamento com Preservação de Contexto:** A aplicação direciona o usuário para:
   ```
   https://playsquad.com/register?url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3D-cBJgAaWimo
   ```
3. **Onboarding / Registro:**
   - Solicita: Nome, Email, Senha, Nome do Workspace (arquitetura multi-tenant) e confirmação de idade (16+ anos).
   - Oferece autenticação via Google OAuth.
4. **Resgate no Dashboard:** Após login/cadastro, o parâmetro `url` é resgatado via router e pré-carrega o formulário do **Clips AI** (`/dashboard/clips-ai`).

---

## 3. Engenharia Reversa do Clips AI

### 3.1. Schema Completo do Payload (`POST /clips-ai/jobs`)
```typescript
interface ClipsAiJobRequest {
  // Origem da Mídia
  videoUrl?: string;                   // URL do YouTube / link externo
  storageKey?: string;                 // Chave no bucket S3 se upload direto
  videoFileName: string;
  videoFileSize: number;
  videoMimeType: string;
  _estimatedDurationMinutes?: number;
  idempotencyKey: string;              // UUID anti-duplicação

  // Parâmetros Editoriais & IA
  profile: string;                     // "highlight", "podcast", "educacional", "humor"
  language: "pt" | "en" | "es";        // Idioma da transcrição Whisper
  maxClips: number;                    // Quantidade máxima de cortes desejada
  channelName?: string;                // Contexto de nicho/estilo do canal
  customContext?: string;              // Instruções customizadas do operador (prompt)
  analysisResolution: 360 | 720 | 1080;// Resolução para visão computacional

  // Reenquadramento Vertical (9:16)
  reframeEnabled: boolean;
  reframeAspect: "9:16" | "1:1" | "4:5" | "16:9";
  reframeLayout: "auto" | "single" | "centro" | "split" | "react";
  reframeFocusMode: "auto" | "speaker" | "salient" | "center";

  // Estilo e Posicionamento de Legendas
  reframeSkipSubs: boolean;
  reframeCaptionStyle: CaptionStyleId;
  reframeCaptionPosition: "center-bottom" | "center" | "top";
  reframeFont: string;                 // Ex: "Montserrat", "Anton", "Archivo Black"
  reframeTextColor: string;           // Hex (#FFFFFF)
  reframeHighlightColor: string;       // Hex (#FFE135, #37FF00, etc.)
  reframeMaxLines: number;             // 1 ou 2 linhas
  reframeMaxWordsPerBlock: number;     // 3 a 5 palavras por bloco
}
```

### 3.2. Layouts de Enquadramento 9:16
- **`auto`**: Alterna planos dinamicamente conforme movimentação e quantidade de pessoas em cena.
- **`single`**: Crop 9:16 focado no orador ativo com interpolação suave (pan horizontal).
- **`centro`**: Corte estático no centro do vídeo (ótimo para apresentadores fixos e screencasts).
- **`split` (Dividido)**: Divide a tela vertical em 2 metades (topo e base), enquadrando apresentador e convidado simultaneamente (essencial para podcasts em estúdio).
- **`react`**: Layout no estilo Streamer/Gamer, com o conteúdo principal ocupando 70% e a facecam em Picture-in-Picture ou box inferior dedicado.

### 3.3. Modos de Foco (Detecção Visual)
- **`speaker`**: Rastreamento facial correlacionado com a fala (Active Speaker Detection / lip sync).
- **`salient`**: Mapa de saliência visual (movimento na cena, objetos em destaque, gameplay).
- **`center`**: Foco fixo centralizado.
- **`auto`**: Fusão de orador ativo + saliência.

---

## 4. Estilos de Legenda e Tipografia Cinética (13 Presets)

O PlaySquad renderiza legendas com suporte a pesos pesados (900) e animações personalizadas:

| ID do Estilo | Nome | Cores Padrão | Regra Visual & Animação |
|---|---|---|---|
| **`hormozi`** | Alex Hormozi | Texto branco/preto, Destaque `#37FF00` (verde limão) ou `#FFE135` | Palavra ativa recebe caixa de fundo colorida, `fontWeight: 900`, `UPPERCASE`, pulso de escala `[1, 1.06, 1]`. |
| **`word_by_word`** | Palavra por Palavra | Texto `#FFFFFF`, Destaque `#FFE135` | Revelação sequencial palavra a palavra com transição suave de opacidade e deslocamento vertical (slide-up de 4px). |
| **`word_flash`** | Word Flash | Texto `#FFD60A`, Destaque `#FFFFFF` | Exibe apenas a palavra falada no momento em tamanho gigante no centro, no ritmo exato do áudio. |
| **`karaoke`** | Karaokê | Base opaca 45%, Destaque `#00E5FF` | Efeito wipe contínuo via `clipPath: inset(0 X% 0 0)` preenchendo a frase com a cor ativa. |
| **`keyword_color`** | Palavras-Chave | Texto `#FFFFFF`, Destaque `#FF3B5C` | O modelo identifica palavras de alto impacto/entusiasmo e as colore isoladamente com bounce de escala `1.15`. |
| **`typewriter`** | Máquina de Escrever | Texto `#FFFFFF`, Destaque `#FF570A` | Digitação caractere a caractere com cursor piscante `\|`. |
| **`bg_box`** | Box com Fundo | Texto `#FFFFFF`, Caixa `#FF570A` | Pílula retangular sólida colorida atrás de cada linha, estilo sticker urbano. |
| **`shake`** | Shake / Tremor | Texto `#FFFFFF`, Destaque `#FFD60A` | Micro-vibração nos eixos X e rotação (`x: [-1.5, 1.5], rotate: [-1, 1]`) em momentos de pico de volume/tensão. |
| **`pop_in`** | Pop In | Texto `#FFFFFF` com sombra forte | Efeito mola/bounce com interpolação cúbica elástica `scale: [0.4, 1.15, 1]`. |
| **`glitch`** | Glitch Cyberpunk | Texto com aberração cromática | Dupla sombra offset (`1.5px` vermelho neon e `-1.5px` ciano neon) com jitter horizontal rápido. |
| **`split_color`** | Cor Dividida | Metade branca, metade destaque | Primeira metade da frase em branco e segunda metade na cor de destaque. |
| **`netflix`** | Netflix / Documentário | Texto `#FFFFFF`, Fundo `rgba(20,20,24,0.85)` | Tarja escura translúcida e tipografia limpa, ideal para conteúdos sóbrios. |
| **`minimal`** | Minimalista | Texto `#FFFFFF`, sem borda | Tipografia limpa peso 500 com sombra suave, sem poluição visual. |

---

## 5. Editor de Vídeo & Decupagem Automática de Silêncio

### 5.1. Decupagem Inteligente (Client-Side Web Audio VAD)
O PlaySquad implementou um motor de **Voice Activity Detection** que roda inteiramente no navegador via Web Worker, analisando as amplitudes e frequências do áudio do vídeo localmente:

#### Presets Editoriais de Silêncio:
1. **Suave (`suave`):**
   - *Objetivo:* Mantém os respiros naturais e pausas reflexivas do orador.
   - `paddingMs`: 120 ms
   - `minSilenceMs`: 500 ms
2. **Padrão (`padrao`):**
   - *Objetivo:* Corte equilibrado para podcasts e vídeos educativos.
   - `paddingMs`: 80 ms
   - `minSilenceMs`: 250 ms
3. **Agressiva (`agressiva`):**
   - *Objetivo:* Corta todas as pausas para retenção máxima (formato TikTok/Reels frenético).
   - `paddingMs`: 40 ms
   - `minSilenceMs`: 150 ms

#### Algoritmo de União de Intervalos:
```javascript
function mergeSpeechIntervals(intervals, totalDurationMs, { paddingMs, minSilenceMs }) {
  if (!intervals.length) return [];
  // 1. Aplica margens de respiro (padding)
  const padded = intervals.map(i => ({
    startMs: Math.max(0, i.startMs - paddingMs),
    endMs: Math.min(totalDurationMs, i.endMs + paddingMs)
  })).sort((a, b) => a.startMs - b.startMs);

  // 2. Mescla falas próximas se a pausa entre elas for menor que minSilenceMs
  const merged = [];
  for (const item of padded) {
    const prev = merged[merged.length - 1];
    if (!prev) { merged.push({ ...item }); continue; }
    if (item.startMs - prev.endMs < minSilenceMs) {
      prev.endMs = Math.max(prev.endMs, item.endMs);
    } else {
      merged.push({ ...item });
    }
  }
  return merged.map((range, idx) => ({
    id: `decupage-${idx}`,
    startMs: Math.round(range.startMs),
    endMs: Math.round(range.endMs)
  }));
}
```

### 5.2. Arquitetura Local-First (`IndexedDB`)
O editor utiliza o banco local `tubeonix-editor` com 3 object stores:
- `sessions`: Armazena o estado completo do projeto (tracks, clips, legendas, playhead).
- `assets`: Armazena blobs de vídeos e imagens importadas com prefixo `localasset:`.
- `clipSessions`: Vincula os cortes gerados pelo Clips AI ao editor instantaneamente.
**Vantagem crucial:** O operador clica em "Editar Corte" no Clips AI e o vídeo abre em **0 milissegundos**, sem upload ou download adicional.

---

## 6. Audio Lab & Síntese de Voz

1. **Camadas de Provedores:**
   - **Kokoro TTS (Flash/Lite):** Modelo de 82M parâmetros, open-weights, roda localmente em CPU/GPU a 20x tempo real. Ideal para gerações rápidas e custo zero.
   - **Fish Audio (Prime/Plus):** Clonagem de voz com poucos segundos de referência, suporte a 83 idiomas e controle dinâmico de prosódia.
2. **Sistema de Speech Tags (`[tag]`):**
   Permite inserir instruções expressivas no meio do texto da narração:
   - *Emoções:* `[happy]`, `[angry]`, `[excited]`, `[calm]`, `[nervous]`, `[sarcastic]`, `[curious]`
   - *Tons:* `[whispering]`, `[shouting]`, `[soft tone]`, `[emphasis]`
   - *Sons humanos:* `[laughing]`, `[sighing]`, `[groaning]`, `[clear throat]`
   - *Pausas:* `[break]`, `[long-break]`
3. **Music Kit Generator:**
   - Combinação de **Gênero** (Lo-Fi, Epic, Corporate, Cinematic, Electronic, Ambient) + **Mood** (Happy, Sad, Energetic, Calm, Dramatic, Mysterious) para trilha de fundo automática com ducking de volume.

---

## 7. Ferramentas de Inteligência & Radar de Conteúdo

1. **Monitor Outlier (`/influencer-spy` e `/outlier-detector`):**
   - Compara o desempenho recente de vídeos de canais concorrentes contra a **mediana histórica do canal**.
   - Calcula: Multiplicador Outlier (ex.: `3.8x da média`), Views Per Day (velocidade de tração), Taxa de Engajamento e Retenção média estimada.
2. **Trend Scanner (`/trend-scanner`):**
   - Agendamento de monitoramento (6h, 12h, diário) em 5 verticais do Google.
   - Alertas proativos de palavras-chave em ascensão súbita.
3. **Thumb Analyzer (`/thumb-analyzer`):**
   - Cálculo de **Hook Score (0–100)** para miniaturas.
   - Diagnóstico em 4 pilares: Expressão Facial/Olhar, Contraste de Cores, Legibilidade do Texto em Telas Pequenas de Celular e Curiosidade gerada.

---

## 8. Gerador de Roteiros & Chapter Forge

1. **Script Generator (Wizard de 4 Passos):**
   - Mapeia inspiração de criadores de referência, premissa/tema, estilo narrativo (Storytelling, Explicativo, Provocativo, Humor, Direto ao Ponto) e duração estimada.
   - Estrutura obrigatória: Gancho em 3s (`[HOOK]`), entrega do primeiro valor em 10s (`[VALUE]`), quebras de padrão e fechamento em loop infinito perfeito para Shorts.
2. **Chapter Forge:**
   - Transforma a transcrição de vídeos longos em blocos de capítulos com timestamps formatados (`00:00 - Intro`, `02:15 - Análise...`) com botão de cópia direta para a descrição do YouTube.

---

## 9. Prompt Generator para Vídeos de IA (VEO 3 / Kling / Runway)

- Segmenta o roteiro em blocos de 8 segundos (`blockDurationSeconds: 8`).
- Gera prompts visuais descritivos e cinematográficos sincronizados com cada segmento de áudio, permitindo enriquecer o corte com B-roll gerado por IA com coerência semântica.

---

## 10. Radar de Afiliados & Produtos em Alta

- Mapeia produtos mais vendidos e vídeos de criadores associados a esses produtos.
- Cruza temas em alta com as ofertas de afiliado cadastradas no nosso sistema (`Docs/sistema/SISTEMA-AFILIADOS.md`), sugerindo inserções de ofertas de forma contextual.

---

## 11. Regras e Dicas Críticas de Engenharia Extraídas da Plataforma

1. **Idempotência Client-Side (`idempotencyKey`):** Cada job pesado de renderização envia um UUID único gerado no navegador, prevenindo múltiplos renders e desperdício de processamento caso o operador dê duplo clique.
2. **Estimativa Prévia de Recursos (`/estimate`):** O frontend valida a duração do vídeo e calcula a estimativa de tempo e custo antes de despachar o job para a fila.
3. **Inferência Visual Otimizada em 360p:** A detecção de faces, oradores e saliência roda em baixa resolução (360p), economizando 80% de memória e tempo de CPU/GPU, deixando a alta fidelidade (1080p) apenas para o render final do FFmpeg.
4. **Margens de Respiro na Decupagem:** As margens de costura (`paddingMs: 40-120ms`) são indispensáveis para garantir que o corte de silêncio não mutile consoantes ou torne o áudio artificial.
5. **Ducking Dinâmico com Sidechain:** Ao sobrepor música de fundo, a voz da narração atua como gatilho no compressor sidechain, reduzindo a trilha em -14 dB e mantendo 100% de inteligibilidade vocal.

