# Plano mestre — estado, decisões e próximos passos

Documento de continuidade. Reúne o que foi decidido em 14/09/2026 sobre **advertência de direitos
autorais**, **infraestrutura**, **banco de dados**, **marca** e **monetização por afiliados**.

Serve para retomar o trabalho do zero: se o contexto de conversa se perder, comece por aqui.

Última atualização: **14/09/2026** (curso concluído, origem dos 83 clips apurada, plano A1+PostgreSQL detalhado).

---

## 0. Situação apurada em 14/09/2026

Tudo abaixo foi verificado na produção, não é estimativa.

### Infraestrutura real

```
shape:  VM.Standard.E2.1.Micro   1 OCPU / 1.0 GB   x86_64
disco:  48 GB, 72% usado (14 GB livres)
swap:   4 GB, com 559 MB em uso   ← pressão de memória real
IP:     147.15.124.191
painel: https://toolscut.alessandromelo.com.br
```

**Correção importante:** o [`PLANO-ORACLE.md`](PLANO-ORACLE.md) diz "migração não iniciada", mas a
produção **já está na Oracle** — só que no shape errado. `E2.1.Micro` é shape **fixo**, não `.Flex`:
não existe caminho de aumentar RAM. O plano previa `VM.Standard.A1.Flex` 2 OCPU/12 GB, que também é
Always Free. Aquele documento precisa ser corrigido.

### Código versus produção

`md5sum` de `db.py`, `main.py` e `pipeline_runner.py` **bate** entre local e servidor. Porém há
~300 linhas modificadas e **não commitadas** em 6 arquivos do `clip-processor` desde 11/09/2026.

> **Produção está rodando código não commitado.** Não existe ponto de rollback. Commitar é
> pré-requisito de qualquer correção.

### Volume publicado

| Nicho | published | rejected | failed | em trânsito |
|---|---|---|---|---|
| futebol | **83** | 11 | 29 | 2 `pending`, 1 `pending_cut` |
| politica | 25 | 4 | 65 | 2 `cutting` |

Os 2 clips em `cutting` são o bug 4 acontecendo agora — estado sem recuperação automática.

---

## 1. Advertência de direitos autorais — o assunto que bloqueia todo o resto

### O fato

Advertência recebida em **14/09/2026**, reclamante **Supernova**, expira em **13/12/2026** se o
Curso de Direitos Autorais for concluído. Dois vídeos removidos do canal de futebol:

| Vídeo | Duração | Trecho reclamado |
|---|---|---|
| "Pênalti de Kaio Jorge: Tiro ao Alvo!" | 0:10 | 0:00 – 0:09 |
| "Chutaram o Vini Jr no chão e o VAR não fez nada!" | 0:19 | 0:00 – 0:18 |

O trecho reclamado é **o clip inteiro**. Não há parte autoral.

### Claim de Content ID ≠ advertência

Distinção que explica tudo:

| | Content ID | Takedown manual |
|---|---|---|
| Quem dispara | Algoritmo de impressão digital | Uma pessoa do detentor |
| Consequência | Reivindicação: receita vai pro dono | **Advertência (strike)** |
| Vídeo | Continua no ar | Removido |
| 3 ocorrências | Nada | **Canal removido** |

O que chegou foi **takedown manual** ("pedido de remoção"). Alguém da Supernova olhou o canal e
denunciou. Nenhum ajuste de imagem afeta isso — quem denunciou foi gente.

### Por que outros canais de cortes não levam strike

A pergunta certa não é "que técnica eles usam", é "quem é o dono do conteúdo e o que ele quer".

- **Podcast e talk show** (Flow, Inteligência Ltda, Jovem Pan, Casé TV, Podpah): o dono **quer**
  viralizar. Vários mantêm programa oficial de cortes, liberam o material ou simplesmente não
  reclamam. Quando reclamam, é via Content ID — claim, não strike. Modelo de negócio deles é
  alcance.
