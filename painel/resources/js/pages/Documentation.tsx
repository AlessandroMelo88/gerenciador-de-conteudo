import { Head, usePage } from '@inertiajs/react';

import { AppSidebar } from '@/components/app-sidebar';
import { SiteHeader } from '@/components/site-header';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';
import { SparklesIcon } from 'lucide-react';

type PageProps = {
    auth: { user: { name: string; email: string } | null };
};

const CHAIN = [
    'Descobre vídeo novo (RSS)',
    'Baixa',
    'Transcreve',
    'IA seleciona momentos',
    'Corta + legenda + marca d\'água',
];

export default function Documentation() {
    const { props } = usePage<PageProps>();

    return (
        <>
            <Head title="Documentação" />
            <SidebarProvider>
                <AppSidebar user={props.auth.user} />
                <SidebarInset>
                    <SiteHeader title="Documentação do Painel" />
                    <div className="flex flex-1 flex-col gap-6 p-4">
                        <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4">
                            <div className="mb-2 flex items-center gap-2 font-medium text-amber-200">
                                <SparklesIcon className="size-4" />
                                Como o pipeline funciona, resumido
                            </div>
                            <p className="mb-3 text-sm text-muted-foreground">
                                Se você não mexer em nada, o sistema publica sozinho, em loop:
                            </p>
                            <div className="flex flex-wrap items-center gap-1.5 text-sm">
                                {CHAIN.map((step) => (
                                    <span key={step} className="flex items-center gap-1.5">
                                        <Badge variant="secondary">{step}</Badge>
                                        <span className="text-muted-foreground">→</span>
                                    </span>
                                ))}
                                <Badge className="bg-amber-500 text-amber-950">Fila de aprovação</Badge>
                                <span className="text-muted-foreground">→</span>
                                <Badge className="bg-emerald-500 text-emerald-950">Publica (cota diária)</Badge>
                            </div>
                            <p className="mt-3 text-sm text-muted-foreground">
                                As seções abaixo explicam cada tela do painel. Clique no título de cada uma pra
                                abrir/fechar.
                            </p>
                        </div>

                        <Accordion type="multiple" className="max-w-3xl">
                            <AccordionItem value="dashboard">
                                <AccordionTrigger>Dashboard</AccordionTrigger>
                                <AccordionContent>
                                    <div className="prose prose-sm prose-invert max-w-none">
                                        <p>
                                            Tela inicial — o que está acontecendo agora e o que precisa da sua
                                            decisão.
                                        </p>
                                        <ul>
                                            <li>
                                                <strong>Cota de Uploads</strong> — quantos vídeos já foram publicados
                                                hoje por canal-destino, e o limite diário.
                                            </li>
                                            <li>
                                                <strong>Fila de aprovação</strong> — clips prontos, cortados e com
                                                legenda, esperando você aprovar ou rejeitar.
                                            </li>
                                            <li>
                                                <strong>Na fila (aguardando cota)</strong> — já aprovados, publicando
                                                sozinhos assim que a cota diária liberar.
                                            </li>
                                            <li>
                                                <strong>Últimas falhas</strong> — clips que quebraram em algum passo
                                                do pipeline, com botão de reprocessar.
                                            </li>
                                            <li>
                                                Colunas <code>Canal fonte</code>/<code>Formato</code> mostram de onde
                                                veio o clip e se é curto ou longo.
                                            </li>
                                            <li>
                                                Coluna <code>Trecho</code> mostra o intervalo de tempo do vídeo
                                                original usado no clip.
                                            </li>
                                            <li>
                                                Botão <em>Ver clip</em> mostra o vídeo cortado direto na tela, sem
                                                sair do painel.
                                            </li>
                                        </ul>
                                    </div>
                                </AccordionContent>
                            </AccordionItem>

                            <AccordionItem value="canais-destino">
                                <AccordionTrigger>Canais Destino</AccordionTrigger>
                                <AccordionContent>
                                    <div className="prose prose-sm prose-invert max-w-none">
                                        <p>
                                            Os canais do YouTube onde os clips são publicados (ex: &quot;Futebol em
                                            Cortes&quot;).
                                        </p>
                                        <ul>
                                            <li>
                                                Se o canal ainda não existe no YouTube, crie-o primeiro em
                                                studio.youtube.com — o painel não cria canais novos, só publica
                                                neles.
                                            </li>
                                            <li>
                                                <strong>Nome/Slug</strong> — slug é o identificador único usado
                                                internamente.
                                            </li>
                                            <li>
                                                <strong>Nicho</strong> — categoria do canal, usada pra filtrar canais
                                                fonte compatíveis.
                                            </li>
                                            <li>
                                                <strong>YouTube Channel ID</strong> — o ID que começa com
                                                &quot;UC&quot;.
                                            </li>
                                            <li>
                                                <strong>Marca d&apos;água</strong> — PNG aplicado automaticamente no
                                                canto superior direito de todo vídeo cortado.
                                            </li>
                                            <li>
                                                <strong>Autorização OAuth</strong> — feita manualmente por canal, via
                                                comando no terminal (não dá pra fazer com 1 clique).
                                            </li>
                                            <li>
                                                <strong>Ativo</strong> — desliga a publicação nesse canal sem apagar
                                                a configuração.
                                            </li>
                                        </ul>
                                    </div>
                                </AccordionContent>
                            </AccordionItem>

                            <AccordionItem value="canais-fonte">
                                <AccordionTrigger>Canais Fonte</AccordionTrigger>
                                <AccordionContent>
                                    <div className="prose prose-sm prose-invert max-w-none">
                                        <p>
                                            Os canais do YouTube que o robô monitora pra encontrar conteúdo bruto (ex:
                                            TNT Sports, ESPN Brasil).
                                        </p>
                                        <ul>
                                            <li>Adicionar um novo: cola a URL do canal e escolhe o nicho de destino.</li>
                                            <li>
                                                <strong>Nicho</strong> vem de uma tabela no banco — pode criar um novo
                                                direto no formulário, e ele já ganha uma aba nesta tela.
                                            </li>
                                            <li>
                                                <strong>Ativo</strong> — desliga o monitoramento sem apagar o canal.
                                            </li>
                                            <li>
                                                <strong>Blacklisted</strong> — afeta apenas vídeos novos daqui pra
                                                frente; para purgar a fila já existente é preciso SQL manual.
                                            </li>
                                            <li>
                                                O formato curto/longo é decidido automaticamente pela duração de cada
                                                vídeo (≥10min vira longo horizontal, senão vira até 3 shorts
                                                verticais) — não é escolhido por canal.
                                            </li>
                                        </ul>
                                    </div>
                                </AccordionContent>
                            </AccordionItem>

                            <AccordionItem value="videos">
                                <AccordionTrigger>Vídeos</AccordionTrigger>
                                <AccordionContent>
                                    <div className="prose prose-sm prose-invert max-w-none">
                                        <p>
                                            Lista de todo vídeo bruto (fonte) já baixado ou tentado pelo pipeline —
                                            não são os clips finais, são a matéria-prima.
                                        </p>
                                        <ul>
                                            <li>Abas: Ativos / Falharam / Todos.</li>
                                            <li>
                                                Filtros por status, busca por título/canal, e um toggle &quot;Só sem
                                                uso (seguro apagar)&quot;.
                                            </li>
                                            <li>
                                                <strong>Arquivo local</strong> — se o .mp4 bruto ainda está no disco.
                                            </li>
                                            <li>
                                                <strong>Uso</strong> — resume se dá pra apagar com segurança
                                                (&quot;Sem uso&quot;/&quot;Falhou&quot;) ou se ainda está em
                                                andamento/publicado.
                                            </li>
                                            <li>Apagar arquivo por linha, ou em lote pelos selecionados.</li>
                                            <li>
                                                &quot;Limpar vídeos antigos&quot; apaga do banco vídeos velhos que
                                                nunca geraram clip, e libera espaço dos que já geraram mas não
                                                precisam mais do bruto.
                                            </li>
                                        </ul>
                                    </div>
                                </AccordionContent>
                            </AccordionItem>

                            <AccordionItem value="processar-video">
                                <AccordionTrigger>Processar Vídeo</AccordionTrigger>
                                <AccordionContent>
                                    <div className="prose prose-sm prose-invert max-w-none">
                                        <p>
                                            Envio manual de um vídeo específico pro pipeline, fora do monitoramento
                                            automático de canais.
                                        </p>
                                        <p>
                                            Cola a URL, escolhe o formato (curto ou longo), e o vídeo entra na fila
                                            normal — mesmo fluxo de download → transcrição → seleção → corte que os
                                            vídeos descobertos automaticamente.
                                        </p>
                                    </div>
                                </AccordionContent>
                            </AccordionItem>
                        </Accordion>
                    </div>
                </SidebarInset>
            </SidebarProvider>
        </>
    );
}
