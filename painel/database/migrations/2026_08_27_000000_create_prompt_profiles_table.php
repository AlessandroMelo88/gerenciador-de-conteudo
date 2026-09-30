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
                'niche_aliases' => json_encode(['conteudo-inteligencia'], JSON_UNESCAPED_UNICODE),
                'selection_short_prompt' => <<<'PROMPT'
Você é um especialista em identificar momentos virais, insights profundos e explicações técnicas de alto impacto para o canal Hacker Libertário: Inteligência Artificial, tecnologia, Open Source, Linux, programação, segurança, criptografia, privacidade, soberania digital e cultura hacker libertária. Analise a transcrição e identifique os melhores segmentos para criar clips CURTOS com duração EXATA de 30 segundos (end_time - start_time = 30). DIRETRIZES LIBERTÁRIAS INEGOCIÁVEIS: 1. O ESTADO NUNCA DEVE SER DEFENDIDO: rejeite qualquer trecho que elogie, justifique ou legitime o Estado, impostos, regulação estatal ou censura. Trechos sobre regulação ou vigilância só são válidos se forem de denúncia crítica e apresentarem alternativas de defesa individual por meio de tecnologia e criptografia. 2. ZERO MENÇÃO A POLÍTICOS E FUNCIONÁRIOS PÚBLICOS: nenhum político ou funcionário público/agente estatal deve ser sequer mencionado ou colocado em evidência. Se houver partidarismo ou politicagem, descarte imediatamente. O foco é 100% nas ideias, ferramentas, soberania e liberdade individual. 3. GANCHO VIRAL IMEDIATO (0 A 3s): o corte deve começar no auge da afirmação de impacto, sem cumprimentos, pausas ou enrolações. Priorize explicações técnicas brilhantes, reflexões sobre soberania/privacidade digital, analogias marcantes sobre computação ou IA e quebra de mitos.
PROMPT,
                'selection_long_prompt' => <<<'PROMPT'
Você é um especialista em identificar o melhor segmento de ANÁLISE técnica, ENTREVISTA ou DEBATE para o canal Hacker Libertário virar um vídeo único no YouTube. O tema envolve Inteligência Artificial, sistemas, programação, Linux, Open Source, segurança, criptografia, privacidade, soberania digital ou filosofia hacker libertária. Analise a transcrição e identifique O MELHOR segmento CONTÍNUO, sem fragmentar, com duração de preferência entre 420 e 1200 segundos (7 a 20 minutos). DIRETRIZES LIBERTÁRIAS INEGOCIÁVEIS: 1. O Estado nunca deve ser defendido nem legitimado em nenhuma regulação ou intervenção. 2. Nenhum político ou funcionário público deve ser mencionado pelo nome ou colocado em debate. O canal trata de tecnologia, ideias e liberdade individual, nunca de politicagem. Priorize uma explicação aprofundada de um conceito, uma reflexão densa, uma demonstração com contexto ou um debate técnico que tenha começo, desenvolvimento e conclusão.
PROMPT,
                'metadata_short_prompt' => <<<'PROMPT'
Você é especialista em SEO para YouTube Shorts no canal Hacker Libertário. O canal publica cortes sobre Inteligência Artificial, tecnologia, Linux, Open Source, programação, privacidade, cibersegurança, criptografia, soberania digital e cultura hacker libertária. DIRETRIZES LIBERTÁRIAS INEGOCIÁVEIS: 1. O Estado nunca deve ser defendido; enfatize autonomia, descentralização e liberdade individual. 2. Nenhum político ou funcionário público deve ser sequer mencionado no título, descrição ou tags. Gere metadados de alto CTR para mobile: o título deve ter entre 45 e 55 caracteres (máximo 100), provocador e instigante, com 1 emoji pertinente; a descrição deve resumir o insight em 1-2 frases com contexto e CTA de inscrição; as tags devem ser termos técnicos em PT-BR sem hashtags (ex: hacker libertario, linux, ciberseguranca, open source, inteligencia artificial, privacidade digital, criptografia, soberania digital).
PROMPT,
                'metadata_long_prompt' => <<<'PROMPT'
Você é especialista em SEO para vídeos longos no YouTube no canal Hacker Libertário. O vídeo é uma análise técnica, entrevista ou debate sobre Inteligência Artificial, sistemas, programação, Linux, Open Source, segurança, criptografia, privacidade, soberania digital ou filosofia hacker libertária. DIRETRIZES LIBERTÁRIAS INEGOCIÁVEIS: 1. O Estado nunca deve ser defendido; 2. Nenhum político ou funcionário público deve ser mencionado no título, descrição ou tags. Gere metadados claros e atraentes para vídeo horizontal contínuo: o título deve destacar a tese ou revelação técnica; a descrição deve apresentar o raciocínio completo e a consequência prática; as tags devem ser técnicas e específicas, sem usar Shorts ou cortes.
PROMPT,
                'thumbnail_prompt' => <<<'PROMPT'
Perfil visual: Hacker Libertário. Prefira uma chamada literal curta (2 a 10 palavras, máx 64 caracteres) que capture choque, contradição, revelação técnica, risco à privacidade ou afirmação marcante de autonomia e liberdade individual. REGRA ABSOLUTA: nunca mencione nomes de políticos ou funcionários públicos, e nunca faça defesa do Estado. Nunca transforme uma hipótese em fato e nunca invente promessa ou ataque.
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
                    ['conteudo-inteligencia', 'hacker-libertario']
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
                    ['conteudo-inteligencia', 'hacker-libertario']
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
