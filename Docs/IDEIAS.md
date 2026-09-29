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
