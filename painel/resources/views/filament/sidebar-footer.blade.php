<div class="px-2 pb-3">
    <ul class="fi-sidebar-group-items">
        <li class="fi-sidebar-item">
            <form method="POST" action="{{ route('filament.admin.auth.logout') }}">
                @csrf
                <button type="submit" class="fi-sidebar-item-btn w-full">
                    <svg class="fi-icon fi-size-lg fi-sidebar-item-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 9V5.25A2.25 2.25 0 0 1 10.5 3h6a2.25 2.25 0 0 1 2.25 2.25v13.5A2.25 2.25 0 0 1 16.5 21h-6a2.25 2.25 0 0 1-2.25-2.25V15m-3 0-3-3m0 0 3-3m-3 3H15" />
                    </svg>
                    <span class="fi-sidebar-item-label">Sair</span>
                </button>
            </form>
        </li>
    </ul>
</div>
