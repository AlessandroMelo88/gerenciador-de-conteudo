<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="15">
    <title>Atualizando o painel</title>
    <style>
        :root { color-scheme: light dark; --bg: #f7f7f5; --fg: #1c1c1a; --muted: #6b6b66; --accent: #8a6d1f; }
        @media (prefers-color-scheme: dark) { :root { --bg: #151514; --fg: #ededea; --muted: #a3a39c; --accent: #d4b25a; } }
        * { box-sizing: border-box; }
        body { margin: 0; min-height: 100vh; display: grid; place-items: center; padding: 16px;
               background: var(--bg); color: var(--fg); font: 16px/1.5 system-ui, -apple-system, sans-serif; }
        main { max-width: 420px; text-align: center; }
        .spinner { width: 36px; height: 36px; margin: 0 auto 20px; border-radius: 50%;
                   border: 3px solid color-mix(in srgb, var(--accent) 25%, transparent);
                   border-top-color: var(--accent); animation: gira 0.9s linear infinite; }
        h1 { font-size: 1.25rem; margin: 0 0 8px; }
        p { margin: 0; color: var(--muted); }
        @keyframes gira { to { transform: rotate(360deg); } }
        @media (prefers-reduced-motion: reduce) { .spinner { animation: none; } }
    </style>
</head>
<body>
    <main>
        <div class="spinner" aria-hidden="true"></div>
        <h1>Atualizando o painel</h1>
        <p>Uma versão nova está entrando no ar. Leva menos de um minuto — esta página recarrega sozinha.</p>
    </main>
</body>
</html>
