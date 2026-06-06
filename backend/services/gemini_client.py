"""Gemini API service — wrapper for all LLM calls.

Uses google-genai SDK (the newer, simpler SDK).
All agents use Gemini for text generation, JSON structured output,
and vision tasks (reading menu photos, shop photos).
"""

import json
from google import genai
from config import GEMINI_API_KEY

# Initialize the Gemini client
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


async def generate_text(prompt: str, model: str = "gemini-2.5-flash") -> str:
    """Generate text from a prompt. Returns raw text response."""
    if not client:
        return '{"error": "No Gemini API key configured"}'

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )
    return response.text


async def generate_json(prompt: str, model: str = "gemini-2.5-flash") -> dict:
    """Generate a JSON response from a prompt.
    
    Automatically strips markdown code fences if Gemini wraps the response.
    Returns parsed Python dict.
    """
    full_prompt = f"{prompt}\n\nRespond with ONLY valid JSON. No markdown, no explanations, no code fences."

    text = await generate_text(full_prompt, model)

    # Strip markdown code fences if present
    text = text.strip()
    if text.startswith("```"):
        # Remove first line (```json or ```) and last line (```)
        lines = text.split("\n")
        text = "\n".join(lines[1:])
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    return json.loads(text)


async def analyze_image(image_url: str, prompt: str, model: str = "gemini-2.5-flash") -> str:
    """Analyze an image using Gemini Vision.
    
    Used for:
    - Reading menu photos → extracting items + prices
    - Reading shop front photos → extracting business details
    - Understanding uploaded documents
    """
    if not client:
        return '{"error": "No Gemini API key configured"}'

    response = client.models.generate_content(
        model=model,
        contents=[
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {"file_data": {"file_uri": image_url, "mime_type": "image/jpeg"}},
                ],
            }
        ],
    )
    return response.text


async def analyze_image_json(image_url: str, prompt: str, model: str = "gemini-2.5-flash") -> dict:
    """Analyze an image and return structured JSON output."""
    full_prompt = f"{prompt}\n\nRespond with ONLY valid JSON. No markdown, no explanations."
    text = await analyze_image(image_url, full_prompt, model)

    # Strip markdown code fences
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:])
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    return json.loads(text)
