FROM node:20.19-alpine AS build

WORKDIR /app

ENV NPM_CONFIG_AUDIT=false \
    NPM_CONFIG_FUND=false \
    NPM_CONFIG_FETCH_RETRIES=10 \
    NPM_CONFIG_FETCH_RETRY_MINTIMEOUT=20000 \
    NPM_CONFIG_FETCH_RETRY_MAXTIMEOUT=120000 \
    NPM_CONFIG_FETCH_TIMEOUT=600000

COPY package.json package-lock.json ./

RUN --mount=type=cache,target=/root/.npm \
    npm ci --include=dev --prefer-offline \
    && test -x node_modules/.bin/tsc \
    && test -x node_modules/.bin/vite

COPY . .

ARG VITE_API_BASE_URL=http://localhost:8000/api/v1
ARG VITE_ADMIN_APP_NAME=Панель управления

ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_ADMIN_APP_NAME=$VITE_ADMIN_APP_NAME

RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]