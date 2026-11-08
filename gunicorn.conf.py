bind = "0.0.0.0:8000"

workers = 2
worker_class = "sync"

timeout = 30
graceful_timeout = 30
keepalive = 5

accesslog = "-"
errorlog = "-"
loglevel = "info"

capture_output = True

# Writable runtime directory for the non-root user
chdir = "/app"
control_socket_dir = "/tmp"

control_socket_disable = True
