from anthropic import Anthropic
import os

def send_prompt(prompt: str) -> str:
    client = Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),  # This is the default and can be omitted
    )
    response = client.messages.create(
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
        model="claude-3-5-sonnet-20241022",
    )
    return response.content[0].text

def translate_java_to_other_language(java_code: str, language: str) -> str:
    if language == "python":
        language = "python3"
    prompt = f"""You are an expert programmer. Please translate the following Java code to {language},
    preserve all original comments from the Java code, and feel free toadd neccesary comments to make it more readable.
    Only return the translated {language} code without any explanation or markdown formatting.

    Here's the Java code:
    {java_code}"""

    prompt = f"""You are an expert programmer. Translate this Java code to idiomatic {language}.
    - Preserve all original comments
    - Only return the translated {language} code without any explanation or markdown formatting
    - Remove trailing whitespace or tabs for all lines

    Java code:
    {java_code}"""

    try:
        translated_code = send_prompt(prompt)
        return translated_code.strip()
    except Exception as e:
        raise Exception(f"Failed to translate Java code: {str(e)}")
