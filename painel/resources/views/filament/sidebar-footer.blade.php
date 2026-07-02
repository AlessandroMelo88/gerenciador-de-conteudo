<div class="fi-sidebar-footer flex flex-col gap-y-1 px-2 py-3">
    <form method="POST" action="{{ route('filament.admin.auth.logout') }}">
        @csrf
        <button
            type="submit"
            class="fi-sidebar-item-button group flex w-full items-center gap-x-3 rounded-lg px-2 py-2 outline-none transition duration-75 hover:bg-white/5 focus-visible:bg-white/5"
        >
            <x-heroicon-o-arrow-right-on-rectangle
                class="fi-sidebar-item-icon h-6 w-6 shrink-0 text-gray-400 group-hover:text-white"
            />
            <span class="fi-sidebar-item-label flex-1 truncate text-sm font-medium text-gray-400 group-hover:text-white">
                Sair
            </span>
        </button>
    </form>
</div>
