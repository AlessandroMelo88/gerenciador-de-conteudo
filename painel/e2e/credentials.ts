import type { Page } from '@playwright/test';

// Espelha database/seeders/E2ESeeder.php — conta e oferta só existem em banco de teste.
export const EMAIL = 'e2e@canaldecortes.test';
export const PASSWORD = 'e2e-senha-segura-123';
export const OFFER_SLUG = 'e2eoffer';
export const OFFER_URL = 'https://go.hotmart.com/E2E-DESTINO';

export const PAGES: Array<[string, string]> = [
    ['/painel', 'Dashboard'],
    ['/painel/assistente', 'Assistente'],
    ['/painel/canais-destino', 'Canais'],
    ['/painel/canais-fonte', 'Canais'],
    ['/painel/videos', 'Vídeos'],
    ['/painel/processar-video', 'Processar'],
    ['/painel/transcricoes', 'Transcri'],
    ['/painel/links-uteis', 'Links'],
    ['/painel/documentacao', 'Document'],
    ['/painel/ofertas', 'Ofertas'],
    ['/painel/ofertas/performance', 'Performance'],
    ['/painel/configuracoes', 'Configura'],
];

/** Abre /login e espera o Inertia hidratar — sem isso o clique cai no submit nativo do form. */
export async function openLogin(page: Page) {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
}
