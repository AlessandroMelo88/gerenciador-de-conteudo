<x-filament-panels::page>
    <x-filament::section>
        <x-slot name="heading">Enfileirar vídeos manualmente</x-slot>
        <x-slot name="description">
            Cole um ou mais links do YouTube, um por linha. Cada URL entra no pipeline normal
            (download → transcrição → seleção → corte → aprovação).
        </x-slot>

        <form wire:submit="submit">
            {{ $this->form }}

            <div class="mt-4 flex gap-x-3">
                @foreach ($this->getFormActions() as $action)
                    {{ $action }}
                @endforeach
            </div>
        </form>
    </x-filament::section>
</x-filament-panels::page>
