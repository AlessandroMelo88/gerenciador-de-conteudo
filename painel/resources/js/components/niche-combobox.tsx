import { useState } from 'react';
import { router } from '@inertiajs/react';
import { CheckIcon, ChevronsUpDownIcon, PlusIcon } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
} from '@/components/ui/command';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Field, FieldLabel } from '@/components/ui/field';
import { Input } from '@/components/ui/input';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { cn } from '@/lib/utils';

export type Niche = { slug: string; label: string };

function slugify(value: string): string {
    return value
        .toLowerCase()
        .normalize('NFD')
        .replace(/[̀-ͯ]/g, '')
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/(^-|-$)/g, '');
}

export function NicheCombobox({
    niches,
    value,
    onChange,
}: {
    niches: Niche[];
    value: string;
    onChange: (slug: string) => void;
}) {
    const [open, setOpen] = useState(false);
    const [createOpen, setCreateOpen] = useState(false);
    const [newLabel, setNewLabel] = useState('');
    const [newSlug, setNewSlug] = useState('');
    const [creating, setCreating] = useState(false);

    const selected = niches.find((n) => n.slug === value);

    function submitCreate() {
        setCreating(true);
        router.post(
            '/painel/niches',
            { label: newLabel, slug: newSlug },
            {
                preserveScroll: true,
                onSuccess: () => {
                    onChange(newSlug);
                    setCreateOpen(false);
                    setNewLabel('');
                    setNewSlug('');
                },
                onFinish: () => setCreating(false),
            },
        );
    }

    return (
        <>
            <Popover open={open} onOpenChange={setOpen}>
                <PopoverTrigger asChild>
                    <Button variant="outline" role="combobox" aria-expanded={open} className="w-full justify-between font-normal">
                        {selected ? selected.label : 'Selecione um nicho…'}
                        <ChevronsUpDownIcon className="ml-2 size-4 shrink-0 opacity-50" />
                    </Button>
                </PopoverTrigger>
                <PopoverContent className="w-[--radix-popover-trigger-width] p-0">
                    <Command>
                        <CommandInput placeholder="Buscar nicho…" />
                        <CommandList>
                            <CommandEmpty>Nenhum nicho encontrado.</CommandEmpty>
                            <CommandGroup>
                                {niches.map((niche) => (
                                    <CommandItem
                                        key={niche.slug}
                                        value={niche.label}
                                        onSelect={() => {
                                            onChange(niche.slug);
                                            setOpen(false);
                                        }}
                                    >
                                        <CheckIcon
                                            className={cn('mr-2 size-4', value === niche.slug ? 'opacity-100' : 'opacity-0')}
                                        />
                                        {niche.label}
                                    </CommandItem>
                                ))}
                            </CommandGroup>
                        </CommandList>
                        <div className="border-t p-1">
                            <Button
                                variant="ghost"
                                size="sm"
                                className="w-full justify-start"
                                onClick={() => {
                                    setOpen(false);
                                    setCreateOpen(true);
                                }}
                            >
                                <PlusIcon className="mr-2 size-4" />
                                Novo nicho
                            </Button>
                        </div>
                    </Command>
                </PopoverContent>
            </Popover>

            <Dialog open={createOpen} onOpenChange={setCreateOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Novo nicho</DialogTitle>
                    </DialogHeader>
                    <div className="grid gap-4">
                        <Field>
                            <FieldLabel htmlFor="niche-label">Nome do nicho</FieldLabel>
                            <Input
                                id="niche-label"
                                value={newLabel}
                                onChange={(e) => {
                                    setNewLabel(e.target.value);
                                    setNewSlug(slugify(e.target.value));
                                }}
                            />
                        </Field>
                        <Field>
                            <FieldLabel htmlFor="niche-slug">Slug</FieldLabel>
                            <Input id="niche-slug" value={newSlug} onChange={(e) => setNewSlug(e.target.value)} />
                        </Field>
                    </div>
                    <DialogFooter>
                        <Button onClick={submitCreate} disabled={creating || !newLabel || !newSlug}>
                            Criar
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </>
    );
}
