from pathlib import Path
from uuid import uuid4

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag.loaders import SUPPORTED_SUFFIXES, load_document
from app.rag.vectorstore import get_vector_store


KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "knowledge"


def ingest_knowledge() -> tuple[int, int]:
    files = [
        path for path in KNOWLEDGE_DIR.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    ]

    docs = []
    for path in files:
        loaded = load_document(path)
        for doc in loaded:
            doc.metadata["source_file"] = path.name
        docs.extend(loaded)

    if not docs:
        return 0, 0

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=150,
        add_start_index=True,
    )
    chunks = splitter.split_documents(docs)

    vector_store = get_vector_store()
    ids = [str(uuid4()) for _ in chunks]
    vector_store.add_documents(chunks, ids=ids)
    return len(files), len(chunks)


if __name__ == "__main__":
    file_count, chunk_count = ingest_knowledge()
    print(f"Processed {file_count} file(s), added {chunk_count} chunk(s).")
