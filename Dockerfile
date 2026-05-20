# ── Stage 1: Build ──────────────────────────────────────────────────────────
# Compile TypeScript → JavaScript.
# This stage stays in the builder and is never shipped.
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json tsconfig.json ./
RUN npm ci

COPY src ./src
RUN npm run build

# ── Stage 2: Runtime ────────────────────────────────────────────────────────
# Lean production image — only compiled JS and production dependencies.
# No TypeScript, ts-node, or devDependencies (~80 MB vs ~500 MB in builder).
FROM node:20-alpine AS runtime

WORKDIR /app
ENV NODE_ENV=production

COPY package*.json ./
RUN npm ci --omit=dev

COPY --from=builder /app/dist ./dist

EXPOSE 3000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost:3000/health || exit 1

CMD ["node", "dist/index.js"]
