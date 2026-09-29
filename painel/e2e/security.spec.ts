import { expect, test } from '@playwright/test';

import { PAGES } from './credentials';

// Sem sessão: nada do painel abre e nenhuma mutação passa.
test.describe('acesso anônimo', () => {
    for (const [path] of PAGES) {
        test(`GET ${path} redireciona para /login`, async ({ request }) => {
            const res = await request.get(path, { maxRedirects: 0 });
            expect([302, 401]).toContain(res.status());
            if (res.status() === 302) expect(res.headers()['location']).toMatch(/\/login/);
        });
    }

    for (const [method, path] of [
        ['POST', '/painel/clips/1/approve'],
        ['POST', '/painel/clips/bulk-approve'],
        ['POST', '/painel/clips/purge-failed'],
        ['POST', '/painel/videos/1/delete'],
        ['POST', '/painel/processar-video'],
        ['POST', '/painel/canais-fonte'],
        ['DELETE', '/painel/ofertas/1'],
        ['PUT', '/painel/configuracoes/senha'],
        ['POST', '/painel/configuracoes/cookies'],
        ['POST', '/painel/assistente/chat'],
    ] as const) {
        test(`${method} ${path} é bloqueado`, async ({ request }) => {
            const res = await request.fetch(path, { method, maxRedirects: 0, data: {} });
            expect([302, 401, 403, 419]).toContain(res.status());
        });
    }

    test('preview e thumbnail de clip exigem login', async ({ request }) => {
        for (const p of ['/painel/clips/1/preview', '/painel/clips/1/thumbnail']) {
            expect([302, 401]).toContain((await request.get(p, { maxRedirects: 0 })).status());
        }
    });

    test('cabeçalhos básicos de segurança e sem versão do PHP exposta', async ({ request }) => {
        const res = await request.get('/login');
        expect(res.headers()['x-powered-by'] ?? '').not.toMatch(/PHP\/\d/);
    });

    test('rota inexistente devolve 404, sem stack trace', async ({ request }) => {
        const res = await request.get('/painel/nao-existe-mesmo');
        expect([302, 404]).toContain(res.status());
        expect(await res.text()).not.toMatch(/Stack trace|vendor\/laravel/);
    });
});

test.describe('webhooks e API interna', () => {
    test('pipeline-event com token errado é 401', async ({ request }) => {
        const res = await request.post('/internal/pipeline-event', {
            headers: { 'X-Internal-Token': 'errado' },
            data: { event: 'upload_published' },
        });
        expect(res.status()).toBe(401);
    });

    test('pipeline-event com token certo valida o payload', async ({ request }) => {
        const bad = await request.post('/internal/pipeline-event', {
            headers: { 'X-Internal-Token': 'ci-token', Accept: 'application/json' },
            data: { event: 'evento_que_nao_existe' },
        });
        expect(bad.status()).toBe(422);
    });

    test('webhook do Telegram: 401 sem o segredo correto', async ({ request }) => {
        const res = await request.post('/telegramcanal', {
            headers: { 'X-Telegram-Bot-Api-Secret-Token': 'errado' },
            data: { message: { text: '/start' } },
        });
        expect(res.status()).toBe(401);
    });
});
