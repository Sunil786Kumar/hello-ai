import re

from pydantic import BaseModel
from pypdf import PdfReader


class Chunk(BaseModel):
    id: int
    page: int
    text: str


BOILERPLATE = [
    r"Page \d+ of \d+ v\w+ \w+",
    r"Level 11, Midtown Centre, 150 Mary Street \| GPO Box 390 Brisbane Q 4001 \| t 1300 366 311 \| rta\.qld\.gov\.au",
    r"General tenancy agreement \(Form 18a\) Residential Tenancies and Rooming Accommodation Act 2008",
]


def clean(text: str) -> str:
    """Collapse whitespace, then remove the letterhead repeated on every page."""
    text = re.sub(r"\s+", " ", text)
    for pattern in BOILERPLATE:
        text = re.sub(pattern, " ", text)
    return re.sub(r"\s+", " ", text).strip()


def chunk_page(text: str, page: int, start_id: int, size: int = 150, overlap: int = 30) -> list[Chunk]:
    """Split one page into chunks of `size` words, each overlapping the previous by `overlap` words."""
    words = clean(text).split(" ")
    chunks = []
    step = size - overlap
    for i in range(0, len(words), step):
        piece = words[i : i + size]
        if piece == [""]:          # empty page
            break
        chunks.append(Chunk(id=start_id + len(chunks), page=page, text=" ".join(piece)))
        if i + size >= len(words):  # reached the end of the page
            break
    return chunks


def chunk_pdf(path: str) -> list[Chunk]:
    reader = PdfReader(path)
    all_chunks: list[Chunk] = []
    for page_number, page in enumerate(reader.pages, start=1):
        all_chunks += chunk_page(page.extract_text(), page_number, start_id=len(all_chunks))
    return all_chunks


if __name__ == "__main__":
    chunks = chunk_pdf("docs/form18a.pdf")
    print(f"{len(chunks)} chunks\n")
    for c in chunks[:3]:
        print(f"[chunk {c.id}, page {c.page}] {c.text[:200]}...\n")