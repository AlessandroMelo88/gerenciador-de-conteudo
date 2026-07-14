<?php

namespace App\Filament\Pages;

use BackedEnum;
use Filament\Pages\Page;

class Documentation extends Page
{
    protected static string|BackedEnum|null $navigationIcon = 'heroicon-o-book-open';

    protected static ?string $navigationLabel = 'Documentação';

    protected static ?string $title = 'Documentação do Painel';

    protected static ?int $navigationSort = 100;

    protected string $view = 'filament.pages.documentation';
}
