import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import type { ComponentProps } from 'react';

type ConfirmButtonProps = {
    description: string;
    onConfirm: () => void;
    children: React.ReactNode;
    disabled?: boolean;
    className?: string;
} & Pick<ComponentProps<typeof Button>, 'variant' | 'size'>;

export function ConfirmButton({ description, onConfirm, children, disabled, className, variant, size }: ConfirmButtonProps) {
    return (
        <AlertDialog>
            <AlertDialogTrigger asChild>
                <Button variant={variant} size={size} disabled={disabled} className={className}>
                    {children}
                </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
                <AlertDialogHeader>
                    <AlertDialogTitle>Tem certeza?</AlertDialogTitle>
                    <AlertDialogDescription>{description}</AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                    <AlertDialogCancel>Cancelar</AlertDialogCancel>
                    <AlertDialogAction onClick={onConfirm}>Confirmar</AlertDialogAction>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    );
}
