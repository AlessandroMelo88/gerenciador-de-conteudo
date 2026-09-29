import { expect, test } from '@playwright/test';

import { EMAIL, openLogin, PASSWORD } from './credentials';

test.describe('login', () => {
    test('visitante anônimo é mandado para /login', async ({ page }) => {
        await page.goto('/painel');
        await expect(page).toHaveURL(/\/login/);
        await expect(page.getByRole('button', { name: 'Entrar' })).toBeVisible();
    });

    test('a raiz redireciona deslogado para o login', async ({ page }) => {
        await page.goto('/');
        await expect(page).toHaveURL(/\/login/);
    });

    test('senha errada não entra e mostra erro', async ({ page }) => {
        await openLogin(page);
        await page.locator('#email').fill(EMAIL);
        await page.locator('#password').fill('senha-errada-999');
        await page.getByRole('button', { name: 'Entrar' }).click();
        await expect(page).toHaveURL(/\/login/);
        await expect(page.locator('p.text-destructive')).toBeVisible();
    });

    test('credencial correta entra, e logout volta ao login', async ({ page }) => {
        await openLogin(page);
        await page.locator('#email').fill(EMAIL);
        await page.locator('#password').fill(PASSWORD);
        await page.getByRole('button', { name: 'Entrar' }).click();
        await expect(page).toHaveURL(/\/painel/);

        const status = await page.evaluate(async () => {
            const token = decodeURIComponent(
                document.cookie
                    .split('; ')
                    .find((c) => c.startsWith('XSRF-TOKEN='))
                    ?.split('=')[1] ?? '',
            );
            const r = await fetch('/logout', {
                method: 'POST',
                headers: { 'X-XSRF-TOKEN': token },
                redirect: 'manual',
            });
            return r.type === 'opaqueredirect' ? 302 : r.status;
        });
        expect([200, 204, 302]).toContain(status);
        await page.goto('/painel');
        await expect(page).toHaveURL(/\/login/);
    });

    test('a página de login não expõe credencial pré-preenchida', async ({ page }) => {
        await openLogin(page);
        await expect(page.locator('#email')).toHaveValue('');
        await expect(page.locator('#password')).toHaveValue('');
    });
});
