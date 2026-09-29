# Retenção em cortes — lições do vídeo "Edit Labs AI"

**Fonte:** vídeo do canal Paul Labs (`youtube.com/watch?v=DS5mYfDTdTw`, 26/09/2026) e o repositório
`github.com/paullabs/edit-labs-ai` (plugin de Claude Code que transforma podcast em cortes verticais).
A descrição do vídeo só traz capítulos e links; o conteúdo útil está nas skills `corte-viral` e
`motion-vox` do repositório. Este texto é uma síntese própria, não cópia.

## O que o vídeo faz

Fluxo em sete etapas, com **decisão humana em cada porta**: baixar → achar momentos (`MOMENTOS.md`)
→ cortar e aprovar → vertical → motion design → B-roll → render e verificação. Regra central:
*a aprovação humana vale mais que o parecer do agente*.

## Incorporado (só o necessário)

`clip-processor/src/selector.py` → `RETENTION_SHORTFORM_RULES`, nos prompts de **formato curto**
(o longo não recebe). Cobre só lacunas que os prompts não tinham:

- rejeitar início que depende de contexto anterior ("como eu falei", pronome sem referente);
- rejeitar trecho cujo assunto central não se entende sem o resto do vídeo;
- pergunta/tensão aberta no começo precisa ser respondida dentro do trecho;
- suspense genérico e opinião sem razão reprovam;
- não preencher cota (zero cortes é válido).

Ficou de fora de propósito: tempos-alvo (3 s, 8 s), cadência de beats, bons sinais e pesos de score,
porque não foram validados no nosso conteúdo e custam tokens no Groq gratuito. Tudo isso, mais
legendas, enquadramento, áudio e B-roll, está em [`Docs/IDEIAS.md`](../IDEIAS.md).

## Dicas do vídeo para o operador

- Ensine o Claude com **referências de vídeos que você admira** e peça uma **documentação de estilo**;
  a partir daí, atualize a skill com seus erros e acertos a cada rodada (capítulos 12:35–16:21).
- Corte primeiro pelo **potencial**; quem decide publicar é o humano.
- Mostre o custo (créditos) antes de gerar qualquer asset.
