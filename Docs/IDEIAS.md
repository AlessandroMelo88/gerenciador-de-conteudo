# Ideias para avaliar depois

Coisas legais que **não são necessárias agora**. Nada aqui está decidido nem priorizado. Para
promover uma ideia: abrir uma tarefa com necessidade e critério de sucesso, e tirá-la daqui.

## Origem: vídeo "Edit Labs AI" (26/09/2026)

Síntese em [`estudos/RETENCAO-CORTES-EDIT-LABS.md`](estudos/RETENCAO-CORTES-EDIT-LABS.md).

### Seleção (prompt)

- **Relógio de retenção no prompt:** âncora na primeira frase, proposta em ~3 s, primeiro valor em
  ~8 s, novidade a cada 3–8 s. Tempos vêm de outro canal e não foram validados aqui; pode conflitar
  com o gancho de 0–5 s da política e reduzir a quantidade de cortes. Só vale com A/B em clipes reais.
- **Bons sinais** (número com escala, contradição, causalidade, antes/depois, confissão) e **score com
  piso crítico** (média boa não compensa falha em clareza/payoff).
- **Perfis de retórica** por tipo (resposta rápida, contrarian, dinheiro, história, humor,
  transformação), cada um com estrutura e relógio próprios. Caberia em `selection_short_prompt` no banco.
- **Relatório de métricas por clipe** (latências de proposta e primeiro valor) para teste A/B.

### Vídeo

- **Legendas por unidade de sentido:** 2–6 palavras, até 2 linhas, 0,8–2,2 s (mínimo 0,55 s), destaque
  de 1–3 palavras. Zona segura 1080×1920: 90 px esq., 170 px dir., 160 px topo, 310 px base.
- **Enquadramento pelo falante** (correlação boca × áudio, nunca o maior rosto, nunca dividir a tela).
- **Remoção de pausa com critério:** >550 ms é candidato; 250–550 ms só por motivo editorial.
- **Abertura sem lixo** (sem fade-in, logo longo, frame vazio, texto abstrato) e **punch-in** 1,05–1,15
  por ≥1,2 s em número/confissão/reação.
- **Áudio:** voz em ~-14 LUFS, pico verdadeiro máximo -1 dB.

### Produto

- **B-roll e motion com IA (Higgsfield):** crédito autorizado antes, com custo informado; imagem
  aprovada não autoriza vídeo; sem rosto real gerado; rótulo de IA na plataforma. Custa dinheiro e a
  regra global restringe APIs GPT a imagem e tradução.
- **Portas de aprovação humana por etapa** (cortar → vertical → motion → B-roll → render). Hoje só
  aprovamos ou rejeitamos o clipe pronto na fila.
- **Documento de estilo por canal** a partir de vídeos de referência, atualizado com erros e acertos.

## Origem: Benchmark PlaySquad (PlaySquad.com) — 29/09/2026

Síntese técnica detalhada em [`estudos/BENCHMARK-PLAYSQUAD.md`](estudos/BENCHMARK-PLAYSQUAD.md) e roadmap acionável em [`TODO-PLAYSQUAD.md`](TODO-PLAYSQUAD.md).

### Legendas e Tipografia Cinética
- **13 Presets Estilizados:** Hormozi (fundo neon na palavra ativa, peso 900), Karaokê contínuo via wipe de cor, Word-by-Word com slide vertical, Word Flash (1 palavra gigante no ritmo), Glitch cyberpunk com aberração cromática, Shake com micro-rotação em momentos de impacto, Pop-in com bounce elástico, Typewriter com cursor e Box sólido estilo sticker adesivo.
- **Configuração de Legendas por Canal:** Suporte a seleção de fonte, cores (texto e highlight), número máximo de linhas (1 ou 2) e densidade de palavras por bloco (3 a 5 palavras).

### Enquadramento e Ritmo
- **Layouts de Reframe 9:16:** Modo `split` para podcasts (duas metades horizontais para oradores simultâneos), modo `react` (gameplay/vídeo em cima e facecam embaixo) e `single` com pan suave.
- **Modos de Foco:** Active speaker detection (movimento de lábios sincronizado com áudio) e detecção de saliência visual.
- **Decupagem de Silêncio com 3 Presets:** Suave (`padding: 120ms`, `min_silence: 500ms`), Padrão (`padding: 80ms`, `min_silence: 250ms`) e Agressiva (`padding: 40ms`, `min_silence: 150ms`). Algoritmo com união de intervalos (evita picotar falas próximas).

### Áudio e Inteligência
- **Kokoro TTS (82M params):** Execução 100% local em CPU/GPU (20x tempo real) para voiceover e narração sem custo de API externa.
- **Speech Tags:** Suporte a tags expressivas (`[happy]`, `[whispering]`, `[shouting]`, `[laughing]`, `[break]`).
- **Music Kit Generator:** Trilha sonora por gênero/humor com ducking dinâmico sob a voz (-14 dB).
- **Monitor Outlier:** Detecção de vídeos de canais concorrentes com multiplicadores 3x–10x acima da média histórica.
- **Thumb Analyzer com Hook Score:** Predição de CTR avaliando contraste, legibilidade mobile e expressão facial.
- **Editor Local-First com IndexedDB:** Cache de vídeo no navegador para abertura de cortes em 0ms.

