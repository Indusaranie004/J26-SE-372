
"""
Check the Gemini API connection for Component C.

This test does not send any legal evidence.
"""

import os

from dotenv import load_dotenv
from google import genai

def main():
    # load env variables from component-c/.env
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing. Check your .env file."
        )

    # create Gemini client
    client = genai.Client(api_key=api_key)

    print(f"Testing Gemini API with model: {model_name}")

    # send a simplle test request
    response = client.models.generate_content(
        model=model_name,
        contents=(
            "This is an API connection test "
            "Reply with: Gemini connection successful"
        ),
    )

    if not response.text:
        raise RuntimeError("Gemini returned no text response")

    print("Model response:", response.text.strip())

if __name__ == "__main__":
    main()