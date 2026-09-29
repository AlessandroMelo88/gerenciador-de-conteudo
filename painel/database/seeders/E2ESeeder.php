<?php

namespace Database\Seeders;

use App\Models\DestinationChannel;
use App\Models\GeneratedClip;
use App\Models\Offer;
use App\Models\SourceChannel;
use App\Models\SourceVideo;
use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Hash;

/**
 * Massa fixa para os testes E2E do Playwright (painel/e2e). Idempotente: pode rodar de novo
 * e devolve o mesmo cenário (os clips "E2E" são recriados).
 *
 *   php artisan db:seed --class=E2ESeeder
 *
 * Recusa rodar em produção: cria uma conta de senha conhecida (ver o aviso em DatabaseSeeder).
 */
class E2ESeeder extends Seeder
{
    public const EMAIL = 'e2e@canaldecortes.test';

    public const PASSWORD = 'e2e-senha-segura-123';

    public const OFFER_SLUG = 'e2eoffer';

    public const OFFER_URL = 'https://go.hotmart.com/E2E-DESTINO';

    public function run(): void
    {
        if (app()->environment('production')) {
            $this->command?->error('E2ESeeder recusado em produção.');

            return;
        }

        User::query()->updateOrCreate(
            ['email' => self::EMAIL],
            ['name' => 'Operador E2E', 'password' => Hash::make(self::PASSWORD)],
        );

        DB::table('niches')->insertOrIgnore([
            'slug' => 'futebol', 'label' => 'Futebol', 'created_at' => now(), 'updated_at' => now(),
        ]);

        $this->offers();
        $this->pipeline();
    }

    private function offers(): void
    {
        $offer = Offer::query()->firstOrNew(['slug' => self::OFFER_SLUG]);
        $offer->fill(Offer::factory()->approved()->make([
            'title' => 'Oferta E2E',
            'affiliate_url' => self::OFFER_URL,
        ])->getAttributes());
        $offer->slug = self::OFFER_SLUG;
        $offer->save();

        Offer::query()->where('title', 'like', 'Rascunho E2E%')->delete();
        Offer::factory()->count(2)->create(['title' => 'Rascunho E2E']);
    }

    private function pipeline(): void
    {
        $dest = DestinationChannel::query()->firstOrCreate(
            ['slug' => 'e2e-destino'],
            DestinationChannel::factory()->make(['slug' => 'e2e-destino', 'name' => 'Destino E2E'])->getAttributes(),
        );
        $source = SourceChannel::query()->firstOrCreate(
            ['youtube_channel_id' => 'UCe2eFonte0000000000000A'],
            SourceChannel::factory()->make([
                'youtube_channel_id' => 'UCe2eFonte0000000000000A',
                'channel_name' => 'Fonte E2E',
                'channel_handle' => '@fonte-e2e',
            ])->getAttributes(),
        );

        // Recria só o que é "E2E": clips antes dos vídeos (FK sem cascade).
        $videoIds = SourceVideo::query()->where('title', 'like', 'E2E %')->pluck('id');
        GeneratedClip::query()->whereIn('source_video_id', $videoIds)->delete();
        SourceVideo::query()->whereIn('id', $videoIds)->delete();

        $mk = fn (string $title, string $status, string $yt) => SourceVideo::factory()->create([
            'channel_id' => $source->id, 'title' => $title, 'status' => $status, 'youtube_video_id' => $yt,
        ]);
        $fila = $mk('E2E Video Fila', 'pending', 'e2eVideoFi1');
        $falho = $mk('E2E Video Falho', 'failed', 'e2eVideoFa1');
        $mk('E2E Video Pausado', 'pending', 'e2eVideoPa1')->update(['paused' => true]);
        $mk('E2E Video Extra', 'pending', 'e2eVideoEx1');

        $clip = fn (string $title, string $status, ?SourceVideo $video = null) => GeneratedClip::factory()->create([
            'source_video_id' => ($video ?? $fila)->id,
            'destination_channel_id' => $dest->id,
            'title' => $title,
            'status' => $status,
        ]);
        foreach (range(1, 10) as $i) {
            $clip("E2E Clip Pendente {$i}", 'pending');
        }
        $clip('E2E Clip Aprovado', 'approved');
        $clip('E2E Clip Falho 1', 'failed', $falho);
        $clip('E2E Clip Falho 2', 'failed', $falho);
        $clip('E2E Clip Falho 3', 'failed', $falho);
    }
}
