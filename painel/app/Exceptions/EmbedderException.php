<?php

namespace App\Exceptions;

use RuntimeException;

/** O sidecar de embeddings falhou (timeout, HTTP de erro, resposta inválida ou sem configuração). */
class EmbedderException extends RuntimeException {}
