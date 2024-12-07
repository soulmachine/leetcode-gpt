from anthropic import Anthropic
import os

def generate_code(prompt: str) -> str:
    client = Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),  # This is the default and can be omitted
    )
    response = client.messages.create(
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
        model="claude-3-5-sonnet-20241022",
    )
    return response.content[0].text
