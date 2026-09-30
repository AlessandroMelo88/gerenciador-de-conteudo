# TODO: Inovações e Ideias Inspiradas no PlaySquad (PlaySquad.com)

Documento completo de tarefas, especificações técnicas, regras editoriais e dicas de arquitetura extraídas a partir da engenharia reversa exaustiva e testes práticos realizados na plataforma **PlaySquad** (`https://playsquad.com/`) em 29/09/2026.

As tarefas estão divididas por subsistema do nosso ecossistema (`clip-processor`, `painel`, `pipeline`, `banco de dados` e `prompts`), priorizadas de acordo com o impacto na retenção, viralidade dos cortes e produtividade do operador.

---

## Mapeamento Completo de Ferramentas do PlaySquad vs Nosso Sistema

| Ferramenta PlaySquad | Função Principal | Equivalente no Nosso Sistema | Status / Ação Necessária |
|---|---|---|---|
| **Clips AI** | Geração automática de cortes a partir de URLs do YouTube | `selector.py` + `video_processor.py` | Evoluir com layouts (`split`, `react`) e foco facial |
| **Video Reframe** | Conversão de 16:9 para 9:16 com detecção de orador ativo | `media_composer.py` | Implementar `split` e rastreamento de orador ativo |
| **Legendas Cinéticas** | 13 estilos animados palavra por palavra | `render_sonnet55_shorts.py` | Generalizar os 13 estilos em filtros FFmpeg/ASS |
| **Video Editor (Web NLE)** | Timeline multi-pistas no navegador com decupagem | `ChannelTemplateModal` / Painel | Evoluir para timeline com `IndexedDB` local-first |
| **Decupagem de Silêncio** | VAD com 3 perfis (`suave`, `padrao`, `agressiva`) | Não possui corte de pausas | **Novo módulo:** `SilenceDecoupler` no daemon |
| **Audio Lab** | TTS e clonagem com Kokoro, Fish Audio e Speech Tags | Apenas transcrição Whisper | **Novo módulo:** narração e voiceover local |
| **Audio Sync** | Alinhamento temporal texto-áudio e extração de stems | `transcriber.py` | Sincronizar timestamps em nível de fonema/palavra |
| **Music Kit Generator** | Trilhas automáticas por gênero e humor com ducking | Áudio dinâmico no `video_quality.py` | Adicionar ducking com `sidechaincompress` no FFmpeg |
| **Outlier Detector** | Rastreio de vídeos 3x–10x acima da média em concorrentes | Não possui | **Novo módulo:** monitor de concorrência no painel |
| **Trend Scanner** | Varredura de tópicos em 5 verticais do Google | `rss_poller.py` | Expandir para Google Trends e YouTube Search |
| **Viral Finder** | Radar de vídeos em alta com filtro de período e score | Não possui | Filtro inteligente de pautas virais para o operador |
| **Thumb Analyzer** | Predição de CTR e cálculo de Hook Score (0–100) | Geração estática de capa | Diagnóstico de contraste, legibilidade e expressão |
| **Script Generator** | Wizard de roteiro (gancho 3s, storytelling, loop) | Prompts no `prompts/` | Gerador estruturado de roteiros longos e curtos |
| **Chapter Forge** | Geração automática de capítulos para o YouTube | Não possui | Geração de timestamps formatados para a descrição |
| **Prompt Generator (VEO 3)**| Prompts visuais sincronizados com blocos de 8s de áudio| Não possui | Suporte a B-roll de IA sincronizado |
| **Radar Viral (TikTok Shop)**| Mapeamento de produtos em alta e criadores de topo | `SISTEMA-AFILIADOS.md` | Cruzar produtos afiliados com formatos virais |

---

## 1. Engine de Legendas Cinéticas (FFmpeg / ASS / Canvas)

