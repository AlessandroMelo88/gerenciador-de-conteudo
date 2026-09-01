<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class PromptProfile extends Model
{
    use HasFactory;

    protected $table = 'prompt_profiles';

    protected $fillable = [
        'slug',
        'name',
        'niche',
        'niche_aliases',
        'selection_short_prompt',
        'selection_long_prompt',
        'metadata_short_prompt',
        'metadata_long_prompt',
        'thumbnail_prompt',
        'active',
    ];

    protected $casts = [
        'niche_aliases' => 'array',
        'active' => 'bool',
    ];

    /** @return HasMany<SourceChannel, $this> */
    public function sourceChannels(): HasMany
    {
        return $this->hasMany(SourceChannel::class, 'prompt_profile_id');
    }

    /** @return HasMany<DestinationChannel, $this> */
    public function destinationChannels(): HasMany
    {
        return $this->hasMany(DestinationChannel::class, 'prompt_profile_id');
    }

    /** @param Builder<self> $query */
    public function scopeActive(Builder $query): void
    {
        $query->where('active', true);
    }

    public static function resolveId(?int $profileId, ?string $niche): ?int
    {
        $niche = trim((string) $niche);
        if ($profileId === null && $niche === '') {
            return null;
        }

        $query = self::query()->active();
        if ($profileId !== null) {
            $query->whereKey($profileId);
        }

        if ($niche !== '') {
            $query->where(function (Builder $query) use ($niche): void {
                $query
                    ->where('slug', $niche)
                    ->orWhere('niche', $niche)
                    ->orWhereJsonContains('niche_aliases', $niche);
            });
        }

        $id = $query->orderBy('id')->value('id');

        return $id === null ? null : (int) $id;
    }
}
