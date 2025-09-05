# 🚀 TractionBuild Railway Deployment Guide

## Overview

This guide will help you deploy TractionBuild to Railway, transforming your local development environment into a production-ready service accessible to others.

## Prerequisites

### Required Accounts & Tools
- **Railway Account**: [Sign up at railway.app](https://railway.app)
- **Railway CLI**: `npm install -g @railway/cli`
- **Git**: For version control
- **API Keys**: OpenAI and xAI

### System Requirements
- Node.js (for Railway CLI)
- Git
- Internet connection

## Quick Deployment (5 minutes)

### Step 1: Clone & Setup
```bash
# Clone your repository (if not already done)
git clone https://github.com/yourusername/tractionbuild.git
cd tractionbuild

# Login to Railway
railway login
```

### Step 2: Initialize Railway Project
```bash
# Run deployment script
.\deploy_railway.ps1 -Init
```

This will:
- ✅ Create Railway project
- ✅ Add Neo4j database
- ✅ Add Redis (optional)
- ✅ Set up production environment

### Step 3: Configure Environment
```bash
# Set up database
.\deploy_railway.ps1 -SetupDatabase

# Deploy application
.\deploy_railway.ps1 -Deploy
```

You'll be prompted to enter:
- `OPENAI_API_KEY`
- `XAI_API_KEY`

### Step 4: Test Deployment
```bash
# Test the deployment
.\deploy_railway.ps1 -Test
```

## Manual Deployment (Detailed)

If you prefer step-by-step control:

### 1. Initialize Railway Project
```bash
# Login to Railway
railway login

# Create project
railway init tractionbuild

# Set production environment
railway environment production
```

### 2. Add Services
```bash
# Add Neo4j database
railway add neo4j

# Add Redis (optional for caching)
railway add redis
```

### 3. Configure Environment Variables
```bash
# Required API Keys
railway variables set OPENAI_API_KEY your_openai_key
railway variables set XAI_API_KEY your_xai_key

# Application Settings
railway variables set ENVIRONMENT production
railway variables set DEBUG false
railway variables set LOG_LEVEL INFO
railway variables set PROJECT_NAME tractionbuild
```

### 4. Deploy
```bash
# Deploy to Railway
railway up
```

### 5. Get Deployment URL
```bash
# Get your application URL
railway domain
```

## Environment Configuration

### Required Variables
```bash
OPENAI_API_KEY=your_openai_api_key
XAI_API_KEY=your_xai_api_key
```

### Database (Auto-configured by Railway)
Railway automatically provides:
- `NEO4J_URI`
- `NEO4J_USER`
- `NEO4J_PASSWORD`

### Optional Variables
```bash
REDIS_URL=redis://...          # For caching
VAULT_ADDR=http://...          # For secrets management
```

## Testing Your Deployment

### Health Check
```bash
# Visit your deployment URL + /health
# Example: https://tractionbuild-production.up.railway.app/health
```

### API Testing
```bash
# Test API documentation
# Visit: https://your-app-url/docs

# Create a test project
curl -X POST https://your-app-url/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Railway Test",
    "description": "Testing Railway deployment",
    "hypothesis": "Railway deployment works",
    "target_avatars": ["startup_founder"],
    "workflow": "default_software_build"
  }'
```

### Salem AI Testing
```bash
# Test Salem marketing asset generation
curl -X POST https://your-app-url/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Salem Marketing Test",
    "description": "Testing Salem AI on Railway",
    "hypothesis": "Salem generates marketing assets in production",
    "target_avatars": ["tech_startup_founder"],
    "workflow": "default_software_build"
  }'
```

## Troubleshooting

### Common Issues

#### 1. Build Failures
```bash
# Check build logs
railway logs

# Common fixes:
# - Check requirements.txt has all dependencies
# - Ensure Python version is compatible
# - Check for missing system dependencies
```

#### 2. Database Connection Issues
```bash
# Check Neo4j service
railway service

# Verify database variables
railway variables
```

#### 3. API Key Issues
```bash
# Verify API keys are set
railway variables list

# Update if needed
railway variables set OPENAI_API_KEY new_key
```

#### 4. Port Issues
Railway automatically assigns ports. Make sure your app binds to `0.0.0.0` and uses the `PORT` environment variable.

### Debug Commands
```bash
# View all services
railway service

# View environment variables
railway variables list

# View logs
railway logs

# View metrics
railway metrics
```

## Production Optimization

### Performance Tuning
```yaml
# In railway.json
{
  "deploy": {
    "startCommand": "uvicorn app_v1_real_integration:app --host 0.0.0.0 --port $PORT --workers 4",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300
  }
}
```

### Monitoring
```bash
# Enable Railway metrics
railway metrics

# View application logs
railway logs --follow
```

### Scaling
```bash
# Add more resources if needed
railway service --help

# Set up alerts
railway alerts create
```

## Cost Optimization

### Railway Pricing
- **Hobby Plan**: Free for small projects
- **Pro Plan**: $5/month for production workloads
- **Teams Plan**: For larger teams

### Resource Optimization
- Use Neo4j efficiently (connection pooling enabled)
- Implement caching with Redis
- Monitor usage with Railway metrics

## Backup & Recovery

### Database Backups
Railway automatically backs up Neo4j databases. You can also:
```bash
# Manual backup
railway backup create

# List backups
railway backup list
```

### Code Deployment
```bash
# Deploy specific branch
git push origin main

# Rollback if needed
railway deployment rollback <deployment-id>
```

## Security Best Practices

### API Keys
- ✅ Store in Railway variables (not in code)
- ✅ Rotate keys regularly
- ✅ Use different keys for different environments

### Network Security
- ✅ Railway provides HTTPS by default
- ✅ Configure CORS properly for production
- ✅ Use Railway's built-in firewall

### Data Protection
- ✅ Neo4j data is encrypted at rest
- ✅ Use Railway's backup features
- ✅ Implement proper access controls

## Next Steps After Deployment

### 1. User Acquisition
- Share your Railway URL with potential users
- Create a simple landing page
- Gather feedback and iterate

### 2. Feature Enhancement
- Add user authentication
- Implement project templates
- Add analytics and monitoring

### 3. Performance Monitoring
- Set up Railway alerts
- Monitor API usage
- Track user engagement

## Support & Resources

### Railway Resources
- [Railway Documentation](https://docs.railway.app/)
- [Railway Discord](https://discord.gg/railway)
- [Railway Status Page](https://railway.instatus.com/)

### TractionBuild Resources
- [API Documentation](https://your-app-url/docs)
- [Health Check](https://your-app-url/health)
- [Project Management](https://your-app-url/)

---

## 🎉 Deployment Complete!

Your TractionBuild application is now live on Railway! 🚀

**Next Steps:**
1. ✅ Share the URL with users
2. ✅ Monitor performance with Railway metrics
3. ✅ Gather feedback and iterate
4. ✅ Consider upgrading to Pro plan for production workloads

**Your Railway URL:** Check `railway domain` for your live application!

---

*This deployment makes TractionBuild accessible to anyone with the URL, enabling real user testing and feedback collection.*
