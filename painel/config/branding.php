<?php

/*
 * Marca exibida pelo painel (PLANO-MESTRE seção 5): mesmo backend e banco, tema diferente.
 *
 * Seleção, nesta ordem:
 *   1. BRAND_DOMAINS — host=marca, separado por vírgula. Ex.: "painel.umbrellasolutions.com.br=umbrella"
 *   2. APP_BRAND — marca padrão quando o host não está no mapa.
 * Marca desconhecida cai em canaldecortes.
 *
 * Cores e tipografia moram em resources/css/app.css, em [data-brand="<chave>"].
 */

$domains = [];
foreach (explode(',', (string) env('BRAND_DOMAINS', '')) as $pair) {
    [$host, $brand] = array_pad(explode('=', $pair, 2), 2, '');
    $host = strtolower(trim($host));
    $brand = trim($brand);
    if ($host !== '' && $brand !== '') {
        $domains[$host] = $brand;
    }
}

return [
    'default' => env('APP_BRAND', 'canaldecortes'),

    'domains' => $domains,

    'brands' => [
        'canaldecortes' => [
            'name' => 'Canal de Cortes',
            'tagline' => 'Pipeline de clipes',
            'icon' => 'clapperboard',
            // Caminho público de um SVG/PNG. Vazio = ícone + gradiente do tema.
            'logo' => env('BRAND_CANALDECORTES_LOGO'),
        ],
        'umbrella' => [
            'name' => 'Umbrella Solutions',
            'tagline' => 'Soluções digitais',
            'icon' => 'umbrella',
            'logo' => env('BRAND_UMBRELLA_LOGO'),
        ],
    ],
];