- **Imagem de jogo** (CBF, Globo, Paramount, Supernova e afins): o dono **vende exclusividade**.
  Alcance de terceiro destrói o produto que ele licenciou. Fiscaliza ativamente e usa takedown
  manual — exatamente o que aconteceu.

É a economia do detentor que decide, não a técnica do cortador.

### O que não funciona

Cortar borda, dar zoom, espelhar, alterar pitch: isso mira a impressão digital do Content ID. Não
afeta denúncia humana, é burla de detecção pelos termos do YouTube (risco de remoção do canal por
si só) e não muda nada na esfera legal. Descartado.

### Conclusão que preserva o nicho

**O problema não é "futebol". É "imagem de jogo de emissora".**

O canal de futebol não precisa mudar de nicho nem perder os 100 inscritos. Precisa mudar de
**fonte**: cortar de programas de futebol que aceitam cortes — podcasts, talk shows e canais de
comentarista — em vez de lance de partida de detentor de transmissão. Mesmo público, mesmo formato,
mesmo pipeline. Só muda a linha em `source_channels`.

### Regras confirmadas pelo Curso de Direitos Autorais (concluído em 14/09/2026)

- **3 advertências ativas encerram o canal** e excluem **todas as contas associadas**. Com 1 ou 2, o
  canal segue funcionando.
- Cada advertência expira em **90 dias**, desde que o curso tenha sido concluído. O curso está feito,
  então esta advertência cai em **13/12/2026**.
- **Música comercial de fundo é a outra fonte de advertência.** Usar só a Biblioteca de Áudio do
  YouTube ou trilha livre de royalties com licença explícita. Vale conferir se o
  `video_processor.py` insere alguma trilha — hoje não parece inserir, mas precisa ser verificado
  antes de qualquer feature de áudio.

> "Excluir o vídeo não removerá a advertência." Confirmado pela própria tela do YouTube. Apagar não
> desfaz nada.

### Origem real dos 83 clips de futebol

Apurado no banco em 14/09/2026 — **o risco não está distribuído por igual**:

| Fonte | Publicados | Classe | Risco |
|---|---|---|---|
| ESPN Brasil (`@espnbrasil`) | **44** | Emissora / detentora | **Alto** |
| Jovem Pan Esportes (`@jovempanesportes`) | 11 | Programa falado / opinião | Baixo |
| TNT Sports Brasil (`@TNTSportsBR`) | 8 | Emissora / detentora | **Alto** |
| CazéTV (`@CazeTV`) | 8 | Detentora de transmissão | **Alto** |
| Canal do Nicola (`@CanaldoNicola`) | 7 | Jornalista / comentário | Baixo |
| TiaGOL (`@canal_tiagol`) | 5 | Canal de cortes | **Foi este que gerou a advertência** |

Os dois vídeos removidos (`sOrylGoZsZI` — Vini Jr; `ejqCsRW3A64` — Kaio Jorge) vieram do **TiaGOL**.
Detalhe que importa: o TiaGOL é ele mesmo um canal de cortes, ou seja, o material já chegou de
segunda mão e a Supernova reclamou na ponta final. Cortar de canal de cortes acumula o risco de dois
elos.

**60 dos 83 (72%) vêm de emissora/detentora** — ESPN, TNT e CazéTV. É essa a exposição real, não os
5 do TiaGOL. As duas fontes seguras (Jovem Pan Esportes e Canal do Nicola) somam apenas 18.

Conclusão operacional: desativar ESPN, TNT, CazéTV e TiaGOL em `source_channels`; manter Jovem Pan
Esportes e Canal do Nicola sob verificação; procurar novas fontes de programa falado.

### Executado em 15/09/2026

**Desativadas** (`active=0`, nada apagado — reverter é `active=1`): SporTV (id 3), ge.globo (4),
ESPN Brasil (5), TNT Sports (7), CazéTV (204), TiaGOL (277).

