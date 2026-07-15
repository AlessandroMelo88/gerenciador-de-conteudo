import { router } from '@inertiajs/react';

import { Badge } from '@/components/ui/badge';
import { ConfirmButton } from '@/components/confirm-button';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import type { ActiveWindowVideo } from '@/types/dashboard';

const STATUS_LABEL: Record<string, string> = {
    pending: 'Pendente',
    downloading: 'Baixando',
    downloaded: 'Baixado',
    transcribing: 'Transcrevendo',
    selecting: 'Selecionando',
    cutting: 'Cortando',
    publishing: 'Publicando',
    published: 'Publicado',
    failed: 'Falha',
};

function ScoreBadge({ score }: { score: number | null }) {
    if (score === null) {
        return <Badge variant="secondary">—</Badge>;
    }
    return <Badge variant={score >= 7 ? 'default' : 'destructive'}>{score}</Badge>;
}

export function ActiveWindowTable({ videos }: { videos: ActiveWindowVideo[] }) {
    const curtoCount = videos.filter((v) => v.format === 'curto').length;
    const longoCount = videos.filter((v) => v.format === 'longo').length;

    if (videos.length === 0) {
        return (
            <div className="flex items-center justify-center rounded-lg border border-dashed py-12 text-sm text-muted-foreground">
                Nenhum vídeo baixado agora — a janela está vazia, o próximo ciclo (até 20 min) repõe.
            </div>
        );
    }

    return (
        <div>
            <p className="mb-3 text-sm text-muted-foreground">
                {videos.length} vídeo(s) com arquivo em disco agora ({curtoCount} curto / {longoCount} longo).
                Ordenado por score — os de nota mais baixa (ou sem score ainda) aparecem primeiro, são os
                melhores candidatos a apagar pra abrir vaga.
            </p>
            <div className="overflow-x-auto rounded-lg border">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Título</TableHead>
                            <TableHead>Canal</TableHead>
                            <TableHead>Formato</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Publicado</TableHead>
                            <TableHead>Score</TableHead>
                            <TableHead>Clips</TableHead>
                            <TableHead>Ações</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {videos.map((video) => (
                            <TableRow key={video.id}>
                                <TableCell className="max-w-[280px] truncate" title={video.title}>
                                    {video.title}
                                </TableCell>
                                <TableCell className="text-muted-foreground">{video.sourceChannelName ?? '—'}</TableCell>
                                <TableCell>
                                    <Badge variant={video.format === 'longo' ? 'default' : 'secondary'}>
                                        {video.format === 'longo' ? 'Longo' : 'Curto'}
                                    </Badge>
                                </TableCell>
                                <TableCell className="text-muted-foreground">
                                    {STATUS_LABEL[video.status] ?? video.status}
                                </TableCell>
                                <TableCell className="text-muted-foreground">{video.publishedAt ?? '—'}</TableCell>
                                <TableCell>
                                    <ScoreBadge score={video.score} />
                                </TableCell>
                                <TableCell className="text-muted-foreground">{video.clipCount}</TableCell>
                                <TableCell>
                                    <ConfirmButton
                                        variant="destructive"
                                        size="sm"
                                        description={`Apagar o arquivo bruto de "${video.title}"? Os clips já cortados NÃO são afetados; libera vaga na janela.`}
                                        onConfirm={() =>
                                            router.post(
                                                `/painel/videos/${video.id}/delete`,
                                                {},
                                                { preserveScroll: true },
                                            )
                                        }
                                    >
                                        Apagar
                                    </ConfirmButton>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </div>
        </div>
    );
}
