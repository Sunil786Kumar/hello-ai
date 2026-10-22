import re

from chunk_pdf import Chunk, chunk_pdf

STOPWORDS = {
    "a", "an", "and", "are", "be", "can", "do", "does", "for", "how", "i", "if", "in",
    "is", "it", "my", "of", "on", "or", "the", "to", "what", "when", "who", "much", "many",
}


def tokenize(text: str) -> list[str]:
    """Lowercase the text and split it into words, dropping punctuation."""
    return re.findall(r"[a-z0-9]+", text.lower())


def keyword_search(query: str, chunks: list[Chunk], k: int = 3) -> list[tuple[int, Chunk]]:
    terms = [w for w in tokenize(query) if w not in STOPWORDS]
    scored = []
    for chunk in chunks:
        chunk_words = tokenize(chunk.text)
        score = sum(chunk_words.count(t) for t in terms)
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return scored[:k]


if __name__ == "__main__":
    chunks = chunk_pdf("docs/form18a.pdf")
    questions = [
        "How much notice to end the tenancy?",
        "When can the lessor enter?",
        "Who pays for water?",
        "Can I have a cat?",
    ]
    for q in questions:
        print(f"\nQ: {q}")
        results = keyword_search(q, chunks)
        if not results:
            print("   (no matches)")
        for score, c in results:
            print(f"   score {score} | page {c.page} | {c.text[:150]}...")