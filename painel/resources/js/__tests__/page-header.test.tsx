import { render, screen } from '@testing-library/react';

import { PageHeader } from '@/components/page-header';

describe('PageHeader', () => {
    it('não renderiza nada sem descrição nem ações', () => {
        const { container } = render(<PageHeader />);
        expect(container).toBeEmptyDOMElement();
    });

    it('mostra descrição e ações', () => {
        render(<PageHeader description="Resumo" actions={<button>Novo</button>} />);
        expect(screen.getByText('Resumo')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Novo' })).toBeInTheDocument();
    });
});
