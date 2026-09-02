# Plano de migração — Oracle Cloud (Always Free)

**Objetivo:** tirar o pipeline do SSD da máquina local e deixar na máquina só o código de desenvolvimento.
**Restrição inegociável:** custo R$ 0. Nenhuma cobrança no cartão, em nenhum cenário.

Status geral: **NÃO INICIADO** (fase 1, pré-requisitos de código, em andamento) · Última atualização: **13/08/2026**

---

## Decisão tomada

**Opção A — tudo numa instância só.** Uma VM Ampere A1 (ARM) rodando o `docker-compose` inteiro: `clip-processor` + MySQL + Redis + painel.

Por quê, em uma frase: o gargalo é **disco**, não banco — o MySQL do projeto tem alguns MB, os 22 GB eram vídeo; então mover o banco para fora não resolveria nada, e sair de um SSD de 228 GB compartilhado para ~150 GB dedicados resolve.

Alternativas descartadas e o motivo:

| Alternativa | Por que não |
|---|---|
| Banco no Supabase | É PostgreSQL. O pipeline é MySQL cru (`INSERT ... ON DUPLICATE KEY`, `DELETE sv FROM ...`, `SUM(status IN %s)`) — exigiria reescrever `db.py`, `publisher.py`, `internal_api.py`, `queue_controls.py` e as migrations. Free tier de 500 MB e **pausa após 1 semana sem requisição**, que num pipeline com estados sem recuperação vira mais uma fonte de travamento silencioso |
| Banco no Aiven free (MySQL) | 1 GB, e também desliga por inatividade. Sem vantagem sobre manter local |
| MySQL HeatWave Always Free (Oracle) | Tecnicamente ótimo — MySQL nativo, 50 GB + 50 GB de backup, sem alteração de código. Guardado como **upgrade futuro** se o disco apertar; não vale a complexidade agora |
| GCP e2-micro | 1 GB de RAM, 30 GB de disco, **1 GB de egress/mês**. Não roda ffmpeg nem guarda vídeo |
| AWS t3.micro | 1 GB de RAM e expira em 12 meses |

---

## ⚠️ Prazo externo: 18/08/2026

Em 12/06/2026 a Oracle reduziu o Always Free do Ampere A1 de 4 OCPU/24 GB para **2 OCPU/12 GB** (1.500 OCPU-horas + 9.000 GB-horas por mês), sem anúncio público. Instâncias acima do novo limite são desligadas a partir de **18/08/2026**.

Armadilha registrada na cobertura do caso: se um recurso for **terminado**, pode não ser possível recriá-lo acima do novo limite. Ou seja, uma instância antiga em 4/24 perde a proteção se você destruí-la. **Redimensionar, nunca terminar**, se já existir uma.

---

## Como o custo zero é garantido

Não é confiança, é construção. Quatro camadas:

### 1. Não fazer upgrade para Pay As You Go (a camada que realmente importa)

A documentação da Oracle é explícita: **o cartão não é cobrado a menos que você faça upgrade da conta.** Enquanto a conta for "Always Free", não existe caminho de cobrança — o pior caso é o recurso ser recusado ou desligado, nunca faturado.

Consequência prática: **quando o console oferecer "Upgrade to Pay As You Go", recusar sempre.** Ele aparece com frequência, inclusive como saída sugerida para erro de capacidade.

O relato de que contas PAYG mantêm 4 OCPU/24 GB de graça é de suporte, não de documentação — e mesmo que fosse verdade, aceitar PAYG destrói a garantia acima em troca de CPU que este projeto não precisa. Não vale.

### 2. Provisionar só recursos com o selo "Always Free-eligible"

O console marca cada shape e volume elegível. Se não tem o selo, não cria. Teto por trás disso:

| Recurso | Limite Always Free | Uso previsto do projeto |
|---|---|---|
| Ampere A1 (`VM.Standard.A1.Flex`) | 2 OCPU / 12 GB, 1–2 instâncias | 1 instância, 2 OCPU / 12 GB |
| Block volume (boot + block) | **200 GB no total**, mínimo 47 GB de boot | 1 boot de 50 GB + 1 block de 150 GB |
| Backups de volume | 5 no total | 1 do boot, semanal |
| Egress | 10 TB/mês | upload pro YouTube: irrelevante |
| Object Storage | 20 GB (contas free-only) | não usar |
| Load balancer | 1 flexível, 10 Mbps | não usar |

A soma de boot + block **não pode passar de 200 GB** — é o único limite que este projeto chega perto de encostar.

### 3. Orçamento com alerta em US$ 1

`Billing & Cost Management → Budgets`: criar orçamento de US$ 1 no compartimento raiz, com alerta em 100% do valor **previsto e realizado**, disparando para o e-mail da conta. Numa conta Always Free o gasto é sempre US$ 0 — então qualquer e-mail desse alerta significa que algo saiu do free tier, e chega antes de virar fatura.

