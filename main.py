from datetime import date
from typing import Literal
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Hello AI")

DocType = Literal["lease", "bas", "rates_notice", "trust_deed"]


class DocumentIn(BaseModel):
    """Like a Swift struct conforming to Codable, with validation built in."""
    title: str = Field(min_length=1, max_length=200)
    doc_type: DocType
    issued_on: date
    tags: list[str] = []


class Document(DocumentIn):
    id: UUID


# In-memory store for now; Phase 1 week 3 swaps this for Postgres.
documents: dict[UUID, Document] = {}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/documents", status_code=201)
async def create_document(doc: DocumentIn) -> Document:
    saved = Document(id=uuid4(), **doc.model_dump())
    documents[saved.id] = saved
    return saved


@app.get("/documents/{doc_id}")
async def get_document(doc_id: UUID) -> Document:
    doc = documents.get(doc_id)
    if doc is None:  # Python's version of guard let
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@app.get("/documents")
async def list_documents(doc_type: DocType | None = None) -> list[Document]:
    return [d for d in documents.values() if doc_type is None or d.doc_type == doc_type]
