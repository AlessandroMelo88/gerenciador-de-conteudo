<?php

namespace App\Http\Controllers;

use App\Services\MetricsReport;
use Inertia\Inertia;
use Inertia\Response;

class MetricsController extends Controller
{
    /** GET /painel/metricas — o que rende mais visualização, por formato e por canal-fonte. */
    public function index(MetricsReport $report): Response
    {
        return Inertia::render('Metrics', $report->build());
    }
}
