from fastapi import APIRouter, Depends

from ..dependencies import get_engine

router = APIRouter()


@router.get("/documents")
def list_documents(engine=Depends(get_engine)):
    """List the indexed documents and their word counts.

    Upload/re-index endpoints will live here in a later phase.
    """
    index = engine.index
    return {
        "count": index.total_documents(),
        "documents": [
            {
                "document": file_name,
                "word_count": index.document_lengths.get(file_name, 0),
            }
            for file_name in sorted(index.documents)
        ],
    }
