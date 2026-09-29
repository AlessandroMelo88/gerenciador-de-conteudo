# Biblioteca de assets

Esta pasta é montada no `clip-processor` como `/app/assets`.

```text
assets/
├── channels/
│   └── <slug-do-canal>/
│       ├── intro.jpg
│       ├── intro.mp4
│       ├── encerramento.jpg
│       ├── encerramento.mp4
│       └── audio/
│           └── faixa-do-canal.wav
└── audio/
    └── originais mantidos como acervo, sem uso automático
```

Os nomes visuais canônicos são `intro` e `encerramento`, sempre em minúsculas.
Quando os dois formatos existem, o pipeline prefere o vídeo e usa a imagem como
fallback. `intro_2.jpg` é mantido como uma variação opcional e não é escolhido
automaticamente.

Os assets são sempre associados a um canal de destino. Para vídeos `longo`,
intros e encerramentos vêm da pasta do canal; a trilha só pode vir de
`channels/<slug>/audio/`. Faixas em `assets/audio/` ficam como originais e não
são um fallback compartilhado. A música entra nos 15 segundos finais, começa
no volume configurado (24% por padrão) e sobe gradualmente até 100% nos 8
segundos finais. As faixas do canal alternam pelo id do clip.

Os arquivos de áudio desta pasta foram copiados de
`/Users/sierra/Producao_Musical/02_Faixas`. A origem disponibiliza seis WAVs
completos, mas não possui arquivos de letra nem letras nos metadados; por isso,
nenhum texto foi inventado. Ao adicionar uma letra, use o mesmo nome-base da
faixa e a extensão `.txt` (ou `.md`).
