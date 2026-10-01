# Plano — vídeo longo automático, escolhido por canal

**Status:** IDEIA · plano escrito em 01/10/2026, nada implementado.
**Origem:** PR #1 do Ricardo (`release/rico`) fazia todo vídeo gerar Shorts **e** longo, sem chave para
desligar. Recusado como está; o dono quer decidir **por canal destino**, nas configurações do canal.

## Como é hoje (`master`)

O formato é decidido **uma vez por vídeo-fonte**, pela duração (`_detect_format` em
`clip-processor/src/rss_poller.py`):

| Fonte | Formato gravado em `source_videos.format` | O que sai |
|---|---|---|
| menos de 7 min (`MIN_LONGFORM_SECONDS = 420`) | `curto` | até 3 Shorts |
| 7 min ou mais | `longo` | **um** corte contínuo de 7 a 20 min, e **nenhum** Short |

Ou seja: fonte longa vira só longo, fonte curta vira só Shorts. Nunca os dois. A cota do longo já existe
(`MAX_LONGO_UPLOADS_PER_DAY`, padrão 2) e a publicação já reserva horário para ele.

O que **não** existe: o dono não consegue dizer "este canal não quer longo" nem "este canal quer Shorts
**e** longo da mesma fonte".

## O que queremos

Um seletor nas configurações do canal destino, com três modos:

| Modo | Comportamento | Quando usar |
|---|---|---|
| **Automático** (padrão) | Igual a hoje: a duração da fonte decide | Todos os canais, até o dono mudar |
| **Só Shorts** | Fonte longa também gera Shorts, nunca longo | Canal de futebol, se quiser cortar o render e a fila |
| **Shorts + longo** | Fonte com trecho contínuo de 7 min ou mais gera Shorts **e** um longo | Canal de política, se o dono quiser |

**Regra de ouro:** o padrão é "Automático", então **nada muda em produção** até o dono escolher outro
modo num canal. Isso é o que a PR do Ricardo não oferecia.

## Onde guardar a escolha

`destination_channels` já tem `template_config` (JSON) e o padrão de configuração por canal já existe em
mídia (`SISTEMA-MIDIA-POR-CANAL.md`) e perfis de prompt (`PLANO-PROMPTS-EDITAVEIS.md`). Duas opções:

| Opção | Prós | Contras |
|---|---|---|
| **Coluna nova** `destination_channels.long_format_mode` (`auto` \| `short_only` \| `both`) | Simples de consultar em SQL e de validar; migration pequena | Uma migration por opção futura |
| Chave dentro de `template_config` (JSON) | Sem migration | Mistura com configuração de template; sem validação no banco |

**Recomendação:** coluna nova, com default `auto`.

## O ponto difícil: o formato hoje é da fonte, não do canal

`source_videos.format` é gravado na ingestão, **antes** de existir clip. O canal destino só é conhecido
pelo nicho da fonte (`source_channels.target_niche`). Para o modo "Shorts + longo" é preciso gerar dois
conjuntos de clips da mesma fonte. Caminho sugerido:

1. A decisão passa a usar o canal destino do nicho da fonte, lendo `long_format_mode`.
2. `generated_clips.format` (já existe) passa a ser a fonte da verdade do formato **do clip**; o
   `source_videos.format` continua só como padrão. (A PR do Ricardo seguiu esse caminho: painel e cota
   leem o formato do clip, com `format` nulo caindo no formato da fonte.)
3. No modo `both`, o seletor roda **duas vezes** para a mesma fonte (curto e longo), cada uma com seu
   prompt (`SYSTEM_PROMPT` e `LONG_SYSTEM_PROMPT` já existem). O longo só entra se a IA devolver um trecho
   contínuo válido; **sem fallback cego de 13 min**.
4. O raw da fonte só pode ser apagado quando **todos** os clips dela estiverem terminais
   (`_maybe_finalize_source_video` já faz isso; conferir que cobre os dois formatos).

## Riscos e cuidados

- **Disco e render na A1:** `both` dobra o trabalho por fonte. Mexe na janela de download e no bug 12
  (disco). Começar ligando em **um** canal e medir.
- **Cota e fila:** o longo respeita `MAX_LONGO_UPLOADS_PER_DAY`; mais clips = mais itens na aprovação.
  Considerar um teto de longos pendentes por canal.
- **Custo de IA:** duas chamadas de seleção por fonte no modo `both`.
- **Fonte curta no modo `both`:** abaixo de 7 min não há longo; gera só Shorts. Sem erro.
- **Migration antes do código:** a coluna precisa existir antes de o `clip-processor` subir (o `deploy.sh`
  já migra antes de reiniciar, conferir).
- **Fonte longa no modo `short_only`:** hoje fonte longa vira só longo; no novo modo ela precisa gerar
  Shorts a partir do mesmo texto. O seletor de Shorts lê o início da transcrição (corte de caracteres);
  pode ser preciso ampliar a cobertura (item "seletor em janelas" da PR do Ricardo).

## Etapas

1. **Migration + modelo:** coluna `long_format_mode` (default `auto`), validação no painel.
2. **Painel:** campo em *Canais Destino* (select de três opções, com a explicação acima em linguagem simples).
3. **Pipeline:** ler o modo na decisão do formato; `auto` mantém o código atual intacto.
4. **Modo `short_only`:** fonte longa gera Shorts (primeiro modo testável, sem render extra).
5. **Modo `both`:** duas seleções por fonte, clips com `format` próprio.
6. **Testes:** `auto` idêntico ao atual (regressão); cada modo com fonte curta e longa; finalização do raw.
7. **Rollout:** deploy com tudo em `auto`; depois ligar **um** canal, observar render, disco, cota e
   fila por alguns dias antes de ligar o segundo.

## Decisões em aberto (do dono)

- Qual canal liga `both` primeiro?
- O canal de futebol deve ficar em `auto` ou ir para `short_only`?
- Teto de longos pendentes de aprovação por canal?

Antes de codar: spec curta em `Docs/specs/` (skill `padroes-projeto`), branch `feature/longo-por-canal`.
