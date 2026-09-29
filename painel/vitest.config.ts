import react from '@vitejs/plugin-react';
import path from 'node:path';
import { defineConfig } from 'vitest/config';

export default defineConfig({
    plugins: [react()],
    resolve: { alias: { '@': path.resolve(__dirname, 'resources/js') } },
    test: {
        environment: 'jsdom',
        globals: true,
        setupFiles: ['resources/js/__tests__/setup.ts'],
        include: ['resources/js/**/*.test.{ts,tsx}'],
        coverage: {
            provider: 'v8',
            include: ['resources/js/lib/**', 'resources/js/hooks/**', 'resources/js/components/*.tsx'],
            exclude: ['resources/js/components/ui/**'],
            reporter: ['text-summary', 'lcov'],
            thresholds: { lines: 20, functions: 20, statements: 20 },
        },
    },
});
