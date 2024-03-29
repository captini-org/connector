FROM node:18-alpine AS builder

ARG ROOT_URL
ARG WEBSOCKET_URL

WORKDIR /app
COPY angular.json karma.conf.js package.json README.md tsconfig.app.json tsconfig.spec.json package-lock.json tsconfig.json ./
RUN npm ci

COPY . .
RUN find src -name "*.ts" -exec sed -i "s_https://captini-backend.herokuapp.com_${ROOT_URL}_g; s_http://127.0.0.1:8000_${ROOT_URL}_g" '{}' \;
RUN sed -i "s_http://127.0.0.1:8083_${ROOT_URL}_; s_ws://0.0.0.0:3000_${WEBSOCKET_URL}_" src/app/common/global.ts && cat src/app/common/global.ts
RUN npm run build

FROM nginx:1.23.3 AS prod-runtime

RUN echo 'server { listen 80; root /usr/share/nginx/html; location / { try_files $uri $uri/ /; } }' > /etc/nginx/conf.d/default.conf

COPY --from=builder /app/dist/front-end-captini /usr/share/nginx/html
