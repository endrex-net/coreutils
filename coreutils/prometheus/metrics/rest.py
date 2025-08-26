from prometheus_client import Counter, Histogram

from coreutils.prometheus.registry import prometheus_registry


REQUEST_COUNT = Counter(
    "rest_request_count",
    "Total number of HTTP requests",
    ["method", "endpoint", "http_status"],
    registry=prometheus_registry,
)

REQUEST_LATENCY = Histogram(
    "rest_request_latency_seconds",
    "HTTP request processing time in seconds",
    ["method", "endpoint"],
    registry=prometheus_registry,
)