### 4. Conferência após provisionar

Depois de subir tudo, `Billing → Cost Analysis` filtrando o mês corrente. Tem que ser US$ 0,00 em todos os serviços. Repetir na primeira virada de mês, que é quando cobrança escondida aparece.

**Sobre a cobrança temporária no cartão:** a Oracle valida o cartão periodicamente com uma *authorization hold* (pré-autorização). Aparece na fatura como pendência e é liberada pelo banco em 3 a 5 dias. Não é cobrança e não vira fatura.

**O que eu não posso garantir:** mudança unilateral de política pela Oracle — foi exatamente o que aconteceu em junho/2026 com o corte do A1. A defesa contra isso é o alerta de orçamento e o backup do banco fora da Oracle (fase 6).

---

## Riscos conhecidos

| Risco | Probabilidade | Mitigação |
|---|---|---|
| `Out of host capacity` ao criar a A1 | **Alta** — em várias regiões é quase impossível provisionar na primeira tentativa | Script de retry (`oci-instance-creator`); tentar outro *fault domain*; em último caso, mudar a home region na criação da conta |
| **Reclamação por ociosidade** | Média | Instância com menos de 20% de CPU, rede e memória por 7 dias pode ser recuperada. O pipeline roda a cada 20 min com ffmpeg pesado, então normalmente passa — mas se a fila for pausada por semanas, o risco é real |
| Build ARM lento | Certa, uma vez | O Dockerfile compila whisper.cpp do zero; em 2 OCPU leva 10–20 min no primeiro build |
| Porta fechada mesmo com Security List liberada | Alta | As imagens da Oracle trazem regras de `iptables`/`firewalld` locais além da Security List da VCN. Precisa liberar **nos dois lugares** |
| Perda de dados na migração | Baixa | Dump do MySQL antes, restauração validada por contagem de linhas antes do cutover |

---

## Fases

Marcar o checkbox ao concluir. Cada fase termina com uma verificação objetiva.

### Fase 0 — Conta e blindagem de cobrança  ⬜ NÃO INICIADA

- [ ] Confirmar o tipo da conta no console (`Always Free` vs `Pay As You Go`)
- [ ] Se já existir instância: conferir o shape e, se estiver acima de 2 OCPU/12 GB, **redimensionar antes de 18/08/2026** (nunca terminar)
- [ ] Criar orçamento de US$ 1 com alerta em 100% previsto e realizado
- [ ] Registrar a home region da conta (todo recurso Always Free precisa nascer nela)

**Verificação:** `Cost Analysis` do mês corrente em US$ 0,00 e orçamento ativo.

### Fase 1 — Corrigir os vazamentos antes de migrar  🟡 EM ANDAMENTO (12–13/08/2026)

Migrar sem isso só transfere o problema: em ritmo normal, 8.5 GB de `_raw` a cada poucas semanas enche 150 GB do mesmo jeito.

