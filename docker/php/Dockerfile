FROM node:22-bookworm-slim AS frontend

WORKDIR /build
COPY painel/package.json painel/package-lock.json ./
RUN npm ci --ignore-scripts
COPY painel/resources ./resources
COPY painel/vite.config.js painel/tsconfig.json painel/components.json ./
RUN npm run build

FROM composer:2.8 AS vendor

WORKDIR /app
COPY painel/composer.json painel/composer.lock ./
RUN composer install \
    --no-dev \
    --no-interaction \
    --no-progress \
    --prefer-dist \
    --no-scripts \
    --optimize-autoloader

FROM php:8.3-fpm-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libicu-dev \
        libonig-dev \
        libxml2-dev \
        libzip-dev \
        unzip \
    && docker-php-ext-install -j"$(nproc)" bcmath intl mbstring opcache pcntl pdo_mysql \
    && pecl install redis \
    && docker-php-ext-enable redis \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /var/www/html/painel

COPY painel ./
COPY --from=vendor /app/vendor ./vendor
COPY --from=frontend /build/public/build ./public/build
COPY docker/php/bootstrap-panel /usr/local/bin/bootstrap-panel

RUN chmod +x /usr/local/bin/bootstrap-panel \
    && mkdir -p storage/framework/cache/data storage/framework/sessions storage/framework/views storage/logs bootstrap/cache \
    && chown -R www-data:www-data storage bootstrap/cache

CMD ["php-fpm", "-F"]
