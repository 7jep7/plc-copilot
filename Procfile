web: gunicorn -w 1 -k uvicorn.workers.UvicornWorker app.main:app --timeout 120 --preload --max-requests 1000 --max-requests-jitter 100
worker: celery -A app.worker worker --loglevel=info