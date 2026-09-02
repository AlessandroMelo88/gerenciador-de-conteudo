export type ClipFormat = 'curto' | 'longo';

export type ClipRow = {
    id: number;
    title: string;
    score: number | null;
    trecho: string;
    startTime?: number | null;
    endTime?: number | null;
    sourceVideoTitle: string | null;
    sourceChannelName: string | null;
    format: ClipFormat;
    destinationChannelName: string | null;
    destinationChannelSlug?: string | null;
    niche?: string | null;
    createdAt: string | null;
    updatedAt: string | null;
    uploadError: string | null;
    previewUrl: string;
    thumbnailUrl?: string;
    hasVideoFile?: boolean;
    hasThumbnailFile?: boolean;
    description?: string | null;
    tags?: string | null;
    destinationTemplate?: {
        headerTitle?: string;
        headerBadge?: string;
        accentColor?: string;
        bgStyle?: string;
        subtitleColor?: string;
        ctaText?: string;
    } | null;
    destinationChannelWatermarkUrl?: string | null;
};

export type QuotaChannel = {
    name: string;
    count: number;
    limit: number;
};

export type PipelineOverview = {
    publishedCurto: number;
    publishedLongo: number;
    backlogCurto: number;
    backlogLongo: number;
};

export type ActiveWindowVideo = {
    id: number;
    title: string;
    format: ClipFormat;
    status: string;
    progress: number;
    paused: boolean;
    priority: number;
    queuePosition: number | null;
    processing: boolean;
    canDelete: boolean;
    sourceChannelName: string | null;
    publishedAt: string | null;
    score: number | null;
    clipCount: number;
};

export type DashboardPageProps = {
    quota: QuotaChannel[];
    overview: PipelineOverview;
    pendingClips: ClipRow[];
    queuedClips: ClipRow[];
    failures: ClipRow[];
    failedSourceVideoCount: number;
    activeWindow: ActiveWindowVideo[];
    auth: {
        user: { name: string; email: string } | null;
    };
    flash: {
        success: string | null;
        error: string | null;
    };
};
