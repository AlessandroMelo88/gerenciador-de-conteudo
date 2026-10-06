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
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { type ComponentProps, useState } from 'react';

/** Mesmos valores do enum VideoPrivacy no Laravel e do contrato com o clip-processor. */
export type Privacy = 'private' | 'public';

type ApproveButtonProps = {
    description: string;
    /** Padrão do canal destino, só para rotular a opção "Padrão do canal". */
    channelDefault?: Privacy | null;
    /** privacy = null significa herdar o padrão do canal. */
    onConfirm: (privacy: Privacy | null) => void;
    children: React.ReactNode;
    disabled?: boolean;
    className?: string;
} & Pick<ComponentProps<typeof Button>, 'variant' | 'size'>;

const ROTULO: Record<Privacy, string> = { private: 'Privado', public: 'Público' };

export function ApproveButton({
    description,
    channelDefault,
    onConfirm,
    children,
    disabled,
    className,
    variant,
    size,
}: ApproveButtonProps) {
    // 'canal' é o caminho comum: confirmar sem mexer em nada mantém o padrão do canal.
    const [escolha, setEscolha] = useState<'canal' | Privacy>('canal');

    const rotuloPadrao = channelDefault
        ? `Padrão do canal (${ROTULO[channelDefault]})`
        : 'Padrão do canal';

    return (
        <AlertDialog onOpenChange={(aberto) => aberto && setEscolha('canal')}>
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

                <div className="space-y-3">
                    <p className="text-sm font-medium text-foreground">Privacidade no YouTube</p>
                    <RadioGroup value={escolha} onValueChange={(v) => setEscolha(v as 'canal' | Privacy)}>
                        <div className="flex items-center gap-2">
                            <RadioGroupItem value="canal" id="privacidade-canal" />
                            <Label htmlFor="privacidade-canal" className="font-normal">
                                {rotuloPadrao}
                            </Label>
                        </div>
                        <div className="flex items-center gap-2">
                            <RadioGroupItem value="private" id="privacidade-privado" />
                            <Label htmlFor="privacidade-privado" className="font-normal">
                                Privado — só você vê, não aparece no canal
                            </Label>
                        </div>
                        <div className="flex items-center gap-2">
                            <RadioGroupItem value="public" id="privacidade-publico" />
                            <Label htmlFor="privacidade-publico" className="font-normal">
                                Público — vai ao ar assim que subir
                            </Label>
                        </div>
                    </RadioGroup>
                </div>

                <AlertDialogFooter>
                    <AlertDialogCancel>Cancelar</AlertDialogCancel>
                    <AlertDialogAction onClick={() => onConfirm(escolha === 'canal' ? null : escolha)}>
                        Confirmar
                    </AlertDialogAction>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    );
}
