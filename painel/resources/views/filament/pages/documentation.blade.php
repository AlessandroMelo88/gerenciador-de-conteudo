<x-filament-panels::page>

    <x-filament::section icon="heroicon-o-sparkles" icon-color="warning">
        <x-slot name="heading">Como o pipeline funciona, resumido</x-slot>

        <div class="prose dark:prose-invert max-w-none text-sm">
            <p>Se você não mexer em nada, o sistema publica sozinho, em loop:</p>
        </div>

        <div class="mt-3 flex flex-wrap items-center gap-2 text-xs font-medium">
            <x-filament::badge color="gray">Descobre vídeo novo (RSS)</x-filament::badge>
            <span class="text-gray-400">→</span>
            <x-filament::badge color="gray">Baixa</x-filament::badge>
            <span class="text-gray-400">→</span>
            <x-filament::badge color="gray">Transcreve</x-filament::badge>
            <span class="text-gray-400">→</span>
            <x-filament::badge color="gray">IA seleciona momentos</x-filament::badge>
            <span class="text-gray-400">→</span>
            <x-filament::badge color="gray">Corta + legenda + marca d'água</x-filament::badge>
            <span class="text-gray-400">→</span>
            <x-filament::badge color="warning">Fila de aprovação</x-filament::badge>
            <span class="text-gray-400">→</span>
            <x-filament::badge color="success">Publica (cota diária)</x-filament::badge>
        </div>

        <div class="prose dark:prose-invert max-w-none text-sm mt-3">
            <p>As seções abaixo explicam cada tela do painel. Clique no título de cada uma pra abrir/fechar.</p>
        </div>
    </x-filament::section>

    <x-filament::section icon="heroicon-o-home" collapsible collapsed>
        <x-slot name="heading">Dashboard</x-slot>
        <x-slot name="description">Tela inicial — o que está acontecendo agora e o que precisa da sua decisão.</x-slot>

        <div class="prose dark:prose-invert max-w-none text-sm">
            <ul>
                <li><strong>Cota de Uploads</strong> — quantos vídeos cada canal-destino já publicou hoje vs. o limite diário (<code>MAX_UPLOADS_PER_DAY</code>). Zera à meia-noite (horário de São Paulo).</li>
                <li><strong>Fila de aprovação</strong> — clips prontos aguardando você aprovar ou rejeitar. Aprovar coloca o clip na fila de publicação; rejeitar apaga o MP4 do corte (o vídeo bruto original é preservado).</li>
                <li><strong>Na fila (aguardando cota)</strong> — clips já aprovados que ainda não subiram porque a cota diária foi atingida. Publicam sozinhos, em ordem (round-robin entre canais fonte, pra um canal com muito conteúdo represado não engolir a cota do dia inteiro). Use "Rejeitar" aqui só se a notícia ficou velha/irrelevante.</li>
                <li><strong>Últimas falhas</strong> — clips que quebraram em algum passo do processamento, só pra referência/debug.</li>
                <li><strong>Colunas "Canal fonte" e "Formato"</strong> — de onde o clip veio e se é Curto (short vertical) ou Longo (corte único horizontal).</li>
                <li><strong>Coluna "Trecho"</strong> — o intervalo de tempo (mm:ss–mm:ss) do vídeo original que virou esse clip. Vários clips com o mesmo "Vídeo fonte" não são duplicados: são trechos diferentes do mesmo vídeo. Se o título aparecer idêntico ao do vídeo original em vários clips, é sinal de que a geração de título/descrição por IA falhou (confira a chave <code>ANTHROPIC_API_KEY</code>) e caiu no fallback.</li>
                <li><strong>"Ver clip"</strong> — abre um player de vídeo leve embutido na própria linha, pra você conferir a legenda e a qualidade do corte antes de aprovar, sem precisar baixar o arquivo.</li>
            </ul>
        </div>
    </x-filament::section>

    <x-filament::section icon="heroicon-o-tv" collapsible collapsed>
        <x-slot name="heading">Canais Destino</x-slot>
        <x-slot name="description">Os canais do YouTube onde os clips são publicados (ex: "Futebol em Cortes").</x-slot>

        <div class="prose dark:prose-invert max-w-none text-sm">
            <p><strong>Criando um canal que ainda não existe no YouTube:</strong> crie o canal primeiro em <code>studio.youtube.com</code> (o painel não cria canais novos, só publica em canais que já existem). Depois copie o <strong>Channel ID</strong> dele (começa com "UC...", em Configurações avançadas do canal) e cole aqui.</p>
            <ul>
                <li><strong>Nome / Slug</strong> — identifica o canal internamente (o slug é usado no nome do arquivo de marca d'água e no comando de autorização OAuth).</li>
                <li><strong>Nicho</strong> — categoria de conteúdo (ex: futebol, podcast). Carrega os nichos já cadastrados; dá pra criar um nicho novo direto no select (ver seção Canais Fonte abaixo sobre nichos).</li>
                <li><strong>YouTube Channel ID</strong> — necessário pra saber em qual canal publicar via API.</li>
                <li><strong>Marca d'água</strong> — envie um PNG com fundo transparente aqui e ele passa a ser aplicado automaticamente no canto superior direito de todo vídeo cortado pra esse canal. <em>Isso é diferente do ícone/capa do canal no YouTube</em> — a API do YouTube não permite trocar ícone/capa por código, então isso só dá pra fazer manualmente no <code>studio.youtube.com</code>.</li>
                <li><strong>Autorização OAuth</strong> — não dá pra autorizar com um clique: o YouTube exige que você mesmo faça login na sua conta Google e aprove o acesso, então é um comando que você roda uma vez por canal (o botão "Copiar" no formulário de edição do canal copia o comando pronto). Depois de autorizado, a coluna "OAuth" na listagem mostra o status.</li>
                <li><strong>Ativo</strong> — desligar impede que novos clips sejam direcionados pra esse canal (não afeta os já publicados).</li>
                <li><strong>Apagar</strong> — o ícone de lixeira na linha da tabela (ou no formulário de edição) remove o canal-destino definitivamente. Diferente de desativar, que só pausa.</li>
            </ul>
        </div>
    </x-filament::section>

    <x-filament::section icon="heroicon-o-rss" collapsible collapsed>
        <x-slot name="heading">Canais Fonte</x-slot>
        <x-slot name="description">Os canais do YouTube que o robô monitora pra encontrar conteúdo bruto (ex: TNT Sports, ESPN Brasil).</x-slot>

        <div class="prose dark:prose-invert max-w-none text-sm">
            <p><strong>Como adicionar um canal novo:</strong> clique em "Novo Canal-fonte", cole a URL do canal (ou o @handle, ou o channel_id direto) e escolha o nicho. O sistema resolve automaticamente o RSS do canal e passa a monitorar vídeos novos publicados por ele — sem precisar copiar/colar cada vídeo manualmente.</p>
            <ul>
                <li><strong>Nicho</strong> — vem de uma lista real guardada no banco (tabela de nichos), não uma lista fixa no código. Ao criar um canal-fonte ou canal-destino, o select mostra os nichos já cadastrados; se precisar de um nicho novo (ex: "política"), dá pra criar direto no select ("+ criar opção") — ele passa a existir pra sempre e já aparece nos próximos cadastros.</li>
                <li><strong>Tabs no topo da listagem</strong> — uma tab "Todos" + uma tab por nicho cadastrado. Ao criar um nicho novo, a tab dele aparece aqui automaticamente, sem precisar mexer em código.</li>
                <li><strong>Ativo</strong> — desligar pausa o monitoramento desse canal (para de trazer vídeos novos; o que já foi trazido continua no pipeline).</li>
                <li><strong>Blacklisted</strong> — bloqueia o canal por completo (usado quando um canal fonte gera muito conteúdo ruim/irrelevante).</li>
                <li><strong>Apagar</strong> — remove o canal-fonte da lista de monitoramento (os vídeos já trazidos por ele continuam no banco).</li>
            </ul>
            <p>Formato curto vs. longo é decidido automaticamente pelo robô com base na duração real do vídeo: 10 minutos ou mais vira um corte longo horizontal; vídeos mais curtos geram até 3 clips verticais (shorts). Você não escolhe isso por canal.</p>
        </div>
    </x-filament::section>

    <x-filament::section icon="heroicon-o-film" collapsible collapsed>
        <x-slot name="heading">Vídeos</x-slot>
        <x-slot name="description">Lista de todo vídeo bruto (fonte) já baixado ou tentado pelo pipeline — não são os clips finais, são a matéria-prima.</x-slot>

        <div class="prose dark:prose-invert max-w-none text-sm">
            <ul>
                <li><strong>Abas no topo</strong> — "Ativos" (padrão, esconde falhas), "Falharam" (só o que deu erro), "Todos".</li>
                <li><strong>Filtros</strong> (ícone de funil) — por status específico e por data de publicação no YouTube.</li>
                <li><strong>Coluna "Arquivo local"</strong> — mostra se o .mp4 bruto ainda existe no disco do servidor.</li>
                <li><strong>Coluna "Uso"</strong> — indica se é seguro apagar o arquivo bruto (já gerou clips e nenhum está em andamento/publicado) ou se ainda está em uso.</li>
                <li><strong>Apagar um vídeo</strong> — no menu de ações da linha, "Apagar arquivo local" libera espaço em disco sem afetar os clips já cortados. Pra vários de uma vez, use a seleção + "Apagar arquivos selecionados".</li>
                <li><strong>"Limpar vídeos antigos"</strong> — botão no topo da tabela: escolha uma data e ele apaga do banco os vídeos anteriores a ela que nunca geraram clip (não serão mais processados, já que o download sempre prioriza notícia recente), e libera do disco o arquivo bruto dos que já geraram clip e não precisam mais dele. Clips já cortados e publicados nunca são afetados.</li>
            </ul>
        </div>
    </x-filament::section>

    <x-filament::section icon="heroicon-o-link" collapsible collapsed>
        <x-slot name="heading">Processar Vídeo</x-slot>
        <x-slot name="description">Envio manual de um vídeo específico pro pipeline, fora do monitoramento automático de canais.</x-slot>

        <div class="prose dark:prose-invert max-w-none text-sm">
            <p>Use quando você encontrar um vídeo específico (de qualquer canal, mesmo um que não está na sua lista de Canais Fonte) e quiser processá-lo agora: cole a URL, escolha o formato (curto = shorts verticais, longo = corte único horizontal de 10-20min) e envie. Ele entra na fila normal (download → transcrição → IA → corte → aprovação) como qualquer outro vídeo.</p>
        </div>
    </x-filament::section>

</x-filament-panels::page>
