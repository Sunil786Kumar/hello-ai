from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()

question = (
    "Explain, in about 300 words, the main costs an Australian residential "
    "property investor should budget for each year."
)

with client.messages.stream(
    model="claude-haiku-5-5",
    max_tokens=800,
    system="You are an assistant for an Australian property investor.",
    messages=[{"role": "user", "content": question}],
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)

    final = stream.get_final_message()

print(f"\n\n(input tokens: {final.usage.input_tokens}, output tokens: {final.usage.output_tokens})")