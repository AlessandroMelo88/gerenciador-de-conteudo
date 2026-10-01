# Progresso — o que foi feito e o que falta

**Atualizado em 01/10/2026.** Produção: commit `99fbba4`, VM A1, no ar em https://toolscut.alessandromelo.com.br.
Esta página responde duas perguntas: **o que já está pronto** e **o que ainda falta**. Para o detalhe técnico
siga o link da coluna "Onde está". Para a conversa de "onde paramos", veja [`ESTADO-DO-PROJETO.md`](ESTADO-DO-PROJETO.md).
Índice de todos os documentos: [`README.md`](README.md).

**Como ler:** FEITO = no ar em produção · EM ANDAMENTO = começou, falta terminar · IDEIA = escrito, não implementado ·
PENDÊNCIA DO DONO = só você consegue fazer · OBSOLETO = superado, guardado em `historico/`.

---

## 1. FEITO (em produção)

| Item | Quando / commit | Onde está documentado | O que falta |
|---|---|---|---|
| Pipeline completo: descobre vídeo no RSS, baixa, transcreve, escolhe cortes com IA, corta, legenda e publica | desde 17/06/2026 | [`sistema/SISTEMA-CLIP-PROCESSOR.md`](sistema/SISTEMA-CLIP-PROCESSOR.md) | nada |
| Painel web (Laravel + React + shadcn) com fila de aprovação | ago/2026, `dca6e44` | [`sistema/SISTEMA-PAINEL.md`](sistema/SISTEMA-PAINEL.md) | nada |
| Correção de vazamento de disco e estados presos (bugs 1, 2, 5, 9, 12, 13, 14, 15, 16) | ago–set/2026 | [`operacao/BUGS.md`](operacao/BUGS.md) | nada |
| Bugs 11 (SIGTERM), 4 (recuperação de `cutting`/`publishing`/`transcribing`) e 17 (vaga presa por aprovação) | 01/10/2026, `99fbba4` | [`operacao/BUGS.md`](operacao/BUGS.md) | vigiar: `cutting` volta a `pending_cut` após 3 h sem atualização |
| Direitos autorais: curso concluído, decisão de não contestar, emissoras desativadas, política só corta MBL | 14–17/09/2026 | [`planos/PLANO-MESTRE.md`](planos/PLANO-MESTRE.md) | gate de licença e separar contas Google ficaram fora (ver seção 3) |
| Migração para a VM A1 (12 GB) com PostgreSQL 17 e disco de vídeos dedicado | 17/09/2026 | [`planos/MIGRACAO-A1.md`](planos/MIGRACAO-A1.md), [`planos/PLANO-POSTGRES.md`](planos/PLANO-POSTGRES.md) | DNS da Cloudflare, desligar a VM antiga, reverter adaptações para 1 GB, trocar comandos `mysql` por `psql` no RUNBOOK |
| Justiça por canal na fila de download (teto de 2 vídeos por canal de origem) | 17/09/2026, `d0319a8` | [`sistema/SISTEMA-DOWNLOAD.md`](sistema/SISTEMA-DOWNLOAD.md) | nada |
| Afiliados: ofertas, API com token, worker local, link rastreável, tela de performance, divulgação no Telegram, tema Umbrella | 18/09/2026, `c11b974` | [`sistema/SISTEMA-AFILIADOS.md`](sistema/SISTEMA-AFILIADOS.md) | **o sistema está vazio: 0 ofertas** (ver seção 4) |
| Transcrições (base de conhecimento) + extensão do Chrome + download de aula | 17–18/09/2026 | [`sistema/SISTEMA-TRANSCRICAO.md`](sistema/SISTEMA-TRANSCRICAO.md) | contexto de estudo (ver seção 3) |
| Transcrição de aula do Hotmart (áudio HLS pela Panda Video), validada numa aula real | 30/09–01/10/2026, `ace7714`, `51860e1` | [`sistema/SISTEMA-TRANSCRICAO.md`](sistema/SISTEMA-TRANSCRICAO.md) | outro player de vídeo exige ajuste de host na extensão |
| Vídeo longo por canal destino (`auto`, `short_only`, `both`) com cota de até 10 uploads/dia (6 Shorts + 4 longos), espaçamento de 15 min, revezamento entre canais-fonte e teto de longos aguardando | 01/10/2026, `59b0eb1` | [`planos/PLANO-LONGO-POR-CANAL.md`](planos/PLANO-LONGO-POR-CANAL.md) | acompanhar o resultado; só o futebol está em `both` |
| Métricas de visualização: coleta a cada hora pela API do YouTube e tela `/painel/metricas` (por formato e por canal-fonte) | 01/10/2026, `59b0eb1` | [`sistema/SISTEMA-PUBLICACAO.md`](sistema/SISTEMA-PUBLICACAO.md) | esperar alguns dias de dados; depois usar para decidir prioridade dos canais-fonte |
| Busca nas transcrições: texto, semântica e híbrida (pgvector, embedder) | 30/09/2026, `74e0e57` | [`sistema/SISTEMA-BUSCA-TRANSCRICOES.md`](sistema/SISTEMA-BUSCA-TRANSCRICOES.md), [`adr/0001`](adr/0001-busca-vetorial-nas-transcricoes.md) | nada; transcrições novas ganham vetor sozinhas |
| Lotes 1–9 da branch do Ricardo: prompts por perfil, render de qualidade, frescor e prioridade por canal-fonte, mídia por canal, CI, Makefile, ADRs | 30/09/2026, `ace7714` | [`sistema/SISTEMA-FRESCOR-E-PRIORIDADE.md`](sistema/SISTEMA-FRESCOR-E-PRIORIDADE.md), [`sistema/SISTEMA-MIDIA-POR-CANAL.md`](sistema/SISTEMA-MIDIA-POR-CANAL.md), [`operacao/DESENVOLVIMENTO.md`](operacao/DESENVOLVIMENTO.md) | perfil real do MBL (ver seção 2) e ligar o `CI gate` na proteção da `master` |
| Watchdog sem falso deadlock quando a janela está cheia por clip aguardando aprovação | 30/09/2026, `08dfed9` | [`sistema/SISTEMA-ALERTAS-E-MONITORAMENTO.md`](sistema/SISTEMA-ALERTAS-E-MONITORAMENTO.md) | nada |
| Webhook do Telegram com segredo e token do bot rotacionado | 30/09/2026, `e09912b` | [`ESTADO-DO-PROJETO.md`](ESTADO-DO-PROJETO.md) §8 | resta o token antigo no histórico público do git (inofensivo depois de rotacionado) |

