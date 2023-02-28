FROM node:18-alpine AS builder

ARG ROOT_URL

WORKDIR /app
COPY angular.json karma.conf.js package.json README.md tsconfig.app.json tsconfig.spec.json package-lock.json tsconfig.json ./
RUN npm ci

COPY . .
RUN find src -name "*.ts" -exec sed -i "s_https://captini-backend.herokuapp.com_${ROOT_URL}_g" '{}' \;
RUN npm run build

FROM nginx:1.23.3 AS prod-runtime
COPY --from=builder /app/dist/front-end-captini /usr/share/nginx/html
