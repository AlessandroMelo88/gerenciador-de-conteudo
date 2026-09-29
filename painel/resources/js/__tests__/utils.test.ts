import { cn } from '@/lib/utils';

describe('cn', () => {
    it('junta classes e ignora valores falsos', () => {
        expect(cn('a', false && 'b', undefined, 'c')).toBe('a c');
    });

    it('resolve conflito do tailwind pela última classe', () => {
        expect(cn('p-2', 'p-4')).toBe('p-4');
    });
});
