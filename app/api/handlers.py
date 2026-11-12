import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.schemas import ErrorResponse
from app.services.errors import QAServiceError

logger = logging.getLogger(__name__)


def _error_response(request: Request, status_code: int, code: str, message: str) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    request.state.error_code = code
    body = ErrorResponse(
        error={"code": code, "message": message, "request_id": request_id}
    ).model_dump()
    return JSONResponse(
        status_code=status_code,
        content=body,
        headers={"X-Request-ID": request_id},
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, _: RequestValidationError) -> JSONResponse:
        return _error_response(request, 422, "validation_error", "Request validation failed.")

    @app.exception_handler(QAServiceError)
    async def qa_error(request: Request, exc: QAServiceError) -> JSONResponse:
        return _error_response(request, exc.status_code, exc.code, exc.message)

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        logger.exception("request_id=%s unexpected request failure", request_id, exc_info=exc)
        return _error_response(request, 500, "internal_error", "An unexpected error occurred.")
