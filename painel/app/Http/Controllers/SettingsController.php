<?php

namespace App\Http\Controllers;

use App\Models\SystemSetting;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\Rules\Password;
use Inertia\Inertia;
use Inertia\Response;

class SettingsController extends Controller
{
    public function show(): Response
    {
        $cookiePath = file_exists('/var/www/html/youtube/cookies.txt')
            ? '/var/www/html/youtube/cookies.txt'
            : base_path('../youtube/cookies.txt');

        $cookiesInfo = null;
        if (file_exists($cookiePath)) {
            $cookiesInfo = [
                'exists' => true,
                'size' => filesize($cookiePath),
                'updated_at' => date('d/m/Y H:i:s', filemtime($cookiePath)),
                'lines' => count(file($cookiePath)),
            ];
        }

        return Inertia::render('Settings', [
            'settings' => [
                'allow_local_download' => (bool) SystemSetting::get('allow_local_download', false),
            ],
            'cookiesInfo' => $cookiesInfo,
        ]);
    }

    public function updateCookies(Request $request): RedirectResponse
    {
        $content = '';
        if ($request->hasFile('cookies_file')) {
            $request->validate([
                'cookies_file' => ['required', 'file', 'max:2048'],
            ]);
            $content = file_get_contents($request->file('cookies_file')->getRealPath());
        } elseif ($request->filled('cookies_content')) {
            $request->validate([
                'cookies_content' => ['required', 'string'],
            ]);
            $content = $request->input('cookies_content');
        } else {
            return back()->with('error', 'Envie um arquivo ou cole o conteúdo dos cookies.');
        }

        $paths = [
            '/var/www/html/youtube/cookies.txt',
            base_path('../youtube/cookies.txt'),
        ];

        $saved = false;
        foreach ($paths as $path) {
            $dir = dirname($path);
            if (is_dir($dir)) {
                file_put_contents($path, trim($content)."\n");
                $saved = true;
            }
        }

        if (! $saved) {
            return back()->with('error', 'Não foi possível salvar o arquivo de cookies no caminho esperado.');
        }

        return back()->with('success', 'Cookies do YouTube atualizados com sucesso!');
    }

    public function updateSystemSettings(Request $request): RedirectResponse
    {
        $data = $request->validate([
            'allow_local_download' => ['required', 'boolean'],
        ]);

        SystemSetting::set(
            'allow_local_download',
            $data['allow_local_download'],
            'Permitir download e processamento local de vídeos'
        );

        return back()->with('success', 'Configurações do sistema atualizadas');
    }

    public function updatePassword(Request $request): RedirectResponse
    {
        $data = $request->validate([
            'current_password' => ['required', 'current_password'],
            'password' => ['required', Password::min(8), 'confirmed'],
        ]);

        Auth::user()->update(['password' => Hash::make($data['password'])]);

        return back()->with('success', 'Senha atualizada');
    }
}
