<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Afiliados (PLANO-MESTRE seção 6): o worker local empurra ofertas via
     * POST /api/offers; o operador revisa no painel; /o/{slug} rastreia cliques.
     *
     * Portável MySQL 8.4 / PostgreSQL 17: só Schema builder, sem enum nativo —
     * network/status/channel são string validada na aplicação (App\Models\Offer).
     */
    public function up(): void
    {
        Schema::create('offers', function (Blueprint $table) {
            $table->id();
            $table->string('network', 40);
            $table->string('external_id', 191)->nullable();
            $table->string('niche', 50);
            $table->string('title', 255);
            $table->text('description')->nullable();
            $table->text('product_url')->nullable();
            $table->text('affiliate_url');
            $table->string('slug', 64)->unique();
            $table->text('image_url')->nullable();
            $table->unsignedInteger('price_cents')->nullable();
            $table->string('currency', 3)->default('BRL');
            $table->decimal('commission_percent', 5, 2)->nullable();
            $table->string('cta_text', 255)->nullable();
            $table->text('copy_short')->nullable();
            $table->text('copy_long')->nullable();
            $table->string('ai_provider', 30)->nullable();
            $table->string('status', 20)->default('draft')->index();
            $table->unsignedInteger('clicks_count')->default(0);
            $table->timestamp('approved_at')->nullable();
            $table->timestamps();

            // external_id NULL não colide (NULLs são distintos em MySQL e PostgreSQL),
            // então ofertas manuais sem id externo convivem sem conflito.
            $table->unique(['network', 'external_id']);
        });

        Schema::create('offer_clicks', function (Blueprint $table) {
            $table->id();
            $table->foreignId('offer_id')->constrained('offers')->cascadeOnDelete();
            $table->string('channel', 40)->nullable();
            // sha256(ip + app.key) — nunca o IP cru (LGPD).
            $table->string('ip_hash', 64)->nullable();
            $table->string('user_agent', 255)->nullable();
            $table->string('referer', 512)->nullable();
            $table->timestamp('created_at')->nullable();

            $table->index(['offer_id', 'created_at']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('offer_clicks');
        Schema::dropIfExists('offers');
    }
};
