# ADR-0004 — Todo caminho de IA nasce com cascata Anthropic → Groq

**Status:** Aceita · **Data:** 27/07/2026 (registrada como ADR em 25/08/2026, revisada em 30/09/2026)

## Contexto

`ANTHROPIC_API_KEY` fica vazia na operação normal; quem roda em produção é o fallback Groq.
`selector.py` já tinha essa cascata, `metadata_generator.py` não: falhava sempre e caía no título
bruto do vídeo original, produzindo três clips com título idêntico por vídeo — parecia vídeo
duplicado na fila de aprovação (`CLAUDE.md`, "Vídeos duplicados na fila").

## Decisão

Qualquer chamada de modelo no pipeline segue a ordem **Anthropic → Groq → fallback determinístico**,
e o fallback determinístico só executa quando as duas APIs falham. Nenhum novo caminho de IA entra
sem os três degraus. A implementação está duplicada entre `selector.py` e `metadata_generator.py`;
unificá-la em um módulo único (`ai_client.py`) é uma refatoração desejada, ainda não feita.

## Consequências

- Ao ler `selector.py`/`metadata_generator.py`, o ramo Anthropic é o que **não** executa em produção.
- Ids de modelo e ordem de fallback devem viver em um lugar só (constantes de config), não em cada módulo.
- Testes de cada estágio de IA precisam cobrir os três degraus, não só o cliente injetado.
- Mudanças de default de provider (por exemplo Groq como primeiro degrau) não podem remover a cascata.
