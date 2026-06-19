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

# Copy package files and install Node deps
COPY package*.json ./
RUN npm ci --only=production

# Copy frontend build
COPY --from=frontend-builder /app/.next ./.next
COPY --from=frontend-builder /app/public ./public

# Install backend dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything else
COPY . .

# Expose alleen de frontend port — Railway zet PORT=3000, geen conflict met uvicorn op 8000
EXPOSE 3000

# Start: uvicorn backend op 8000 in achtergrond, Next.js frontend op PORT(=3000) in voorgrond
CMD ["sh", "-c", "cd /app/backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 & cd /app && exec npm start"]
