"""Server-side timing header for the transformer (pure ASGI, no dependencies).

Adds ``x-churn-server-time-ms`` to every HTTP response: wall time from the
request entering the transformer's ASGI app to the response headers being sent
(Feast lookup, predictor hop, calibration, TreeSHAP). It excludes APIM, the
network, the Istio ingress gateway, the sidecar and Knative's queue-proxy, so it
is the number to hold against the service-side SLOs (precomputed p99 < 50 ms,
rescoring p99 < 150 ms). ``churn.deploy.smoke_test`` reads it through APIM.

KServe 0.13 has no hook for custom response headers, so ``install()`` wraps
``RESTServer.create_application`` (version pinned in serving/requirements.txt).
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

HEADER = "x-churn-server-time-ms"

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


class ServerTimingMiddleware:
    def __init__(self, app: ASGIApp, clock: Callable[[], float] = time.perf_counter) -> None:
        self.app = app
        self.clock = clock

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        start = self.clock()

        async def send_with_timing(message: Message) -> None:
            if message.get("type") == "http.response.start":
                elapsed_ms = (self.clock() - start) * 1000.0
                headers = list(message.get("headers") or [])
                headers.append((HEADER.encode(), f"{elapsed_ms:.2f}".encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_timing)


def install() -> None:  # pragma: no cover - requires the kserve runtime
    from kserve.protocol.rest import server as rest_server

    original = rest_server.RESTServer.create_application
    if getattr(original, "_churn_timing", False):
        return

    def create_application(self):  # type: ignore[no-untyped-def]
        app = original(self)
        app.add_middleware(ServerTimingMiddleware)
        return app

    create_application._churn_timing = True  # type: ignore[attr-defined]
    rest_server.RESTServer.create_application = create_application
