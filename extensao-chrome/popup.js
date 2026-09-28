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

async function enviar(url) {
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

  const resp = await fetch(`${API}/transcrever`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, cookies }),
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

  if (!(await macLigado())) {
    mostra('mac', 'O worker do Mac não respondeu. Ele precisa estar ligado.', 'erro');
    return;
  }
  mostra('mac', 'Mac pronto. Você precisa estar logado neste site.', 'ok');
  $('enviar').disabled = false;

  $('enviar').addEventListener('click', async () => {
    $('enviar').disabled = true;
    mostra('resultado', 'Enviando…');
    try {
      const { dados } = await enviar(url);
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
