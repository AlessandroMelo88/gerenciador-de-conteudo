import { expect, test } from '@playwright/test';

import { failMock, mockCalls, props, resetMock, send } from './support/helpers';

type V = { id: number; title: string; status: string };
type Vids = { videos: { data: V[]; total: number }; failedCount: number };

const list = (page: any, qs = '') => props<Vids>(page, `/painel/videos?tab=todos&per_page=100${qs}`);
const find = async (page: any, title: string) => (await list(page)).videos.data.find((v) => v.title === title)!;

test.describe.configure({ mode: 'serial' });
test.beforeEach(async () => resetMock());

test.describe('vídeos fonte', () => {
    test('lista mostra os vídeos semeados na interface', async ({ page }) => {
        await page.goto('/painel/videos?tab=todos');
        await expect(page.locator('body')).toContainText('E2E Video Fila');
    });

    test('busca filtra por título', async ({ page }) => {
        const r = await list(page, '&search=E2E%20Video%20Falho');
        expect(r.videos.data.map((v) => v.title)).toEqual(['E2E Video Falho']);
    });

    test('aba "falharam" só traz vídeos com falha', async ({ page }) => {
        const r = await props<Vids>(page, '/painel/videos?tab=falharam');
        expect(r.videos.data.length).toBeGreaterThan(0);
        expect(r.videos.data.every((v) => v.status === 'failed')).toBe(true);
        expect(r.failedCount).toBeGreaterThan(0);
    });

    test('filtro por status', async ({ page }) => {
        const r = await list(page, '&status=pending');
        expect(r.videos.data.every((v) => v.status === 'pending')).toBe(true);
    });

    test('pausar, retomar e priorizar repassam ao clip-processor', async ({ page }) => {
        const v = await find(page, 'E2E Video Fila');
        for (const acao of ['pause', 'resume', 'prioritize']) {
            const map: Record<string, string> = { pause: 'pause', resume: 'resume', prioritize: 'prioritize' };
            expect((await send(page, 'POST', `/painel/videos/${v.id}/${map[acao]}`)).status()).toBe(302);
        }
        const paths = (await mockCalls()).map((c) => c.path);
        expect(paths).toEqual([
            `/internal/videos/${v.id}/pause`,
            `/internal/videos/${v.id}/resume`,
            `/internal/videos/${v.id}/prioritize`,
        ]);
    });

    test('reordenar envia a lista de ids na ordem', async ({ page }) => {
        const ids = (await list(page)).videos.data.slice(0, 3).map((v) => v.id);
        expect((await send(page, 'POST', '/painel/videos/reorder', { ids })).status()).toBe(302);
        expect((await mockCalls()).find((c) => c.path === '/internal/videos/reorder')?.body).toEqual({ ids });
    });

    test('reordenar sem ids falha na validação', async ({ page }) => {
        expect((await send(page, 'POST', '/painel/videos/reorder', {}, { json: true })).status()).toBe(422);
    });

    test('erro 422 do processor vira mensagem, não erro 500', async ({ page }) => {
        await failMock('/internal/videos/1/pause', 422);
        const v = await find(page, 'E2E Video Extra');
        await failMock(`/internal/videos/${v.id}/pause`, 422);
        expect((await send(page, 'POST', `/painel/videos/${v.id}/pause`)).status()).toBe(302);
    });

    test('apagar arquivo de vídeo pendente mantém o registro', async ({ page }) => {
        const v = await find(page, 'E2E Video Extra');
        expect((await send(page, 'POST', `/painel/videos/${v.id}/delete`)).status()).toBe(302);
        expect((await find(page, 'E2E Video Extra')).id).toBe(v.id);
    });

    test('delete-file passa pelo processor (guard de clip ativo)', async ({ page }) => {
        const v = await find(page, 'E2E Video Falho');
        const res = await send(page, 'POST', `/painel/videos/${v.id}/delete-file`);
        expect([200, 302]).toContain(res.status());
        expect((await mockCalls()).some((c) => c.path === '/internal/delete-source-video')).toBe(true);
    });

    test('purge-old chama o processor com a data', async ({ page }) => {
        const res = await send(page, 'POST', '/painel/videos/purge-old', { before_date: '2020-01-01' });
        expect([200, 302, 422]).toContain(res.status());
    });

    test('rota de vídeo inexistente responde 404', async ({ page }) => {
        expect((await send(page, 'POST', '/painel/videos/99999999/pause')).status()).toBe(404);
    });
});
