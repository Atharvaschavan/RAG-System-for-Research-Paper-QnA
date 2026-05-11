# 🚀 Deployment Guide

This guide covers deploying the Research Paper Q&A system to various platforms.

---

## 📋 Pre-deployment Checklist

- [ ] `.env` file configured locally & tested
- [ ] All dependencies in `requirements.txt` pinned to versions
- [ ] Error handling & logging verified
- [ ] README.md and documentation complete
- [ ] GitHub repository initialized & clean

---

## 1️⃣ Local Development Server

### Quick Start
```bash
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate (Windows)
pip install -r requirements.txt
streamlit run app.py
```

### With Custom Port
```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

---

## 2️⃣ Streamlit Cloud (Recommended for MVP)

**Pros:** Zero DevOps, automatic scaling, free tier available  
**Cons:** Single-user, limited compute

### Setup

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Initial deployment"
   git push origin main
   ```

2. **Create Streamlit Cloud Account**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub

3. **Deploy App**
   - Click "New app"
   - Select your repository & file (`app.py`)
   - Click "Deploy"

4. **Set Secrets**
   - Go to app settings → Secrets
   - Add your Google API key:
     ```
     GOOGLE_API_KEY = "your_key_here"
     ```

5. **Access Your App**
   - URL: `https://share.streamlit.io/your-username/RA_LLM/app.py`

---

## 3️⃣ Docker & Container Platforms

### Docker Setup

**Dockerfile:**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements & install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Expose port
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Build & Run Locally

```bash
# Build
docker build -t research-paper-qa:latest .

# Run
docker run -e GOOGLE_API_KEY=your_key_here \
           -p 8501:8501 \
           research-paper-qa:latest
```

### Push to Docker Hub

```bash
# Tag
docker tag research-paper-qa:latest your-username/research-paper-qa:latest

# Login
docker login

# Push
docker push your-username/research-paper-qa:latest
```

---

## 4️⃣ Railway.app (Easiest PaaS)

**Pros:** Simple, free tier, GitHub integration  
**Cons:** Limited resources

### Steps

1. **Connect GitHub**
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repo

2. **Configure Environment**
   - Go to Variables
   - Add `GOOGLE_API_KEY`

3. **Add Procfile**
   Create `Procfile` in project root:
   ```
   web: streamlit run app.py --server.port=${PORT:-8501}
   ```

4. **Deploy**
   - Push to GitHub
   - Railway auto-deploys

---

## 5️⃣ AWS (ECS + Fargate)

**Pros:** Scalable, professional, multi-user capable  
**Cons:** Complex, requires AWS knowledge

### Prerequisites
```bash
# Install AWS CLI
pip install awscli

# Configure
aws configure
```

### Deploy

1. **Create ECS Cluster**
   ```bash
   aws ecs create-cluster --cluster-name ra-llm-cluster
   ```

2. **Create Task Definition**
   ```bash
   aws ecs register-task-definition \
     --cli-input-json file://task-definition.json
   ```

3. **Create Service**
   ```bash
   aws ecs create-service \
     --cluster ra-llm-cluster \
     --service-name ra-llm-service \
     --task-definition ra-llm-task
   ```

### Monitoring
```bash
aws ecs describe-services --cluster ra-llm-cluster --services ra-llm-service
```

---

## 6️⃣ Google Cloud Run

**Pros:** Serverless, pay-per-use, good for spiky traffic  
**Cons:** Cold starts, timeout limits

### Setup

1. **Install Google Cloud CLI**
   ```bash
   curl https://sdk.cloud.google.com | bash
   gcloud init
   ```

2. **Create `.gcloudignore`**
   ```
   __pycache__
   .venv/
   .git/
   .gitignore
   ```

3. **Deploy**
   ```bash
   gcloud run deploy research-paper-qa \
     --source . \
     --platform managed \
     --region us-central1 \
     --set-env-vars GOOGLE_API_KEY=your_key_here
   ```

---

## 7️⃣ Azure Container Instances

### Deploy

