# 🐳 Docker Deployment Guide

## Quick Docker Setup

### 1. **Simple Container (Development)**
```bash
# Build the image
docker build -t ai-voice-assistant .

# Run with environment file
docker run -d \
  --name voice-assistant \
  -p 8000:8000 \
  --env-file .env \
  ai-voice-assistant
```

### 2. **Full Production Stack (with PostgreSQL)**
```bash
# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f app
```

### 3. **Development with Hot Reload**
```bash
# Mount source code for development
docker run -d \
  --name voice-assistant-dev \
  -p 8000:8000 \
  -v $(pwd)/src:/app/src \
  --env-file .env \
  ai-voice-assistant \
  uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## Docker Configuration

### **Dockerfile Highlights:**
- ✅ **Python 3.13** - Latest Python for modern compatibility
- ✅ **Non-root user** - Security best practice
- ✅ **Health checks** - Built-in monitoring
- ✅ **Optimized layers** - Fast builds with proper caching
- ✅ **Minimal dependencies** - Only required packages

### **Docker Compose Features:**
- ✅ **PostgreSQL** - Production database (optional)
- ✅ **Nginx** - Reverse proxy and SSL termination
- ✅ **Health monitoring** - Automatic restart on failure
- ✅ **Volume persistence** - Data and logs preserved
- ✅ **Environment variables** - Secure API key management

## Production Deployment

### **Environment Variables Required:**
```bash
# API Keys (required)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+15551234567
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
GHL_API_KEY=xxxxxxxxxxxxx
GHL_WEBHOOK_SECRET=xxxxxxxxxxxxx
AWS_ACCESS_KEY_ID=xxxxxxxxxxxxx
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxx

# Webhook URL (required for GHL integration)
WEBHOOK_BASE_URL=https://yourdomain.com

# Optional (defaults provided)
DATABASE_URL=postgresql://postgres:password@postgres:5432/voice_assistant
ENVIRONMENT=production
```

### **Scaling Options:**
```bash
# Scale the app service
docker-compose up -d --scale app=3

# Use external database
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### **Health Monitoring:**
```bash
# Check container health
docker ps

# Test health endpoint
curl http://localhost:8000/health

# View application logs
docker-compose logs -f app

# Monitor resource usage
docker stats
```

## Deployment Platforms

### **AWS ECS:**
```bash
# Build and push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
docker tag ai-voice-assistant:latest <account>.dkr.ecr.<region>.amazonaws.com/ai-voice-assistant:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/ai-voice-assistant:latest
```

### **Digital Ocean:**
```bash
# Deploy to App Platform
doctl apps create --spec .do/app.yaml
```

### **Kubernetes:**
```bash
# Apply k8s manifests
kubectl apply -f k8s/
```

## Troubleshooting

### **Common Issues:**
1. **Port conflicts**: Change `-p 8001:8000` if port 8000 is busy
2. **API key errors**: Check `.env` file has all required keys
3. **Database connection**: Ensure PostgreSQL is running in compose
4. **Memory issues**: Increase Docker memory limit

### **Debugging:**
```bash
# Interactive shell in container
docker exec -it voice-assistant bash

# Check application logs
docker logs voice-assistant

# Test specific endpoint
docker exec voice-assistant curl localhost:8000/health
```

## Performance Optimization

### **Image Size:**
- Current image: ~200MB (Python 3.13 slim)
- Multi-stage build for production: ~150MB
- Alpine variant: ~100MB (but less compatible)

### **Resource Limits:**
```yaml
# In docker-compose.yml
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
    reservations:
      memory: 256M
```

---

## 🎯 Production-Ready Features

✅ **Security**: Non-root user, minimal attack surface
✅ **Monitoring**: Health checks and logging
✅ **Scalability**: Horizontal scaling support
✅ **Reliability**: Automatic restarts and graceful shutdown
✅ **Performance**: Optimized image layers and caching

*The Docker setup is fully production-ready and interview-demonstration capable!*
