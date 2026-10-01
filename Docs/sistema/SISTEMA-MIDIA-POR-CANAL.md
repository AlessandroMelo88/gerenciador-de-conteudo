# Mídia por canal (intro, encerramento, música)

Cada canal de destino pode ter a própria **intro**, **encerramento** e **música de fundo**. O
robô cola isso no vídeo depois de cortar e legendar. Tudo é opcional: se a mídia não existir ou
der erro, o vídeo sai do mesmo jeito, só sem o enfeite.

Origem: trazido de `origin/release/rico` em 30/09/2026 (Lote 8), adaptado à master. **Atualizado em
01/10/2026:** na `master` e em produção (lotes do `release/rico`, deploy `ace7714` de 30/09/2026).

---

## Para quem opera o painel

**Onde:** Configurações > aba **Mídia do canal**.

| Campo | O que significa |
|---|---|
| Tipo | Intro, Encerramento ou Música de fundo |
| Canal de destino | Obrigatório. Mídia sem canal fica guardada, mas nunca é usada |
| Formato | Todos, Curto ou Longo. Vale como filtro extra dentro do canal |
| Duração (só imagem) | Quantos segundos a imagem fica na tela (1 a 60; padrão 3) |
| Volume (só música) | 0,01 a 1; padrão 0,24 (24%) |
| Prioridade | Em empate, o maior número vence; se ainda empatar, as mídias se revezam entre os vídeos |

```
Vídeo longo pronto (cortado, legendado, com marca d'água)
        |
        v
 tem intro / encerramento / música cadastrados para o canal?
        |                       |
       sim                     não
        |                       |
        v                       v
 cola: intro -> vídeo -> encerramento     publica o vídeo normal
 + música nos 15 s finais
        |
   deu erro no meio?  ---sim--->  publica o vídeo normal (o erro fica no log)
```

Regras que costumam surpreender:

- **Só vídeo longo recebe mídia por padrão.** Shorts saem sem intro nem encerramento. Para ligar nos
  Shorts também, o operador do servidor define `MEDIA_FORMATS=longo,curto`.
- A música toca nos **15 segundos finais**, começa no volume configurado e sobe até 100% nos últimos
  8 segundos.
- Trocar ou apagar uma mídia vale para os próximos vídeos; o que já foi renderizado não muda.
- Apagar a mídia no painel apaga o arquivo também. Apagar um canal de destino deixa a mídia
  dele "sem canal" (guardada, sem uso).
- O quadro "Identidade pronta" é só informativo. Canal incompleto continua publicando.
- **Nenhum arquivo de mídia vai para o repositório** (ele é público). Os arquivos vivem no volume de
  branding do servidor.

---

## Referência técnica

### Banco

Migration `2026_09_30_110000_create_media_assets_table` (idempotente: não faz nada se a tabela já
existe). Tabela `media_assets`: `kind` (`intro`/`outro`/`music`), `name`, `path` (relativo ao disco
`branding`), `destination_channel_id` (FK, `ON DELETE SET NULL`), `format` (`curto`/`longo`/null),
`duration_seconds`, `music_volume`, `priority`, `active`.

Não foi trazida a migration da rico que sobe o volume padrão de 0,12 para 0,24 nas linhas existentes:
a tabela nasce vazia aqui, então o padrão já é 0,24.

### Painel

- `MediaAssetController` (`POST/PATCH/DELETE /painel/configuracoes/midia`): valida tipo x extensão
  (áudio só para música), limite de 100 MB, grava em `branding/media/<tipo>/<uuid>.<ext>`.
- `SettingsController@show` expõe `mediaAssets`, `destinationChannels` e `mediaConfiguration`.
- Tela: `Settings.tsx`, aba "Mídia do canal".

### Clip-processor

- `media_assets.resolve_media_assets`: escolhe por (canal, formato) > prioridade > rodízio pelo id
  do clip, só entre assets **do canal** do clip. Biblioteca do painel primeiro; depois, o que faltar
  vem de `assets/channels/<slug-do-canal>/` (`intro.mp4|jpg|png`, `encerramento.*`, `audio/*.mp3|wav`),
  se a pasta estiver montada em `ASSETS_DIR` (padrão `/app/assets`). Caminho do banco que escape do
  disco de branding e slug com `..` são rejeitados.
- `media_composer.compose_media`: normaliza cada trecho para o mesmo canvas, une com crossfade de
  até 0,35 s, mixa a música e normaliza o áudio para -14 LUFS. Encode configurável por
  `MEDIA_FFMPEG_PRESET` (padrão `veryfast`) e `MEDIA_FFMPEG_CRF` (padrão `20`).
- `video_processor.apply_channel_media`: chamado em `process_clip` depois do render final e antes
  dos metadados. **Nunca levanta exceção**: grava a composição em `<id>_branded.mp4`, confere que
  não está vazia e só então substitui `<id>.mp4`; em qualquer falha apaga o parcial e mantém o clip
  original.

Variáveis de ambiente (todas opcionais):

| Variável | Padrão | Efeito |
|---|---|---|
| `MEDIA_FORMATS` | `longo` | Formatos que recebem mídia |
| `ASSETS_DIR` | `/app/assets` | Raiz da pasta opcional `channels/<slug>/` |
| `MEDIA_FFMPEG_PRESET` | `veryfast` | Preset do x264 na composição |
| `MEDIA_FFMPEG_CRF` | `20` | CRF do x264 na composição |

### Ficou de fora de propósito

- Binários de `assets/` da rico (191 MB de WAV/MP4/PNG, licença das trilhas desconhecida).
- Card de "vídeo relacionado" no encerramento e o link na descrição (`related_video.py`): depende da
  reescrita do publicador e do render (lotes próprios).
- Mount `./assets:/app/assets:ro` no compose: o arquivo compartilhado não foi tocado. Sem o mount, só
  a biblioteca do painel funciona; para usar a pasta por canal, acrescentar o volume ao serviço
  `clip-processor`.
- Exigir mídia para liberar vídeo longo (a rico falhava o clip sem assets): aqui é sempre opcional.

### Testes

`clip-processor/tests/test_media_assets.py`, `test_media_channel_flow.py`, `test_media_composer.py`,
`test_media_composer_transitions.py`, `painel/tests/Feature/MediaAssetResourceTest.php`.