**Adicionadas**, via `SourceChannelsSeeder` — canal de pessoa física ou produção própria, conteúdo
falado, e nenhum é canal de cortes:

| Canal | Handle | Formato observado |
|---|---|---|
| PVC | `@PVCoelho` | **curto** (299–452s) |
| Denílson Show | `@DenilsonShow` | **curto** (163–378s) |
| Charla Podcast | `@CharlaPodcast` | misto (165–913s) |
| Mauro Cezar Pereira | `@MauroCezar` | longo (491–983s) |
| ~~Rica Perrone~~ | `@RicaPerrone` | **desativado em 16/09/2026 — sem feed RSS** |
| Tati Mantovani | `@TatiMantovani` | longo (502–866s) |
| Marcelo Bechler | `@MarceloBechler1` | longo (481–2878s) |
| Fred Caldeira | `@FredCaldeira` | longo (701–3903s) |
| Desimpedidos | `@Desimpedidos` | misto (493–2077s) |

PVC, Denílson e Charla entregam vídeo abaixo de `MIN_LONGFORM_SECONDS` (420s), então **mantêm a
cadência de Shorts** do canal — os outros geram corte horizontal longo.

Reprovados na verificação: `@CortesdoCasimitoOFICIAL` e `@CasimiroMiguel` (o primeiro é canal de
cortes, e o conteúdo recente dos dois é reação/variedades, não futebol); `@Pilhado` (é política);
`@JaoBastos` (produção própria, mas é pelada, não análise); `@CanalDoGB` (canal morto, só duas
intros de 11s).

**Risco que sobra:** jornalista de futebol insere imagem de jogo dentro do próprio vídeo. Corte que
cair em cima desse trecho herda o risco da detentora, mesmo vindo de fonte aprovada. O seletor
escolhe por transcrição e **não sabe o que está na tela** — não há hoje como barrar isso
automaticamente. Entra como requisito do gate de licença (seção 2).

### Privar ou apagar?

**Privar. Nunca apagar.**

| | Privar | Apagar |
|---|---|---|
| Remove a advertência | Não | Não |
| Tira da vista do reclamante | Sim | Sim |
| Reversível | Sim | **Não** |
| Preserva métrica e histórico do canal | Sim | Não |
| Preserva prova, caso precise contestar | Sim | **Não** |

Apagar tem exatamente o mesmo efeito de privar sobre a advertência — nenhum — e destrói o que você
pode precisar depois. Os 2 vídeos da advertência já foram removidos pelo YouTube; não há o que fazer
com eles. A decisão vale para os outros 81.

> Nota de sincronia: os 2 removidos continuam como `published` no banco. O sistema não sabe que
> saíram do ar. Reconciliar junto do bug 10.

### Ações imediatas

- [x] Concluir o Curso de Direitos Autorais (sem ele a advertência não expira) — feito em 14/09/2026
- [x] **Confirmado na tela do YouTube Studio (15/09/2026)** que é **advertência**, não reivindicação
      de Content ID: "1 advertência por direitos autorais", recebida em 14/09/2026, **expira em 89
      dias**, reclamante Supernova, 2 vídeos. Os dois já estavam excluídos pelo operador — e a própria
      tela avisa que "excluir o vídeo não removerá a advertência"
- [x] **Decisão: não fazer nada com a advertência.** Das três opções oferecidas pelo YouTube,
      "não fazer nada" é a certa — ela expira sozinha porque o curso está concluído. "Solicitar
      retirada" coloca o canal no radar de quem já denunciou à mão. Contranotificação está descartada
      (ver abaixo)
- [ ] **Não** enviar contranotificação nesses dois — entrega nome e endereço ao reclamante e aceita
      foro judicial, e o clip é 100% material deles
