from langchain_core.documents import Document

from app.rag.chunking import load_markdown_documents, split_documents


def test_split_documents_preserves_heading_metadata_and_overlap() -> None:
    source = Document(
        page_content="# VPN\n\n## Setup\n\n" + "connect vpn securely " * 70,
        metadata={"document": "vpn.md"},
    )

    chunks = split_documents([source], chunk_size=120, chunk_overlap=20)

    assert len(chunks) > 1
    assert all(chunk.metadata["document"] == "vpn.md" for chunk in chunks)
    assert all(chunk.metadata["section"] == "Setup" for chunk in chunks)
    assert all(chunk.metadata["chunk_id"].startswith("vpn:") for chunk in chunks)
    assert all(len(chunk.page_content) <= 120 for chunk in chunks)
    assert set(chunks[0].page_content.split()) & set(chunks[1].page_content.split())


def test_headings_inside_fenced_code_are_not_sections() -> None:
    source = Document(
        page_content="# Guide\n\n```md\n## Not a heading\n```\n\n## Real section\nDetails.",
        metadata={"document": "guide.md"},
    )

    chunks = split_documents([source])

    assert {chunk.metadata["section"] for chunk in chunks} == {"Guide", "Real section"}


def test_load_markdown_documents_reads_sorted_files(tmp_path) -> None:
    (tmp_path / "b.md").write_text("# B", encoding="utf-8")
    (tmp_path / "a.md").write_text("# A", encoding="utf-8")

    documents = load_markdown_documents(tmp_path)

    assert [document.metadata["document"] for document in documents] == ["a.md", "b.md"]
