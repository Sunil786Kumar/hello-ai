import json
import math
import os
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

from chunk_pdf import Chunk, chunk_pdf
from search import keyword_search

load_dotenv()

API_URL = "https://api.voyageai.com/v1/embeddings"
MODEL = "voyage-4-lite"
CACHE = Path("chunk_embeddings.json")


def embed(texts: list[str], input_type: str, batch_size: int = 20) -> list[list[float]]:
    """Send texts to Voyage in small batches and get one embedding back per text."""
    vectors: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        for attempt in range(1, 6):
            response = httpx.post(
                API_URL,
                headers={"Authorization": f"Bearer {os.environ['VOYAGE_API_KEY']}"},
                json={"input": batch, "model": MODEL, "input_type": input_type},
                timeout=60,
            )
            if response.status_code == 429:  # rate limited: wait and try again
                print(f"  Rate limited (attempt {attempt}/5): {response.text[:150]}")
                print("  Waiting 25 seconds...")
                time.sleep(25)
                continue
            if response.is_error:
                print(f"  Voyage error {response.status_code}: {response.text[:300]}")
            response.raise_for_status()
            break
        else:
            raise RuntimeError("Still rate limited after 5 attempts. Check your Voyage dashboard limits.")
        data = sorted(response.json()["data"], key=lambda item: item["index"])
        vectors += [item["embedding"] for item in data]
        print(f"  Embedded {len(vectors)}/{len(texts)}")
    return vectors


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """How close two embeddings are in meaning: 1.0 = same direction, 0 = unrelated."""
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def load_or_create_embeddings(chunks: list[Chunk]) -> list[list[float]]:
    """Embed every chunk once and save the result, so later runs don't pay again."""
    texts = [c.text for c in chunks]
    if CACHE.exists():
        saved = json.loads(CACHE.read_text())
        if saved["model"] == MODEL and saved["texts"] == texts:
            return saved["vectors"]
        print("Chunks changed since last run, re-embedding...")
    vectors = embed(texts, input_type="document")
    CACHE.write_text(json.dumps({"model": MODEL, "texts": texts, "vectors": vectors}))
    return vectors


def semantic_search(query: str, chunks: list[Chunk], vectors: list[list[float]], k: int = 3) -> list[tuple[float, Chunk]]:
    query_vector = embed([query], input_type="query")[0]
    scored = [(cosine_similarity(query_vector, v), c) for v, c in zip(vectors, chunks)]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return scored[:k]


if __name__ == "__main__":
    chunks = chunk_pdf("docs/form18a.pdf")
    vectors = load_or_create_embeddings(chunks)
    print(f"{len(vectors)} chunks embedded, {len(vectors[0])} numbers each")

    questions = [
        "When can the lessor enter?",
        "Can I keep a cat?",
        "How much notice to end the tenancy?",
        "Who pays for water?",
    ]
    for q in questions:
        print(f"\nQ: {q}")
        print("  Keyword:")
        for score, c in keyword_search(q, chunks):
            print(f"    {score:>5} | page {c.page} | {c.text[:110]}...")
        print("  Semantic:")
        for score, c in semantic_search(q, chunks, vectors):
            print(f"    {score:.3f} | page {c.page} | {c.text[:110]}...")