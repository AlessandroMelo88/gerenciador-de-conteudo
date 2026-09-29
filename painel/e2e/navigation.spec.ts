import { expect, test } from '@playwright/test';

import { PAGES } from './credentials';

// Toda tela autenticada tem que abrir sem erro de servidor nem exceção de JS no navegador.
for (const [path, marker] of PAGES) {
    test(`abre ${path} sem erros`, async ({ page }) => {
        const jsErrors: string[] = [];
        page.on('pageerror', (e) => jsErrors.push(e.message));

        const res = await page.goto(path);
        expect(res?.status(), `status de ${path}`).toBeLessThan(400);
        await expect(page).toHaveURL(new RegExp(path.replace(/\//g, '\\/')));
        await expect(page.locator('body')).toContainText(new RegExp(marker, 'i'));
        await expect(page.locator('text=Server Error')).toHaveCount(0);
        expect(jsErrors, `erros de JS em ${path}`).toEqual([]);
    });
}

test('a sidebar leva às seções principais', async ({ page }) => {
    await page.goto('/painel');
    await page
        .getByRole('link', { name: /Vídeos/ })
        .first()
        .click();
    await expect(page).toHaveURL(/\/painel\/videos/);
    await page
        .getByRole('link', { name: /Canais Fonte/ })
        .first()
        .click();
    await expect(page).toHaveURL(/\/painel\/canais-fonte/);
});

test('POST sem token CSRF é recusado', async ({ page, request }) => {
    await page.goto('/painel');
    const res = await request.post('/painel/niches', { data: { slug: 'x', label: 'x' }, maxRedirects: 0 });
    expect([302, 401, 403, 419]).toContain(res.status());
});
