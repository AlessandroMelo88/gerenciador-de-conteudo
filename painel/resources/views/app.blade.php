@php($brand = \App\Support\Brand::resolve(request()))
<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}" class="dark" data-brand="{{ $brand['key'] }}">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="csrf-token" content="{{ csrf_token() }}">

        <title inertia>{{ $brand['name'] }}</title>

        @if ($brand['key'] === 'umbrella')
            {{-- Tipografia de título da Umbrella; o corpo segue Geist (empacotada no Vite). --}}
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800&display=swap" rel="stylesheet">
        @endif

        @fonts
        @routes
        @viteReactRefresh
        @vite(['resources/css/app.css', 'resources/js/app.tsx'])
        @inertiaHead
    </head>
    <body class="bg-background text-foreground antialiased">
        @inertia
    </body>
</html>
