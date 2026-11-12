import time
import os

from flask import Blueprint, Response, g, request
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
    multiprocess,
)

metrics_bp = Blueprint("metrics", __name__)

REQUEST_COUNT = Counter(
    "roomops_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "roomops_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)


def start_timer():
    if request.path != "/metrics":
        g.request_start_time = time.perf_counter()


def record_request(response):
    if request.path != "/metrics":
        duration = time.perf_counter() - g.request_start_time
        endpoint = request.endpoint or "unmatched"

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status=str(response.status_code),
        ).inc()

        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=endpoint,
        ).observe(duration)

    return response


@metrics_bp.get("/metrics")
def metrics():
    multiproc_dir = os.getenv("PROMETHEUS_MULTIPROC_DIR")

    if multiproc_dir and os.path.isdir(multiproc_dir):
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        output = generate_latest(registry)
    else:
        output = generate_latest()

    return Response(
        output,
        mimetype="text/plain; version=0.0.4; charset=utf-8",
    )