```bash
# Set variables
RESOURCE_GROUP="ra-llm-rg"
REGISTRY_NAME="rallmregistry"
IMAGE_NAME="research-paper-qa"

# Create resource group
az group create --name $RESOURCE_GROUP --location eastus

# Build image
az acr build --registry $REGISTRY_NAME --image $IMAGE_NAME:latest .

# Deploy
az container create \
  --resource-group $RESOURCE_GROUP \
  --name research-paper-qa \
  --image $REGISTRY_NAME.azurecr.io/$IMAGE_NAME:latest \
  --environment-variables GOOGLE_API_KEY=your_key_here \
  --ports 8501
```

---

## 8️⃣ Heroku (Sunset - Not Recommended)

Heroku is discontinuing free tier. Use Railway or Streamlit Cloud instead.

---

## Environment Variables Reference

| Variable | Required | Example |
|----------|----------|---------|
| `GOOGLE_API_KEY` | ✅ | `AIza...` |
| `LOG_LEVEL` | ❌ | `INFO` |
| `DEBUG` | ❌ | `false` |
| `CHUNK_SIZE` | ❌ | `500` |
| `TOP_K` | ❌ | `4` |
| `PORT` | ❌ | `8501` |

---

## Monitoring & Logging

### Local Logging
```bash
streamlit run app.py --logger.level=debug
```

### Cloud Logging

**AWS CloudWatch**
```bash
aws logs tail /aws/ecs/ra-llm --follow
```

**Google Cloud Logging**
```bash
gcloud logging read --limit 100 --format json
```

---

## Performance Optimization

### For Production

1. **Caching**
   - Enable query cache (default: ON)
   - Use Redis for multi-instance setups

2. **Model Loading**
   - Pre-download embeddings model
   - Use GPU if available

3. **Concurrent Requests**
   - Use Streamlit Community Cloud for single-user
   - Use FastAPI + async for multi-user

---

## Scaling Considerations

| Traffic Level | Recommended | Setup |
|---------------|-------------|-------|
| **<100 QPS** | Streamlit Cloud | Single instance |
| **100-1000 QPS** | Cloud Run / Container | Auto-scaling |
| **>1000 QPS** | ECS / Kubernetes | Load balancing + DB |

### Multi-Instance Setup
```python
# Use Redis for shared cache
import redis
cache = redis.Redis(host='localhost', port=6379)
```

---

## Troubleshooting Deployments

### Issue: "API Key not found"
```bash
# Verify environment variable
echo $GOOGLE_API_KEY  # or: $env:GOOGLE_API_KEY (PowerShell)
```

### Issue: "Port already in use"
```bash
streamlit run app.py --server.port 8502
```

### Issue: "Out of memory"
```dockerfile
# Increase memory in Docker
# When running: docker run -m 2g ...
```

### Issue: "Slow PDF processing"
- Reduce `CHUNK_SIZE`
- Use GPU with `embedding_device=cuda`
- Pre-process PDFs offline

---

## CI/CD Pipeline Example

### GitHub Actions `.github/workflows/deploy.yml`

```yaml
name: Deploy to Streamlit Cloud

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: |
          pip install streamlit
          streamlit run app.py --logger.level=error
```

---

## Security Best Practices

1. **Never commit `.env` files**
   - Use `.gitignore`
   - Use platform-specific secrets manager

2. **Rotate API keys regularly**
   ```bash
   # In Google AI Studio, regenerate key quarterly
   ```

3. **Use HTTPS only**
   - All cloud platforms enforce this by default

4. **Limit API rate**
   - Google Generative AI: 60 RPM free tier
   - Consider rate limiting

5. **Monitor usage**
   - Set up billing alerts
   - Track API call metrics

---

## Cost Estimation

| Platform | Free Tier | Paid Starting |
|----------|-----------|---------------|
| **Streamlit Cloud** | 1 app | $5/month |
| **Railway** | $5 credits | Usage-based |
| **Cloud Run** | 2M requests | $0.40 per 1M |
| **ECS Fargate** | 30 days trial | ~$15/month |
| **Google Generative AI** | 60 RPM | Varies |

---

## Support & Resources

- [Streamlit Docs](https://docs.streamlit.io/)
- [LangChain Docs](https://python.langchain.com/)
- [Google Generative AI](https://ai.google.dev/)
- [Docker Docs](https://docs.docker.com/)

---

**Last Updated:** May 2026