## 2. EM ANDAMENTO

| Item | Onde está documentado | O que falta |
|---|---|---|
| Primeira oferta real de afiliado (fase atual do projeto: sair da dependência do YouTube) | [`sistema/SISTEMA-AFILIADOS.md`](sistema/SISTEMA-AFILIADOS.md), [`planos/PLANO-MESTRE.md`](planos/PLANO-MESTRE.md) | cadastrar a oferta, aprovar, copiar o link rastreável e conferir o clique |
| Divulgação automática no Telegram | [`planos/PLANO-MESTRE.md`](planos/PLANO-MESTRE.md) (fase 8) | criar os canais e pôr o bot como administrador |
| Marca Umbrella Solutions (tema já troca pelo host) | [`planos/PLANO-MESTRE.md`](planos/PLANO-MESTRE.md) (fase 7), [`sistema/SISTEMA-AFILIADOS.md`](sistema/SISTEMA-AFILIADOS.md) | DNS, vhost, certificado e logo |
| Integração da branch do Ricardo (`release/rico`): lotes 1–9 em produção; PR #1 comentada e fechada em 01/10/2026 | [`ESTADO-DO-PROJETO.md`](ESTADO-DO-PROJETO.md) §6 | nada pendente; ficou de fora por decisão: vídeo longo automático sem chave, filtro de palavrão que reprova, Fact Check, tópicos por assunto, Hacker Libertário, cron nativo |
| Perfil de prompt do MBL (lote 6) | [`planos/PLANO-PROMPTS-EDITAVEIS.md`](planos/PLANO-PROMPTS-EDITAVEIS.md) | escrever `prompts/channels/mbl.yaml`, compilar com `--apply`, ligar o perfil no painel |
| Bugs abertos: 6 (painel não apaga backlog de download), 8 (Docker Desktop sob disco cheio), 10 (287 `clip_path` sem arquivo) | [`operacao/BUGS.md`](operacao/BUGS.md) | decidir se entram agora; o bug 8 pode estar superado pela VM nova; o número do bug 10 não foi reconferido na A1 |
| Pendências da migração A1 | [`planos/MIGRACAO-A1.md`](planos/MIGRACAO-A1.md) | registro A da Cloudflare, desligar a VM Micro, reverter adaptações de 1 GB, atualizar comandos `mysql` nos docs |

## 3. PLANEJADO / IDEIA (escrito, não implementado)

