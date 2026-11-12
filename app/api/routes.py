from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import get_qa_service
from app.api.schemas import AskRequest, AskResponse, ErrorResponse, HealthResponse
from app.services.qa import QAService

router = APIRouter()


@router.post(
    "/ask",
    response_model=AskResponse,
    responses={
        422: {"model": ErrorResponse, "description": "Request validation failed"},
        502: {"model": ErrorResponse, "description": "Language model error"},
        503: {"model": ErrorResponse, "description": "Knowledge index unavailable"},
        504: {"model": ErrorResponse, "description": "Language model timeout"},
        500: {"model": ErrorResponse, "description": "Unexpected server error"},
    },
    tags=["question answering"],
)
async def ask(
    payload: AskRequest,
    request: Request,
    service: Annotated[QAService, Depends(get_qa_service)],
) -> AskResponse:
    result = await service.ask(payload.question, payload.top_k)
    request.state.retrieval_count = len(result["sources"])
    return AskResponse(**result, request_id=request.state.request_id)


@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health(
    service: Annotated[QAService, Depends(get_qa_service)],
) -> HealthResponse:
    return HealthResponse(**await service.health())
