import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

export type PromptProfile = {
    id: number;
    slug: string;
    name: string;
    niche: string;
    nicheAliases?: string[];
};

export function PromptProfileSelect({
    profiles,
    value,
    niche,
    onChange,
}: {
    profiles: PromptProfile[];
    value: string;
    niche?: string;
    onChange: (id: string) => void;
}) {
    const configuredNiche = niche?.trim().toLocaleLowerCase();
    const compatibleProfiles = profiles.filter((profile) => {
        if (!configuredNiche) {
            return true;
        }
        return [profile.slug, profile.niche, ...(profile.nicheAliases ?? [])].some(
            (candidate) => candidate.toLocaleLowerCase() === configuredNiche,
        );
    });

    return (
        <Select value={value || 'auto'} onValueChange={(selected) => onChange(selected === 'auto' ? '' : selected)}>
            <SelectTrigger className="w-full">
                <SelectValue placeholder="Automático pelo nicho" />
            </SelectTrigger>
            <SelectContent>
                <SelectItem value="auto">Automático pelo nicho</SelectItem>
                {compatibleProfiles.map((profile) => (
                    <SelectItem key={profile.id} value={String(profile.id)}>
                        {profile.name}
                    </SelectItem>
                ))}
            </SelectContent>
        </Select>
    );
}
