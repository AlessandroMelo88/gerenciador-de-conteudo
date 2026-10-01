<?php

namespace App\Enums;

/** Formato de vídeo de um canal destino. Contrato com o clip-processor: auto | short_only | both. */
enum LongFormatMode: string
{
    case Auto = 'auto';
    case ShortOnly = 'short_only';
    case Both = 'both';
}
