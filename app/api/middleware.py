import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


async def request_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = request.headers.get("X-Request-ID", "").strip()
    if not request_id or len(request_id) > 128 or any(ord(char) < 32 for char in request_id):
        request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    request.state.retrieval_count = 0
    started_at = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        duration_ms = (time.perf_counter() - started_at) * 1000
        error_code = getattr(request.state, "error_code", "")
        log = logger.info if status_code < 400 else logger.warning
        log(
            "request_id=%s status=%d duration_ms=%.2f retrieval_count=%d error_code=%s",
            request_id,
            status_code,
            duration_ms,
            request.state.retrieval_count,
            error_code,
        )
