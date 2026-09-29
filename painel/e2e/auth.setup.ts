import { expect, test as setup } from '@playwright/test';

import { EMAIL, openLogin, PASSWORD } from './credentials';

setup('autentica o operador e guarda a sessão', async ({ page }) => {
    await openLogin(page);
    await page.locator('#email').fill(EMAIL);
    await page.locator('#password').fill(PASSWORD);
    await page.getByRole('button', { name: 'Entrar' }).click();
    await expect(page).toHaveURL(/\/painel/);
    await page.context().storageState({ path: 'e2e/.auth/user.json' });
});
