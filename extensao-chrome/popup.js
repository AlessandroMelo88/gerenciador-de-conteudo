// Transcrever esta aula — manda o link da aba e a sessão DESTE site para o
// worker do Mac (127.0.0.1). Nada vai para o servidor: o worker guarda a sessão
// no cookies.txt local e só o link entra na fila do banco.

const API = 'http://127.0.0.1:8765';
const SEGUNDO_NIVEL = new Set(['com', 'net', 'org', 'gov', 'edu', 'co']);

// Mesma regra de scripts/extensao_api.py: hub.asimov.academy -> asimov.academy.
function siteDaAula(host) {
  const partes = host.toLowerCase().replace(/^\.+|\.+$/g, '').split('.');
  if (partes.length >= 3 && partes.at(-1).length === 2 && SEGUNDO_NIVEL.has(partes.at(-2))) {
    return partes.slice(-3).join('.');
  }
  return partes.slice(-2).join('.');
}

const $ = (id) => document.getElementById(id);

function mostra(id, texto, classe) {
  const el = $(id);
  el.textContent = texto;
  el.className = `${el.className.split(' ')[0]} ${classe || ''}`.trim();
}

async function abaAtual() {
  const [aba] = await chrome.tabs.query({ active: true, currentWindow: true });
  return aba;
}

async function macLigado() {
  try {
    const resp = await fetch(`${API}/status`, { signal: AbortSignal.timeout(2000) });
    return resp.ok;
  } catch {
    return false;
  }
}

// Captura do player HLS feita pelo background.js (só existe no Hotmart e similares).
async function capturaDaAba(aba) {
  const chave = Captura.chaveDaAba(aba.id);
  const r = await chrome.storage.session.get(chave);
  return r[chave] || null;
}

// Fora do Hotmart a extensão não tem acesso prévio ao site: pede na hora do clique
// (precisa do gesto do usuário). Se já foi concedido, resolve sem perguntar de novo.
async function garanteAcessoAoSite(site) {
  if (Captura.hostPermitido(`https://${site}/`)) return true;
  return chrome.permissions.request({ origins: [`*://*.${site}/*`] });
}

// Função injetada na página para ler o nome da aula e módulo do DOM real.
function extrairInfoDaPagina() {
  const host = window.location.hostname.toLowerCase();

  // 1. Hotmart Club
  if (host.includes('hotmart.com')) {
    let aula = '';
    let modulo = '';
    let curso = '';

    // Nome do curso
    const cursoEl =
      document.querySelector('header h1, header h2, [class*="course-name"], [class*="product-name"]') ||
      document.querySelector('.club-navigation__title, [data-testid*="product-title"]');
    if (cursoEl) curso = cursoEl.textContent.trim();
    if (!curso && document.title.includes('|')) {
      curso = document.title.split('|')[0].trim();
    }

    // Título da aula e módulo na área de conteúdo
    const titulos = Array.from(document.querySelectorAll('h1, h2, [class*="lesson-title"], [class*="content-title"]'));
    for (const el of titulos) {
      const txt = (el.textContent || '').trim();
      if (txt && !/^(voltar|informaç|menu|aulas|concluir)/i.test(txt) && txt.length > 3) {
        aula = txt;
        const anterior = el.previousElementSibling;
        if (anterior && anterior.textContent.trim() && !/voltar/i.test(anterior.textContent)) {
          modulo = anterior.textContent.trim();
        }
        break;
      }
    }

    // Se ainda não achou aula, busca na barra lateral pela aula ativa
    if (!aula) {
      const activeEl = document.querySelector('[class*="active"], [class*="playing"], [aria-current="true"]');
      if (activeEl) {
        aula = (activeEl.textContent || '').replace(/tocando agora/gi, '').trim();
      }
    }

    // Se ainda não achou módulo, busca o módulo aberto
    if (!modulo) {
      const modEl = document.querySelector('[class*="module"][class*="open"], [class*="section"][class*="active"], [class*="expanded"]');
      if (modEl) {
        const h = modEl.querySelector('h2, h3, [class*="title"], [class*="name"]');
        if (h) modulo = h.textContent.trim();
      }
    }

    const partes = [];
    if (modulo) partes.push(`[${modulo}]`);
    if (aula) partes.push(aula);
    if (!partes.length && document.title) partes.push(document.title.split('|')[0].trim());
    if (curso && !partes.join(' ').toLowerCase().includes(curso.toLowerCase())) {
      partes.push(`• ${curso}`);
    }

    return partes.join(' ').trim();
  }

  // 2. YouTube
  if (host.includes('youtube.com')) {
    const el = document.querySelector('h1.ytd-watch-metadata, #title h1, h1 yt-formatted-string');
    if (el && el.textContent.trim()) return el.textContent.trim();
  }

  // 3. Fallback genérico: h1 ou document.title limpo
  const h1 = document.querySelector('h1');
  if (h1 && h1.textContent.trim() && h1.textContent.trim().length > 3) {
    return h1.textContent.trim();
  }

  return document.title.split('|')[0].split(' - ')[0].trim();
}

