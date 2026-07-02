<div
    wire:poll.5000ms
    class="fi-widget rounded-xl bg-white shadow-sm ring-1 ring-gray-950/5 dark:bg-gray-900 dark:ring-white/10"
>
    {{-- Tabs --}}
    <div class="border-b border-gray-200 dark:border-white/10">
        <div class="flex gap-0 px-4">
            @php
                $tabs = [
                    'pending'  => ['label' => 'Fila de aprovação', 'count' => $pendingClips->count()],
                    'uploads'  => ['label' => 'Últimos uploads',   'count' => $uploads->count()],
                    'failures' => ['label' => 'Últimas falhas',    'count' => $failures->count()],
                ];
            @endphp

            @foreach ($tabs as $key => $tab)
                <button
                    wire:click="setTab('{{ $key }}')"
                    class="flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors duration-75 focus:outline-none
                        {{ $activeTab === $key
                            ? 'border-primary-500 text-primary-600 dark:border-primary-400 dark:text-primary-400'
                            : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300' }}"
                >
                    {{ $tab['label'] }}
                    <span class="min-w-[1.25rem] rounded-full px-1.5 py-0.5 text-center text-xs
                        {{ $activeTab === $key
                            ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/50 dark:text-primary-300'
                            : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400' }}">
                        {{ $tab['count'] }}
                    </span>
                </button>
            @endforeach
        </div>
    </div>

    <div class="p-4">

        {{-- ── Fila de aprovação ── --}}
        @if ($activeTab === 'pending')
            @if ($pendingClips->isEmpty())
                <div class="flex flex-col items-center justify-center py-12 text-gray-400 dark:text-gray-500">
                    <x-heroicon-o-check-circle class="mb-3 h-10 w-10"/>
                    <p class="text-sm">Nenhum clip aguardando aprovação</p>
                </div>
            @else
                <div class="overflow-x-auto">
                    <table class="w-full text-sm">
                        <thead>
                            <tr class="border-b border-gray-100 dark:border-white/10 text-left">
                                <th class="pb-2 pr-4 font-medium text-gray-500 dark:text-gray-400">ID</th>
                                <th class="pb-2 pr-4 font-medium text-gray-500 dark:text-gray-400">Título</th>
                                <th class="pb-2 pr-4 font-medium text-gray-500 dark:text-gray-400">Vídeo-fonte</th>
                                <th class="pb-2 pr-4 font-medium text-gray-500 dark:text-gray-400">Destino</th>
                                <th class="pb-2 pr-4 font-medium text-gray-500 dark:text-gray-400">Score</th>
                                <th class="pb-2 font-medium text-gray-500 dark:text-gray-400">Ações</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                            @foreach ($pendingClips as $clip)
                                <tr class="hover:bg-gray-50 dark:hover:bg-white/5 transition-colors duration-75">
                                    <td class="py-2.5 pr-4 text-gray-400 dark:text-gray-500">{{ $clip->id }}</td>
                                    <td class="py-2.5 pr-4 font-medium text-gray-900 dark:text-white max-w-xs">
                                        <span title="{{ $clip->title }}">{{ str($clip->title)->limit(55) }}</span>
                                    </td>
                                    <td class="py-2.5 pr-4 text-gray-500 dark:text-gray-400 max-w-[200px]">
                                        <span title="{{ $clip->sourceVideo?->title }}">{{ str($clip->sourceVideo?->title ?? '')->limit(40) }}</span>
                                    </td>
                                    <td class="py-2.5 pr-4 text-gray-500 dark:text-gray-400">{{ $clip->destinationChannel?->name }}</td>
                                    <td class="py-2.5 pr-4">
                                        <span class="inline-flex rounded-full px-2 py-0.5 text-xs font-semibold bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
                                            {{ $clip->score }}
                                        </span>
                                    </td>
                                    <td class="py-2.5">
                                        <div class="flex gap-2">
                                            <button
                                                wire:click="aprovar({{ $clip->id }})"
                                                wire:confirm="Aprovar clip #{{ $clip->id }}?"
                                                wire:loading.attr="disabled"
                                                class="rounded-lg bg-green-600 px-3 py-1 text-xs font-semibold text-white hover:bg-green-500 active:scale-95 transition disabled:opacity-50"
                                            >
                                                Aprovar
                                            </button>
                                            <button
                                                wire:click="rejeitar({{ $clip->id }})"
                                                wire:confirm="Rejeitar clip #{{ $clip->id }}? O MP4 será removido do disco."
                                                wire:loading.attr="disabled"
                                                class="rounded-lg bg-red-600 px-3 py-1 text-xs font-semibold text-white hover:bg-red-500 active:scale-95 transition disabled:opacity-50"
                                            >
                                                Rejeitar
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            @endforeach
                        </tbody>
                    </table>
                </div>
            @endif
        @endif

        {{-- ── Últimos uploads ── --}}
        @if ($activeTab === 'uploads')
            @if ($uploads->isEmpty())
                <div class="flex flex-col items-center justify-center py-12 text-gray-400 dark:text-gray-500">
                    <x-heroicon-o-arrow-up-tray class="mb-3 h-10 w-10"/>
                    <p class="text-sm">Nenhum upload publicado ainda</p>
                </div>
            @else
                <div class="overflow-x-auto">
                    <table class="w-full text-sm">
                        <thead>
                            <tr class="border-b border-gray-100 dark:border-white/10 text-left">
                                <th class="pb-2 pr-4 font-medium text-gray-500 dark:text-gray-400">ID</th>
                                <th class="pb-2 pr-4 font-medium text-gray-500 dark:text-gray-400">Título</th>
                                <th class="pb-2 pr-4 font-medium text-gray-500 dark:text-gray-400">Canal</th>
                                <th class="pb-2 pr-4 font-medium text-gray-500 dark:text-gray-400">YouTube</th>
                                <th class="pb-2 font-medium text-gray-500 dark:text-gray-400">Publicado</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                            @foreach ($uploads as $clip)
                                <tr class="hover:bg-gray-50 dark:hover:bg-white/5 transition-colors duration-75">
                                    <td class="py-2.5 pr-4 text-gray-400 dark:text-gray-500">{{ $clip->id }}</td>
                                    <td class="py-2.5 pr-4 font-medium text-gray-900 dark:text-white">
                                        <span title="{{ $clip->title }}">{{ str($clip->title)->limit(55) }}</span>
                                    </td>
                                    <td class="py-2.5 pr-4 text-gray-500 dark:text-gray-400">{{ $clip->destinationChannel?->name }}</td>
                                    <td class="py-2.5 pr-4">
                                        @if ($clip->youtube_video_id)
                                            <a
                                                href="https://youtu.be/{{ $clip->youtube_video_id }}"
                                                target="_blank"
                                                class="text-primary-500 hover:underline dark:text-primary-400 font-mono text-xs"
                                            >youtu.be/{{ $clip->youtube_video_id }}</a>
                                        @endif
                                    </td>
                                    <td class="py-2.5 text-gray-500 dark:text-gray-400">{{ $clip->updated_at?->diffForHumans() }}</td>
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
                <div class="flex flex-col items-center justify-center py-12 text-gray-400 dark:text-gray-500">
                    <x-heroicon-o-check-circle class="mb-3 h-10 w-10"/>
                    <p class="text-sm">Nenhuma falha registrada</p>
                </div>
            @else
                @if ($failedSourceVideoCount > 0)
                    <p class="mb-3 text-xs text-gray-500 dark:text-gray-400">
                        Vídeos-fonte com falha: <strong>{{ $failedSourceVideoCount }}</strong>
                    </p>
                @endif
                <div class="overflow-x-auto">
                    <table class="w-full text-sm">
                        <thead>
                            <tr class="border-b border-gray-100 dark:border-white/10 text-left">
                                <th class="pb-2 pr-4 font-medium text-gray-500 dark:text-gray-400">ID</th>
                                <th class="pb-2 pr-4 font-medium text-gray-500 dark:text-gray-400">Título</th>
                                <th class="pb-2 pr-4 font-medium text-gray-500 dark:text-gray-400">Destino</th>
                                <th class="pb-2 font-medium text-gray-500 dark:text-gray-400">Quando</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                            @foreach ($failures as $clip)
                                <tr class="hover:bg-gray-50 dark:hover:bg-white/5 transition-colors duration-75">
                                    <td class="py-2.5 pr-4 text-gray-400 dark:text-gray-500">{{ $clip->id }}</td>
                                    <td class="py-2.5 pr-4 font-medium text-gray-900 dark:text-white">
                                        <span title="{{ $clip->title }}">{{ str($clip->title)->limit(55) }}</span>
                                    </td>
                                    <td class="py-2.5 pr-4 text-gray-500 dark:text-gray-400">{{ $clip->destinationChannel?->name }}</td>
                                    <td class="py-2.5 text-gray-500 dark:text-gray-400">{{ $clip->updated_at?->diffForHumans() }}</td>
                                </tr>
                            @endforeach
                        </tbody>
                    </table>
                </div>
            @endif
        @endif

    </div>
</div>