| Item | Onde está documentado | O que falta |
|---|---|---|
| Revisão de palavrão antes de publicar: lista com minutagem, escolha por clip, áudio censurado | [`planos/PLANO-REVISAO-DE-PALAVRAO.md`](planos/PLANO-REVISAO-DE-PALAVRAO.md) | decisão do dono para entrar; hoje nada implementado |
| Prompts de IA editáveis pelo painel, com métricas por versão | [`planos/PLANO-PROMPTS-EDITAVEIS.md`](planos/PLANO-PROMPTS-EDITAVEIS.md) | editor, versionamento no banco e métricas (os perfis em YAML do lote 6 cobrem só parte) |
| Deploy automático diário às 6h, sem reiniciar no meio de um corte | [`planos/CI-CD.md`](planos/CI-CD.md) | escolher a opção, gerar chave SSH só do deploy, modo não interativo no `deploy.sh` (o bug 11 que bloqueava já foi corrigido) |
| Gate de licença por canal-fonte (`license_status`) e kill switch | [`planos/PLANO-MESTRE.md`](planos/PLANO-MESTRE.md) (fases 1–3) | nunca implementado; a política atual (só MBL) reduziu a urgência |
| Contexto de estudo nas transcrições: curso, seção, resumo e tópicos por IA | [`historico/RETOMADA-TRANSCRICOES.md`](historico/RETOMADA-TRANSCRICOES.md) | tudo |
| Descrições automáticas e blog; cursos e produto próprio | [`planos/PLANO-MESTRE.md`](planos/PLANO-MESTRE.md) (fases 8–9) | tudo |
| Separar as contas Google dos dois canais | [`planos/PLANO-MESTRE.md`](planos/PLANO-MESTRE.md) | adiado em 16/09/2026 |
| Monitor do Better Stack por palavra-chave (pega página em branco com status 200) | [`ESTADO-DO-PROJETO.md`](ESTADO-DO-PROJETO.md) §5–6 | sugerido, não feito |
| Teto separado para clip aguardando aprovação (alternativa do bug 17) | [`operacao/BUGS.md`](operacao/BUGS.md) | decisão de produto |

## 4. PENDÊNCIA DO DONO (só você faz)

| Item | Onde está documentado | O que falta |
|---|---|---|
| Cadastrar a primeira oferta de afiliado e testar o caminho inteiro | [`ESTADO-DO-PROJETO.md`](ESTADO-DO-PROJETO.md) §0 | você escolher a oferta |
| Criar os canais do Telegram e pôr o bot como administrador | [`ESTADO-DO-PROJETO.md`](ESTADO-DO-PROJETO.md) §6 | você criar os canais |
| DNS da Umbrella e do `toolscut` na Cloudflare, certificado e logo | [`planos/MIGRACAO-A1.md`](planos/MIGRACAO-A1.md), [`ESTADO-DO-PROJETO.md`](ESTADO-DO-PROJETO.md) §6 | acesso ao DNS |
| Ligar o `CI gate` na proteção da `master` no GitHub | [`operacao/DESENVOLVIMENTO.md`](operacao/DESENVOLVIMENTO.md) | configuração no GitHub |
| Confirmar a rotação do token do Telegram no BotFather (checkpoint de 30/09 diz que foi feita) | [`ESTADO-DO-PROJETO.md`](ESTADO-DO-PROJETO.md) §6 e §8 | conferir e dar baixa |
| Trocar a senha da conta da Asimov (passou em texto puro pelo chat em 17/09) | [`historico/RETOMADA-TRANSCRICOES.md`](historico/RETOMADA-TRANSCRICOES.md) | trocar a senha |
| Decidir se os contadores da barra lateral do painel (valores fixos no código) passam a contar de verdade | [`historico/RETOMADA-TRANSCRICOES.md`](historico/RETOMADA-TRANSCRICOES.md) | decisão |
| Apagar 3 branches locais já mescladas | [`ESTADO-DO-PROJETO.md`](ESTADO-DO-PROJETO.md) §6 | `git branch -d` das três |
| Reescrita do histórico do git (senhas antigas já rotacionadas) | [`operacao/BUGS.md`](operacao/BUGS.md) (bug 16) | adiada; decidir se vale |

## 5. OBSOLETO (guardado, não vale mais)

| Item | Onde está | Por que não vale |
|---|---|---|
| Plano de migração para a Oracle com MySQL | [`historico/PLANO-ORACLE.md`](historico/PLANO-ORACLE.md) | a migração foi feita de outro jeito (A1 + PostgreSQL) |
| Retomada de transcrições de 18/09/2026 | [`historico/RETOMADA-TRANSCRICOES.md`](historico/RETOMADA-TRANSCRICOES.md) | superada pelo checkpoint (itens ainda abertos estão acima) |
| Retomada da sessão do Claude Code de 15/09/2026 | [`historico/RETOMADA-SESSAO-CRON.md`](historico/RETOMADA-SESSAO-CRON.md) | agendamento de uma noite só |
| Retrato "estado atual" de agosto/2026 | [`historico/ESTADO-AGOSTO-2026.md`](historico/ESTADO-AGOSTO-2026.md) | descreve MySQL, migração não iniciada e bugs já corrigidos |
| VM antiga (E2.1.Micro, 1 GB) | [`planos/MIGRACAO-A1.md`](planos/MIGRACAO-A1.md) | virou proxy e rollback; será desligada |
| MySQL e Filament | [`adr/0007-postgresql-17-como-banco-unico.md`](adr/0007-postgresql-17-como-banco-unico.md) | substituídos por PostgreSQL 17 e React |