- [ ] Pausar publicação do nicho futebol (3 clips a caminho viram advertência 2)
- [x] ~~Tornar privados os 83 clips de futebol publicados~~ — **decisão do operador em 15/09/2026:
      não privar.** Motivo: vídeo de corte perde tração rápido, então a exposição residual dos já
      publicados é baixa, e privar não remove a advertência de qualquer forma. O cuidado passa a
      valer **daqui para frente**, via troca de fonte
- [ ] **Separar as contas Google dos dois canais** — o aviso do YouTube diz "seu canal e todos os
      canais associados". Hoje uma 3ª advertência no futebol leva o de política junto. Ação mais
      barata e de maior impacto da lista.
      **Decisão do operador (16/09/2026): adiado, as contas seguem juntas por enquanto.** Risco
      aceito conscientemente; reavaliar se chegar uma 2ª advertência
- [x] Auditar de quais `source_channels` vieram os 83 e classificar cada fonte — ver tabela acima e
      a seção 2.1

> **Correção de escopo apurada em 15/09/2026:** a produção tem **8** canais-fonte de futebol ativos,
> não 6. Além dos já listados, **SporTV** (`@canalsportv`) e **ge.globo** (`@globoesporte`) estão
> ativos — ambos Globo, a detentora mais agressiva em takedown manual. São **6 de 8** em alto risco.
>
> A mesma exposição existe no nicho **política** e nunca foi olhada: CNN Brasil, Band Jornalismo,
> UOL, Jovem Pan News, ICL e O Antagonista são telejornal, mesma classe de detentor. Não é urgente
> (a advertência veio do futebol), mas o problema não está contido num nicho só.

---

## 2. Gate de licença — a correção estrutural

Verificado: **não existe nenhuma verificação de licença no `clip-processor`.** Zero ocorrência de
`license` nos módulos. `rss_poller.py:243` lê `source_channels` e ingere tudo que o feed devolver.
A tabela não tem coluna de licença.

### O que entra

1. **`source_channels.license_status`** — enum:

   | Valor | Significado |
   |---|---|
   | `owned` | Conteúdo próprio |
   | `creative_commons` | Fonte publica sob CC-BY |
   | `permission` | Autorização escrita do detentor, ou programa oficial de cortes |
   | `public_domain` | Ato oficial / obra não protegida |
   | `unverified` | **Padrão. Não ingere.** |

   Regra: **whitelist, nunca blacklist.** O poller só ingere o que não for `unverified`.

2. **`source_videos.license`** — o `yt-dlp` expõe o campo `license` do YouTube
   (`creativeCommon` vs `youtube`). Sinal real, gratuito e automatizável, por vídeo e não só por
   canal. Vídeo que não for CC e não vier de fonte aprovada não entra no corte.

3. **Kill switch por canal destino** no painel, para pausar um nicho sem derrubar o outro.

### Classificação das fontes por nicho

**Política — tem caminho legítimo e abundante.** TV Câmara, TV Senado, TV Justiça, EBC/Agência
Brasil. Ato oficial não é obra protegida (Lei 9.610, art. 8º) e boa parte desse material é
publicada com licença de reuso. **Verificar fonte por fonte antes de marcar** — não assumir.

**Futebol — trocar a fonte, não o nicho.** Sair de lance de partida e ir para programa falado:
podcast de futebol, talk show, canal de comentarista. Muitos têm programa oficial de cortes. Para
cada candidato, registrar a evidência da permissão (link da política, e-mail de autorização) antes
de marcar como `permission`.

---

## 3. Banco de dados — MySQL para PostgreSQL

**Decisão: sim, migrar. Junto com a troca de VM, não antes.**

### Por que é barato

O suporte já existe no código, não é reescrita:

- `db.py` detecta o driver por `DB_CONNECTION` / `POSTGRES_HOST` e usa `psycopg2` ou `pymysql`
- `PostgresConnectionWrapper` e `PostgresCursorWrapper` uniformizam cursor de dicionário e
  `lastrowid`
