import { expect, type APIResponse, type Page } from '@playwright/test';

const MOCK = process.env.MOCK_PROCESSOR_URL ?? 'http://127.0.0.1:8098';

export type Call = { method: string; path: string; body: Record<string, unknown> | null; token: string | null };

/** Props do Inertia da página (lê o JSON embutido no HTML, sem depender da UI). */
export async function props<T = Record<string, any>>(page: Page, path: string): Promise<T> {
    const res = await page.request.get(path);
    expect(res.status(), `GET ${path}`).toBe(200);
    const html = await res.text();
    const m = html.match(/<script data-page="app" type="application\/json">([\s\S]*?)<\/script>/);
    expect(m, `data-page em ${path}`).not.toBeNull();
    return JSON.parse(m![1]).props as T;
}

async function xsrf(page: Page): Promise<string> {
    const cookies = await page.context().cookies();
    return decodeURIComponent(cookies.find((c) => c.name === 'XSRF-TOKEN')?.value ?? '');
}

/** Requisição mutável autenticada, com CSRF. Não segue redirect (302 = sucesso do `back()`). */
export async function send(
    page: Page,
    method: 'POST' | 'PUT' | 'PATCH' | 'DELETE',
    path: string,
    data?: Record<string, unknown>,
    { json = false }: { json?: boolean } = {},
): Promise<APIResponse> {
    // garante cookie XSRF/sessão
    if (!(await xsrf(page))) await page.request.get('/painel');
    return page.request.fetch(path, {
        method,
        data,
        maxRedirects: 0,
        headers: {
            'X-XSRF-TOKEN': await xsrf(page),
            ...(json ? { Accept: 'application/json' } : {}),
        },
    });
}

export async function resetMock() {
    await fetch(`${MOCK}/__reset`, { method: 'POST' });
}

export async function mockCalls(): Promise<Call[]> {
    return (await fetch(`${MOCK}/__calls`)).json();
}

export async function failMock(path: string, status = 500) {
    await fetch(`${MOCK}/__fail`, { method: 'POST', body: JSON.stringify({ path, status }) });
}

export const uniq = (p: string) => `${p}-${Date.now().toString(36)}${Math.floor(Math.random() * 1e4)}`;
