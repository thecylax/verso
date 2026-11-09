FROM node:22-alpine

ENV CI=true
RUN corepack enable
WORKDIR /repo/apps/web

COPY package.json pnpm-lock.yaml ./
RUN corepack pnpm install --frozen-lockfile

COPY . .

EXPOSE 5173
CMD ["pnpm", "dev", "--host", "0.0.0.0", "--port", "5173"]
