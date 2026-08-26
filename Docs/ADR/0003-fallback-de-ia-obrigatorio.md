# ADR-0003 — Todo caminho de IA nasce com cascata Anthropic → Groq

**Status:** aceito · **Data:** 27/07/2026 (registrado como ADR em 25/08/2026)

## Contexto

`ANTHROPIC_API_KEY` fica vazia na operação normal; quem roda em produção é o fallback Groq.
`selector.py` já tinha essa cascata, `metadata_generator.py` não: falhava sempre e caía no título
bruto do vídeo original, produzindo três clips com título idêntico por vídeo — parecia vídeo
duplicado na fila de aprovação (`CLAUDE.md`, "Vídeos duplicados na fila").

## Decisão

Qualquer chamada de modelo no pipeline segue a ordem **Anthropic → Groq → fallback determinístico**,
e o fallback determinístico só executa quando as duas APIs falham. Nenhum novo caminho de IA entra
sem os três degraus. A implementação atual está duplicada entre `selector.py` e
`metadata_generator.py`; unificá-la em um `ai_client.py` é o item 2 (Alta) de `TODO-REFATORACAO.md`.

## Consequências

- Ao ler `selector.py`/`metadata_generator.py`, o ramo Anthropic é o que **não** executa em produção.
- Ids de modelo e ordem de fallback devem viver em um lugar só (constantes de config), não em cada módulo.
- Testes de cada estágio de IA precisam cobrir os três degraus, não só o cliente injetado.
