from fastapi import Request

from app.services.qa import QAService


def get_qa_service(request: Request) -> QAService:
    return request.app.state.qa_service
