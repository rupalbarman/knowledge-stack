# Build the static bundle
FROM node:22-alpine AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Only set this for local/compose testing without a reverse proxy in front -
# omit it for the real deployment target so the app calls same-origin
# /api/* paths instead, proxied to file-api by nginx.conf below (see
# lib/api.ts's API_BASE_URL fallback).
ARG VITE_BACKEND_URL
ENV VITE_BACKEND_URL=${VITE_BACKEND_URL}
RUN npm run build

# Serve the built bundle
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
