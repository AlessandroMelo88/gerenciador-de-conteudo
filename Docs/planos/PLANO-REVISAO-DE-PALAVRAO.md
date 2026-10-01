# Plano — revisão de palavrão antes de publicar

**Status:** IDEIA · registrada em 01/10/2026, nada implementado. Decisão do dono: não entra agora.
**Origem:** PR #1 do Ricardo (`release/rico`) trazia um filtro que reprova o clip se título, descrição,
tags ou thumbnail tiverem palavrão. Foi recusado: reprovar sozinho é cego ao contexto.

## O problema

Um "porra" isolado não desmonetiza um vídeo; vários palavrões repetidos desmonetizam. Quem sabe
distinguir é uma pessoa lendo o contexto, não uma lista de palavras. Podcast de futebol e política
tem muito palavrão, então um bloqueio automático derrubaria clip bom.

Hoje a `master` **não tem nenhum filtro de palavrão** no pipeline. O prompt só pede à IA que evite.

## O que o dono quer (nas palavras dele)

1. Assistir ao vídeo **dentro da plataforma** (a tela de aprovação) e ver uma **lista com minutagem e
   segundo de cada palavrão**.
2. Ler o contexto de cada ocorrência e **decidir ele mesmo** se aprova.
3. Escolher, por clip, **publicar com palavrão ou sem palavrão**.
4. Quando for "sem palavrão": tirar o som da palavra (bip, silêncio ou animação), **mantendo a palavra
   escrita na legenda** — a legenda, na avaliação do dono, não é o problema.

## Como poderia funcionar (rascunho, a validar)

| Etapa | O que faz | Onde encaixa |
|---|---|---|
| Detectar | Procura palavrão na transcrição com tempo por palavra (Whisper/Groq entregam) e grava `{clip, início_s, fim_s, palavra, contexto}` | transcrição já existente |
| Mostrar | Na aprovação do clip, lista clicável: clicar pula o player para o segundo e mostra a frase em volta; contagem total e densidade (palavrões por minuto) | painel, modal de preview do clip |
| Decidir | Botão por clip: "publicar como está" ou "censurar áudio". Opcional: alerta quando a densidade passa de um limite | painel |
| Censurar | Só nos intervalos marcados: silêncio ou bip no áudio, com ffmpeg, **sem tocar na legenda**. Gera um segundo arquivo; o original fica | `video_processor.py` (já refaz render/legenda) |
| Publicar | Sobe a versão escolhida | `publisher.py` |

**Custo conhecido:** a versão censurada exige reprocessar o áudio do clip (render extra). Por isso a
decisão deve acontecer **antes** do upload, na fila de aprovação, e só os clips marcados "sem
palavrão" pagam o render.

## Perguntas em aberto

- Lista de palavras: fixa no código ou editável no painel (por canal)?
- Limite de densidade para o alerta (ex.: mais de N por minuto)?
- Silêncio, bip ou animação? Bip e animação passam outra mensagem ao espectador; silêncio é o mais seguro.
- Vale por canal destino (futebol aceita mais, política menos) ou global?
- Título, descrição e tags também entram na revisão? (Provavelmente sim, mas é texto: dá para a IA reescrever.)

## Ordem sugerida quando for implementar

1. Só **detectar e mostrar** a lista na aprovação (zero reprocessamento, valor imediato).
2. Depois a **censura de áudio** sob demanda.
3. Por último a regra por canal e o alerta de densidade.

Antes de codar: spec curta em `Docs/specs/` (skill `padroes-projeto`).
