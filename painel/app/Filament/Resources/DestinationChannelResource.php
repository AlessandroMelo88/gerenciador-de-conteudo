<?php

namespace App\Filament\Resources;

use App\Filament\Resources\DestinationChannelResource\Pages;
use App\Models\DestinationChannel;
use App\Models\Niche;
use BackedEnum;
use Filament\Actions\BulkActionGroup;
use Filament\Actions\DeleteAction;
use Filament\Actions\DeleteBulkAction;
use Filament\Forms\Components\FileUpload;
use Filament\Forms\Components\Placeholder;
use Filament\Forms\Components\Textarea;
use Filament\Forms\Components\TextInput;
use Filament\Forms\Components\Toggle;
use Filament\Resources\Resource;
use Filament\Schemas\Schema;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Columns\ToggleColumn;
use Filament\Tables\Table;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\HtmlString;

class DestinationChannelResource extends Resource
{
    protected static ?string $model = DestinationChannel::class;

    protected static string|BackedEnum|null $navigationIcon = 'heroicon-o-tv';

    protected static ?string $modelLabel = 'Canal destino';

    protected static ?string $pluralModelLabel = 'Canais destino';

    public static function form(Schema $schema): Schema
    {
        return $schema->schema([
            TextInput::make('slug')
                ->required()
                ->helperText('Identificador único (ex: futebol-em-cortes)'),

            TextInput::make('name')->label('Nome')->required(),

            Niche::selectField('niche', 'Nicho'),

            TextInput::make('youtube_channel_id')
                ->required()
                ->label('YouTube Channel ID (UC...)')
                ->helperText('O ID do canal no YouTube (começa com "UC"). Se o canal ainda não existe, crie-o primeiro em studio.youtube.com — o painel não cria canais novos no YouTube, só publica neles.'),

            Textarea::make('credit_template')
                ->label('Template de créditos')
                ->helperText('Placeholder disponível: {channel_handle}')
                ->default('Créditos: @{channel_handle}'),

            Toggle::make('active')->label('Ativo')->default(true),

            FileUpload::make('watermark_upload')
                ->label('Marca d\'água (overlay nos vídeos)')
                ->image()
                ->disk('branding')
                ->directory('')
                ->visibility('private')
                ->dehydrated(false)
                ->getUploadedFileNameForStorageUsing(
                    fn ($file, callable $get) => 'watermark-'.($get('slug') ?: 'canal').'.png'
                )
                ->afterStateHydrated(function ($component, ?DestinationChannel $record) {
                    if (! $record) {
                        return;
                    }
                    $path = "watermark-{$record->slug}.png";
                    if (Storage::disk('branding')->exists($path)) {
                        $component->state([$path]);
                    }
                })
                ->helperText(
                    'PNG com fundo transparente, aplicado automaticamente no canto superior direito de todo '
                    .'vídeo cortado deste canal. Isso NÃO é o ícone/capa do canal no YouTube — a API do YouTube '
                    .'não permite trocar ícone/capa por código, isso só dá pra fazer manualmente em studio.youtube.com.'
                )
                ->columnSpanFull(),

            Placeholder::make('oauth_instructions')
                ->label('Autorização OAuth')
                ->content(fn (?DestinationChannel $record) => new HtmlString(
                    $record
                        ? '<div class="text-sm space-y-2">'
                            .'<p>Não dá pra autorizar com 1 clique pelo painel: o YouTube exige que <em>você mesmo</em> '
                            .'faça login na sua conta Google e aprove o acesso — isso roda por um comando interativo '
                            .'no terminal, uma vez por canal.</p>'
                            .'<ol class="list-decimal list-inside space-y-1">'
                                .'<li>Abra um terminal no servidor e rode o comando abaixo</li>'
                                .'<li>Abra a URL impressa no navegador, faça login e autorize</li>'
                                .'<li>Cole de volta no terminal a URL completa para onde o navegador tentou redirecionar</li>'
                            .'</ol>'
                            .'<div class="flex items-center gap-2" x-data>'
                                .'<pre x-ref="oauthCmd" class="p-2 bg-gray-100 dark:bg-gray-800 rounded flex-1 overflow-x-auto">docker exec -it clip-processor python -m src.youtube_oauth --channel '.e($record->slug).'</pre>'
                                .'<button type="button" x-on:click="navigator.clipboard.writeText($refs.oauthCmd.innerText); $el.innerText = \'Copiado!\'; setTimeout(() => $el.innerText = \'Copiar\', 1500)" class="fi-btn fi-btn-size-sm fi-color-gray px-3 py-1 rounded border">Copiar</button>'
                            .'</div>'
                          .'</div>'
                        : '<em>Salve o canal primeiro para ver o comando de autorização.</em>'
                ))
                ->columnSpanFull(),
        ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                TextColumn::make('slug')->searchable(),
                TextColumn::make('name')->label('Nome'),
                TextColumn::make('niche')->label('Nicho')->badge(),
                TextColumn::make('oauth_status')
                    ->label('OAuth')
                    ->badge()
                    ->color(fn (string $state): string => match ($state) {
                        'authorized' => 'success',
                        'expired' => 'danger',
                        'missing' => 'gray',
                        default => 'primary',
                    }),
                ToggleColumn::make('active')->label('Ativo'),
                TextColumn::make('youtube_channel_id')->label('YT Channel ID')->copyable(),
            ])
            ->actions([
                DeleteAction::make(),
            ])
            ->bulkActions([
                BulkActionGroup::make([
                    DeleteBulkAction::make(),
                ]),
            ])
            ->defaultSort('created_at', 'desc');
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListDestinationChannels::route('/'),
            'edit'  => Pages\EditDestinationChannel::route('/{record}/edit'),
        ];
    }
}
