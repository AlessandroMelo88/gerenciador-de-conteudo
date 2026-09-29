import { defineConfig, devices } from '@playwright/test';

const baseURL = process.env.E2E_BASE_URL ?? 'http://127.0.0.1:8099';

// Testes lentos e2e: `npm run e2e`. Precisam de banco migrado + `db:seed --class=E2ESeeder`
// e do build do Vite (ver Docs/DESENVOLVIMENTO.md e o job `e2e` do CI).
export default defineConfig({
    testDir: './e2e',
    timeout: 60_000,
    expect: { timeout: 10_000 },
    fullyParallel: false,
    workers: 1,
    retries: process.env.CI ? 2 : 0,
    forbidOnly: !!process.env.CI,
    reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : [['list']],
    use: {
        baseURL,
        locale: 'pt-BR',
        trace: 'retain-on-failure',
        screenshot: 'only-on-failure',
        video: 'retain-on-failure',
    },
    projects: [
        { name: 'setup', testMatch: /auth\.setup\.ts/ },
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'], storageState: 'e2e/.auth/user.json' },
            dependencies: ['setup'],
            testIgnore: [
                /auth\.setup\.ts/,
                /login\.spec\.ts/,
                /public\.spec\.ts/,
                /mobile\.spec\.ts/,
                /security\.spec\.ts/,
            ],
        },
        {
            name: 'anon',
            use: { ...devices['Desktop Chrome'] },
            testMatch: [/login\.spec\.ts/, /public\.spec\.ts/, /security\.spec\.ts/],
        },
        {
            name: 'mobile',
            use: { ...devices['Pixel 7'], storageState: 'e2e/.auth/user.json' },
            dependencies: ['setup'],
            testMatch: /mobile\.spec\.ts/,
        },
    ],
    // Clip-processor falso (e2e/support/mock-processor.mjs) + painel real apontando para ele.
    // Com E2E_BASE_URL o painel já está de pé e só o mock é gerenciado aqui.
    webServer: [
        {
            command: 'node e2e/support/mock-processor.mjs',
            url: 'http://127.0.0.1:8098/health',
            reuseExistingServer: !process.env.CI,
            timeout: 15_000,
        },
        ...(process.env.E2E_BASE_URL
            ? []
            : [
                  {
                      command:
                          'cd public && PHP_CLI_SERVER_WORKERS=4 php -d expose_php=0 -S 127.0.0.1:8099 ../vendor/laravel/framework/src/Illuminate/Foundation/resources/server.php',
                      url: `${baseURL}/login`,
                      reuseExistingServer: !process.env.CI,
                      timeout: 60_000,
                      env: {
                          CLIP_PROCESSOR_INTERNAL_URL: 'http://127.0.0.1:8098',
                          CLIP_PROCESSOR_INTERNAL_TOKEN: 'ci-token',
                      },
                  },
              ]),
    ],
});
