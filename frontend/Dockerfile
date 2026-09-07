# ==============================================================================
# Aşama 1: Builder (React + TypeScript Derlemesi)
# ==============================================================================
FROM node:20-alpine AS builder
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ==============================================================================
# Aşama 2: Production (Nginx ile Statik Dosyaları Sunma - Ultra Hafif ~25MB)
# ==============================================================================
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
