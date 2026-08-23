# LAWTRIX Production Deployment Guide

## 🚨 PRE-DEPLOYMENT SECURITY CHECKLIST

### ✅ Required Actions BEFORE First Deploy

1. **API Keys - CRITICAL**
   - [ ] Rotate ALL API keys (Sarvam, Gemini exposed in git)
   - [ ] Get new Sarvam AI key: https://sarvam.ai
   - [ ] Get new Gemini key: https://makersuite.google.com/app/apikey
   - [ ] Update all keys in production environment variables

2. **Environment Configuration**
   - [ ] Copy `.env.example` to `.env` (backend)
   - [ ] Copy `.env.example` to `.env.local` (frontend)
   - [ ] Fill in ALL required values
   - [ ] Set `ENVIRONMENT=production`
   - [ ] Configure CORS_ORIGINS with actual domain (NO wildcards!)

3. **Git Repository Cleanup**
   - [ ] Run: `git filter-branch --index-filter "git rm --cached --ignore-unmatch chakravyuha/backend/.env" HEAD`
   - [ ] Force push to overwrite history: `git push origin --force --all`
   - [ ] Verify no secrets in git: `git log --all -- '*.env'` (should be empty)

---

## 🔧 Environment Variables

### Backend (Required)

```bash
# LLM Providers
SARVAM_API_KEY=sk_xxxxx  # Get from https://sarvam.ai
GEMINI_API_KEY=AIxxxxx   # Get from Google AI Studio
LLM_PRIORITY=gemini,mistral,openrouter,ollama,sarvam

# Database
DATABASE_URL=postgresql://user:pass@host:5432/lawtrix

# Redis (for rate limiting)
REDIS_URL=redis://localhost:6379/0

# CORS - CRITICAL: Use actual domains, NO "*"!
CORS_ORIGINS=https://lawtrix.app,https://www.lawtrix.app

# Environment
ENVIRONMENT=production
PORT=8000
LOG_LEVEL=INFO
```

### Frontend (Required)

```bash
NEXT_PUBLIC_API_URL=https://api.lawtrix.app
NEXT_PUBLIC_ENVIRONMENT=production
```

---

## 🚀 Deployment Options

### Option 1: Railway (Recommended)

**Backend:**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy from chakravyuha/backend/
cd chakravyuha/backend
railway init
railway up

# Set environment variables
railway variables set SARVAM_API_KEY=sk_xxxxx
railway variables set GEMINI_API_KEY=AIxxxxx
railway variables set CORS_ORIGINS=https://lawtrix.app
railway variables set ENVIRONMENT=production
```

**Frontend:**
```bash
# Deploy from chakravyuha/chakravyuha-ui/
cd chakravyuha/chakravyuha-ui
vercel --prod

# Set environment variables in Vercel dashboard
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

### Option 2: Docker

```dockerfile
# Backend Dockerfile (chakravyuha/backend/Dockerfile)
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t lawtrix-backend ./chakravyuha/backend
docker run -p 8000:8000 --env-file ./chakravyuha/backend/.env lawtrix-backend
```

### Option 3: Traditional Server

```bash
# Backend
cd chakravyuha/backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend
cd chakravyuha/chakravyuha-ui
npm install
npm run build
npm start
```

---

## 🔒 Security Hardening

### 1. HTTPS Setup

**With Nginx:**
```nginx
server {
    listen 443 ssl http2;
    server_name api.lawtrix.app;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. Rate Limiting

Install slowapi:
```bash
pip install slowapi
```

Add to `main.py`:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to routes:
@router.post("/api/schemes/check")
@limiter.limit("10/minute")
async def check_eligibility(request: Request):
    ...
```

### 3. Database Security

```bash
# Use connection pooling
DATABASE_URL=postgresql://user:pass@host:5432/lawtrix?pool_size=20&max_overflow=0

# Enable SSL
DATABASE_URL=postgresql://user:pass@host:5432/lawtrix?sslmode=require
```

---

## 📊 Monitoring & Logging

### Error Tracking (Sentry)

```bash
# Install
pip install sentry-sdk[fastapi]

# Configure in main.py
import sentry_sdk
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment=os.getenv("ENVIRONMENT"),
)
```

### Health Checks

Already implemented at `/health` endpoint.

Monitor with:
```bash
# Simple uptime monitor
*/5 * * * * curl -f https://api.lawtrix.app/health || alert
```

---

## 🧪 Pre-Deployment Testing

```bash
# Backend tests
cd chakravyuha/backend
pytest --cov=. --cov-report=html
# Target: 80%+ coverage

# Frontend build
cd chakravyuha/chakravyuha-ui
npm run build
# Should complete with no errors

# E2E tests
npm run test:e2e
```

---

## 🔄 Deployment Workflow

1. **Development**
   ```bash
   git checkout -b feature/my-feature
   # Make changes
   git commit -m "feat: add feature"
   git push origin feature/my-feature
   ```

2. **Staging** (optional)
   ```bash
   git checkout staging
   git merge feature/my-feature
   railway up --environment staging
   ```

3. **Production**
   ```bash
   git checkout main
   git merge staging
   git tag v1.0.1
   railway up --environment production
   ```

---

## 🚨 Rollback Procedure

**Railway:**
```bash
railway rollback
```

**Docker:**
```bash
docker pull lawtrix-backend:previous-tag
docker stop lawtrix-backend
docker run -d --name lawtrix-backend lawtrix-backend:previous-tag
```

**Traditional:**
```bash
git revert HEAD
git push
# Redeploy
```

---

## 📞 Support & Troubleshooting

### Common Issues

**1. "We can't reach the service"**
- Check `NEXT_PUBLIC_API_URL` in frontend `.env.local`
- Verify backend is running: `curl https://api.lawtrix.app/health`
- Check CORS settings allow your frontend domain

**2. "Invalid API key"**
- Verify keys are set in environment (not hardcoded)
- Check key hasn't been revoked
- Rotate and update if exposed

**3. "Rate limit exceeded"**
- Implement caching for frequent requests
- Add Redis for distributed rate limiting
- Consider upgrading plan limits

---

## 📝 Post-Deployment

- [ ] Test all critical user flows (RTI, CPGRAMS, schemes)
- [ ] Monitor error rates in Sentry
- [ ] Check logs for warnings
- [ ] Verify analytics tracking
- [ ] Update documentation with prod URLs
- [ ] Announce to users

---

## 🔐 Security Incident Response

If API keys are leaked:
1. Immediately rotate all keys
2. Review git history: `git log --all -- '*.env'`
3. Check billing for unauthorized usage
4. Update keys in all environments
5. Force push cleaned history if needed

---

**Last Updated**: 2026-08-23
**Maintainer**: LAWTRIX Team
