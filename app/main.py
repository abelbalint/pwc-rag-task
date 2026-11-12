from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.handlers import register_exception_handlers
from app.api.middleware import request_context_middleware
from app.api.routes import router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.services.qa import QAService


def create_app(
    settings_override: Settings | None = None,
    qa_service_override: QAService | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if qa_service_override is None:
            settings = settings_override or get_settings()
            configure_logging(settings.log_level)
            app.state.qa_service = QAService.from_settings(settings)
        else:
            app.state.qa_service = qa_service_override
        yield

    app = FastAPI(title="Acme IT Helpdesk RAG", version="0.1.0", lifespan=lifespan)
    app.middleware("http")(request_context_middleware)
    register_exception_handlers(app)
    app.include_router(router)
    return app


app = create_app()