- [x] Bug 2 — `<clip_id>_raw.mp4` apagado na finalização do vídeo fonte (12/08/2026, commit `5009112`)
- [x] Bug 5 — mesma varredura para `_subtitled.mp4` (12/08/2026)
- [x] Bug 9 — download falho apaga o arquivo e zera `local_path` (13/08/2026)
- [x] Bug 4, parte 1 — `recover_stuck_selecting` agora roda a cada 30 min e trata `local_path IS NULL` (13/08/2026)
- [ ] Bug 4, parte 2 — recuperação para `cutting`, `publishing` e `transcribing` ([`BUGS.md`](BUGS.md#4-parcial--estados-sem-recuperação-automática-seguram-arquivo-em-disco))
- [ ] Bug 11 — container não honra SIGTERM; todo restart pode criar estado preso novo
- [ ] Bug 10 — reconciliar os 287 `clip_path` que apontam para arquivo inexistente
- [ ] Limpeza retroativa do resíduo de `_raw`/`_subtitled` anterior a 12/08/2026
- [ ] Rebuild e validação local: `docker compose build clip-processor && docker compose up -d clip-processor`

**Verificação:** um ciclo completo de corte sem deixar `_raw`/`_subtitled` para trás.

Os bugs 4 e 11 são os que mais importam para a migração: numa instância de 2 OCPU o corte é mais lento,
a janela de tempo para o processo morrer no meio de um `cutting` cresce, e sem recuperação automática
cada ocorrência segura arquivo em 150 GB dedicados em vez de 228 GB compartilhados.

### Fase 2 — Provisionar a instância  ⬜ NÃO INICIADA

- [ ] VM `VM.Standard.A1.Flex`, 2 OCPU / 12 GB, imagem **Ubuntu 24.04 ARM** (ou Oracle Linux 9 ARM)
- [ ] Boot volume 50 GB
- [ ] Block volume 150 GB, anexado e montado em `/mnt/videos` (soma 200 GB — no teto exato)
- [ ] Chave SSH guardada fora da máquina de desenvolvimento
- [ ] Security List: liberar 22 (SSH) e 443; **não** expor 3306 nem 6379
- [ ] Liberar as mesmas portas no firewall local da imagem (`iptables`/`firewalld`)

**Verificação:** SSH conecta e `lsblk` mostra os 150 GB montados.

### Fase 3 — Compose próprio, sem os outros projetos  ⬜ NÃO INICIADA

O `docker-compose.yml` atual vive na raiz `wordpress/` e é **compartilhado com kelnab, feeb, placebeads, riodelux e gringo**. Nada disso vai para a Oracle.

- [ ] Escrever um `docker-compose.yml` novo, só com `clip-processor`, `mysql`, `redis`, `nginx`, `php`
- [ ] Apontar os volumes de vídeo para `/mnt/videos` (o block volume, não o boot)
- [ ] Conferir imagens com suporte arm64 (`mysql:8.4` e `redis:alpine` têm)
- [ ] `.env` novo no servidor, com segredos **regerados** — não copiar senha de desenvolvimento para produção

**Verificação:** `docker compose up -d` sobe os 5 serviços e `docker compose ps` mostra todos healthy.

### Fase 4 — Dados e segredos  ⬜ NÃO INICIADA

- [ ] Dump: `mysqldump ... clips_automation` completo, incluindo as tabelas do painel
- [ ] Restaurar no servidor e **conferir contagem de linhas tabela a tabela**
- [ ] Aplicar `mysql/init/01..07` se o dump não trouxer o schema (as tabelas do pipeline **não** são migrations do Laravel — `php artisan migrate:fresh` não as reconstrói)
- [ ] Copiar `youtube/token-*.json` (OAuth por canal-destino) e `branding/watermark-*.png`
- [ ] **Não migrar os vídeos.** São transitórios: raws são apagados após publicar, e o backlog rebaixa sozinho pelo RSS

**Verificação:** painel no servidor lista os mesmos canais e clips que o local.

### Fase 5 — Acesso ao painel  ⬜ NÃO INICIADA

Hoje o acesso é pelo vhost `canaldecortes.local`, que só existe na máquina local.

- [ ] Escolher a forma de acesso: **Tailscale/WireGuard** (recomendado — nada exposto na internet) ou domínio + Let's Encrypt
- [ ] Ajustar `LARAVEL_HOST_HEADER` e o vhost do nginx para o novo hostname
- [ ] Confirmar que o sidecar (8090) continua **sem porta publicada**, alcançável só pela rede `internal`

**Verificação:** login no painel a partir de outra máquina, e `curl` externo na 8090 falhando.

### Fase 6 — Cutover  ⬜ NÃO INICIADA

- [ ] Parar o `clip-processor` local (evita dois pipelines publicando no mesmo canal e queimando cota em dobro)
- [ ] Rodar 24h só no servidor, acompanhando `docker compose logs`
- [ ] Conferir: download acontece, corte acontece, upload acontece, cota respeitada
- [ ] Backup do MySQL agendado **para fora da Oracle** (a política deles já mudou uma vez)
- [ ] Só então liberar o espaço na máquina local

**Verificação:** um clip publicado de ponta a ponta pelo servidor.

---

## Depois da migração

- A máquina local fica só com código; o `docker-compose.yml` compartilhado da raiz `wordpress/` continua servindo os outros projetos, sem o `clip-processor`
- Reavaliar o MySQL HeatWave Always Free se o block volume passar de ~70% de uso
- Manter o alerta de orçamento ativo para sempre

---

## Fontes

- [Always Free Resources — Oracle Docs](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)
- [FAQ on Oracle's Cloud Free Tier](https://www.oracle.com/cloud/free/faq/)
- [Oracle Cloud Infrastructure Free Tier — Docs](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm)
- [Oracle Quietly Halves Free Tier Ampere A1 Compute Limits — InfoQ](https://www.infoq.com/news/2026/07/oracle-cloud-free-tier-limits/)
- [Oracle Cloud free tier 2026: 4 OCPU/24GB cut to 2 OCPU/12GB — TerminalBytes](https://terminalbytes.com/oracle-cloud-free-tier-changes-2026/)
- [Creating and Connecting to a HeatWave MySQL Always Free Instance](https://blogs.oracle.com/mysql/heatwave-mysql-always-free-tier)
- [Supabase Free Tier Limits in 2026](https://www.itpathsolutions.com/supabase-free-tier-limits)
- [Always-Free MySQL Database Hosting — Aiven](https://aiven.io/free-mysql-database)
