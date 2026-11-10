import os

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

# Prometheus multiprocess metrics setup


def on_starting(server):
    metrics_dir = os.environ["PROMETHEUS_MULTIPROC_DIR"]

    os.makedirs(metrics_dir, exist_ok=True)

    for name in os.listdir(metrics_dir):
        path = os.path.join(metrics_dir, name)
        if os.path.isfile(path):
            os.remove(path)


def child_exit(server, worker):
    from prometheus_client import multiprocess

    multiprocess.mark_process_dead(worker.pid)
