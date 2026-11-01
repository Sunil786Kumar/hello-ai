import re

from anthropic import Anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from db_search import db_search

load_dotenv()
client = Anthropic()
MODEL = "claude-haiku-5-5"


# --- 1. The shape of an answer ---
class Citation(BaseModel):
    page: int
    quote: str = Field(description="Exact words copied from the extract that support the answer")


class Answer(BaseModel):
    found: bool = Field(description="False if the extracts do not contain the answer")
    answer: str
    citations: list[Citation] = []


SYSTEM = (
    "You answer questions about a Queensland residential tenancy agreement (RTA Form 18a). "
    "Use only the extracts provided. Support every claim with a citation: the page and an exact quote copied from the extract. "
    "If the extracts don't contain the answer, set found to false and say what is missing. Never use outside knowledge."
)


# --- 2. Checking Claude's quotes against the real text ---
def normalise(text: str) -> str:
    """Lowercase, unify curly quotes and collapse whitespace so small formatting differences don't matter."""
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip().lower()


def quote_is_real(citation: Citation, retrieved: list[tuple[int, str, float]]) -> bool:
    """True if the quote appears word for word in a retrieved chunk from the cited page."""
    return any(page == citation.page and normalise(citation.quote) in normalise(text) for page, text, _ in retrieved)


# --- 3. Retrieve, then generate ---
def ask(question: str, k: int = 4) -> tuple[Answer, list[tuple[int, str, float]]]:
    retrieved = db_search(question, k=k)  # step 1: find the relevant chunks
    extracts = "\n\n".join(f"[Extract {i}, page {page}]\n{text}" for i, (page, text, _) in enumerate(retrieved, start=1))

    response = client.messages.create(  # step 2: Claude answers from them
        model=MODEL,
        max_tokens=1000,
        system=SYSTEM,
        tools=[{
            "name": "give_answer",
            "description": "Return the answer with its citations.",
            "input_schema": Answer.model_json_schema(),
        }],
        tool_choice={"type": "tool", "name": "give_answer"},
        messages=[{"role": "user", "content": f"Extracts:\n\n{extracts}\n\nQuestion: {question}"}],
    )
    tool_block = next(b for b in response.content if b.type == "tool_use")
    return Answer.model_validate(tool_block.input), retrieved


if __name__ == "__main__":
    questions = [
        "When can the lessor enter the premises?",
        "Can I keep a cat?",
        "How much notice does a tenant need to give to end a periodic tenancy?",
        "How much is the weekly rent?",
    ]
    for q in questions:
        answer, retrieved = ask(q)
        print(f"\nQ: {q}")
        print(f"Searched pages: {[page for page, _, _ in retrieved]}")
        print(f"Found: {answer.found}")
        print(f"A: {answer.answer}")
        for c in answer.citations:
            check = "verified" if quote_is_real(c, retrieved) else "NOT FOUND in extracts"
            print(f'   [page {c.page}] "{c.quote[:100]}" ({check})')