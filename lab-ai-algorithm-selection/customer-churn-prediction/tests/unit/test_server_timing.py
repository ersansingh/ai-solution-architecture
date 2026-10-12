import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "serving"))

from churn_serving.timing import HEADER, ServerTimingMiddleware  # noqa: E402

from churn.deploy.smoke_test import SERVER_TIMING_HEADER  # noqa: E402


def test_header_name_matches_smoke_test():
    assert HEADER == SERVER_TIMING_HEADER


def test_middleware_adds_server_time_header():
    ticks = iter([1.000, 1.0125])
    sent = []

    async def app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": [(b"a", b"b")]})
        await send({"type": "http.response.body", "body": b"{}"})

    async def send(message):
        sent.append(message)

    mw = ServerTimingMiddleware(app, clock=lambda: next(ticks))
    asyncio.run(mw({"type": "http"}, None, send))
    headers = dict(sent[0]["headers"])
    assert headers[HEADER.encode()] == b"12.50"
    assert headers[b"a"] == b"b"
    assert sent[1]["type"] == "http.response.body"


def test_non_http_scopes_pass_through():
    seen = []

    async def app(scope, receive, send):
        seen.append(scope["type"])

    asyncio.run(ServerTimingMiddleware(app)({"type": "lifespan"}, None, None))
    assert seen == ["lifespan"]
