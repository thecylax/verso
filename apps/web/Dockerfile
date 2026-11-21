FROM node:22-alpine AS development

ENV CI=true
RUN corepack enable
WORKDIR /repo/apps/web

COPY package.json pnpm-lock.yaml ./
RUN corepack pnpm install --frozen-lockfile

COPY . .

EXPOSE 5173
CMD ["pnpm", "dev", "--host", "0.0.0.0", "--port", "5173"]

FROM development AS build
RUN corepack pnpm build

FROM nginx:1.27-alpine AS production

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /repo/apps/web/build /usr/share/nginx/html

EXPOSE 80
