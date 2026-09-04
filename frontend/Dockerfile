# ==============================================================================
# IP-SAKTI Sahayak — Frontend Dockerfile (Next.js 16)
# ==============================================================================

FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production \
    PORT=3000

# Install dependencies first for layer caching
COPY package.json package-lock.json ./
RUN npm ci

# Copy application source
COPY . .

# Build argument to bake in API URL at build time if needed
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-http://localhost:8000}

# Build Next.js application
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
