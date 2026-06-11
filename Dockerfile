# Multi-stage build: Frontend + Backend

# Stage 1: Frontend build
FROM node:18-alpine AS frontend-builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Runtime
FROM python:3.10-slim
WORKDIR /app

# Install Node for serving
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

# Copy frontend build
COPY --from=frontend-builder /app/.next ./.next
COPY --from=frontend-builder /app/public ./public
COPY --from=frontend-builder /app/package*.json ./

# Install backend dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything else
COPY . .

# Expose ports
EXPOSE 3000 8000

# Run both servers
CMD ["sh", "-c", "npm start & uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