- Queries já compatibilizadas: `ON CONFLICT ... DO NOTHING` vs `INSERT IGNORE`, `INTERVAL` ANSI vs
  `DATE_SUB`
- Laravel troca por `DB_CONNECTION=pgsql`
- [`BANCO-DE-DADOS.md`](BANCO-DE-DADOS.md) já documenta o modo híbrido (MySQL 8.4 / PostgreSQL 17)

### Por que compensa

Argumento vindo do próprio histórico: o commit `16fe65c` corrige *"mysql repeatable read snapshot"* —
o isolamento padrão do MySQL entregava snapshot velho ao daemon. O padrão do Postgres
(`READ COMMITTED`) não tem essa armadilha. Some a isso JSON nativo melhor, CTE melhor, e o
[`painel-kit`](../../CLAUDE.md) já padroniza PostgreSQL em projeto novo — o serviço de afiliados
nasceria em Postgres de qualquer jeito, e dois bancos diferentes na mesma VM é desperdício.

### Por que não agora

Ganho zero para a advertência, que é o que está queimando. E a migração de dados é **muito** mais
segura numa instância nova e vazia do que trocando o motor debaixo de um sistema em produção.
Fazer os dois no mesmo movimento: A1 nova sobe já com Postgres, dados entram uma vez só.

---

## 4. Infraestrutura — migrar para A1 Flex 12 GB

| Opção | RAM | Custo/mês | Nota |
|---|---|---|---|
| **A1.Flex 2 OCPU / 12 GB** | 12 GB | **R$ 0** | Always Free. ARM (aarch64) |
| E5.Flex 1 OCPU / 8 GB | 8 GB | ~US$ 16 ≈ R$ 85 | x86, pago, pior negócio |
| E2.1.Micro (atual) | 1 GB | R$ 0 | shape fixo, sem upgrade |

Doze GB custam **zero**. A instância atual é a versão fraca da mesma faixa gratuita.

Pontos de atenção:

- É **ARM**, não é resize. Instância nova + migração. `mysql`/`postgres`, `redis`, `php`, `nginx`
  têm imagem arm64; `whisper.cpp` precisa recompilar (10–15 min, uma vez)
- Cota A1 = 1.500 OCPU-horas/mês, que é exatamente 2 OCPU rodando 24/7. Não sobra para 2ª instância
- Cotas do x86 Micro e do A1 são **separadas** — dá para subir a A1, validar e só então derrubar a
  Micro. Downtime baixo
- Ganho concreto: acaba o `mem_limit` apertado, ffmpeg volta a multi-thread (hoje está em
  single-thread/ultrafast por causa de 1 GB — commit `6ce2e78`)

### Migração combinada A1 + PostgreSQL — passo a passo

Instância nova e vazia é o momento mais seguro para trocar o motor do banco: nada em produção é
alterado até o cutover, e o rollback é simplesmente continuar na Micro.

**Etapa 1 — provisionar (não mexe em produção)**
- [ ] VM `VM.Standard.A1.Flex`, 2 OCPU / 12 GB, Ubuntu 24.04 **ARM**
- [ ] Boot volume 50 GB + block volume 150 GB montado em `/mnt/videos`
- [ ] Security List e firewall local da imagem: liberar 22 e 443 **nos dois lugares**; não expor
      5432 nem 6379
- [ ] Orçamento de US$ 1 com alerta, como previsto no `PLANO-ORACLE.md`

**Etapa 2 — compose próprio com Postgres**
- [ ] `docker-compose.yml` novo só com `clip-processor`, `postgres`, `redis`, `nginx`, `php` —
      sem kelnab, feeb, placebeads, riodelux, gringo
- [ ] Imagem `postgres:17-alpine` (tem arm64)
- [ ] `.env` novo com segredos **regerados**: `DB_CONNECTION=pgsql`, `POSTGRES_HOST`, porta 5432
- [ ] Rebuild ARM do `whisper.cpp` (10–15 min, uma vez)

