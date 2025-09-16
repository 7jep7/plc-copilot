# Gunicorn configuration for production deployment
# Use with: gunicorn -c gunicorn.conf.py

import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

# Worker processes
workers = 1  # Single worker for free tier, can be increased for paid plans
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120  # Increased timeout for heavy operations
keepalive = 2

# Memory management
max_requests = 1000  # Restart workers after this many requests
max_requests_jitter = 50
preload_app = False  # Don't preload to save memory

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"

# Process naming
proc_name = "plc-copilot"

# Restart workers gracefully
graceful_timeout = 120