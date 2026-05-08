bind = "0.0.0.0:8000"
workers = 3
threads = 2
worker_class = "sync"
timeout = 120
keepalive = 5

accesslog = "logs/gunicorn-access.log"
errorlog = "logs/gunicorn-error.log"
loglevel = "info"

proc_name = "shopzone"
daemon = False

capture_output = True
enable_stdio_inheritance = True