- [ ] **TODO-PS-01: Implementar os 13 Estilos de Legenda no `clip-processor` (`media_composer.py` / `video_processor.py`)**
  - [ ] **1. Hormozi (`hormozi`):** Caixa alta obrigatória (`UPPERCASE`), fonte ultra-bold (Montserrat Black / Anton peso 900), caixa de fundo com cor de destaque (`#37FF00` verde elétrico ou `#FFE135` amarelo neon), texto preto sobre destaque e branco no restante, pulso elástico de escala `1.06`.
  - [ ] **2. Word-by-Word (`word_by_word`):** Revelação sequencial palavra por palavra com transição suave de opacidade e slide-up de 4px no eixo Y.
  - [ ] **3. Word Flash (`word_flash`):** Exibição central de uma única palavra gigante por vez, pulsando no ritmo exato do áudio (`opacity: 0.2 -> 1 -> 0.2`).
  - [ ] **4. Karaokê (`karaoke`):** Efeito contínuo de preenchimento de cor via wipe temporal (`\k` no ASS ou `clipPath: inset` no Canvas) conforme a voz avança nas sílabas.
  - [ ] **5. Palavras-Chave (`keyword_color`):** O seletor de IA identifica termos de alto impacto/entusiasmo e aplica cor de destaque isolada com pop de escala `1.15`.
  - [ ] **6. Máquina de Escrever (`typewriter`):** Digitação caractere a caractere com cursor vertical piscante `|`.
  - [ ] **7. Box Sólido (`bg_box`):** Pílula retangular sólida com cantos arredondados atrás de cada linha de texto estilo sticker adesivo.
  - [ ] **8. Shake / Vibração (`shake`):** Micro-deslocamento nos eixos X e rotação (`x: [-1.5, 1.5], rotate: [-1, 1]`) em frases de impacto ou volume elevado.
  - [ ] **9. Pop In (`pop_in`):** Efeito bounce com interpolação elástica cúbica (`scale: [0.4, 1.15, 1]`) a cada nova frase falada.
  - [ ] **10. Glitch Cyberpunk (`glitch`):** Aberração cromática dupla estéreo (`textShadow: 1.5px vermelho, -1.5px azul`) com jitter horizontal rápido.
  - [ ] **11. Cor Dividida (`split_color`):** Divide a sentença em 50% cor base (branco) e 50% cor de destaque (amarelo/ciano).
  - [ ] **12. Netflix / Documentário (`netflix`):** Tarja escura translúcida `rgba(20,20,24,0.85)` com tipografia clean peso 500 para temas sérios.
  - [ ] **13. Minimalista (`minimal`):** Tipografia limpa sem contornos, com sombra suave de 2px.

- [ ] **TODO-PS-02: Parâmetros Configuráveis de Legenda no Banco e Painel**
  - [ ] Adicionar campos na tabela `destination_channels` ou `channel_templates`:
    - `caption_style` (enum dos 13 estilos)
    - `caption_position` (`center-bottom`, `center`, `top`)
    - `caption_font` (Anton, Montserrat, Roboto, Archivo Black)
    - `caption_text_color` (padrão `#FFFFFF`)
    - `caption_highlight_color` (padrão `#FFE135` ou `#37FF00`)
    - `caption_max_lines` (1 ou 2)
    - `caption_max_words_per_block` (3 a 5 palavras por bloco)

---

## 2. Enquadramento e Reframe 9:16 Inteligente

- [ ] **TODO-PS-03: Layouts de Enquadramento 9:16 no `clip-processor`**
  - [ ] **Layout `split` (Bipartido):** Para vídeos com 2 participantes (podcasts, entrevistas, debates). O frame 9:16 é dividido horizontalmente em duas metades: topo enquadra o orador A e base enquadra o orador B.
  - [ ] **Layout `react` (Game/Streamer/React):** O conteúdo da tela ocupa os 70% superiores e a webcam do criador ocupa os 30% inferiores ou box flutuante.
  - [ ] **Layout `single` (Dynamic Pan & Crop):** Rastreia o orador ativo com interpolação suave de pan no eixo X, sem cortes bruscos.
  - [ ] **Layout `centro` (Estático):** Corte fixo centralizado com background desfocado (blur), já existente no nosso projeto como padrão.
  - [ ] **Layout `auto`:** Alternância dinâmica de layout dependendo da quantidade de rostos detectados em cena.

