FROM node:20-alpine

WORKDIR /app

# pnpm via Corepack (recommended for Node images)
RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml .npmrc ./
RUN pnpm install --frozen-lockfile

COPY . .

# Build once; run via `vite preview` (works with current adapter-auto setup)
RUN pnpm build

EXPOSE 4173

CMD ["pnpm", "preview", "--", "--host", "0.0.0.0", "--port", "4173"]
