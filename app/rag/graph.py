import asyncio
from typing import TypedDict

from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, START, StateGraph

from app.providers.vector_store import VectorStore

NO_CONTEXT_ANSWER = (
    "I do not have enough information in the knowledge base to answer this question."
)

_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Answer the question using only the supplied context. If the context does not contain "
            "the answer, say that you do not know. Cite factual claims with the source in "
            "[document: section] format. Do not invent facts or citations.",
        ),
        ("human", "Context:\n{context}\n\nQuestion: {question}"),
    ]
)


class RetrievedChunk(TypedDict):
    document: Document
    score: float


class QAState(TypedDict, total=False):
    question: str
    top_k: int
    documents: list[RetrievedChunk]
    answer: str
    answered: bool


def _format_context(documents: list[RetrievedChunk]) -> str:
    return "\n\n".join(
        f"[Source: {item['document'].metadata['document']}: "
        f"{item['document'].metadata['section']}]\n{item['document'].page_content}"
        for item in documents
    )


def build_qa_graph(
    llm: BaseChatModel,
    vector_store: VectorStore,
    score_threshold: float,
):
    async def retrieve(state: QAState) -> dict[str, list[RetrievedChunk]]:
        matches = await asyncio.to_thread(vector_store.search, state["question"], state["top_k"])
        documents = [
            {"document": document, "score": score}
            for document, score in matches
            if score >= score_threshold
        ]
        return {"documents": documents}

    async def generate(state: QAState) -> dict[str, str | bool]:
        prompt = _PROMPT.invoke(
            {"context": _format_context(state["documents"]), "question": state["question"]}
        )
        response = await llm.ainvoke(prompt)
        content = response.content
        answer = content if isinstance(content, str) else str(content)
        return {"answer": answer, "answered": True}

    def no_context(_: QAState) -> dict[str, str | bool]:
        return {"answer": NO_CONTEXT_ANSWER, "answered": False}

    def has_context(state: QAState) -> str:
        return "generate" if state["documents"] else "no_context"

    builder = StateGraph(QAState)
    builder.add_node("retrieve", retrieve)
    builder.add_node("generate", generate)
    builder.add_node("no_context", no_context)
    builder.add_edge(START, "retrieve")
    builder.add_conditional_edges(
        "retrieve", has_context, {"generate": "generate", "no_context": "no_context"}
    )
    builder.add_edge("generate", END)
    builder.add_edge("no_context", END)
    return builder.compile()
