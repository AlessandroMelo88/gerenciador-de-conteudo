// Lógica PURA da captura do player HLS (sem chamar chrome.*): testável com node.
// Usada pelo background.js (importScripts) e pelo popup.js (<script>).
(function (raiz) {
  // Hosts de onde o player puxa o .m3u8. O Hotmart serve o vídeo pela Panda Video
  // (*.tv.pandavideo.com.br), não por hotmart.com. Se aparecer outro domínio, ajuste aqui E em
  // host_permissions/urls do background.js, extensao_api.py (MEDIA_HOSTS_PADRAO) e no README.
  const SUFIXOS_PLAYER = ['hotmart.com', 'pandavideo.com.br'];
  // Páginas de aula que exigem captura (o yt-dlp não lê a página).
  const SUFIXOS_PAGINA = ['hotmart.com'];

  function hostDe(url) {
    try { return new URL(url).hostname.toLowerCase(); } catch { return ''; }
  }

  function hostPermitido(url, sufixos = SUFIXOS_PLAYER) {
    const h = hostDe(url);
    return !!h && sufixos.some((s) => h === s || h.endsWith('.' + s));
  }

  function ehPlaylist(url) {
    try { return new URL(url).pathname.toLowerCase().endsWith('.m3u8'); } catch { return false; }
  }

  // 2 = master (playlist.m3u8), 1 = qualquer outro .m3u8 (video.m3u8, variantes), 0 = não serve.
  function prioridade(url) {
    if (!ehPlaylist(url)) return 0;
    return new URL(url).pathname.toLowerCase().endsWith('/playlist.m3u8') ? 2 : 1;
  }

  // Decide se a captura nova substitui a guardada: o master nunca é trocado por variante;
  // mesma prioridade = a mais recente (aula nova no mesmo SPA).
  function escolher(atual, nova) {
    if (!nova || !prioridade(nova.media_url)) return atual || null;
    if (!atual) return nova;
    return prioridade(nova.media_url) >= prioridade(atual.media_url) ? nova : atual;
  }

  function cabecalho(headers, nome) {
    const h = (headers || []).find((x) => x.name.toLowerCase() === nome.toLowerCase());
    return h ? h.value : '';
  }

  // Monta a captura a partir do que o webRequest.onSendHeaders entrega.
  function capturaDe(detalhes, sufixos = SUFIXOS_PLAYER) {
    if (!detalhes || detalhes.tabId < 0) return null;
    if (!hostPermitido(detalhes.url, sufixos) || !prioridade(detalhes.url)) return null;
    return {
      media_url: detalhes.url,
      media_referer: cabecalho(detalhes.requestHeaders, 'Referer'),
      em: detalhes.timeStamp || Date.now(),
    };
  }

  // Só páginas do Hotmart exigem captura; no resto o yt-dlp lê a página normalmente.
  function exigeCaptura(urlDaAba) {
    return hostPermitido(urlDaAba, SUFIXOS_PAGINA);
  }

  const chaveDaAba = (tabId) => `captura:${tabId}`;

  const api = { SUFIXOS_PLAYER, SUFIXOS_PAGINA, hostPermitido, ehPlaylist, prioridade, escolher, capturaDe, exigeCaptura, chaveDaAba };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else raiz.Captura = api;
})(typeof self !== 'undefined' ? self : globalThis);
