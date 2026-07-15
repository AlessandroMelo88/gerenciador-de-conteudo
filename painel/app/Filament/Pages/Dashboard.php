<?php

namespace App\Filament\Pages;

use Filament\Pages\Dashboard as BaseDashboard;
use Illuminate\Contracts\Support\Htmlable;
use Illuminate\Support\HtmlString;

class Dashboard extends BaseDashboard
{
    public function getSubheading(): string|Htmlable|null
    {
        return new HtmlString(
            'Central de controle do pipeline: baixa → transcreve → IA seleciona momentos → corta → publica. '
            .'Clips com o mesmo título vindo do mesmo vídeo não são duplicados — veja a coluna "Trecho".'
        );
    }
}
