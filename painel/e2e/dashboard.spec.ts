import { expect, test } from '@playwright/test';

import { mockCalls, props, resetMock, send, failMock } from './support/helpers';

type Clip = { id: number; title: string };
type Dash = { pendingClips: Clip[]; queuedClips: Clip[]; failures: Clip[]; failedSourceVideoCount: number };

const dash = (page: any) => props<Dash>(page, '/painel');

test.describe.configure({ mode: 'serial' });
test.beforeEach(async () => resetMock());

test.describe('dashboard · fila de aprovação', () => {
    test('mostra os clips pendentes semeados', async ({ page }) => {
        await page.goto('/painel');
        const d = await dash(page);
        expect(d.pendingClips.length).toBeGreaterThanOrEqual(5);
        await expect(page.locator('body')).toContainText('E2E Clip Pendente');
    });

    test('aprovar pela interface confirma, move para a fila e aciona publish-now', async ({ page }) => {
        const before = await dash(page);
        const target = before.pendingClips[0];
        await page.goto('/painel');
        await page.getByRole('button', { name: 'Aprovar', exact: true }).first().click();
        await page.getByRole('button', { name: 'Confirmar' }).click();

        await expect.poll(async () => (await dash(page)).queuedClips.some((c) => c.id === target.id)).toBe(true);
        expect((await dash(page)).pendingClips.some((c) => c.id === target.id)).toBe(false);
        expect((await mockCalls()).filter((c) => c.path === '/internal/publish-now')).toHaveLength(1);
    });

    test('cancelar a confirmação não altera o clip', async ({ page }) => {
        const before = await dash(page);
        await page.goto('/painel');
        await page.getByRole('button', { name: 'Aprovar', exact: true }).first().click();
        await page.getByRole('button', { name: 'Cancelar' }).click();
        const after = await dash(page);
        expect(after.pendingClips.map((c) => c.id)).toEqual(before.pendingClips.map((c) => c.id));
        expect(await mockCalls()).toHaveLength(0);
    });

    test('aprovar duas vezes o mesmo clip só publica uma vez', async ({ page }) => {
        const [c] = (await dash(page)).pendingClips;
        expect((await send(page, 'POST', `/painel/clips/${c.id}/approve`)).status()).toBe(302);
        expect((await send(page, 'POST', `/painel/clips/${c.id}/approve`)).status()).toBe(302);
        expect((await mockCalls()).filter((x) => x.path === '/internal/publish-now')).toHaveLength(1);
    });

    test('rejeitar chama o clip-processor com o id e o token interno', async ({ page }) => {
        const [c] = (await dash(page)).pendingClips;
        expect((await send(page, 'POST', `/painel/clips/${c.id}/reject`)).status()).toBe(302);
        const call = (await mockCalls()).find((x) => x.path === '/internal/reject-clip');
        expect(call?.body).toEqual({ clip_id: c.id });
        expect(call?.token).toBe('ci-token');
    });

    test('falha do clip-processor ao rejeitar não derruba o painel', async ({ page }) => {
        await failMock('/internal/reject-clip', 500);
        const [c] = (await dash(page)).pendingClips;
        expect((await send(page, 'POST', `/painel/clips/${c.id}/reject`)).status()).toBe(302);
        await page.goto('/painel');
        await expect(page.locator('text=Server Error')).toHaveCount(0);
    });

    test('aprovação em lote só atinge pendentes', async ({ page }) => {
        const d = await dash(page);
        const ids = d.pendingClips.slice(0, 3).map((c) => c.id);
        expect((await send(page, 'POST', '/painel/clips/bulk-approve', { ids })).status()).toBe(302);
        const after = await dash(page);
        for (const id of ids) expect(after.queuedClips.some((c) => c.id === id)).toBe(true);
    });

    test('rejeição em lote chama o processor uma vez por clip', async ({ page }) => {
        const ids = (await dash(page)).pendingClips.slice(0, 2).map((c) => c.id);
        expect((await send(page, 'POST', '/painel/clips/bulk-reject', { ids })).status()).toBe(302);
        const rejected = (await mockCalls()).filter((x) => x.path === '/internal/reject-clip');
        expect(rejected.map((x) => x.body?.clip_id).sort()).toEqual([...ids].sort());
    });

    test('lote sem ids é rejeitado pela validação', async ({ page }) => {
        const res = await send(page, 'POST', '/painel/clips/bulk-approve', {}, { json: true });
        expect(res.status()).toBe(422);
    });

    test('clip inexistente responde 404', async ({ page }) => {
        expect((await send(page, 'POST', '/painel/clips/99999999/approve')).status()).toBe(404);
    });

    test('reprocessar clip com falha o tira da lista de falhas', async ({ page }) => {
        const d = await dash(page);
        const [f] = d.failures;
        expect(f, 'seed deve ter clips falhos').toBeTruthy();
        expect((await send(page, 'POST', `/painel/clips/${f.id}/reprocess`)).status()).toBe(302);
        expect((await dash(page)).failures.some((c) => c.id === f.id)).toBe(false);
    });

    test('reprocessar clip que não está em falha é ignorado', async ({ page }) => {
        const [p] = (await dash(page)).pendingClips;
        expect((await send(page, 'POST', `/painel/clips/${p.id}/reprocess`)).status()).toBe(302);
        expect((await dash(page)).pendingClips.some((c) => c.id === p.id)).toBe(true);
    });

    test('remover clip apaga o registro', async ({ page }) => {
        const [f] = (await dash(page)).failures;
        test.skip(!f, 'sem clip falho: rode db:seed --class=E2ESeeder antes de cada execução');
        expect((await send(page, 'POST', `/painel/clips/${f.id}/delete`)).status()).toBe(302);
        expect((await dash(page)).failures.some((c) => c.id === f.id)).toBe(false);
    });

    test('purge-failed preserva os registros', async ({ page }) => {
        const before = (await dash(page)).failures.length;
        expect((await send(page, 'POST', '/painel/clips/purge-failed')).status()).toBe(302);
        expect((await dash(page)).failures.length).toBe(before);
    });
});
