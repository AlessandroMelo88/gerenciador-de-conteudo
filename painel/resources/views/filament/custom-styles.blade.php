<style>
    /* Sidebar: cor de fundo diferente do conteúdo principal */
    .fi-sidebar {
        background-color: #0c1220 !important;
        border-right: 1px solid rgba(255,255,255,0.06) !important;
    }

    /* Fonte menor nos itens de navegação */
    .fi-sidebar-item-label {
        font-size: 0.78rem !important;
    }

    /* Ícones da sidebar levemente menores */
    .fi-sidebar-item-icon {
        width: 1.1rem !important;
        height: 1.1rem !important;
    }

    /* Heading das páginas de listagem: mesma escala do Dashboard */
    .fi-header-heading {
        font-size: 1.125rem !important;
        font-weight: 600 !important;
    }

    /* Garante que a aside da sidebar seja flex-column para o footer ficar no rodapé */
    .fi-sidebar {
        display: flex !important;
        flex-direction: column !important;
    }

    /* Nav cresce para ocupar o espaço restante, empurrando o footer para baixo */
    .fi-sidebar-nav {
        flex: 1 1 0% !important;
        overflow-y: auto !important;
    }
</style>
