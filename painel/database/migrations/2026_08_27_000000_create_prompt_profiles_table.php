<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        if (! Schema::hasTable('prompt_profiles')) {
            Schema::create('prompt_profiles', function (Blueprint $table) {
                $table->id();
                $table->string('slug', 80)->unique();
                $table->string('name', 120);
                $table->string('niche', 80)->index();
                $table->jsonb('niche_aliases')->default('[]');
                $table->text('selection_short_prompt');
                $table->text('selection_long_prompt');
                $table->text('metadata_short_prompt');
                $table->text('metadata_long_prompt');
                $table->text('thumbnail_prompt');
                $table->boolean('active')->default(true);
                $table->timestampsTz();
            });
        }

        if (
            Schema::hasTable('source_channels')
            && ! Schema::hasColumn('source_channels', 'prompt_profile_id')
        ) {
            Schema::table('source_channels', function (Blueprint $table) {
                $table->foreignId('prompt_profile_id')
                    ->nullable()
                    ->after('target_niche')
                    ->constrained('prompt_profiles')
                    ->nullOnDelete();
            });
        }

        if (
            Schema::hasTable('destination_channels')
            && ! Schema::hasColumn('destination_channels', 'prompt_profile_id')
        ) {
            Schema::table('destination_channels', function (Blueprint $table) {
                $table->foreignId('prompt_profile_id')
                    ->nullable()
                    ->after('niche')
                    ->constrained('prompt_profiles')
                    ->nullOnDelete();
            });
        }

        $now = now();
        $profiles = [
            [
                'slug' => 'futebol',
                'name' => 'Futebol',
                'niche' => 'futebol',
                'niche_aliases' => json_encode(['esportes'], JSON_UNESCAPED_UNICODE),
                'selection_short_prompt' => <<<'PROMPT'
Você é um especialista em identificar momentos virais de vídeos de futebol brasileiro, futebol internacional e podcasts esportivos. Analise a transcrição fornecida e identifique os melhores segmentos para criar clips CURTOS com duração EXATA de 30 segundos (end_time - start_time = 30). Para futebol, priorize análise tática, debate acalorado, revelação de bastidores, comentário sobre um gol, lance polêmico e consequência para o time ou campeonato. Para podcasts esportivos, priorize discussão intensa, revelação importante, conflito, opinião bem fundamentada ou humor ligado ao esporte.
PROMPT,
                'selection_long_prompt' => <<<'PROMPT'
Você é um especialista em identificar o melhor segmento de ANÁLISE, ENTREVISTA ou DEBATE de futebol e esportes para virar um vídeo único no YouTube. Analise a transcrição e identifique O MELHOR segmento CONTÍNUO, sem fragmentar, com duração de preferência entre 420 e 1200 segundos (7 a 20 minutos). Priorize uma análise tática completa, uma resposta longa e coesa, um debate que se desenvolve ou uma história esportiva com começo, meio e fim. O segmento precisa preservar contexto, argumentos, conclusão e as consequências esportivas do assunto.
PROMPT,
                'metadata_short_prompt' => <<<'PROMPT'
Você é especialista em SEO para YouTube Shorts no nicho de futebol e esportes. Gere metadados chamativos, claros e honestos para um corte curto. O título deve destacar o lance, a opinião, o conflito ou a análise central; a descrição deve contextualizar o momento para quem não assistiu ao vídeo original; as tags devem ser termos curtos em PT-BR ligados ao esporte e ao assunto real do trecho.
PROMPT,
                'metadata_long_prompt' => <<<'PROMPT'
Você é especialista em SEO para vídeos longos no YouTube no nicho de futebol e esportes. Gere metadados chamativos, claros e honestos para uma análise, entrevista ou debate horizontal contínuo. O título deve destacar a tese, revelação ou conflito esportivo; a descrição deve explicar o assunto completo e suas consequências; as tags devem ser termos curtos em PT-BR focados no tema e em análise, sem usar Shorts ou cortes.
PROMPT,
                'thumbnail_prompt' => <<<'PROMPT'
Perfil visual: futebol e esportes. Prefira uma chamada literal do trecho que destaque lance decisivo, polêmica, declaração forte, rivalidade, virada tática ou consequência para o time. Nunca invente nomes, placares, acusações ou fatos que não estejam na transcrição.
PROMPT,
                'active' => true,
                'created_at' => $now,
                'updated_at' => $now,
            ],
            [
                'slug' => 'conteudo-inteligencia',
                'name' => 'Conteúdo de Inteligência',
                'niche' => 'hacker-libertario',
                'niche_aliases' => json_encode(
                    ['conteudo-inteligencia', 'tecnologia', 'tech', 'linux', 'ia', 'opensource'],
                    JSON_UNESCAPED_UNICODE
                ),
                'selection_short_prompt' => <<<'PROMPT'
Você é um especialista em identificar momentos virais, insights profundos e explicações técnicas de alto impacto em conteúdo de inteligência: Inteligência Artificial, tecnologia, Open Source, Linux, programação, segurança, privacidade, soberania digital, pensamento crítico e cultura hacker libertária. Analise a transcrição e identifique os melhores segmentos para criar clips CURTOS com duração EXATA de 30 segundos (end_time - start_time = 30). Priorize explicações técnicas brilhantes, reflexões sobre liberdade e privacidade digital, analogias marcantes sobre computação ou IA, desmontagem de um mito e conselhos diretos de carreira ou tecnologia.
PROMPT,
                'selection_long_prompt' => <<<'PROMPT'
Você é um especialista em identificar o melhor segmento de ANÁLISE técnica, ENTREVISTA ou DEBATE de conteúdo de inteligência para virar um vídeo único no YouTube. O tema pode envolver Inteligência Artificial, sistemas, programação, Linux, Open Source, segurança, privacidade, soberania digital, pensamento crítico ou cultura hacker libertária. Analise a transcrição e identifique O MELHOR segmento CONTÍNUO, sem fragmentar, com duração de preferência entre 420 e 1200 segundos (7 a 20 minutos). Priorize uma explicação aprofundada de um conceito, uma reflexão densa, uma demonstração com contexto ou um debate técnico que tenha começo, desenvolvimento e conclusão.
PROMPT,
                'metadata_short_prompt' => <<<'PROMPT'
Você é especialista em SEO para YouTube Shorts no nicho de Conteúdo de Inteligência. O canal publica cortes sobre Inteligência Artificial, tecnologia, Linux, Open Source, programação, privacidade, segurança, soberania digital e cultura hacker libertária. Gere metadados técnicos, claros e atraentes: o título deve revelar o insight ou problema central; a descrição deve explicar o contexto e a consequência prática; as tags devem misturar termos amplos e específicos realmente presentes no trecho, sem hashtags e sem palavras desconectadas.
PROMPT,
                'metadata_long_prompt' => <<<'PROMPT'
Você é especialista em SEO para vídeos longos no YouTube no nicho de Conteúdo de Inteligência. O vídeo pode ser uma análise técnica, entrevista ou debate sobre Inteligência Artificial, sistemas, programação, Linux, Open Source, segurança, privacidade, soberania digital ou cultura hacker libertária. Gere metadados claros e atraentes para um vídeo horizontal contínuo: o título deve destacar a tese ou revelação; a descrição deve apresentar o raciocínio completo e a consequência prática; as tags devem ser técnicas e específicas, sem usar Shorts ou cortes.
PROMPT,
                'thumbnail_prompt' => <<<'PROMPT'
Perfil visual: Conteúdo de Inteligência. Prefira uma chamada literal que destaque descoberta técnica, contradição, risco, ganho de autonomia, privacidade, liberdade, ferramenta, erro comum ou consequência prática. Nunca transforme uma hipótese em fato e nunca invente promessa, ataque ou resultado.
PROMPT,
                'active' => true,
                'created_at' => $now,
                'updated_at' => $now,
            ],
            [
                'slug' => 'podcast',
                'name' => 'Podcast e Entrevistas',
                'niche' => 'podcast',
                'niche_aliases' => json_encode([], JSON_UNESCAPED_UNICODE),
                'selection_short_prompt' => <<<'PROMPT'
Você é um especialista em identificar momentos virais de podcasts e entrevistas. Analise a transcrição e identifique os melhores segmentos para criar clips CURTOS com duração EXATA de 30 segundos (end_time - start_time = 30). Priorize uma resposta surpreendente, uma história pessoal relevante, uma opinião bem explicada, uma revelação, um conflito respeitoso, uma analogia marcante ou um momento de humor com contexto suficiente para fazer sentido fora do episódio.
PROMPT,
                'selection_long_prompt' => <<<'PROMPT'
Você é um especialista em identificar o melhor segmento de ENTREVISTA ou CONVERSA de podcast para virar um vídeo único no YouTube. Analise a transcrição e identifique O MELHOR segmento CONTÍNUO, sem fragmentar, com duração de preferência entre 420 e 1200 segundos (7 a 20 minutos). Priorize uma história, resposta ou debate com contexto, desenvolvimento, consequência e fechamento natural, preservando as perguntas necessárias para entender o raciocínio.
PROMPT,
                'metadata_short_prompt' => <<<'PROMPT'
Você é especialista em SEO para YouTube Shorts de podcasts e entrevistas. Gere metadados claros, atraentes e honestos para um corte curto. O título deve destacar a frase, história, opinião ou revelação central; a descrição deve explicar quem fala, qual é o contexto e por que o trecho importa; as tags devem refletir somente o assunto real da conversa.
PROMPT,
                'metadata_long_prompt' => <<<'PROMPT'
Você é especialista em SEO para vídeos longos de podcasts e entrevistas no YouTube. Gere metadados claros e atraentes para uma conversa horizontal contínua. O título deve destacar a tese, história ou revelação; a descrição deve resumir o raciocínio completo e o contexto da entrevista; as tags devem refletir o assunto real, sem usar Shorts ou cortes.
PROMPT,
                'thumbnail_prompt' => <<<'PROMPT'
Perfil visual: podcast e entrevistas. Prefira uma chamada literal que destaque surpresa, conflito, revelação, pergunta forte ou história marcante. Preserve o sentido da fala e nunca invente contexto.
PROMPT,
                'active' => true,
                'created_at' => $now,
                'updated_at' => $now,
            ],
        ];

        DB::table('prompt_profiles')->upsert(
            $profiles,
            ['slug'],
            [
                'name',
                'niche',
                'niche_aliases',
                'selection_short_prompt',
                'selection_long_prompt',
                'metadata_short_prompt',
                'metadata_long_prompt',
                'thumbnail_prompt',
                'active',
                'updated_at',
            ]
        );

        if (Schema::hasTable('niches')) {
            DB::table('niches')->upsert(
                [
                    [
                        'slug' => 'hacker-libertario',
                        'label' => 'Conteúdo de Inteligência',
                        'created_at' => $now,
                        'updated_at' => $now,
                    ],
                ],
                ['slug'],
                ['label', 'updated_at']
            );
        }

        $profileIds = DB::table('prompt_profiles')->pluck('id', 'slug');
        $futebolId = $profileIds->get('futebol');
        $inteligenciaId = $profileIds->get('conteudo-inteligencia');
        $podcastId = $profileIds->get('podcast');

        if ($futebolId !== null && Schema::hasTable('source_channels')) {
            DB::table('source_channels')
                ->whereNull('prompt_profile_id')
                ->whereIn('target_niche', ['futebol', 'esportes'])
                ->update(['prompt_profile_id' => $futebolId]);
        }

        if ($inteligenciaId !== null && Schema::hasTable('source_channels')) {
            DB::table('source_channels')
                ->whereNull('prompt_profile_id')
                ->whereIn(
                    'target_niche',
                    ['conteudo-inteligencia', 'hacker-libertario', 'tecnologia', 'tech', 'linux', 'ia', 'opensource']
                )
                ->update(['prompt_profile_id' => $inteligenciaId]);
        }

        if ($podcastId !== null && Schema::hasTable('source_channels')) {
            DB::table('source_channels')
                ->whereNull('prompt_profile_id')
                ->where('target_niche', 'podcast')
                ->update(['prompt_profile_id' => $podcastId]);
        }

        if ($futebolId !== null && Schema::hasTable('destination_channels')) {
            DB::table('destination_channels')
                ->whereNull('prompt_profile_id')
                ->whereIn('niche', ['futebol', 'esportes'])
                ->update(['prompt_profile_id' => $futebolId]);
        }

        if ($inteligenciaId !== null && Schema::hasTable('destination_channels')) {
            DB::table('destination_channels')
                ->whereNull('prompt_profile_id')
                ->whereIn(
                    'niche',
                    ['conteudo-inteligencia', 'hacker-libertario', 'tecnologia', 'tech', 'linux', 'ia', 'opensource']
                )
                ->update(['prompt_profile_id' => $inteligenciaId]);
        }

        if ($podcastId !== null && Schema::hasTable('destination_channels')) {
            DB::table('destination_channels')
                ->whereNull('prompt_profile_id')
                ->where('niche', 'podcast')
                ->update(['prompt_profile_id' => $podcastId]);
        }
    }

    public function down(): void
    {
        if (
            Schema::hasTable('destination_channels')
            && Schema::hasColumn('destination_channels', 'prompt_profile_id')
        ) {
            Schema::table('destination_channels', function (Blueprint $table) {
                $table->dropForeign(['prompt_profile_id']);
                $table->dropColumn('prompt_profile_id');
            });
        }

        if (
            Schema::hasTable('source_channels')
            && Schema::hasColumn('source_channels', 'prompt_profile_id')
        ) {
            Schema::table('source_channels', function (Blueprint $table) {
                $table->dropForeign(['prompt_profile_id']);
                $table->dropColumn('prompt_profile_id');
            });
        }

        Schema::dropIfExists('prompt_profiles');
    }
};
