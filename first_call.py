from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()          # reads ANTHROPIC_API_KEY from .env
client = Anthropic()   # picks up the key automatically

response = client.messages.create(
    model="claude-haiku-5-5",   # the small, cheap model, good for testing
    max_tokens=300,
    system="You are an assistant for an Australian property investor. Be concise.",
    messages=[
        {"role": "user", "content": "In two sentences, what is a council rates notice?"}
    ],
)

print(response.content[0].text)
print(response.usage)