async function enviar(url, aba, captura) {
  const site = siteDaAula(new URL(url).hostname);
  const cookies = (await chrome.cookies.getAll({ domain: site })).map((c) => ({
    domain: c.domain,
    path: c.path,
    secure: c.secure,
    httpOnly: c.httpOnly,
    hostOnly: c.hostOnly,
    name: c.name,
    value: c.value,
    expirationDate: c.expirationDate,
  }));

  const tituloFinal = $('titulo')?.value.trim() || aba.title || '';

  const resp = await fetch(`${API}/transcrever`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      url,
      cookies,
      title: tituloFinal,
      ...(captura ? { media_url: captura.media_url, media_referer: captura.media_referer } : {}),
    }),
  });
  return { status: resp.status, dados: await resp.json() };
}

(async () => {
  const aba = await abaAtual();
  const url = aba?.url || '';
  $('url').textContent = url;

  if (!/^https?:\/\//.test(url)) {
    mostra('mac', 'Abra a página da aula antes de clicar.', 'erro');
    return;
  }

  // Tenta extrair o título e módulo da aula diretamente do DOM
  let tituloDetectado = aba.title || '';
  try {
    if (chrome.scripting && aba.id) {
      const [exec] = await chrome.scripting.executeScript({
        target: { tabId: aba.id },
        func: extrairInfoDaPagina,
      });
      if (exec?.result) {
        tituloDetectado = exec.result;
      }
    }
  } catch {
    // Permissão restrita na aba ativa cai de volta no título da aba
  }
  if ($('titulo')) {
    $('titulo').value = tituloDetectado;
  }

  if (!(await macLigado())) {
    mostra('mac', 'O worker do Mac não respondeu. Ele precisa estar ligado.', 'erro');
    return;
  }
  mostra('mac', 'Mac pronto. Você precisa estar logado neste site.', 'ok');
  $('enviar').disabled = false;

  $('enviar').addEventListener('click', async () => {
    $('enviar').disabled = true;
    try {
      // Primeiro await do clique: o pedido de permissão exige o gesto do usuário.
      if (!(await garanteAcessoAoSite(siteDaAula(new URL(url).hostname)))) {
        mostra('resultado', 'Sem permissão para ler a sessão deste site. Clique de novo e aceite.', 'erro');
        $('enviar').disabled = false;
        return;
      }
      const captura = await capturaDaAba(aba);
      if (Captura.exigeCaptura(url) && !captura) {
        mostra('resultado', 'Dê play no vídeo por 2 segundos e clique de novo.', 'erro');
        $('enviar').disabled = false;
        return;
      }
      mostra('resultado', 'Enviando…');
      const { dados } = await enviar(url, aba, captura);
      if (dados.ok) {
        mostra('resultado', `Na fila (#${dados.job_id}). Acompanhe em Transcrições.`, 'ok');
      } else {
        mostra('resultado', dados.erro || 'Falhou.', 'erro');
        $('enviar').disabled = false;
      }
    } catch (e) {
      mostra('resultado', `Não consegui falar com o Mac: ${e.message}`, 'erro');
      $('enviar').disabled = false;
    }
  });
})();
