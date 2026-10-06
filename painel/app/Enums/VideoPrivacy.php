<?php

namespace App\Enums;

/** Privacidade do vídeo no YouTube. Contrato com o clip-processor: private | public. */
enum VideoPrivacy: string
{
    case Private = 'private';
    case Public = 'public';
}