- [ ] **TODO-PS-04: Modos de Foco Inteligente com OpenCV / MediaPipe**
  - [ ] **Modo `speaker` (Active Speaker):** Correlaciona movimento labial com energia do áudio para identificar quem está falando no momento e focar a câmera na pessoa certa.
  - [ ] **Modo `salient`:** Rastreia pontos de maior saliência visual e movimento em cenas sem orador visível (gameplay, tutoriais, screencasts).
  - [ ] **Modo `center`:** Foco estático no terço central.

---

## 3. Decupagem de Silêncio e Edição de Ritmo

- [ ] **TODO-PS-05: Módulo de Decupagem Inteligente com 3 Perfis Editoriais**
  - [ ] Criar classe `SilenceDecoupler` no `clip-processor` (com `pydub`, `librosa` ou `webrtcvad` / `silero-vad`):
    - **Perfil Suave (`suave`):** Mantém respiros naturais (`padding_ms: 120`, `min_silence_ms: 500`).
    - **Perfil Padrão (`padrao`):** Corte equilibrado (`padding_ms: 80`, `min_silence_ms: 250`).
    - **Perfil Agressivo (`agressiva`):** Ritmo frenético TikTok/Shorts (`padding_ms: 40`, `min_silence_ms: 150`).
  - [ ] Adicionar flag `--silence-cut [suave|padrao|agressiva|off]` no pipeline de corte de shorts.
  - [ ] Implementar a união de intervalos (merge speech intervals) para evitar picotar falas contínuas com micro-pausas.

---

## 4. Audio Lab & Síntese de Voz Expressiva

- [ ] **TODO-PS-06: Integração do Kokoro TTS no `clip-processor` / `painel`**
  - [ ] Adicionar worker para `kokoro-onnx` ou `kokoro` Python:
    - Execução 100% local, em CPU ou GPU, a mais de 20x tempo real.
    - Custo zero de API e sem dependência de chaves externas.
    - Uso para narração de roteiros, intros automáticas e voiceovers de cortes informativos.
- [ ] **TODO-PS-07: Parser e Renderizador de Speech Tags (`[tag]`)**
  - [ ] Suportar tags expressivas no gerador de áudio e roteiro:
    - Emoções: `[happy]`, `[sad]`, `[angry]`, `[excited]`, `[calm]`, `[sarcastic]`
    - Tom: `[whispering]`, `[soft tone]`, `[shouting]`, `[emphasis]`
    - Efeitos: `[laughing]`, `[sighing]`, `[clear throat]`
    - Pausas: `[break]`, `[long-break]`
- [ ] **TODO-PS-08: Gerador de Music Kits com Ducking Automático**
  - [ ] Biblioteca de trilhas classificadas por Gênero (`lo-fi`, `epic`, `corporate`, `cinematic`, `ambient`) e Mood (`happy`, `sad`, `energetic`, `dramatic`).
  - [ ] Aplicação de filtro FFmpeg `sidechaincompress` (audio ducking): a música de fundo abaixa automaticamente em -12 dB a -18 dB sempre que houver voz falada na trilha principal.

---

## 5. Radar Viral, Monitor Outlier e Inteligência

- [ ] **TODO-PS-09: Módulo "Monitor Outlier" de Canais Concorrentes**
  - [ ] Criar comando/serviço no painel para calcular a mediana histórica de visualizações dos canais cadastrados.
  - [ ] Identificar vídeos **Outliers** com multiplicadores de desempenho:
    - Tag `3x acima da média`, `5x acima da média`, `10x viral breakout`.
    - Métricas rastreadas: Views, Likes, Comentários, Taxa de Engajamento (%) e Views Per Day (velocidade de tração).
  - [ ] Disparar alerta via Telegram para a equipe quando um concorrente tiver um vídeo com multiplicador >3.0x nas primeiras 24 horas.

- [ ] **TODO-PS-10: Radar "Viral Finder" por Palavra-Chave**
  - [ ] Buscar vídeos em alta no YouTube/TikTok por nicho com filtros de data (última hora, hoje, 3 dias, 7 dias, 30 dias) e visualizações mínimas.
  - [ ] Cálculo de **Score Viral** baseado na aceleração de visualizações por hora relativa ao tamanho do canal.

