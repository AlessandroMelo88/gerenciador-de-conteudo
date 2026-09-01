<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class SystemSetting extends Model
{
    protected $fillable = ['key', 'value', 'description'];

    public static function get(string $key, mixed $default = null): mixed
    {
        $setting = static::where('key', $key)->first();
        if (!$setting) {
            return $default;
        }

        $val = $setting->value;
        if ($val === 'true') return true;
        if ($val === 'false') return false;

        return $val;
    }

    public static function set(string $key, mixed $value, ?string $description = null): void
    {
        $stringValue = is_bool($value) ? ($value ? 'true' : 'false') : (string)$value;

        static::updateOrCreate(
            ['key' => $key],
            ['value' => $stringValue, 'description' => $description]
        );
    }
}
