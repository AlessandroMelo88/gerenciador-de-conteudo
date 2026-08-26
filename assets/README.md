# Biblioteca de assets

Esta pasta é montada no `clip-processor` como `/app/assets`.

```text
assets/
├── channels/
│   └── <slug-do-canal>/
│       ├── intro.jpg
│       ├── intro.mp4
│       ├── encerramento.jpg
│       └── encerramento.mp4
└── audio/
    ├── faixa_completa.wav
    └── faixa_completa.txt   # letra, quando existir
```

Os nomes visuais canônicos são `intro` e `encerramento`, sempre em minúsculas.
Quando os dois formatos existem, o pipeline prefere o vídeo e usa a imagem como
fallback. `intro_2.jpg` é mantido como uma variação opcional e não é escolhido
automaticamente.

Para vídeos `longo`, o pipeline exige os três assets: intro, encerramento e uma
faixa em `audio/`. A música é misturada somente no segmento de encerramento, em
volume baixo, garantindo que um trecho da faixa apareça no fechamento sem cobrir
a fala do conteúdo principal. As faixas são alternadas de forma determinística
pelo id do clip.

Os arquivos de áudio desta pasta foram copiados de
`/Users/sierra/Producao_Musical/02_Faixas`. A origem disponibiliza seis WAVs
completos, mas não possui arquivos de letra nem letras nos metadados; por isso,
nenhum texto foi inventado. Ao adicionar uma letra, use o mesmo nome-base da
faixa e a extensão `.txt` (ou `.md`).
