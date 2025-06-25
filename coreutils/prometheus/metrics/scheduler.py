from prometheus_client import Counter, Histogram

from coreutils.prometheus.registry import prometheus_registry


job_duration_hist = Histogram(
    "apscheduler_async_job_duration_seconds",
    "Duration of asynchronous APScheduler jobs in seconds",
    ["job_name"],
    registry=prometheus_registry,
)

job_failure_counter = Counter(
    "apscheduler_async_job_failures_total",
    "Total number of failed asynchronous APScheduler jobs",
    ["job_name"],
    registry=prometheus_registry,
)
