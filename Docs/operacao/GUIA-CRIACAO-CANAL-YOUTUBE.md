# Guia Operacional: Criação, Autenticação OAuth e Automação de Canal no YouTube

Este guia descreve o passo a passo completo para criar um canal no YouTube, configurar as credenciais no Google Cloud Console, gerar o token OAuth seguro e integrá-lo ao pipeline autônomo do **Canal de Cortes**.

---

## 1. Mapeamento de Contas e Canais

No projeto, os canais de destino são isolados por token e podem estar em contas Google distintas:

| Canal Destino | Slug | Nicho | Channel ID Oficial | Conta Google / E-mail | Status |
|---|---|---|---|---|---|
| **Futebol em Cortes** | `futebol-em-cortes` | `futebol` | `UCcyeBQFAkUNeDJbBM7JJqLw` | Money Intel | Ativo / Produção |
| **Fatos & Debates** | `fatos-e-debates` | `politica` | `UCCx9rlpbNdfLBTLqGah78cA` | Money Intel | Ativo / Produção |
| **Novo Canal** | *(definido na criação)* | `futebol` / `politica` / `podcast` | `UC...` | `alessandrobm1988@gmail.com` | Novo |
| **Ponto de Vista Cortes** | `pontodevista-cortes` | `podcast` | `UCXTo4hgJ3pLlpXO0qjyVh8A` | `@pontodevistacortes-wd` | Canal criado; falta token OAuth |

> ℹ️ **Nota sobre o "Podcast Cortes":** Foi inserido originalmente via `BaselineSeeder.php` como dado base de exemplo para a estrutura do banco de dados (com ID `UC_PLACEHOLDER_PODCAST`). Ele não existe no YouTube e pode ser excluído no painel sem afetar outros canais.

---

## 2. Passo 1: Criar o Canal no YouTube (Conta de Marca)

