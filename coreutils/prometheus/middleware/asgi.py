from __future__ import annotations

import logging
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from http import HTTPMethod, HTTPStatus
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from starlette.types import ASGIApp, Message, Receive, Scope, Send

from coreutils.prometheus.metrics.rest import REQUEST_COUNT, REQUEST_LATENCY


log = logging.getLogger(__name__)

UUID_REGEX = re.compile(
    r"/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}"
)


def normalize_endpoint(path: str) -> str:
    return UUID_REGEX.sub("/{id}", path)


def is_monitorable_endpoint(path: str, route: Any | None, method: str) -> bool:
    ignore_paths = ["/docs", "/metrics"]
    ignore_methods = {"OPTIONS"}

    if method in ignore_methods:
        return False

    if any(ignored in path for ignored in ignore_paths):
        return False

    if not path.startswith("/api/"):
        return False

    return True


@dataclass
class AsgiPrometheusMiddleware:
    app: ASGIApp

    # Нормализация и фильтрация
    normalizer: Callable[[str], str] = field(default=normalize_endpoint)
    monitor_predicate: Callable[[str, Any | None, str], bool] = field(
        default=is_monitorable_endpoint
    )

    # Хуки записи метрик — меняйте, если у ваших метрик другие имена/метки
    record_count: Callable[[str, str, int], None] = field(
        default=lambda method, endpoint, status: REQUEST_COUNT.labels(
            method=method, endpoint=endpoint, http_status=status
        ).inc()
    )
    observe_latency: Callable[[str, str, float], None] = field(
        default=lambda method, endpoint, seconds: REQUEST_LATENCY.labels(
            method=method, endpoint=endpoint
        ).observe(seconds)
    )

    # Включить "мягкий" fallback-мониторинг даже если route недоступен
    # (см. пояснение ниже)
    enable_route_missing_fallback: bool = True

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:  # noqa: C901
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method: str = scope.get("method", HTTPMethod.GET).upper()
        raw_path: str = scope.get("path", "/")
        # route почти всегда отсутствует на стадии middleware; оставляем
        # попытку получить:
        route = scope.get("route")

        # Основная проверка наблюдаемости
        monitorable = self.monitor_predicate(raw_path, route, method)

        # Fallback: если route недоступен, воспроизводим ту же логику,
        # но без условия на route (иначе метрики "замолчат" в middleware-слое)
        if not monitorable and self.enable_route_missing_fallback and route is None:
            monitorable = (
                method not in {"OPTIONS"}
                and raw_path.startswith("/api/")
                and not any(x in raw_path for x in ["/monitoring", "/docs", "/metrics"])
            )

        if not monitorable:
            # Просто прокидываем
            await self.app(scope, receive, send)
            return

        # Нормализованный endpoint для меток
        endpoint = self.normalizer(raw_path)

        start = time.perf_counter()
        status_code: int | None = None
        body_finished = False

        async def wrapped_send(message: Message) -> None:
            nonlocal status_code, body_finished
            if message["type"] == "http.response.start":
                # Сохраняем код ответа (может понадобиться для счётчика)
                status_code = int(message.get("status", HTTPStatus.OK))
            elif message["type"] == "http.response.body":
                # Фиксируем момент завершения ответа (more_body == False)
                if not message.get("more_body", False):
                    body_finished = True
                    elapsed = time.perf_counter() - start
                    # Латентность пишем как только знаем, что ответ завершён
                    try:
                        self.observe_latency(method, endpoint, elapsed)
                    except Exception:
                        # Никаких исключений из отправки метрик не допускаем наружу
                        log.exception("Failed to record metrics")
            await send(message)

        try:
            await self.app(scope, receive, wrapped_send)
        except Exception:
            # При ошибке учитываем как 500 и латентность до момента исключения
            status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            try:
                elapsed = time.perf_counter() - start
                self.observe_latency(method, endpoint, elapsed)
            except Exception:
                log.exception("Failed to record metrics")
            # Пробрасываем дальше — пусть обработчики ошибок отвечают как обычно
            raise
        finally:
            # Если код ответа так и не был зафиксирован (теоретически),
            # ставим 500/200 в разумных пределах
            final_status = (
                status_code
                if status_code is not None
                else (
                    HTTPStatus.OK if body_finished else HTTPStatus.INTERNAL_SERVER_ERROR
                )
            )
            try:
                self.record_count(method, endpoint, final_status)
            except Exception:
                log.exception("Failed to record metrics")
