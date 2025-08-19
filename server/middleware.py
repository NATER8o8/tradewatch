
from starlette.types import ASGIApp, Receive, Scope, Send
from typing import Callable
from urllib.parse import parse_qs

class NoGzipFlagMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope.get("type") == "http":
            qs = scope.get("query_string", b"").decode("utf-8")
            params = parse_qs(qs)
            if params.get("gzip", ["1"])[0] == "0":
                # Signal to downstream to skip gzip by setting 'x-no-gzip' header on response
                orig_send = send
                async def send_wrapper(message):
                    if message["type"] == "http.response.start":
                        headers = message.setdefault("headers", [])
                        headers.append((b"x-no-gzip", b"1"))
                    await orig_send(message)
                return await self.app(scope, receive, send_wrapper)
        return await self.app(scope, receive, send)
