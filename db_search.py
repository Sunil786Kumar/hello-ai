import os

import psycopg
from dotenv import load_dotenv

from embed_search import MODEL, embed
from load_chunks import to_pgvector

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL", "dbname=hello_ai")

SEARCH_SQL = """
SELECT page,
       text,
       1 - (embedding <=> %(query)s::vector) AS similarity
FROM chunks
WHERE embedding_model = %(model)s
ORDER BY embedding <=> %(query)s::vector
LIMIT %(k)s;
"""


def db_search(question: str, k: int = 3) -> list[tuple[int, str, float]]:
    query_vector = to_pgvector(embed([question], input_type="query")[0])  # one Voyage call
    with psycopg.connect(DATABASE_URL) as conn:
        return conn.execute(SEARCH_SQL, {"query": query_vector, "model": MODEL, "k": k}).fetchall()


if __name__ == "__main__":
    questions = [
        "When can the lessor enter?",
        "Can I keep a cat?",
        "How much notice to end the tenancy?",
        "Who pays for water?",
    ]
    for q in questions:
        print(f"\nQ: {q}")
        for page, text, similarity in db_search(q):
            print(f"   {similarity:.3f} | page {page} | {text[:110]}...")