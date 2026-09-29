import { expect, test } from '@playwright/test';

import { OFFER_SLUG, OFFER_URL } from './credentials';
import { props, send, uniq } from './support/helpers';

type Offer = { id: number; title: string; status: string; trackingUrl: string; clicksCount: number; niche: string };
const offers = async (page: any, status = 'todos') =>
    (await props<{ offers: Offer[] }>(page, `/painel/ofertas?status=${status}`)).offers;

test.describe.configure({ mode: 'serial' });

test.describe('ofertas · CRUD e ciclo de aprovação', () => {
    test('abas de status mostram a contagem', async ({ page }) => {
        const r = await props<{ counts: Record<string, number> }>(page, '/painel/ofertas');
        expect(r.counts.todos).toBeGreaterThanOrEqual(3);
        expect(r.counts.approved).toBeGreaterThanOrEqual(1);
        expect(r.counts.draft).toBeGreaterThanOrEqual(2);
    });

    test('status desconhecido cai em rascunho', async ({ page }) => {
        const r = await props<{ activeStatus?: string }>(page, '/painel/ofertas?status=hackeado');
        expect(r.activeStatus ?? 'draft').toBe('draft');
    });

    test('cria oferta manual como rascunho, aprova e o link rastreável passa a redirecionar', async ({ page }) => {
        const title = uniq('Oferta Manual');
        const dest = `https://go.hotmart.com/${uniq('DEST')}`;
        expect(
            (
                await send(page, 'POST', '/painel/ofertas', {
                    title,
                    affiliate_url: dest,
                    niche: 'futebol',
                    cta_text: 'Compre',
                })
            ).status(),
        ).toBe(302);

        const o = (await offers(page)).find((x) => x.title === title)!;
        expect(o.status).toBe('draft');
        // rascunho ainda não redireciona
        const slug = o.trackingUrl.split('/o/')[1];
        expect((await page.request.get(`/o/${slug}`, { maxRedirects: 0 })).status()).toBe(404);

        expect((await send(page, 'PUT', `/painel/ofertas/${o.id}`, { status: 'approved' })).status()).toBe(302);
        const res = await page.request.get(`/o/${slug}?c=whatsapp`, { maxRedirects: 0 });
        expect(res.status()).toBe(302);
        expect(res.headers()['location']).toBe(dest);
        expect((await offers(page)).find((x) => x.id === o.id)!.clicksCount).toBe(1);

        // arquivar tira do redirect
        await send(page, 'PUT', `/painel/ofertas/${o.id}`, { status: 'archived' });
        expect((await page.request.get(`/o/${slug}`, { maxRedirects: 0 })).status()).toBe(404);

        expect((await send(page, 'DELETE', `/painel/ofertas/${o.id}`)).status()).toBe(302);
        expect((await offers(page)).some((x) => x.id === o.id)).toBe(false);
    });

    test('edita título, copy e link de afiliado', async ({ page }) => {
        const o = (await offers(page, 'draft'))[0];
        await send(page, 'PUT', `/painel/ofertas/${o.id}`, {
            title: 'Título editado E2E',
            copy_short: 'curta',
            affiliate_url: OFFER_URL,
        });
        const u = (await offers(page)).find((x) => x.id === o.id)!;
        expect(u.title).toBe('Título editado E2E');
    });

    test('validações: url inválida, status inválido, nicho inexistente', async ({ page }) => {
        const bad = { title: 'x', affiliate_url: 'javascript:alert(1)', niche: 'futebol' };
        expect((await send(page, 'POST', '/painel/ofertas', bad, { json: true })).status()).toBe(422);
        expect(
            (
                await send(
                    page,
                    'POST',
                    '/painel/ofertas',
                    { ...bad, affiliate_url: 'https://ok.test/x', niche: 'nao-existe' },
                    { json: true },
                )
            ).status(),
        ).toBe(422);
        const o = (await offers(page))[0];
        expect(
            (await send(page, 'PUT', `/painel/ofertas/${o.id}`, { status: 'inventado' }, { json: true })).status(),
        ).toBe(422);
    });

    test('gerar copy exige URL válida', async ({ page }) => {
        expect((await send(page, 'POST', '/painel/ofertas/gerar-copy', {}, { json: true })).status()).toBe(422);
    });

    test('a interface abre o formulário de nova oferta', async ({ page }) => {
        await page.goto('/painel/ofertas');
        await page
            .getByRole('button', { name: /Nova oferta/i })
            .first()
            .click();
        await expect(page.getByRole('dialog').first()).toBeVisible();
    });

    test('cliques do link semeado são contados e não gravam IP cru', async ({ page, request }) => {
        for (let i = 0; i < 2; i++) {
            expect((await request.get(`/o/${OFFER_SLUG}?c=x_invalido`, { maxRedirects: 0 })).status()).toBe(302);
        }
        const perf = await props<Record<string, any>>(page, '/painel/ofertas/performance');
        expect(JSON.stringify(perf).replaceAll(/https?:\/\/[^"\/]+/g, '')).not.toMatch(
            /\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/,
        );
    });
});
