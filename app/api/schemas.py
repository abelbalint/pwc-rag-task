from pydantic import BaseModel, ConfigDict, Field, field_validator


class AskRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"question": "How do I connect to the company VPN?", "top_k": 4}]
        }
    )

    question: str = Field(min_length=1, max_length=1000)
    top_k: int | None = Field(default=None, ge=1, le=10)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Question must not be blank")
        return value


class SourceResponse(BaseModel):
    document: str
    chunk_id: str
    score: float
    snippet: str


class AskResponse(BaseModel):
    answer: str
    answered: bool
    sources: list[SourceResponse]
    request_id: str


class HealthResponse(BaseModel):
    status: str
    llm_provider: str
    embedding_provider: str
    index_loaded: bool
    index_chunks: int


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "error": {
                        "code": "validation_error",
                        "message": "Request validation failed.",
                        "request_id": "4e92ee5b-301f-4d55-ae50-10fbd1270f28",
                    }
                }
            ]
        }
    )

    error: ErrorDetail
