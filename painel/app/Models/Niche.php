<?php

namespace App\Models;

use Filament\Forms\Components\Select;
use Filament\Forms\Components\TextInput;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Support\Str;

class Niche extends Model
{
    protected $fillable = [
        'slug',
        'label',
    ];

    /**
     * Select reutilizável para o campo de nicho (target_niche / niche) em
     * SourceChannelResource e DestinationChannelResource. Carrega os nichos
     * existentes do banco (não uma lista fixa) e permite criar um novo nicho
     * direto do select — assim que criado, ele já aparece nos outros formulários
     * e ganha automaticamente uma tab em Canais Fonte (ver ListSourceChannels::getTabs()).
     */
    public static function selectField(string $name, string $label = 'Nicho'): Select
    {
        return Select::make($name)
            ->label($label)
            ->options(fn () => static::query()->orderBy('label')->pluck('label', 'slug'))
            ->searchable()
            ->preload()
            ->required()
            ->createOptionForm([
                TextInput::make('label')
                    ->label('Nome do nicho')
                    ->required()
                    ->live(onBlur: true)
                    ->afterStateUpdated(fn ($state, callable $set) => $set('slug', Str::slug($state))),
                TextInput::make('slug')
                    ->label('Slug')
                    ->required()
                    ->unique('niches', 'slug'),
            ])
            ->createOptionUsing(function (array $data): string {
                return static::create($data)->slug;
            });
    }
}