1. Acesse o [YouTube](https://www.youtube.com) logado na conta Google desejada (ex: `alessandrobm1988@gmail.com`).
2. Clique na sua foto de perfil > **Configurações** > **Adicionar ou gerenciar seus canais** > **Criar um canal**.
3. **Recomendação Fundamental:** Crie sempre como **Conta de Marca (Brand Account)** para permitir isolamento e segurança.
4. Defina Nome, `@handle`, foto de perfil e banner.
5. **Obter o YouTube Channel ID oficial (`UC...`):**
   - Acesse o [YouTube Studio](https://studio.youtube.com) do canal criado.
   - Vá em **Configurações > Canal > Configurações avançadas > Configurações de canal do YouTube** (ou acesse diretamente [youtube.com/account_advanced](https://www.youtube.com/account_advanced)).
   - Copie o **ID do canal** (começa com `UC`, 24 caracteres).
6. **Verificação por SMS (Obrigatória):**
   - No YouTube Studio > **Configurações > Canal > Qualificação para recursos**.
   - Ative os **Recursos intermediários** confirmando seu número de celular.
   - *Atenção:* Sem isso, o YouTube bloqueia o upload de miniaturas (thumbnails personalizadas) com erro 403 e força todos os vídeos a subirem como Privados.

---

## 3. Passo 2: Configurar o Google Cloud Console

1. Acesse o [Google Cloud Console](https://console.cloud.google.com).
2. Selecione ou crie um projeto (ex: `canal-de-cortes-...`).
3. Em **APIs e Serviços > Biblioteca**, ative:
   - **YouTube Data API v3** (para upload e gerenciamento dos vídeos)
   - **YouTube Analytics API** (para coleta de métricas de retenção diária - SPEC-001)
4. Em **APIs e Serviços > Tela de consentimento OAuth (OAuth consent screen)**:
   - Selecione **Externo (External)**.
   - Preencha Nome do app, e-mail de suporte e e-mail do desenvolvedor.
   - Adicione os **3 escopos obrigatórios**:
     - `https://www.googleapis.com/auth/youtube.upload`
     - `https://www.googleapis.com/auth/youtube.force-ssl`
     - `https://www.googleapis.com/auth/yt-analytics.readonly`
   - Em **Usuários de teste (Test users)**: adicione o e-mail da conta Google do canal.
   - *Dica:* Clique em **Publicar App** para evitar que o token expire a cada 7 dias.

---

## 4. Passo 3: Criar Credenciais OAuth (Desktop App)

1. Em **APIs e Serviços > Credenciais > + Criar Credenciais > ID do cliente OAuth**.
2. Tipo de aplicativo: **App para computador (Desktop application)**.
3. Baixe o JSON gerado e salve na pasta `youtube/` da raiz do repositório como:
   ```bash
   youtube/client_secret.json
   ```

---

## 5. Passo 4: Gerar o Token com Guard de Identidade (Anti-Bug 18)

> ⚠️ **ALERTA CRÍTICO:** Na tela de consentimento que abrir no navegador, **ESCOLHA A CONTA DE MARCA DO CANAL DESTINO**, e NUNCA a conta pessoal!
> (O script `generate_token_channel.py` valida o ID retornado via `channels.list(mine=True)` e aborta sem salvar se a conta for incorreta).

Execute na raiz do projeto:

```bash
cd /Users/alessandrobm1/develop/server/wordpress/canaldecortes
.venv/bin/python youtube/generate_token_channel.py --channel <slug-do-canal> --expect-channel-id <UC_ID_DO_CANAL>
```

Ou usando o atalho do Makefile (após adicionar o mapeamento no script):
```bash
make token-youtube CANAL=<slug-do-canal>
```

O arquivo será salvo permanentemente em:
```bash
youtube/token-<slug-do-canal>.json
```

---

## 6. Passo 5: Cadastrar o Canal no Painel

1. No painel web, acesse **Canais Destino** e clique em **+ Novo Canal Destino**.
2. Preencha:
   - **Nome do Canal:** Nome exibido no YouTube.
   - **Slug:** Exatamente o mesmo slug usado no nome do arquivo de token (`token-<slug>.json`).
   - **Nicho:** `futebol`, `politica` ou `podcast`.
   - **YouTube Channel ID:** O identificador `UC...`.
   - **Conta Google / E-mail:** E-mail vinculado (ex: `alessandrobm1988@gmail.com`).
   - **Formato dos Vídeos:** Automático, Só Shorts ou Shorts + Longo.
   - **Privacidade Padrão:** Privado ou Público.
3. Salve o cadastro. O badge "OAuth autorizado" ficará verde automaticamente.
4. No card do canal, clique em **Template 9:16** para personalizar estilo, cores de legenda e fazer upload da **Marca d'água (`watermark-<slug>.png`)**.

---

## 7. Passo 6: Cadastrar Canais Fonte de Abastecimento

1. Acesse **Canais Fonte** e clique em **+ Novo Canal Fonte**.
2. Cadastre canais com `@handle` (ex: `@flowpodcast`, `@mblivre`, `@geglobo`), URL ou Channel ID.
3. Associe ao **mesmo nicho** do canal de destino.
4. O robô varre o RSS a cada 20 minutos, baixa os vídeos, transcreve e corta automaticamente.

---

## 8. Passo 7: Sincronizar em Produção (VPS Oracle)

Envie o token para o servidor de produção:

```bash
scp -i ~/.ssh/oracle-a1-2026-09-16.key youtube/token-<slug-do-canal>.json ubuntu@129.80.236.185:/home/ubuntu/canaldecortes/youtube/
```

Para reiniciar o serviço em produção:

```bash
ssh -i ~/.ssh/oracle-a1-2026-09-16.key ubuntu@129.80.236.185 "cd /home/ubuntu/canaldecortes && docker compose restart clip-processor"
```

---

## 9. Passo 8: Publicação e Janelas Automáticas

- Os clipes cortados entram na **Fila de Aprovação** no Dashboard.
- Quando aprovados, o robô posta respeitando a cota diária do canal e as janelas nobres de publicação no Brasil (**12h–14h** e **19h–22h**).
- O Watchdog proativo monitora 24/7 tokens expirados, clipes fantasmas e espaço em disco, disparando alertas no Telegram e E-mail.
