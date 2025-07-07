from prometheus_client import Counter, Gauge

from coreutils.prometheus.registry import prometheus_registry


WEBSOCKET_CONNECTIONS = Gauge(
    "websocket_connections_total",
    "Total WebSocket connections",
    ["http_proxy"],
    registry=prometheus_registry,
)

WEBSOCKET_ERRORS = Counter(
    "websocket_connection_errors_total",
    "Total WebSocket connection errors",
    ["endpoint"],
    registry=prometheus_registry,
)


ORDER_UPDATE_PROCESSING_ERRORS = Counter(
    "order_update_processing_errors_total",
    "Total order update message processing errors",
    ["type"],
    registry=prometheus_registry,
)
