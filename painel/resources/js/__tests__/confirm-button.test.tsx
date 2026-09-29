import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { ConfirmButton } from '@/components/confirm-button';

describe('ConfirmButton', () => {
    it('só executa a ação depois da confirmação', async () => {
        const onConfirm = vi.fn();
        render(
            <ConfirmButton description="Apagar mesmo?" onConfirm={onConfirm}>
                Apagar
            </ConfirmButton>,
        );

        await userEvent.click(screen.getByRole('button', { name: 'Apagar' }));
        expect(onConfirm).not.toHaveBeenCalled();
        expect(await screen.findByText('Apagar mesmo?')).toBeInTheDocument();
    });
});
