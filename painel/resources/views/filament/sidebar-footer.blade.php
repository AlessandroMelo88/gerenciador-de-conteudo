<div class="p-3 border-t border-white/10">
    <form method="POST" action="{{ route('filament.admin.auth.logout') }}">
        @csrf
        <button
            type="submit"
            class="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-gray-400 hover:bg-white/5 hover:text-white transition duration-75"
        >
            <x-heroicon-o-arrow-right-on-rectangle class="h-5 w-5 shrink-0"/>
            Sair
        </button>
    </form>
</div>
