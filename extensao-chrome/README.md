# Extensão "Transcrever esta aula"

Um clique na página da aula e ela entra na base de conhecimento (aba **Transcrições** do painel).
Funciona em site com login (Hotmart, Asimov, Vimeo...) usando o login que você **já tem no Chrome**.

## Instalar (uma vez)

1. Chrome → `chrome://extensions`
2. Ligue **Modo do desenvolvedor** (canto superior direito)
3. **Carregar sem compactação** → escolha esta pasta (`extensao-chrome`)
4. Fixe o ícone na barra (ícone de quebra-cabeça → alfinete)

## Usar

Abra a aula logado → clique no ícone → **Transcrever**. O andamento aparece em Transcrições.

## Como funciona e o que sai do seu Mac

```
Chrome (aba da aula) ──link + sessão só deste site──> worker do Mac (127.0.0.1:8765)
                                                         ├─ sessão → ~/.config/canaldecortes/cookies.txt (600)
                                                         └─ link  → fila transcription_jobs (servidor)
```

- A sessão **não vai para o servidor** nem para o repositório: fica no `cookies.txt` do Mac.
- A extensão manda só os cookies do site da aba aberta, não os do navegador inteiro.
- A API local só aceita pedido de extensão (cabeçalho `Origin: chrome-extension://`); um site
  qualquer aberto no Chrome recebe `403`.
- O worker do Mac precisa estar ligado. Se não estiver, a extensão avisa.

Código do lado do Mac: `scripts/extensao_api.py`. Testes: `scripts/test_extensao_api.py`.

## Aulas do Hotmart (player HLS) — v1.1.0

O `yt-dlp` não lê a área de membros do Hotmart (página SPA). Por isso a extensão **observa** o
player e manda o endereço do áudio/vídeo (`.m3u8`) para o seu Mac:

1. Abra a aula logado e **dê play por uns 2 segundos** (é aí que o player pede o `.m3u8`).
2. Clique no ícone → **Transcrever**. Se o popup disser “Dê play no vídeo por 2 segundos e clique
   de novo”, é porque nada foi capturado nesta aba (recarregar a página apaga a captura: dê play de novo).

O que a extensão faz e não faz:

- `background.js` usa `chrome.webRequest` **só para observar** (sem bloquear nem alterar nada) e
  guarda, por aba, o último `.m3u8` (prefere o `playlist.m3u8` master) e o `Referer`. Fica em
  `chrome.storage.session` (some ao fechar o Chrome).
- Permissões: `cookies`, `activeTab`, `webRequest`, `storage`, e `host_permissions` **só**
  `*://*.hotmart.com/*`. Para qualquer outro site, o Chrome pede permissão **na hora do clique**
  (`optional_host_permissions`): aceite uma vez por site.
- O endereço do vídeo é assinado (vale como senha): vai só para o Mac, em
  `~/.config/canaldecortes/media-urls.json` (0600), **nunca** para o servidor ou o banco. Só o
  link da aula e o título entram na fila.
- Sem DRM: se a aula for protegida (Widevine etc.) o job falha dizendo isso. Não se contorna DRM.

### Atualizar / recarregar a extensão

1. `chrome://extensions` → no cartão da extensão, botão de recarregar (seta circular). Como o
   manifest mudou (service worker, permissões), confira se a versão mostrada é **1.1.0** e aceite
   as novas permissões se o Chrome pedir.
2. Reinicie o worker do Mac para ele entender o novo pedido:
   `launchctl kickstart -k gui/$(id -u)/com.canaldecortes.downloader`
3. Para depurar: no cartão da extensão, **service worker** abre o DevTools do `background.js`
   (aba Network/Console); recarregue a aula e veja se aparece o `playlist.m3u8`.

### Se o embed do Hotmart usar outro domínio

Ajuste o domínio em `manifest.json` (`host_permissions`), em `background.js` (`urls` do listener),
em `captura.js` (`SUFIXOS_PLAYER`) e, no Mac, `TRANSCRICAO_MEDIA_HOSTS`.

Testes da lógica pura: `node --test extensao-chrome/captura.test.js`.
