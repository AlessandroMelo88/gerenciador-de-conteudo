<x-filament-widgets::widget wire:poll.5000ms>
    <x-filament::section>

        <x-filament::tabs>
            <x-filament::tabs.item
                wire:click="setTab('pending')"
                :active="$activeTab === 'pending'"
                :badge="$pendingClips->count()"
            >
                Fila de aprovação
            </x-filament::tabs.item>

            <x-filament::tabs.item
                wire:click="setTab('queued')"
                :active="$activeTab === 'queued'"
                :badge="$queuedClips->count()"
            >
                Na fila (aguardando cota)
            </x-filament::tabs.item>

            <x-filament::tabs.item
                wire:click="setTab('failures')"
                :active="$activeTab === 'failures'"
                :badge="$failures->count()"
            >
                Últimas falhas
            </x-filament::tabs.item>
        </x-filament::tabs>

        <div style="margin-top:1rem">

            {{-- ── Fila de aprovação ── --}}
            @if ($activeTab === 'pending')
                @if ($pendingClips->isEmpty())
                    <x-filament::empty-state
                        heading="Tudo em dia"
                        description="Nenhum clip aguardando aprovação"
                        icon="heroicon-o-check-circle"
                    />
                @else
                    <div style="overflow-x:auto">
                        <table style="width:100%;font-size:0.75rem;border-collapse:collapse">
                            <thead>
                                <tr>
                                    <th style="padding:6px 10px;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#6b7280">ID</th>
                                    <th style="padding:6px 10px;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#6b7280">Título</th>
                                    <th style="padding:6px 10px;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#6b7280">Vídeo fonte</th>
                                    <th style="padding:6px 10px;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#6b7280">Trecho</th>
                                    <th style="padding:6px 10px;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#6b7280">Canal fonte</th>
                                    <th style="padding:6px 10px;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#6b7280">Formato</th>
                                    <th style="padding:6px 10px;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#6b7280">Destino</th>
                                    <th style="padding:6px 10px;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#6b7280">Score</th>
                                    <th style="padding:6px 10px;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#6b7280">Ações</th>
                                </tr>
                            </thead>
                            <tbody>
                                @foreach ($pendingClips as $clip)
                                    <tr style="border-top:1px solid rgba(255,255,255,0.06)">
                                        <td style="padding:10px 10px;color:#9ca3af;white-space:nowrap">{{ $clip->id }}</td>
                                        <td style="padding:10px 10px;max-width:220px" x-data="{ previewOpen: false }">
                                            <span title="{{ $clip->title }}" style="display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#e5e7eb">
                                                {{ str($clip->title)->limit(35) }}
                                            </span>
                                            <button
                                                type="button"
                                                x-on:click="previewOpen = !previewOpen"
                                                style="font-size:0.7rem;color:#f59e0b;text-decoration:underline;background:none;border:none;padding:0;margin-top:2px;cursor:pointer"
                                            >
                                                <span x-text="previewOpen ? 'Ocultar clip' : 'Ver clip'"></span>
                                            </button>
                                            <template x-if="previewOpen">
                                                <video controls preload="metadata" style="width:200px;margin-top:6px;border-radius:4px" src="{{ route('clips.preview', $clip->id) }}"></video>
                                            </template>
                                        </td>
                                        <td style="padding:10px 10px;max-width:140px;color:#9ca3af">
                                            <span title="{{ $clip->sourceVideo?->title }}" style="display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
                                                {{ str($clip->sourceVideo?->title ?? '—')->limit(22) }}
                                            </span>
                                        </td>
                                        <td style="padding:10px 10px;color:#9ca3af;white-space:nowrap">{{ $this->formatTrecho($clip->start_time, $clip->end_time) }}</td>
                                        <td style="padding:10px 10px;color:#9ca3af;white-space:nowrap">{{ $clip->sourceVideo?->sourceChannel?->channel_name ?? '—' }}</td>
                                        <td style="padding:10px 10px;white-space:nowrap">
                                            <x-filament::badge :color="$clip->sourceVideo?->format === 'longo' ? 'info' : 'gray'">
                                                {{ $clip->sourceVideo?->format === 'longo' ? 'Longo' : 'Curto' }}
                                            </x-filament::badge>
                                        </td>
                                        <td style="padding:10px 10px;color:#9ca3af;white-space:nowrap">{{ $clip->destinationChannel?->name }}</td>
                                        <td style="padding:10px 10px;white-space:nowrap">
                                            <x-filament::badge color="warning">{{ $clip->score }}</x-filament::badge>
                                        </td>
                                        <td style="padding:10px 10px;white-space:nowrap">
                                            <div style="display:flex;flex-direction:column;gap:4px;align-items:flex-start">
                                                <x-filament::button
                                                    wire:click="aprovar({{ $clip->id }})"
                                                    wire:confirm="Aprovar clip #{{ $clip->id }}?"
                                                    wire:loading.attr="disabled"
                                                    color="success"
                                                    size="xs"
                                                    outlined
                                                >
                                                    Aprovar
                                                </x-filament::button>
                                                <x-filament::button
                                                    wire:click="rejeitar({{ $clip->id }})"
                                                    wire:confirm="Rejeitar clip #{{ $clip->id }}? O MP4 será removido do disco."
                                                    wire:loading.attr="disabled"
                                                    color="danger"
                                                    size="xs"
                                                    outlined
                                                >
                                                    Rejeitar
                                                </x-filament::button>
                                            </div>
                                        </td>
                                    </tr>
                                @endforeach
                            </tbody>
                        </table>
                    </div>
                @endif
            @endif

            {{-- ── Na fila (aprovados aguardando cota diária) ── --}}
            @if ($activeTab === 'queued')
                @if ($queuedClips->isEmpty())
                    <x-filament::empty-state
                        heading="Fila vazia"
                        description="Nenhum clip aprovado aguardando publicação"
                        icon="heroicon-o-check-circle"
                    />
                @else
                    <x-filament::callout color="info" icon="heroicon-o-information-circle" style="margin-bottom:1rem">
                        Publica automaticamente em ordem (mais antigo primeiro), respeitando o limite diário de uploads. Se não fizer nada, a fila segue sozinha. Use "Rejeitar" só se a notícia ficou velha/irrelevante.
                    </x-filament::callout>
                    <div style="overflow-x:auto">
                        <table style="width:100%;font-size:0.75rem;border-collapse:collapse">
                            <thead>
                                <tr>
                                    <th style="padding:6px 10px;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#6b7280">Pos.</th>
                                    <th style="padding:6px 10px;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#6b7280">ID</th>
                                    <th style="padding:6px 10px;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#6b7280">Título</th>
                                    <th style="padding:6px 10px;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#6b7280">Vídeo fonte</th>
                                    <th style="padding:6px 10px;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#6b7280">Trecho</th>
                                    <th style="padding:6px 10px;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#6b7280">Canal fonte</th>
                                    <th style="padding:6px 10px;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#6b7280">Formato</th>
                                    <th style="padding:6px 10px;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#6b7280">Destino</th>
                                    <th style="padding:6px 10px;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#6b7280">Score</th>
                                    <th style="padding:6px 10px;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#6b7280">Aprovado</th>
                                    <th style="padding:6px 10px;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#6b7280">Ações</th>
                                </tr>
                            </thead>
                            <tbody>
                                @foreach ($queuedClips as $index => $clip)
                                    <tr style="border-top:1px solid rgba(255,255,255,0.06)">
                                        <td style="padding:10px 10px;color:#9ca3af;white-space:nowrap">#{{ $index + 1 }}</td>
                                        <td style="padding:10px 10px;color:#9ca3af;white-space:nowrap">{{ $clip->id }}</td>
                                        <td style="padding:10px 10px;max-width:220px" x-data="{ previewOpen: false }">
                                            <span title="{{ $clip->title }}" style="display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#e5e7eb">
                                                {{ str($clip->title)->limit(35) }}
                                            </span>
                                            <button
                                                type="button"
                                                x-on:click="previewOpen = !previewOpen"
                                                style="font-size:0.7rem;color:#f59e0b;text-decoration:underline;background:none;border:none;padding:0;margin-top:2px;cursor:pointer"
                                            >
                                                <span x-text="previewOpen ? 'Ocultar clip' : 'Ver clip'"></span>
                                            </button>
                                            <template x-if="previewOpen">
                                                <video controls preload="metadata" style="width:200px;margin-top:6px;border-radius:4px" src="{{ route('clips.preview', $clip->id) }}"></video>
                                            </template>
                                        </td>
                                        <td style="padding:10px 10px;max-width:140px;color:#9ca3af">
                                            <span title="{{ $clip->sourceVideo?->title }}" style="display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
                                                {{ str($clip->sourceVideo?->title ?? '—')->limit(22) }}
                                            </span>
                                        </td>
                                        <td style="padding:10px 10px;color:#9ca3af;white-space:nowrap">{{ $this->formatTrecho($clip->start_time, $clip->end_time) }}</td>
                                        <td style="padding:10px 10px;color:#9ca3af;white-space:nowrap">{{ $clip->sourceVideo?->sourceChannel?->channel_name ?? '—' }}</td>
                                        <td style="padding:10px 10px;white-space:nowrap">
                                            <x-filament::badge :color="$clip->sourceVideo?->format === 'longo' ? 'info' : 'gray'">
                                                {{ $clip->sourceVideo?->format === 'longo' ? 'Longo' : 'Curto' }}
                                            </x-filament::badge>
                                        </td>
                                        <td style="padding:10px 10px;color:#9ca3af;white-space:nowrap">{{ $clip->destinationChannel?->name }}</td>
                                        <td style="padding:10px 10px;white-space:nowrap">
                                            <x-filament::badge color="warning">{{ $clip->score }}</x-filament::badge>
                                        </td>
                                        <td style="padding:10px 10px;color:#9ca3af;white-space:nowrap">{{ $clip->created_at?->diffForHumans() }}</td>
                                        <td style="padding:10px 10px;white-space:nowrap">
                                            <x-filament::button
                                                wire:click="rejeitar({{ $clip->id }})"
                                                wire:confirm="Rejeitar clip #{{ $clip->id }}? O MP4 será removido do disco e ele sai da fila."
                                                wire:loading.attr="disabled"
                                                color="danger"
                                                size="xs"
                                                outlined
                                            >
                                                Rejeitar
                                            </x-filament::button>
                                        </td>
                                    </tr>
                                @endforeach
                            </tbody>
                        </table>
                    </div>
                @endif
            @endif

            {{-- ── Últimas falhas ── --}}
            @if ($activeTab === 'failures')
                @if ($failures->isEmpty())
                    <x-filament::empty-state
                        heading="Sem falhas"
                        description="Nenhuma falha registrada"
                        icon="heroicon-o-check-circle"
                    />
                @else
                    @if ($failedSourceVideoCount > 0)
                        <x-filament::callout color="danger" icon="heroicon-o-exclamation-triangle" style="margin-bottom:1rem">
                            Vídeos fonte com falha: <strong>{{ $failedSourceVideoCount }}</strong>
                        </x-filament::callout>
                    @endif
                    <div style="overflow-x:auto">
                        <table style="width:100%;font-size:0.75rem;border-collapse:collapse">
                            <thead>
                                <tr>
                                    <th style="padding:6px 10px;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#6b7280">ID</th>
                                    <th style="padding:6px 10px;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#6b7280">Título</th>
                                    <th style="padding:6px 10px;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#6b7280">Destino</th>
                                    <th style="padding:6px 10px;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#6b7280">Quando</th>
                                </tr>
                            </thead>
                            <tbody>
                                @foreach ($failures as $clip)
                                    <tr style="border-top:1px solid rgba(255,255,255,0.06)">
                                        <td style="padding:10px 10px;color:#9ca3af;white-space:nowrap">{{ $clip->id }}</td>
                                        <td style="padding:10px 10px;max-width:260px">
                                            <span title="{{ $clip->title }}" style="display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#e5e7eb">
                                                {{ str($clip->title)->limit(40) }}
                                            </span>
                                        </td>
                                        <td style="padding:10px 10px;color:#9ca3af;white-space:nowrap">{{ $clip->destinationChannel?->name }}</td>
                                        <td style="padding:10px 10px;color:#9ca3af;white-space:nowrap">{{ $clip->updated_at?->diffForHumans() }}</td>
                                    </tr>
                                @endforeach
                            </tbody>
                        </table>
                    </div>
                @endif
            @endif

        </div>

    </x-filament::section>
</x-filament-widgets::widget>
