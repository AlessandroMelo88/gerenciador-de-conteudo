<?php

namespace App\Http\Controllers;

use App\Models\Niche;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;

class NicheController extends Controller
{
    public function store(Request $request): RedirectResponse
    {
        $data = $request->validate([
            'label' => ['required', 'string', 'max:100'],
            'slug' => ['required', 'string', 'max:50', 'unique:niches,slug'],
        ]);

        Niche::create($data);

        return back();
    }
}