---

## 6. Editor Não-Linear e UX no Painel Web

- [ ] **TODO-PS-11: Arquitetura Local-First com IndexedDB no Painel**
  - [ ] Criar store IndexedDB (`clips-editor-store`) no frontend React/Inertia para persistência de rascunhos de edição sem salvar rascunhos parciais no banco de dados do servidor.
  - [ ] Cache local de áudio e frames para preview instantâneo na timeline.

- [ ] **TODO-PS-12: Botão "Editar Corte na Timeline"**
  - [ ] Na listagem de clipes gerados (`ActiveWindowTable` / `ClipQueueTabs`), adicionar botão rápido para abrir o corte em uma interface de ajuste fino (arrastar ponto de início/fim, trocar estilo de legenda, alternar cor de destaque).

- [ ] **TODO-PS-13: Edição Bidirecional Texto-Vídeo na Transcrição**
  - [ ] Ao corrigir uma palavra na transcrição na tela do painel, recalcular automaticamente os timestamps das palavras sem quebrar a sincronia labial e atualizar o arquivo de legendas `.ass`.

---

## 7. Thumbnail Analyzer & Hook Score

- [ ] **TODO-PS-14: Avaliador de Miniaturas com Hook Score (0–100)**
  - [ ] Módulo que analisa a imagem da thumbnail antes da publicação:
    - **Detecção de Expressão e Rosto:** Identifica se há rosto humano, tamanho do rosto na imagem e expressão de curiosidade/surpresa.
    - **Contraste e Cores:** Mede a saturação e o contraste em relação ao fundo escuro do YouTube/TikTok.
    - **Legibilidade Mobile:** Simula a visualização da miniatura reduzida para 120x68 px (tamanho típico em feed móvel) e verifica se o texto permanece legível.
    - **Hook Score:** Nota composta de 0 a 100 com sugestões pontuais de melhoria.

---

## 8. Gerador de Roteiros (Script Generator com Wizard)

- [ ] **TODO-PS-15: Wizard de Criação de Roteiros de 4 Passos no Painel**
  - [ ] **Passo 1 (Inspiração):** Inserção de URLs de vídeos de referência e canais de sucesso.
  - [ ] **Passo 2 (Premissa & Nicho):** Definição do tema central, nicho e sinopse do conteúdo.
  - [ ] **Passo 3 (Estilo Narrativo):** Seleção de estilo (Storytelling, Explicativo, Provocativo/Polêmico, Direto ao Ponto, Humor).
  - [ ] **Passo 4 (Elementos Obrigatórios):**
    - Gancho obrigatório nos primeiros 3 segundos (`[HOOK]`).
    - Primeiro payoff de valor antes dos 10 segundos (`[VALUE]`).
    - Quebras de padrão visuais e auditivas a cada 5 a 8 segundos.
    - Loop infinito perfeito no final do Short para induzir segunda reprodução automática.
    - Call to Action sutil direcionada ao link de afiliado (`/o/{slug}`).

---

## 9. Chapter Forge (Capítulos & Timestamps Automáticos)

- [ ] **TODO-PS-16: Gerador Automático de Capítulos para Vídeos Longos**
  - [ ] Analisar a transcrição completa do vídeo longo e gerar os blocos de capítulos no formato padrão do YouTube:
    ```
    00:00 - Introdução: O Novo Modelo que Surpreendeu o Mercado
    01:24 - Benchmarks: Comparação Direta com Modelos de Topo
    04:12 - Testes Práticos de Velocidade e Consumo de Tokens
    07:45 - Conclusão e Veredito Final
    ```
  - [ ] Botão de "Copiar Capítulos" com 1 clique para colar diretamente na descrição do vídeo publicado.

---

## 10. Prompt Generator para B-Roll de IA (VEO 3 / Kling / Runway)

- [ ] **TODO-PS-17: Gerador de Prompts Visuais Sincronizados com Blocos de Áudio**
  - [ ] Dividir o roteiro/transcrição em blocos de 8 segundos (`blockDurationSeconds: 8`).
  - [ ] Gerar prompts cinematográficos prontos para inserção em ferramentas de geração de vídeo por IA (Google VEO 3, Kling AI, Runway Gen-3).
  - [ ] Prompts incluem iluminação, ângulo de câmera, estilo (foto-realista, cyberpunk, editorial) e ação descrita em inglês.

