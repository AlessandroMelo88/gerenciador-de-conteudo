<?php

namespace App\Http\Controllers;

use Inertia\Inertia;
use Inertia\Response;

class DocumentationController extends Controller
{
    public function show(): Response
    {
        return Inertia::render('Documentation');
    }
}
