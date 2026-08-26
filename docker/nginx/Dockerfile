FROM node:22-bookworm-slim AS frontend

WORKDIR /build
COPY painel/package.json painel/package-lock.json ./
RUN npm ci --ignore-scripts
COPY painel/resources ./resources
COPY painel/vite.config.js painel/tsconfig.json painel/components.json ./
RUN npm run build

FROM nginx:1.27-alpine

COPY docker/nginx/canaldecortes.conf /etc/nginx/conf.d/default.conf
COPY painel/public /var/www/html/painel/public
COPY --from=frontend /build/public/build /var/www/html/painel/public/build
