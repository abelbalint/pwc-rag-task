from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.config import Settings, get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    llm_provider: str
    embedding_provider: str
    index_loaded: bool
    index_chunks: int


@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    # The vector index is wired in a later step; until then it is reported as not loaded.
    return HealthResponse(
        status="ok",
        llm_provider=settings.llm_provider,
        embedding_provider=settings.embedding_provider,
        index_loaded=False,
        index_chunks=0,
    )
