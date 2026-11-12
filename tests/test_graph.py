import asyncio

from langchain_core.documents import Document
from langchain_core.messages import AIMessage

from app.rag.graph import NO_CONTEXT_ANSWER, build_qa_graph


class FakeVectorStore:
    def __init__(self, results: list[tuple[Document, float]]) -> None:
        self.results = results
        self.query: str | None = None
        self.top_k: int | None = None

    def search(self, query: str, top_k: int) -> list[tuple[Document, float]]:
        self.query = query
        self.top_k = top_k
        return self.results

    def replace_documents(self, documents: list[Document]) -> None:
        raise NotImplementedError

    def count(self) -> int:
        return len(self.results)


class CountingLLM:
    def __init__(self, answer: str = "Reset your password at the self-service portal.") -> None:
        self.answer = answer
        self.calls = 0
        self.prompt = ""

    async def ainvoke(self, prompt, **kwargs) -> AIMessage:
        self.calls += 1
        self.prompt = str(prompt)
        return AIMessage(content=self.answer)


def test_graph_retrieves_and_generates_with_source_context() -> None:
    document = Document(
        page_content="Reset a forgotten password at https://password.acme.example.",
        metadata={"document": "password-reset.md", "section": "Resetting", "chunk_id": "pwd:0:0"},
    )
    store = FakeVectorStore([(document, 0.9)])
    llm = CountingLLM()
    graph = build_qa_graph(llm, store, score_threshold=0.3)

    result = asyncio.run(graph.ainvoke({"question": "How do I reset my password?", "top_k": 3}))

    assert result["answered"] is True
    assert result["answer"] == llm.answer
    assert result["documents"][0]["score"] == 0.9
    assert "password-reset.md: Resetting" in llm.prompt
    assert llm.calls == 1
    assert store.query == "How do I reset my password?"
    assert store.top_k == 3


def test_graph_uses_no_context_branch_without_calling_llm() -> None:
    document = Document(
        page_content="Printer toner instructions.",
        metadata={"document": "printing.md", "section": "Toner", "chunk_id": "print:0:0"},
    )
    store = FakeVectorStore([(document, 0.2)])
    llm = CountingLLM()
    graph = build_qa_graph(llm, store, score_threshold=0.3)

    result = asyncio.run(graph.ainvoke({"question": "How do I get a new laptop?", "top_k": 2}))

    assert result["answered"] is False
    assert result["answer"] == NO_CONTEXT_ANSWER
    assert result["documents"] == []
    assert llm.calls == 0


def test_graph_uses_no_context_branch_when_retriever_returns_nothing() -> None:
    store = FakeVectorStore([])
    llm = CountingLLM()
    graph = build_qa_graph(llm, store, score_threshold=0.3)

    result = asyncio.run(graph.ainvoke({"question": "Where is the office?", "top_k": 4}))

    assert result["answered"] is False
    assert llm.calls == 0
