# Deployment Guide

## Render.com Deployment

### Required Manual Environment Variables

When deploying to Render.com, you need to manually set these environment variables in the Render dashboard:

#### Required
- `OPENAI_API_KEY` - Your OpenAI API key (starts with sk-...)

#### Optional
- `SENTRY_DSN` - For error tracking (optional)

### Memory Optimization

The app is optimized for Render's free tier (512MB memory limit):
- Uses single uvicorn process instead of multiple gunicorn workers
- Lazy loading of heavy imports after startup
- Minimal entry point (`minimal_main.py`) for production deployment
- Extended timeout (120s) to handle AI model loading

### Deployment Steps

1. **Fork this repository** to your GitHub account

2. **Connect to Render.com**:
   - Go to [Render.com](https://render.com)
   - Connect your GitHub account
   - Select this repository

3. **Configure Environment Variables**:
   - Go to your service settings in Render
   - Add the required environment variables:
     ```
     OPENAI_API_KEY=sk-proj-your-actual-key-here
     ```

4. **Deploy**:
   - Render will automatically detect the `render.yaml` configuration
   - The deployment will create:
     - Web service (FastAPI backend)
     - Worker service (Celery background tasks)
     - PostgreSQL database
     - Redis cache

### Environment Variable Generation

To generate a secure SECRET_KEY:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Troubleshooting

#### Common Issues:

1. **Build fails with missing environment variables**:
   - Ensure `OPENAI_API_KEY` and `SECRET_KEY` are set in Render dashboard
   - Check that the keys don't have extra spaces or quotes

2. **Database connection errors**:
   - Render automatically configures `DATABASE_URL`
   - Check that the database service is running

3. **CORS errors from frontend**:
   - Update `BACKEND_CORS_ORIGINS` in render.yaml with your frontend domain
   - Format: `"https://yourdomain.com,https://www.yourdomain.com"`

4. **Worker not processing tasks**:
   - Check that Redis service is running
   - Verify `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` are configured

### Health Checks

- Health endpoint: `https://your-app.onrender.com/health`
- API docs: `https://your-app.onrender.com/docs`

### Logs

View logs in the Render dashboard:
- Web service logs show API requests and responses
- Worker logs show background task processing
- Database logs show connection and query information

### Scaling

For production usage:
- Upgrade from Starter to Standard plan for better performance
- Consider increasing worker count for heavy background processing
- Monitor database performance and upgrade if needed

## Local Development vs Production

### Key Differences:

| Feature | Local | Production |
|---------|-------|------------|
| Database | SQLite | PostgreSQL |
| Cache | Optional Redis | Required Redis |
| Workers | Optional | Required for file processing |
| HTTPS | HTTP | HTTPS (automatic) |
| Environment | `.env` file | Render environment variables |

### Migration Notes:

- Local SQLite databases are not migrated to production
- Test your deployment with sample data
- Use the `/health` endpoint to verify all services are running