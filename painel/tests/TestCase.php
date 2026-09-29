<?php

namespace Tests;

use Illuminate\Foundation\Http\Middleware\PreventRequestForgery;
use Illuminate\Foundation\Testing\TestCase as BaseTestCase;

abstract class TestCase extends BaseTestCase
{
    protected function setUp(): void
    {
        parent::setUp();

        $this->withoutVite();
        config([
            'filesystems.disks.branding.root' => storage_path('framework/testing/branding'),
            'filesystems.disks.clips-videos.root' => storage_path('framework/testing/clips-videos'),
        ]);
        $this->withoutMiddleware(PreventRequestForgery::class);
    }
}
