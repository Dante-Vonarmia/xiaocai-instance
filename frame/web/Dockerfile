FROM node:20-alpine AS build

WORKDIR /workspace/frame/web

# 复制 package 清单并安装依赖
COPY frame/web/package*.json ./
RUN npm ci --no-audit --no-fund

COPY frame/web ./

ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ARG VITE_FLARE_CORE_ENTRY_URL
ENV VITE_FLARE_CORE_ENTRY_URL=${VITE_FLARE_CORE_ENTRY_URL}

RUN node ./scripts/patch-flare-chat-core.cjs

RUN npm run build

FROM nginx:1.27-alpine

COPY --from=build /workspace/frame/web/dist /usr/share/nginx/html

RUN cat > /etc/nginx/conf.d/default.conf <<'EOF'
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location /api/ {
        proxy_pass http://inst-xiaocai-api:8001/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location = /api {
        return 301 /api/;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
