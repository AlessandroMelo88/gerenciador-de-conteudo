FROM php:8.3-fpm

RUN apt-get update && apt-get install -y     libzip-dev unzip git curl libpng-dev libjpeg-dev libfreetype6-dev     libwebp-dev libonig-dev libxml2-dev libicu-dev cron procps     && docker-php-ext-configure gd --with-freetype --with-jpeg --with-webp     && docker-php-ext-install intl gd pdo_mysql mysqli zip exif pcntl bcmath     && docker-php-ext-enable opcache

COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

RUN git clone https://github.com/phpredis/phpredis.git /usr/src/php/ext/redis     && docker-php-ext-install redis

WORKDIR /var/www/html/painel
EXPOSE 9000
ENTRYPOINT ["docker-php-entrypoint"]
CMD ["php-fpm"]