---

## 11. Radar de Afiliados & Produtos em Alta

- [ ] **TODO-PS-18: Cruzamento de Vídeos Virais com Produtos Afiliados**
  - [ ] Identificar temas em alta no Radar Viral e associar automaticamente com as ofertas de afiliado cadastradas em [`Docs/sistema/SISTEMA-AFILIADOS.md`](sistema/SISTEMA-AFILIADOS.md).
  - [ ] Sugerir inserção de menção à oferta relevante em vídeos cujo tema possua alta correlação semântica (ex.: vídeo sobre IA e programação sugerir ferramenta ou curso com link `/o/{slug}`).

---

## 12. Regras e Dicas Críticas de Engenharia Extraídas do Benchmark

1. **IdempotencyKey Obrigatório:** Toda requisição de corte ou geração de mídia pesada deve enviar um UUID client-side (`idempotencyKey`), evitando que duplo-clique do operador gere dois renders concorrentes e desperdice CPU/GPU.
2. **Estimativa Prévia de Recursos (`/estimate`):** O frontend deve calcular e exibir a duração estimada e resolução antes de disparar o job no backend.
3. **Resolução de Análise de 360p:** A detecção visual de rostos e saliência deve rodar em frames reduzidos para 360p (muito mais rápido e consome 1/9 da memória), reservando o 1080p apenas para o render final via FFmpeg com aceleração por hardware (`h264_videotoolbox` no Mac / `h264_nvenc` no Linux).
4. **Margens de Respiro na Decupagem:** Nunca cortar exatamente na borda do silêncio; sempre preservar 40 a 120 ms de respiro (`paddingMs`) antes e depois da fala para manter a naturalidade e evitar o corte de consoantes oclusivas (p, b, t, d, k, g).
5. **Ducking Dinâmico com Sidechain:** Sempre que adicionar trilha de fundo musical, utilizar o compressor sidechain do FFmpeg ancorado na trilha de voz com atenuação de -14 dB para garantir 100% de clareza auditiva na narração.

---

## Matriz de Priorização Recomendada

| Prioridade | Tarefa | Impacto | Complexidade |
|---|---|---|---|
| **P0 (Imediata)** | **TODO-PS-01:** 13 Estilos de Legenda no FFmpeg (Hormozi, Karaokê, Word-by-Word) | Altíssimo (retenção direta nos Shorts) | Média |
| **P0 (Imediata)** | **TODO-PS-05:** Decupagem Inteligente de Silêncio (`padrao` e `agressiva`) | Altíssimo (elimina tempos mortos) | Média |
| **P1 (Curto Prazo)**| **TODO-PS-03:** Layouts de Reframe 9:16 (`split` para podcast 2 pessoas) | Alto (expande para podcasts) | Média |
| **P1 (Curto Prazo)**| **TODO-PS-09:** Monitor Outlier no Painel (alerta de concorrentes via Telegram) | Alto (inteligência de pauta) | Baixa |
| **P1 (Curto Prazo)**| **TODO-PS-16:** Chapter Forge (Capítulos automáticos na descrição) | Alto (SEO e retenção no YouTube) | Baixa |
| **P2 (Médio Prazo)**| **TODO-PS-06:** Kokoro TTS local (82M params) para narração sem custo | Alto (autonomia total sem API paga) | Média |
| **P2 (Médio Prazo)**| **TODO-PS-14:** Thumbnail Analyzer com Hook Score no Painel | Médio/Alto (aumento de CTR) | Média |
| **P2 (Médio Prazo)**| **TODO-PS-15:** Wizard de Roteiro com gancho de 3s e loop infinito | Alto (produção de novos conteúdos) | Média |
| **P3 (Longo Prazo)**| **TODO-PS-11 / PS-12:** Timeline Multi-Pistas com `IndexedDB` local-first | Médio (autonomia do operador) | Alta |
