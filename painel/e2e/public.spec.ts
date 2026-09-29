import { expect, test } from '@playwright/test';

import { OFFER_SLUG, OFFER_URL } from './credentials';

test.describe('rotas públicas', () => {
    test('/o/{slug} redireciona 302 para o link de afiliado', async ({ request }) => {
        const res = await request.get(`/o/${OFFER_SLUG}?c=telegram`, { maxRedirects: 0 });
        expect(res.status()).toBe(302);
        expect(res.headers()['location']).toBe(OFFER_URL);
    });

    test('/o/{slug} não usa cookie de sessão (hot path leve)', async ({ request }) => {
        const res = await request.get(`/o/${OFFER_SLUG}`, { maxRedirects: 0 });
        expect(res.headers()['set-cookie'] ?? '').not.toContain('session');
    });

    test('slug inexistente responde 404', async ({ request }) => {
        const res = await request.get('/o/naoexiste9', { maxRedirects: 0 });
        expect(res.status()).toBe(404);
    });

    test('webhook do Telegram recusa chamada sem segredo', async ({ request }) => {
        const res = await request.post('/telegramcanal', { data: {} });
        expect([401, 403, 404]).toContain(res.status());
    });

    test('evento interno do pipeline recusa chamada sem token', async ({ request }) => {
        const res = await request.post('/internal/pipeline-event', { data: {} });
        expect([401, 403]).toContain(res.status());
    });
});
