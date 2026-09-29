<?php

return [

    /*
    |--------------------------------------------------------------------------
    | Pipeline settings
    |--------------------------------------------------------------------------
    |
    | These values are read from the environment here so they remain available
    | when Laravel configuration is cached in production.
    |
    */

    'max_uploads_per_day' => min(max((int) env('MAX_UPLOADS_PER_DAY', 6), 0), 6),

    'manual_approval_required' => filter_var(
        env('MANUAL_APPROVAL_REQUIRED', false),
        FILTER_VALIDATE_BOOLEAN,
    ),

];
