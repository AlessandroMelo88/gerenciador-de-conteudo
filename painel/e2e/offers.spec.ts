import { expect, test } from '@playwright/test';

import { OFFER_SLUG } from './credentials';

test.describe('ofertas (afiliados)', () => {
    test('lista mostra a oferta semeada', async ({ page }) => {
        await page.goto('/painel/ofertas?status=approved');
        await expect(page.locator('body')).toContainText('Oferta E2E');
    });

    test('clique no link rastreável aparece em performance', async ({ page, request }) => {
        const res = await request.get(`/o/${OFFER_SLUG}?c=telegram`, { maxRedirects: 0 });
        expect(res.status()).toBe(302);
        await page.goto('/painel/ofertas/performance');
        await expect(page.locator('body')).toContainText(/Oferta E2E/);
    });
});