**Etapa 3 — schema**
- [ ] `php artisan migrate` contra o Postgres vazio, criando o schema do zero
- [ ] Conferir que os tipos saíram corretos: `enum` do MySQL vira `varchar` + `CHECK`, e
      `AUTO_INCREMENT` vira `GENERATED ... AS IDENTITY` ou `serial`
- [ ] Rodar a suíte do `clip-processor` **dentro do container** com o driver `pgsql` ativo — é o
      teste real dos wrappers de `db.py`, que hoje nunca rodaram em produção

**Etapa 4 — dados**
- [ ] `mysqldump --no-create-info --complete-insert` das tabelas de dado, ou `pgloader` (mais
      seguro com tipos). Ordem: `niches`, `source_channels`, `destination_channels`,
      `source_videos`, `generated_clips`, `system_settings`, `users`
- [ ] **Corrigir as sequences depois do load** — `setval` em cada tabela, senão o primeiro insert
      colide com id existente. É a falha clássica de migração MySQL para Postgres
- [ ] Conferir contagem linha a linha por tabela, origem versus destino
- [ ] Redis: **não** migrar com `FLUSHALL` em cima. Copiar as chaves `video:*` (dedup) — perdê-las
      ressuscita todo o backlog no próximo poll RSS, conforme o `CLAUDE.md`

**Etapa 5 — vídeos e cutover**
- [ ] `rsync` dos arquivos de `/home/ubuntu/.../videos` para `/mnt/videos` na A1
- [ ] Segundo `rsync` incremental na hora do corte, para pegar o delta
- [ ] Pausar o pipeline na Micro, rodar o delta final, subir a A1, apontar o DNS
- [ ] Validar um ciclo completo (poll, download, corte, publicação) antes de desligar a Micro
- [ ] Só então terminar a instância Micro

**Etapa 6 — depois**
- [ ] `deploy.sh`: trocar `SERVER_IP` e a chave SSH
- [ ] Reverter as gambiarras de 1 GB: `mem_limit` estrito (commit `30adbda`), ffmpeg em
      single-thread/ultrafast (commit `6ce2e78`), dashboard limitado a 10 queries
- [ ] Backup do Postgres agendado **para fora da Oracle** (`pg_dump`)
- [ ] Atualizar `PLANO-ORACLE.md`, `DEPLOY.md`, `BANCO-DE-DADOS.md` e `ARCHITECTURE.md`

**Rollback:** enquanto a Micro não for terminada, o rollback é apontar o DNS de volta. Não terminar
a Micro antes de um ciclo completo validado na A1.

---

## 5. Marca — Umbrella Solutions

**Decisão: aprovada.** Separar marca pessoal de marca de serviço.

- `alessandromelo.com.br` — pessoal: blog técnico, portfólio, a skill `post-tech`
- **Umbrella Solutions** — serviço: painel, produtos de afiliado, cursos, landing pages

Não é questão legal e sim de posicionamento: oferta comercial sob marca pessoal mistura autoridade
técnica com venda, e dificulta ceder ou vender a operação depois.

Implementação: **mesmo backend, tema diferente.** O painel Inertia + React 19 + shadcn já separa
tema de estrutura. Um segundo tema (tokens de cor, tipografia, logo) mais um domínio apontando para
o mesmo Laravel resolve — não duplicar código nem banco.

