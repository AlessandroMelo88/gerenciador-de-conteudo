// Service worker: SÓ OBSERVA as requisições do player HLS (Hotmart) e guarda, por aba, o
// último .m3u8 (prefere o master) e o Referer que o player mandou. Não bloqueia nem
// altera nada (sem webRequestBlocking). O popup lê isto ao clicar em Transcrever.
importScripts('captura.js');

// storage.session: o service worker do MV3 é desligado com frequência; memória não basta.
// Fica só neste navegador (não sincroniza) e some ao fechar o Chrome.
const guardaSessao = chrome.storage.session;

chrome.webRequest.onSendHeaders.addListener(
  (detalhes) => {
    const nova = Captura.capturaDe(detalhes);
    if (!nova) return;
    const chave = Captura.chaveDaAba(detalhes.tabId);
    guardaSessao.get(chave).then((r) => {
      const escolhida = Captura.escolher(r[chave], nova);
      if (escolhida !== r[chave]) return guardaSessao.set({ [chave]: escolhida });
    });
  },
  { urls: ['*://*.hotmart.com/*'] },
  ['requestHeaders', 'extraHeaders'],
);

// Recarregou a página da aula: o player vai pedir tudo de novo, então descarta a antiga.
chrome.tabs.onUpdated.addListener((tabId, info) => {
  if (info.status === 'loading') guardaSessao.remove(Captura.chaveDaAba(tabId));
});
chrome.tabs.onRemoved.addListener((tabId) => guardaSessao.remove(Captura.chaveDaAba(tabId)));
