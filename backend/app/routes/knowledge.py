from fastapi import APIRouter, HTTPException

from app.rag.ingest import ingest_knowledge
from app.schemas import IngestResponse


router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post("/ingest", response_model=IngestResponse)
def ingest():
    try:
        files, chunks = ingest_knowledge()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc

    return IngestResponse(
        files_processed=files,
        chunks_added=chunks,
        message="Knowledge ingestion completed." if files else "No supported knowledge files found.",
    )
