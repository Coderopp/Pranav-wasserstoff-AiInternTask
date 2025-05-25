# Railway Deployment Guide

## Quick Start

1. **Fork/Clone** this repository
2. **Connect to Railway**: Go to [railway.app](https://railway.app) and connect your GitHub repository
3. **Deploy Services**: Railway will auto-detect and deploy both frontend and backend services
4. **Set Environment Variables**: Configure your environment variables in Railway dashboard

## Repository Structure for Railway

```
wasserstoff-AiInternTask/
├── railway.json              # Global Railway config (optional)
├── .env.example              # Environment template
├── backend/
│   ├── railway.toml         # Backend Railway config
│   ├── Dockerfile           # Auto-detected by Railway
│   └── requirements.txt     # Auto-detected for Python
├── frontend/
│   ├── railway.toml         # Frontend Railway config
│   ├── package.json         # Auto-detected for Node.js
│   └── vite.config.ts
```

## Deployment Options

### Option 1: Automatic Deployment (Recommended)
1. Connect your GitHub repo to Railway
2. Railway will automatically detect both services
3. Configure environment variables
4. Deploy with one click

### Option 2: Railway CLI
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Deploy
railway up
```

## Environment Variables Setup

### Backend Service Environment Variables
Set these in Railway dashboard for your backend service:

```bash
# Vector Store
QDRANT_URL=your_qdrant_cloud_url
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION=vectorstore

# AI Services
GOOGLE_API_KEY=your_google_api_key
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key

# Models
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=models/embedding-001
LLM_MODEL=llama3-70b-8192

# Application
DATA_DIR=data
```

### Frontend Service Environment Variables
```bash
VITE_API_URL=https://your-backend-service.railway.app
```

## Service Configuration

### Backend Service
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check**: `/health`
- **Port**: Railway automatically sets `$PORT`

### Frontend Service
- **Build Command**: `npm ci && npm run build`
- **Start Command**: `npm run preview -- --host 0.0.0.0 --port $PORT`
- **Health Check**: `/`

## Custom Domains

1. Go to Railway dashboard
2. Select your service
3. Go to "Settings" → "Domains"
4. Add your custom domain
5. Update DNS records as instructed

## Monitoring & Logs

- **Logs**: Available in Railway dashboard under "Deployments"
- **Metrics**: CPU, Memory, Network usage in dashboard
- **Health Checks**: Configured in `railway.toml` files

## Database & Storage

### Vector Database (Qdrant)
- Use Qdrant Cloud for production
- Set `QDRANT_URL` and `QDRANT_API_KEY` in environment variables

### File Storage
- For production, consider using Railway Volumes or cloud storage
- Current setup uses local filesystem (`data/` directory)

## Scaling

Railway provides:
- **Horizontal Scaling**: Multiple instances
- **Vertical Scaling**: More CPU/RAM per instance
- **Auto-scaling**: Based on traffic (Pro plan)

## CI/CD Pipeline

Railway automatically deploys on:
- Git pushes to main branch
- Pull request merges
- Manual deployments

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check `requirements.txt` for backend
   - Check `package.json` for frontend
   - Verify Python/Node versions

2. **Environment Variables**
   - Ensure all required variables are set
   - Check variable names (case-sensitive)

3. **Port Issues**
   - Railway sets `PORT` automatically
   - Use `0.0.0.0` as host, not `localhost`

4. **Health Check Failures**
   - Verify health check endpoints work locally
   - Check timeout settings in `railway.toml`

### Debug Commands
```bash
# Check logs
railway logs

# Connect to shell
railway shell

# Check environment
railway env
```

## Cost Optimization

1. **Use Railway Hobby Plan** for development
2. **Monitor usage** in dashboard
3. **Optimize build times** with proper caching
4. **Use appropriate instance sizes**

## Security Best Practices

1. **Environment Variables**: Never commit API keys
2. **CORS**: Configure proper origins for production
3. **Rate Limiting**: Implement in your FastAPI app
4. **Authentication**: Add proper auth for production use

## Production Checklist

- [ ] Environment variables configured
- [ ] Health checks working
- [ ] Custom domain configured (optional)
- [ ] Monitoring set up
- [ ] Backup strategy for data
- [ ] Error logging configured
- [ ] Performance testing completed
- [ ] Security review completed

## Support

- **Railway Documentation**: [docs.railway.app](https://docs.railway.app)
- **Railway Discord**: Join for community support
- **GitHub Issues**: Report bugs in this repository