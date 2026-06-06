"""Sarvam AI service — Multilingual TTS and Translation for Indian languages.

Sarvam AI provides:
- Text-to-Speech (TTS) in 10+ Indian languages
- Translation between Hindi, English, Tamil, Telugu, etc.
- Transliteration (Hindi → Roman script)

Setup: Set SARVAM_API_KEY in environment variables.
Get API key from: https://dashboard.sarvam.ai

Usage:
    from services.sarvam_client import translate_text, text_to_speech
    translated = await translate_text("Hello", source="en", target="hi")
    audio_url = await text_to_speech("नमस्ते", language="hi")
"""

import httpx
import asyncio
import base64
from config import SARVAM_API_KEY
from services.supabase_client import upload_to_storage

SARVAM_BASE_URL = "https://api.sarvam.ai"


def _headers() -> dict:
    return {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json",
    }


async def translate_text(
    text: str,
    source_lang: str = "en",
    target_lang: str = "hi",
) -> str:
    """Translate text between Indian languages using Sarvam AI.
    
    Supported languages: en, hi, ta, te, kn, ml, mr, bn, gu, pa, or
    Returns translated text string.
    """
    if not SARVAM_API_KEY:
        print("[Sarvam] No API key configured, returning original text")
        return text

    async def _translate():
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{SARVAM_BASE_URL}/translate",
                headers=_headers(),
                json={
                    "input": text,
                    "source_language_code": source_lang,
                    "target_language_code": target_lang,
                    "mode": "formal",
                    "model": "mayura:v1",
                    "enable_preprocessing": True,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("translated_text", text)

    try:
        return await _translate()
    except Exception as e:
        print(f"[Sarvam] Translation error: {e}")
        return text


async def text_to_speech(
    text: str,
    language: str = "hi-IN",
    session_id: str = "",
    filename: str = "speech.wav",
) -> str | None:
    """Convert text to speech using Sarvam AI TTS.
    
    Supported languages: hi-IN, en-IN, ta-IN, te-IN, kn-IN, ml-IN, mr-IN, bn-IN, gu-IN, pa-IN, od-IN
    Returns public URL of the audio file (uploaded to Supabase Storage).
    """
    if not SARVAM_API_KEY:
        print("[Sarvam] No API key configured, skipping TTS")
        return None

    async def _tts():
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{SARVAM_BASE_URL}/text-to-speech",
                headers=_headers(),
                json={
                    "inputs": [text],
                    "target_language_code": language,
                    "speaker": "meera",  # Natural-sounding Hindi female voice
                    "model": "bulbul:v1",
                    "pitch": 0,
                    "pace": 1.0,
                    "loudness": 1.5,
                    "enable_preprocessing": True,
                },
            )
            response.raise_for_status()
            data = response.json()
            # Response contains base64-encoded audio
            audio_b64 = data.get("audios", [None])[0]
            if not audio_b64:
                return None
            return base64.b64decode(audio_b64)

    try:
        audio_bytes = await _tts()
        if not audio_bytes:
            return None

        # Upload to Supabase Storage
        if session_id:
            path = f"audio/{session_id}/{filename}"
            url = await upload_to_storage(
                "genesis-assets",
                path,
                audio_bytes,
                content_type="audio/wav",
            )
            return url
        return None

    except Exception as e:
        print(f"[Sarvam] TTS error: {e}")
        return None


async def transliterate_text(
    text: str,
    source_script: str = "Devanagari",
    target_script: str = "Latin",
) -> str:
    """Transliterate text between scripts (e.g., Hindi → Roman).
    
    source/target scripts: Devanagari, Latin, Tamil, Telugu, Kannada, etc.
    """
    if not SARVAM_API_KEY:
        return text

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{SARVAM_BASE_URL}/transliterate",
                headers=_headers(),
                json={
                    "input": text,
                    "source_script": source_script,
                    "target_script": target_script,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("transliterated_text", text)
    except Exception as e:
        print(f"[Sarvam] Transliteration error: {e}")
        return text


async def translate_for_agents(
    text: str,
    target_languages: list[str] = None,
) -> dict[str, str]:
    """Translate text to multiple Indian languages at once.
    
    Returns dict of language_code → translated_text.
    Useful for creating multilingual website content, legal docs, etc.
    """
    if target_languages is None:
        target_languages = ["hi", "ta", "te", "mr", "bn"]

    results = {"en": text}

    for lang in target_languages:
        translated = await translate_text(text, source_lang="en", target_lang=lang)
        results[lang] = translated

    return results
