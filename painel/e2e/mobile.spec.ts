import { expect, test } from '@playwright/test';

test.describe('viewport mobile', () => {
    for (const path of ['/painel', '/painel/ofertas', '/painel/canais-fonte']) {
        test(`${path} não estoura a largura`, async ({ page }) => {
            await page.goto(path);
            await expect(page.locator('body')).toBeVisible();
            const overflow = await page.evaluate(
                () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
            );
            expect(overflow).toBeLessThanOrEqual(1);
        });
    }
});
