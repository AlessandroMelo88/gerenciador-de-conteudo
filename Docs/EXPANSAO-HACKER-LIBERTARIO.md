# Expansão do Hacker Libertário

> **Atualizado:** 2026-09-29
> **Escopo:** expansão de fontes, estratégia de formatos e organização versionada dos prompts.

## Direção editorial

O Hacker Libertário não é um canal exclusivo de Shorts. A estratégia trabalha com dois formatos complementares:

- **Shorts:** cortes verticais com uma ideia fechada, gancho rápido e duração editorial perto de 30 segundos, com limite desejado de 45 segundos.
- **Vídeos longos:** análises ou conversas contínuas que mantenham contexto e conclusão; quando o assunto comportar, priorizar pelo menos 8 minutos para habilitar intervalos de anúncios no meio do vídeo.

Vídeos monetizados com pelo menos 8 minutos podem habilitar mid-rolls, mas o YouTube não garante que um anúncio será exibido. A participação em receita de anúncios também depende da entrada no Programa de Parcerias e do cumprimento das políticas. Com a base informada de aproximadamente 50 inscritos, o canal ainda está abaixo dos requisitos atuais de anúncios: 1.000 inscritos e 4.000 horas públicas qualificadas em 12 meses, ou 10 milhões de visualizações qualificadas de Shorts em 90 dias. [Requisitos do YPP](https://support.google.com/youtube/answer/72851?hl=pt-BR) · [Mid-rolls em vídeos de 8 minutos ou mais](https://support.google.com/youtube/answer/6175006?hl=pt-BR)

Os critérios publicados pelo YouTube classificam como Shorts vídeos quadrados ou verticais de até 3 minutos; a partir desses critérios, #Shorts não é requisito de classificação. O alvo editorial deste canal é bem menor (30–45 s); hashtags devem ser usadas apenas quando descreverem o tema, sem inserir #Shorts automaticamente. [Classificação de Shorts](https://support.google.com/youtube/answer/15424877?hl=pt-BR)

**Pipeline de formatos:** cada vídeo RSS é transcrito uma vez e alimenta até três Shorts e um vídeo longo na mesma execução. O longo só é tentado quando a transcrição permite selecionar um trecho contínuo de pelo menos 7 minutos sem usar a fonte inteira; fontes curtas continuam gerando Shorts. Cada clip persiste seu formato, então renderização, metadados, cotas e publicação aplicam o fluxo correto.

## Fontes adicionais ativadas

Em 2026-09-28, três fontes foram adicionadas ao nicho hacker-libertario e ativadas no PostgreSQL local. O conjunto passou de 42 para 45 fontes ativas. O perfil editorial associado é o perfil de destino conteudo-inteligencia; o nome do canal público é Hacker Libertário. No snapshot local, ele está ligado ao destino Hacker Libertário e às 45 fontes, sem outro canal de destino ligado a esse perfil.

| Canal | ID oficial do YouTube | RSS | Leitura editorial |
|---|---|---|---|
| TecSec Podcast | UCFfPOYpCwGt8qEd16j1Wa1Q · [canal](https://www.youtube.com/channel/UCFfPOYpCwGt8qEd16j1Wa1Q) | [feed](https://www.youtube.com/feeds/videos.xml?channel_id=UCFfPOYpCwGt8qEd16j1Wa1Q) | Forte aderência a cibersegurança e entrevistas técnicas. O site oficial descreve mais de 170 episódios e o canal derivado Cortes TecSec. [Sobre o TecSec](https://tecsecbr.com/sobre-nos/) |
| Curso em Vídeo | UCrWvhVmt0Qac3HgsjQK62FQ · [canal](https://www.youtube.com/channel/UCrWvhVmt0Qac3HgsjQK62FQ) | [feed](https://www.youtube.com/feeds/videos.xml?channel_id=UCrWvhVmt0Qac3HgsjQK62FQ) | Aulas de programação com potencial para explicações curtas e trechos educativos. O feed estava publicando conteúdo de Python em 2026-09-28. |
| Flow de Dados | UCmiBQ-47u2O8Ia48WJ_ZDKA · [canal](https://www.youtube.com/channel/UCmiBQ-47u2O8Ia48WJ_ZDKA) | [feed](https://www.youtube.com/feeds/videos.xml?channel_id=UCmiBQ-47u2O8Ia48WJ_ZDKA) | Aderência mista: há temas de tecnologia e Linux, mas o feed também contém entretenimento geral. Manter o filtro editorial ativo e reavaliar a qualidade dos itens ingeridos. |

Os três feeds RSS responderam com entradas recentes na validação feita em 2026-09-28. O seed reproduzível está em [scripts/seed_hacker_libertario_additional_sources.sql](../scripts/seed_hacker_libertario_additional_sources.sql). Reaplicar o seed ativa essas fontes se elas já existirem e não estiverem bloqueadas.

Ativar uma fonte permite ingestão pelo pipeline. Isso não confirma, por si só, licença comercial ou elegibilidade para monetização. A política de conteúdo reutilizado avalia clips, compilações e reações no canal como um todo; permissão do criador não substitui comentário original significativo, transformação substancial ou valor educativo/de entretenimento. Revisar direitos de uso e agregar contribuição editorial antes da publicação monetizada. [Políticas de monetização e conteúdo reutilizado](https://support.google.com/youtube/answer/1311392?hl=pt-BR)

## Prompts versionados por camadas

A fonte de edição passa a ser YAML em prompts/. Cada etapa junta camadas na ordem abaixo:

| Camada | Escopo | Exemplos |
|---|---|---|
| Geral | Entra em todos os canais e etapas correspondentes | fidelidade à transcrição, não inventar contexto e seguir o contrato do pipeline |
| Canal | Identidade e regras exclusivas do destino editorial | temas do Hacker Libertário; não defender o Estado; descartar candidatos com menção a políticos ou agentes públicos |
| Alvo | Regras específicas de plataforma e formato | YouTube -> Shorts ou YouTube -> Vídeo longo, duração, apresentação e hashtags |

Arquivos:

- [camada geral](../prompts/layers/general.yaml)
- [canal Hacker Libertário](../prompts/channels/hacker-libertario.yaml)
- [alvo YouTube -> Shorts](../prompts/targets/youtube-shorts.yaml)
- [alvo YouTube -> Vídeo longo](../prompts/targets/youtube-long.yaml)
- [JSON compilado para prompt_profiles](../prompts/compiled/conteudo-inteligencia.json)

O perfil de destino usa o slug de banco `conteudo-inteligencia`, o nicho `hacker-libertario` e o nome editorial armazenado `Conteúdo de Inteligência`. Este conjunto de arquivos é exclusivo do destino Hacker Libertário. As fontes que alimentam esse destino usam a mesma camada editorial; cada outro canal de destino deve receber seu próprio YAML, slug de perfil e JSON, mesmo que pertença ao mesmo nicho. Os aliases ficam vazios para não aplicar automaticamente a identidade libertária a canais genéricos de tecnologia.

O JSON respeita as colunas atuais de prompt_profiles: slug, name, niche, niche_aliases, active, as duas instruções de seleção, as duas instruções de metadata e thumbnail_prompt. A tabela tem apenas um campo de thumbnail; por isso, o compilador inclui nele as duas instruções condicionais de alvo e o runtime deve escolher a regra que corresponde ao formato informado.

Para recompilar usando Ruby e sua biblioteca YAML padrão, execute `ruby scripts/compile_prompt_profiles.rb`; depois revise o JSON e sincronize o banco com `cd painel && php artisan prompts:sync` (ou `docker compose exec php php artisan prompts:sync`). A migration importa os JSONs em instalações novas. A sincronização atualiza os textos e aliases do perfil pelo slug; mudanças manuais nesses mesmos campos no banco serão substituídas pelo YAML compilado. As regras técnicas que o worker acrescenta em runtime continuam obrigatórias e podem impor limites mais restritos que o alvo YAML. Hoje o worker aceita Shorts de 30 a 45 segundos por padrão. Para um teste ocasional mais longo, configure `SHORTS_MAX_DURATION_SECONDS` explicitamente.

## Medição da estratégia

Evitar promessas fixas de alcance, viralização ou um percentual universal de retenção. Comparar os resultados por formato e tema com os dados do próprio canal:

- Shorts: visualizações engajadas, escolha de assistir versus deslizar, retenção e inscritos gerados.
- Vídeos longos: impressões, CTR, duração média, horas assistidas, retenção por trecho e inscritos gerados.
- Revisar os horários de publicação a partir dos períodos de atividade do público no YouTube Studio; horários fixos são hipóteses de experimento, não garantias do algoritmo.
- Usar esses sinais para revisar os alvos dos prompts sem mudar a identidade editorial nem cortar frases e raciocínios no meio.
