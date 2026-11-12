import re
from pathlib import Path

from langchain_core.documents import Document

_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$")


def load_markdown_documents(docs_dir: Path) -> list[Document]:
    if not docs_dir.is_dir():
        raise FileNotFoundError(f"Markdown documents directory does not exist: {docs_dir}")

    return [
        Document(page_content=path.read_text(encoding="utf-8"), metadata={"document": path.name})
        for path in sorted(docs_dir.glob("*.md"))
    ]


def _sections(text: str, document: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    current_title = Path(document).stem.replace("-", " ").title()
    current_lines: list[str] = []
    in_fence = False

    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
        heading = None if in_fence else _HEADING.match(line)
        if heading:
            if any(part.strip() for part in current_lines[1:]):
                sections.append((current_title, "\n".join(current_lines).strip()))
            current_title = heading.group(1).strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_title, "\n".join(current_lines).strip()))
    return [(title, content) for title, content in sections if content]


def _split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start + chunk_size // 2, end)
            if boundary > start:
                end = boundary
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        next_start = max(start + 1, end - chunk_overlap)
        while next_start < end and text[next_start].isspace():
            next_start += 1
        start = next_start
    return chunks


def split_documents(
    documents: list[Document], chunk_size: int = 800, chunk_overlap: int = 100
) -> list[Document]:
    if chunk_size < 1:
        raise ValueError("chunk_size must be greater than zero")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be non-negative and smaller than chunk_size")

    chunks: list[Document] = []
    for document in documents:
        name = document.metadata["document"]
        for section_index, (section, content) in enumerate(_sections(document.page_content, name)):
            for chunk_index, chunk in enumerate(_split_text(content, chunk_size, chunk_overlap)):
                chunk_id = f"{Path(name).stem}:{section_index}:{chunk_index}"
                chunks.append(
                    Document(
                        page_content=chunk,
                        metadata={
                            **document.metadata,
                            "section": section,
                            "chunk_id": chunk_id,
                        },
                    )
                )
    return chunks