**Status (15/09/2026):** tema implementado na branch `afiliadas-fase2`: `config/branding.php`,
`BRAND_DOMAINS`/`APP_BRAND`, tokens em `[data-brand='umbrella']`. Falta domínio (DNS, vhost,
certificado) e logo. Detalhes em [`SISTEMA-AFILIADOS.md`](SISTEMA-AFILIADOS.md#marca-umbrella-solutions).

Ponto prático a resolver antes de faturar: rede de afiliado paga pessoa física, mas CNPJ (MEI
serve) reduz imposto e permite emitir nota. Não bloqueia começar.

---

## 6. Afiliados

### Arquitetura decidida

**Um MySQL/PostgreSQL só, um painel só.** Tabelas `offers` e `offer_clicks` no mesmo banco, sem FK
cruzando com `generated_clips`. Numa VM de 12 GB, subir um segundo banco gasta centenas de MB de RAM
para guardar poucos MB de dado. A separação que importa é de **código e deploy**, não de processo de
banco.

> Correção de rumo registrada: a primeira proposta foi "banco próprio para o serviço de afiliados".
> Está descartada pelo motivo acima.

O microsserviço de verdade é o **worker na máquina local**, e o sentido do fluxo é invertido de
propósito:

```
máquina local (worker, roda quando você quiser)
    busca produto  →  gera copy/criativo com IA
    POST https://<umbrella>/api/offers   (Bearer token)
         ↓
    servidor: tabela `offers`, ofertas prontas, status draft
         ↓
    consumo local e síncrono. Tabela vazia = segue sem anúncio
```

**Local empurra, servidor nunca puxa.** Se o servidor chamasse a máquina local, uma máquina
desligada travaria o pipeline — e este projeto já tem histórico de estado preso sem recuperação.
Assim: sem túnel, sem dependência de uptime, e você revisa a oferta no painel antes de liberar.

### Camadas de IA

| Camada | Modelo | Por quê |
|---|---|---|
| Criativo em lote (copy de campanha, roteiro de curso) | Claude local, em lote, com você no comando | Qualidade alta, cai como `draft` para aprovação |
| Caminho automático por item | Haiku via `ANTHROPIC_API_KEY`, fallback Groq | Centavos por mês. Assinatura de IDE é seat interativo, não backend: quebra sem aviso e não tem retry |

Regra do projeto que vale aqui: **todo caminho novo de IA nasce com fallback Groq** — ver
[`SISTEMA-IA-SELECAO.md`](SISTEMA-IA-SELECAO.md).

### Canais de divulgação — não depende de vídeo

| Canal | Por quê agora | Esforço |
|---|---|---|
| Descrição + comentário fixado nos vídeos existentes | Acervo vira inventário, sem código novo | baixo |
| **Telegram** | O bot **já existe** (`telegram_notifier.py`). Canal por nicho, oferta automática | baixo |
| Blog | Review ranqueia e traz tráfego permanente, independente do YouTube | médio |

Depois: página de links própria no domínio (rastreável, ao contrário de Linktree), Shorts
reaproveitando o 9:16 que o pipeline já gera, Instagram/TikTok, Pinterest para produto físico.

Queimar a oferta dentro do vídeo sai do caminho crítico — vira fase tardia.

### Redes de afiliado

**Conta de comprador na Hotmart já é conta de afiliado.** Mesma conta: ir em Mercado, filtrar por
nicho, pedir afiliação. Não precisa ser vendedor. Vendedor só quando for produto próprio.

- **Digital / intelectual (política):** Hotmart, Eduzz, Kiwify, Monetizze
- **Físico (futebol):** Amazon Associados BR, Mercado Livre Afiliados, Shopee Afiliados,
  Centauro/Netshoes via Awin

Pegadinha: a Product Advertising API da Amazon só libera após 3 vendas em 180 dias. Começar o
automático por Mercado Livre e Shopee, que liberam API mais fácil.

---

## 7. Bugs abertos

Detalhe completo em [`BUGS.md`](BUGS.md).

| # | O quê | Gravidade | Onde corrigir |
|---|---|---|---|
| 11 | Container não honra SIGTERM; todo `docker stop` vira SIGKILL | **Alta** — cria estado preso novo a cada restart | handler de sinal em `main.py` + `stop_grace_period` no compose |
| 4 | Sem recuperação para `cutting`, `publishing`, `transcribing` | **Alta** — causou o incidente de 27/07 | nova query em `db.py` + chamada em `run_recovery_once`. `publishing` precisa checar `youtube_video_id` antes, senão republica duplicado |
| 7 | 4 testes falhando em `test_pipeline_runner.py` | Baixa | 1 é `flask` ausente no host (rodar no container); 3 são mock de cursor esgotado |
| 10 | 287 `clip_path` apontando para arquivo inexistente | Média | **Destrutivo.** Regra 3 do `CLAUDE.md`: filtrar por id, nunca por nome de arquivo. Listar, conferir contagem e tamanho, só então agir |
| 6 | Painel não apaga backlog de download (1062 linhas) | Média | Causa real é o RSS ingerir mais que a janela consome; purgar trata sintoma |
| 3 | Thumbnail não aplicada em vídeo longo | Suspeita | falta confirmar |
| 8 | Docker Desktop trava sob pressão de disco | Fora do projeto | esconde os outros; monitorar |

Ordem: **11 → 4 → 7 → 10 → 6.** O bug 11 primeiro porque ele *gera* o bug 4 — corrigir o 4 com o 11
aberto é enxugar gelo.

---

## 8. Ordem de execução

| # | Fase | Status | Depende de |
|---|---|---|---|
| 0 | Curso de direitos autorais, pausar futebol, privar os 83 clips, separar contas Google | ⬜ | — |
| 1 | Commitar as ~300 linhas pendentes (ponto de rollback) | ⬜ | — |
| 2 | Gate de licença: `license_status`, campo `license` do yt-dlp, kill switch | ⬜ | 1 |
| 3 | Auditar e reclassificar fontes; achar fontes de futebol que aceitam cortes | ⬜ | 2 |
| 4 | Bugs 11 e 4 | ⬜ | 1 |
| 5 | VM A1 12 GB + PostgreSQL no mesmo movimento | ⬜ | 4 |
| 6 | Afiliados: schema, `POST /api/offers`, tela, worker local, tela de performance | 🟡 código pronto nas branches `afiliadas` e `afiliadas-fase2` (15/09/2026), sem deploy — ver [`SISTEMA-AFILIADOS.md`](SISTEMA-AFILIADOS.md) | 5 |
| 7 | Tema Umbrella Solutions e domínio | 🟡 tema pronto na branch `afiliadas-fase2` (seleção por host ou `APP_BRAND`); falta DNS, vhost, certificado e logo | 6 |
| 8 | Divulgação: Telegram, descrições, blog | 🟡 Telegram automático pronto na branch `afiliadas-fase2`; falta criar canais e pôr o bot como admin. Descrições e blog ⬜ | 6 |
| 9 | Produto próprio e cursos | ⬜ | 8 |

---

## 9. Decisões registradas

| Decisão | Motivo |
|---|---|
| Banco único, painel único | Segundo banco custa RAM sem entregar isolamento útil |
| Worker de afiliado empurra, servidor não puxa | Máquina local desligada não pode travar o pipeline |
| PostgreSQL sim, mas junto da migração de VM | Suporte já existe no código; migrar em instância vazia é mais seguro |
| A1 Flex 12 GB, não shape pago | Mesmo custo zero, 12× a RAM |
| Sem burla de Content ID | Não afeta denúncia humana, viola os termos, não muda a esfera legal |
| Trocar a fonte do futebol, não o nicho | O problema é imagem de emissora, não o assunto |
| Marca de serviço separada da pessoal | Não misturar autoridade técnica com oferta comercial |
| Não enviar contranotificação nos 2 vídeos | Clip é 100% material do reclamante; expõe identidade e aceita foro |

---

## 10. Pendente do usuário

- [x] Concluir o curso de direitos autorais — feito em 14/09/2026, regras registradas na seção 1
- [ ] Levantar canais-fonte de futebol com política de cortes permissiva (com link da evidência)
- [ ] Confirmar se o bug 10 entra agora ou depois
- [ ] Confirmar se commita as 300 linhas pendentes antes de qualquer correção
