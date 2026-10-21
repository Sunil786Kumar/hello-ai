from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()

# A long, made-up lease. Caching only kicks in above a minimum size,
# so we generate a few hundred clauses.
LEASE = "\n".join(
    [
        "RESIDENTIAL TENANCY AGREEMENT: 12 Example Street, Warner QLD 4500",
        "Clause 1: Rent is $620 per week, payable fortnightly in advance.",
        "Clause 2: The bond is $2,480, lodged with the RTA.",
        "Clause 3: Pets are allowed with written approval from the lessor.",
        "Clause 4: The tenant must water the garden and mow the lawn monthly.",
    ]
    + [
        f"Clause {i}: The tenant must keep fixture number {i} clean and in good repair, "
        f"and report any damage to fixture {i} to the agent within 7 days."
        for i in range(5, 400)
    ]
)

SYSTEM = [
    {"type": "text", "text": "You answer questions about the lease below. Quote the clause number."},
    {"type": "text", "text": LEASE, "cache_control": {"type": "ephemeral"}},  # cache everything up to here
]


def ask(question: str) -> None:
    response = client.messages.create(
        model="claude-haiku-5-5",
        max_tokens=300,
        system=SYSTEM,
        messages=[{"role": "user", "content": question}],
    )
    answer = "".join(b.text for b in response.content if b.type == "text")
    u = response.usage
    print(f"\nQ: {question}\nA: {answer}")
    print(
        f"   input: {u.input_tokens} | cache written: {u.cache_creation_input_tokens} "
        f"| cache read: {u.cache_read_input_tokens}"
    )


if __name__ == "__main__":
    ask("How much is the bond?")
    ask("Are pets allowed?")
    ask("Who mows the lawn?")