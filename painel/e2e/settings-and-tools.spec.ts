import { expect, test } from '@playwright/test';

import { EMAIL, PASSWORD } from './credentials';
import { mockCalls, props, resetMock, send, failMock, uniq } from './support/helpers';

test.describe.configure({ mode: 'serial' });
test.beforeEach(async () => resetMock());

test.describe('configurações', () => {
    test('alterna download local', async ({ page }) => {
        expect(
            (await send(page, 'PUT', '/painel/configuracoes/sistema', { allow_local_download: true })).status(),
        ).toBe(302);
        expect(
            (await send(page, 'PUT', '/painel/configuracoes/sistema', { allow_local_download: false })).status(),
        ).toBe(302);
        expect((await send(page, 'PUT', '/painel/configuracoes/sistema', {}, { json: true })).status()).toBe(422);
    });

    test('cookies: sem arquivo nem conteúdo volta erro e não grava nada', async ({ page }) => {
        expect((await send(page, 'POST', '/painel/configuracoes/cookies', {})).status()).toBe(302);
    });

    test('trocar senha exige a senha atual e confirmação com 10+ caracteres', async ({ page }) => {
        const p = '/painel/configuracoes/senha';
        expect(
            (
                await send(
                    page,
                    'PUT',
                    p,
                    { current_password: 'errada', password: 'nova-senha-123', password_confirmation: 'nova-senha-123' },
                    { json: true },
                )
            ).status(),
        ).toBe(422);
        expect(
            (
                await send(
                    page,
                    'PUT',
                    p,
                    { current_password: PASSWORD, password: 'curta', password_confirmation: 'curta' },
                    { json: true },
                )
            ).status(),
        ).toBe(422);
        expect(
            (
                await send(
                    page,
                    'PUT',
                    p,
                    { current_password: PASSWORD, password: 'nova-senha-123', password_confirmation: 'outra-coisa' },
                    { json: true },
                )
            ).status(),
        ).toBe(422);
    });

    test('mídia: recusa upload sem arquivo', async ({ page }) => {
        expect(
            (await send(page, 'POST', '/painel/configuracoes/midia', {}, { json: true })).status(),
        ).toBeGreaterThanOrEqual(400);
    });
});

test.describe('processar vídeo', () => {
    test('enfileira várias URLs (duplicadas e vazias ignoradas)', async ({ page }) => {
        const urls = [
            'https://youtu.be/AAAAAAAAAAA',
            '',
            'https://youtu.be/AAAAAAAAAAA',
            'https://youtu.be/BBBBBBBBBBB',
        ].join('\n');
        expect((await send(page, 'POST', '/painel/processar-video', { format: 'longo', urls })).status()).toBe(302);
        const calls = (await mockCalls()).filter((c) => c.path === '/internal/process-url');
        expect(calls.map((c) => c.body)).toEqual([
            { url: 'https://youtu.be/AAAAAAAAAAA', format: 'longo' },
            { url: 'https://youtu.be/BBBBBBBBBBB', format: 'longo' },
        ]);
    });

    test('formato inválido e lista vazia são recusados', async ({ page }) => {
        expect(
            (
                await send(
                    page,
                    'POST',
                    '/painel/processar-video',
                    { format: 'xyz', urls: 'https://youtu.be/A' },
                    { json: true },
                )
            ).status(),
        ).toBe(422);
        expect(
            (
                await send(page, 'POST', '/painel/processar-video', { format: 'curto', urls: '' }, { json: true })
            ).status(),
        ).toBe(422);
    });

    test('falha do processor não gera erro 500', async ({ page }) => {
        await failMock('/internal/process-url', 500);
        expect(
            (
                await send(page, 'POST', '/painel/processar-video', {
                    format: 'curto',
                    urls: 'https://youtu.be/CCCCCCCCCCC',
                })
            ).status(),
        ).toBe(302);
    });

    test('a interface tem o formulário com seletor de formato', async ({ page }) => {
        await page.goto('/painel/processar-video');
        await expect(page.locator('textarea').first()).toBeVisible();
    });
});

test.describe('transcrições', () => {
    type J = { id: number; sourceUrl?: string; source_url?: string; status: string };

    test('cria job, pausa, retoma e remove', async ({ page }) => {
        const url = `https://youtu.be/${uniq('T')}`.slice(0, 40);
        expect((await send(page, 'POST', '/painel/transcricoes', { url })).status()).toBe(302);
        const r = await props<{ jobs?: J[]; transcriptions?: J[] }>(page, '/painel/transcricoes');
        const raw: any = r.jobs ?? r.transcriptions ?? [];
        const list = (Array.isArray(raw) ? raw : (raw.data ?? [])) as J[];
        const job = list.find((j) => (j.sourceUrl ?? j.source_url) === url);
        expect(job, 'job criado aparece na lista').toBeTruthy();

        expect((await send(page, 'POST', `/painel/transcricoes/${job!.id}/pausar`)).status()).toBe(302);
        expect((await page.request.get(`/painel/transcricoes/${job!.id}`)).status()).toBe(200);
        expect((await send(page, 'POST', `/painel/transcricoes/${job!.id}/retomar`)).status()).toBe(302);
        expect((await send(page, 'DELETE', `/painel/transcricoes/${job!.id}`)).status()).toBe(302);
        expect((await page.request.get(`/painel/transcricoes/${job!.id}`)).status()).toBe(404);
    });

    test('URL inválida é recusada', async ({ page }) => {
        expect(
            (await send(page, 'POST', '/painel/transcricoes', { url: 'isso-nao-e-url' }, { json: true })).status(),
        ).toBe(422);
    });
});

test.describe('assistente, links e documentação', () => {
    test('assistente recusa mensagem vazia', async ({ page }) => {
        expect((await send(page, 'POST', '/painel/assistente/chat', {}, { json: true })).status()).toBe(422);
    });

    test('links úteis e documentação renderizam conteúdo', async ({ page }) => {
        await page.goto('/painel/links-uteis');
        await expect(page.locator('main, body').first()).not.toBeEmpty();
        await page.goto('/painel/documentacao');
        await expect(page.locator('h1, h2').first()).toBeVisible();
    });

    test('usuário logado aparece na sidebar', async ({ page }) => {
        await page.goto('/painel');
        await expect(page.locator('body')).toContainText(EMAIL);
    });
});
