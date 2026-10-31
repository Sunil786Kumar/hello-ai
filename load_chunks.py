import hashlib
import os

import psycopg
from dotenv import load_dotenv

from chunk_pdf import chunk_pdf
from embed_search import MODEL, load_or_create_embeddings

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL", "dbname=hello_ai")
DOCUMENT = "form18a.pdf"

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS chunks (
    id              SERIAL PRIMARY KEY,
    document        TEXT         NOT NULL,
    chunk_index     INT          NOT NULL,
    page            INT          NOT NULL,
    text            TEXT         NOT NULL,
    content_hash    TEXT         NOT NULL,
    embedding_model TEXT         NOT NULL,
    embedding       VECTOR(1024) NOT NULL,
    UNIQUE (document, chunk_index)
);
"""


def to_pgvector(vector: list[float]) -> str:
    """Format a Python list as pgvector text, e.g. [0.1,0.2,0.3]."""
    return "[" + ",".join(str(x) for x in vector) + "]"


def content_hash(text: str) -> str:
    """A fingerprint of the chunk's text: any change gives a completely different value."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> None:
    chunks = chunk_pdf(f"docs/{DOCUMENT}")
    vectors = load_or_create_embeddings(chunks)  # reuses chunk_embeddings.json, no new Voyage calls

    with psycopg.connect(DATABASE_URL) as conn:  # commits automatically if everything succeeds
        conn.execute(CREATE_TABLE)

        # Replace this document's rows so the script is safe to run more than once
        conn.execute("DELETE FROM chunks WHERE document = %s", (DOCUMENT,))

        for chunk, vector in zip(chunks, vectors):
            conn.execute(
                """
                INSERT INTO chunks (document, chunk_index, page, text, content_hash, embedding_model, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s::vector)
                """,
                (DOCUMENT, chunk.id, chunk.page, chunk.text, content_hash(chunk.text), MODEL, to_pgvector(vector)),
            )

        count = conn.execute("SELECT COUNT(*) FROM chunks WHERE document = %s", (DOCUMENT,)).fetchone()[0]

    print(f"Loaded {count} chunks from {DOCUMENT} into Postgres")


if __name__ == "__main__":
    main()