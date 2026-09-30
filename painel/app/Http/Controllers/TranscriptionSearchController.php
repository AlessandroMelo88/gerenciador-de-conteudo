<?php

namespace App\Http\Controllers;

use App\Services\TranscriptSearch;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;
use Illuminate\Validation\Rule;

/** GET /painel/transcricoes/busca — trechos das transcrições por texto, significado ou os dois. */
class TranscriptionSearchController extends Controller
{
    public function search(Request $request, TranscriptSearch $busca): JsonResponse
    {
        // Validator manual: a resposta é sempre JSON 422, mesmo sem header Accept.
        $validator = Validator::make($request->query(), [
            'q' => ['required', 'string', 'min:2', 'max:200'],
            'modo' => ['nullable', 'string', Rule::in(TranscriptSearch::MODOS)],
            'limit' => ['nullable', 'integer', 'between:1,50'],
        ]);

        if ($validator->fails()) {
            return response()->json(['message' => 'Parâmetros inválidos.', 'errors' => $validator->errors()], 422);
        }

        $dados = $validator->validated();

        return response()->json($busca->search(
            trim($dados['q']),
            $dados['modo'] ?? 'hibrida',
            (int) ($dados['limit'] ?? 20),
        ));
    }
}
