import { expect, test } from '@playwright/test';

import { mockCalls, props, resetMock, send, uniq, failMock } from './support/helpers';

type Src = {
    id: number;
    channelName: string;
    active: boolean;
    blacklisted: boolean;
    freshnessDays: number;
    inputPriority: number;
};
type Dst = { id: number; slug: string; name: string; active: boolean };

test.describe.configure({ mode: 'serial' });
test.beforeEach(async () => resetMock());

const sources = async (page: any) => (await props<{ channels: Src[] }>(page, '/painel/canais-fonte')).channels;
const dests = async (page: any) => (await props<{ channels: Dst[] }>(page, '/painel/canais-destino')).channels;

test.describe('canais fonte', () => {
    test('lista o canal semeado', async ({ page }) => {
        await page.goto('/painel/canais-fonte');
        await expect(page.locator('body')).toContainText('Fonte E2E');
    });

    test('filtra por aba de nicho', async ({ page }) => {
        const r = await props<{ channels: Src[] }>(page, '/painel/canais-fonte?tab=inexistente');
        expect(r.channels).toHaveLength(0);
    });

    test('atualiza freshness, prioridade, ativo e blacklist', async ({ page }) => {
        const c = (await sources(page)).find((x) => x.channelName === 'Fonte E2E')!;
        const url = `/painel/canais-fonte/${c.id}`;
        expect(
            (
                await send(page, 'PUT', url, { freshness_days: 3, input_priority: 5, active: false, blacklisted: true })
            ).status(),
        ).toBe(302);
        const u = (await sources(page)).find((x) => x.id === c.id)!;
        expect(u).toMatchObject({ freshnessDays: 3, inputPriority: 5, active: false, blacklisted: true });
        await send(page, 'PUT', url, { freshness_days: 1500, input_priority: 0, active: true, blacklisted: false });
    });

    test('valida limites de prioridade e freshness', async ({ page }) => {
        const c = (await sources(page))[0];
        const url = `/painel/canais-fonte/${c.id}`;
        expect((await send(page, 'PUT', url, { input_priority: 99 }, { json: true })).status()).toBe(422);
        expect((await send(page, 'PUT', url, { freshness_days: 7 }, { json: true })).status()).toBe(422);
    });

    test('adicionar canal resolve a URL no processor e cria o registro', async ({ page }) => {
        const res = await send(page, 'POST', '/painel/canais-fonte', {
            url: 'https://www.youtube.com/@resolvido-e2e',
            target_niche: 'futebol',
        });
        expect(res.status()).toBe(302);
        expect((await mockCalls()).some((c) => c.path === '/internal/resolve-channel')).toBe(true);
    });

    test('URL não resolvida volta erro de validação sem criar canal', async ({ page }) => {
        await failMock('/internal/resolve-channel', 422);
        const before = (await sources(page)).length;
        await send(page, 'POST', '/painel/canais-fonte', { url: 'https://x.test/ruim', target_niche: 'futebol' });
        expect((await sources(page)).length).toBe(before);
    });

    test('campos obrigatórios', async ({ page }) => {
        expect((await send(page, 'POST', '/painel/canais-fonte', {}, { json: true })).status()).toBe(422);
    });

    test('excluir canal fonte', async ({ page }) => {
        const c = (await sources(page)).find((x) => x.channelName === 'Canal Resolvido E2E');
        test.skip(!c, 'canal criado no teste anterior não existe');
        expect((await send(page, 'DELETE', `/painel/canais-fonte/${c!.id}`)).status()).toBe(302);
        expect((await sources(page)).some((x) => x.id === c!.id)).toBe(false);
    });
});

test.describe('canais destino', () => {
    test('lista o canal semeado', async ({ page }) => {
        await page.goto('/painel/canais-destino');
        await expect(page.locator('body')).toContainText('Destino E2E');
    });

    test('CRUD completo', async ({ page }) => {
        const slug = uniq('e2e').toLowerCase();
        const created = await send(page, 'POST', '/painel/canais-destino', {
            slug,
            name: 'Canal Novo E2E',
            niche: 'futebol',
            youtube_channel_id: `UC${uniq('x')}`,
            credit_template: 'Via {channel_handle}',
        });
        expect(created.status()).toBe(302);
        const c = (await dests(page)).find((x) => x.slug === slug)!;
        expect(c.name).toBe('Canal Novo E2E');

        expect(
            (
                await send(page, 'PUT', `/painel/canais-destino/${c.id}`, { name: 'Renomeado E2E', active: false })
            ).status(),
        ).toBe(302);
        const u = (await dests(page)).find((x) => x.id === c.id)!;
        expect(u).toMatchObject({ name: 'Renomeado E2E', active: false });

        expect((await send(page, 'DELETE', `/painel/canais-destino/${c.id}`)).status()).toBe(302);
        expect((await dests(page)).some((x) => x.id === c.id)).toBe(false);
    });

    test('slug duplicado é recusado', async ({ page }) => {
        const res = await send(
            page,
            'POST',
            '/painel/canais-destino',
            {
                slug: 'e2e-destino',
                name: 'Dup',
                niche: 'futebol',
                youtube_channel_id: uniq('UCdup'),
            },
            { json: true },
        );
        expect(res.status()).toBe(422);
    });

    test('campos obrigatórios', async ({ page }) => {
        expect((await send(page, 'POST', '/painel/canais-destino', {}, { json: true })).status()).toBe(422);
    });

    test('watermark inexistente responde 404', async ({ page }) => {
        const c = (await dests(page))[0];
        expect((await page.request.get(`/painel/canais-destino/${c.id}/watermark`)).status()).toBe(404);
    });

    test('upload de watermark rejeita arquivo que não é imagem', async ({ page }) => {
        const c = (await dests(page))[0];
        const cookies = await page.context().cookies();
        const token = decodeURIComponent(cookies.find((k) => k.name === 'XSRF-TOKEN')?.value ?? '');
        const res = await page.request.post(`/painel/canais-destino/${c.id}/watermark`, {
            headers: { 'X-XSRF-TOKEN': token, Accept: 'application/json' },
            multipart: { watermark: { name: 'x.txt', mimeType: 'text/plain', buffer: Buffer.from('nao sou imagem') } },
        });
        expect(res.status()).toBe(422);
    });
});

test.describe('nichos', () => {
    test('cria nicho e recusa slug repetido', async ({ page }) => {
        const slug = uniq('nicho').toLowerCase();
        expect((await send(page, 'POST', '/painel/niches', { slug, label: 'Nicho E2E' })).status()).toBe(302);
        expect(
            (await send(page, 'POST', '/painel/niches', { slug, label: 'Nicho E2E' }, { json: true })).status(),
        ).toBe(422);
    });
});
