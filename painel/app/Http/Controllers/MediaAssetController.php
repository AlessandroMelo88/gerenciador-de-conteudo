<?php

namespace App\Http\Controllers;

use App\Models\MediaAsset;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;
use Illuminate\Validation\ValidationException;
use RuntimeException;

class MediaAssetController extends Controller
{
    private const KINDS = ['intro', 'outro', 'music'];

    public function store(Request $request): RedirectResponse
    {
        $data = $request->validate([
            'kind' => ['required', 'string', 'in:'.implode(',', self::KINDS)],
            'name' => ['required', 'string', 'max:120'],
            'file' => [
                'required',
                'file',
                'mimes:mp4,mov,webm,jpg,jpeg,png,mp3,wav,m4a,ogg',
                'max:102400',
            ],
            'destination_channel_id' => ['required', 'integer', 'exists:destination_channels,id'],
            'format' => ['nullable', 'string', 'in:curto,longo'],
            'duration_seconds' => ['nullable', 'integer', 'min:1', 'max:60'],
            'music_volume' => ['nullable', 'numeric', 'min:0.01', 'max:1'],
            'priority' => ['nullable', 'integer', 'min:0', 'max:100'],
            'active' => ['sometimes', 'boolean'],
        ]);

        $file = $request->file('file');
        if ($file === null) {
            throw ValidationException::withMessages(['file' => 'Selecione um arquivo']);
        }

        $extension = strtolower($file->extension());
        $audioExtensions = ['mp3', 'wav', 'm4a', 'ogg'];
        $visualExtensions = ['mp4', 'mov', 'webm', 'jpg', 'jpeg', 'png'];
        $allowedExtensions = $data['kind'] === 'music' ? $audioExtensions : $visualExtensions;
        if (! in_array($extension, $allowedExtensions, true)) {
            throw ValidationException::withMessages([
                'file' => $data['kind'] === 'music'
                    ? 'Músicas devem ser arquivos MP3, WAV, M4A ou OGG'
                    : 'Intros e encerramentos devem ser vídeos MP4/MOV/WEBM ou imagens JPG/PNG',
            ]);
        }

        $path = $file->storeAs(
            "media/{$data['kind']}",
            Str::uuid()->toString().'.'.$extension,
            'branding',
        );
        if (! is_string($path)) {
            throw new RuntimeException('Não foi possível salvar o arquivo de mídia');
        }

        try {
            MediaAsset::create([
                'kind' => $data['kind'],
                'name' => $data['name'],
                'path' => $path,
                'destination_channel_id' => $data['destination_channel_id'],
                'format' => $data['format'] ?? null,
                'duration_seconds' => $data['kind'] === 'music'
                    ? null
                    : ($data['duration_seconds'] ?? 3),
                'music_volume' => $data['kind'] === 'music'
                    ? ($data['music_volume'] ?? 0.24)
                    : null,
                'priority' => $data['priority'] ?? 0,
                'active' => $data['active'] ?? true,
            ]);
        } catch (\Throwable $exception) {
            Storage::disk('branding')->delete($path);
            throw $exception;
        }

        return back()->with('success', 'Mídia adicionada à biblioteca');
    }

    public function update(Request $request, MediaAsset $mediaAsset): RedirectResponse
    {
        $data = $request->validate([
            'name' => ['sometimes', 'string', 'max:120'],
            'destination_channel_id' => ['sometimes', 'required', 'integer', 'exists:destination_channels,id'],
            'format' => ['sometimes', 'nullable', 'string', 'in:curto,longo'],
            'duration_seconds' => ['sometimes', 'nullable', 'integer', 'min:1', 'max:60'],
            'music_volume' => ['sometimes', 'nullable', 'numeric', 'min:0.01', 'max:1'],
            'priority' => ['sometimes', 'integer', 'min:0', 'max:100'],
            'active' => ['sometimes', 'boolean'],
        ]);

        $mediaAsset->update($data);

        return back()->with('success', 'Configuração da mídia atualizada');
    }

    public function destroy(MediaAsset $mediaAsset): RedirectResponse
    {
        Storage::disk('branding')->delete($mediaAsset->path);
        $mediaAsset->delete();

        return back()->with('success', 'Mídia removida');
    }
}
