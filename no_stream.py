from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()

question = (
    "Explain, in about 300 words, the main costs an Australian residential "
    "property investor should budget for each year."
)

response = client.messages.create(
    model="claude-haiku-5-5",
    max_tokens=800,
    system="You are an assistant for an Australian property investor.",
    messages=[{"role": "user", "content": question}],
)
answer = "".join(block.text for block in response.content if block.type == "text")
print(answer)

print(f"\n\n(input tokens: {response.usage.input_tokens}, output tokens: {response.usage.output_tokens})")