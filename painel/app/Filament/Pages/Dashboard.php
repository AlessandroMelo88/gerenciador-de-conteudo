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
            'Central de controle do pipeline (baixa vídeo → transcreve → IA seleciona os melhores momentos → corta → '
            .'publica). Em <strong>Fila de aprovação</strong> você decide o que publicar; em <strong>Na fila</strong> '
            .'ficam os já aprovados aguardando a cota diária de uploads (publicam sozinhos, em ordem); em '
            .'<strong>Últimas falhas</strong> ficam os que quebraram em algum passo. Vários clips com o mesmo título '
            .'vindos do mesmo "Vídeo fonte" não são duplicados — são trechos diferentes do mesmo vídeo (veja a coluna '
            .'"Trecho"); o título só fica idêntico ao original quando a geração de metadata por IA falha.'
        );
    }
}
