import json

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()
MODEL = "claude-haiku-5-5"

# --- 1. Your data (stands in for the Week 1 API or a database) ---
DOCUMENTS = {
    "rates_notice": {
        "title": "Moreton Bay rates notice, Jul-Dec 2026",
        "amount": 1199.50,
        "due_date": "2026-11-30",
        "note": "Council rates are GST-free",
    },
    "lease": {
        "title": "Residential lease, 12 Example Street",
        "weekly_rent": 620.00,
        "start_date": "2026-03-01",
        "end_date": "2027-02-28",
    },
    "pm_invoice": {
        "title": "Property manager invoice, September 2026",
        "amount": 1320.00,
        "includes_gst": True,
        "issued": "2026-10-01",
    },
}


# --- 2. Your tools: ordinary Python functions ---
def get_document(doc_type: str) -> dict:
    doc = DOCUMENTS.get(doc_type)
    return doc if doc else {"error": f"No document of type '{doc_type}'"}


def calculate_gst(amount: float, includes_gst: bool) -> dict:
    if includes_gst:
        gst = amount / 11
        ex_gst = amount - gst
    else:
        gst = amount * 0.10
        ex_gst = amount
    return {
        "gst": round(gst, 2),
        "amount_ex_gst": round(ex_gst, 2),
        "amount_inc_gst": round(ex_gst + gst, 2),
    }


TOOL_FUNCTIONS = {"get_document": get_document, "calculate_gst": calculate_gst}

# --- 3. Descriptions Claude reads to decide when to use each tool ---
TOOLS = [
    {
        "name": "get_document",
        "description": "Look up one of the investor's documents by type. Returns its key figures.",
        "input_schema": {
            "type": "object",
            "properties": {
                "doc_type": {"type": "string", "enum": ["rates_notice", "lease", "pm_invoice"]},
            },
            "required": ["doc_type"],
        },
    },
    {
        "name": "calculate_gst",
        "description": "Calculate Australian GST (10%) for an amount. Always use this instead of doing GST arithmetic yourself.",
        "input_schema": {
            "type": "object",
            "properties": {
                "amount": {"type": "number", "description": "Amount in AUD"},
                "includes_gst": {"type": "boolean", "description": "True if the amount already includes GST"},
            },
            "required": ["amount", "includes_gst"],
        },
    },
]

SYSTEM = (
    "You help an Australian property investor with their documents. "
    "Use the tools to look up figures and do calculations; never guess them."
)


# --- 4. The agent loop ---
def run_agent(question: str, max_turns: int = 10) -> str:
    messages = [{"role": "user", "content": question}]

    for _ in range(max_turns):  # safety cap so a confused model can't loop forever
        response = client.messages.create(
            model=MODEL, max_tokens=1000, system=SYSTEM, tools=TOOLS, messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        # No tool requested: Claude has its final answer
        if response.stop_reason != "tool_use":
            return "".join(block.text for block in response.content if block.type == "text")

        # Claude asked for one or more tools: run them and send the results back
        results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"  -> Claude calls {block.name}({block.input})")
                output = TOOL_FUNCTIONS[block.name](**block.input)
                print(f"  <- result: {output}")
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(output),
                })
        messages.append({"role": "user", "content": results})

    return "Stopped: too many tool calls."


if __name__ == "__main__":
    questions = [
        "How much GST is in my property manager's invoice?",
        "When is my rates notice due, and how much GST is in it?",
        "What's my annual rent from the lease?",
    ]
    for q in questions:
        print(f"\nYou: {q}")
        print(f"Claude: {run_agent(q)}")
