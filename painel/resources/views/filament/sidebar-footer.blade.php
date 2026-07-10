<ul class="fi-sidebar-nav-groups flex flex-col gap-y-1 px-2 pb-3">
    <li class="fi-sidebar-item">
        <form method="POST" action="{{ route('filament.admin.auth.logout') }}">
            @csrf
            <button
                type="submit"
                class="fi-sidebar-item-button group flex w-full items-center gap-x-3 rounded-lg px-2 py-2 outline-none transition duration-75 hover:bg-white/5 focus-visible:bg-white/5"
            >
                <x-heroicon-o-arrow-right-on-rectangle
                    class="fi-sidebar-item-icon h-5 w-5 shrink-0 text-gray-400 group-hover:text-white"
                />
                <span class="fi-sidebar-item-label flex-1 truncate text-gray-400 group-hover:text-white" style="font-size:0.78rem">
                    Sair
                </span>
            </button>
        </form>
    </li>
</ul>
