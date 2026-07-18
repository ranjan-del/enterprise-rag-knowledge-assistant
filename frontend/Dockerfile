# Frontend image for the Enterprise RAG Knowledge Assistant (Angular).
# NOTE: scaffolding only — image is not built during scaffolding.

# Build stage
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

# Serve stage
FROM nginx:alpine
COPY --from=build /app/dist/frontend /usr/share/nginx/html
# TODO: add nginx config to proxy /api to the backend host.
EXPOSE 80
