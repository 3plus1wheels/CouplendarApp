from __future__ import annotations

import requests
from django.conf import settings


class GeminiError(RuntimeError):
    pass


class GeminiPlannerClient:
    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"

    def __init__(self, api_key: str | None = None, timeout_seconds: int = 30) -> None:
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.timeout_seconds = timeout_seconds

    def generate_reply(self, prompt: str) -> str:
        if not self.api_key:
            raise GeminiError("Gemini API key is not configured.")

        payload = {
            "systemInstruction": {
                "parts": [
                    {
                        "text": (
                            "You are Couplendar's planner assistant. Help couples turn a vibe, "
                            "budget, time window, or place idea into a concise date plan. "
                            "Be warm, practical, and specific. Keep responses under 90 words. "
                            "Prefer 3 short bullets when helpful."
                        )
                    }
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0.45,
                "maxOutputTokens": 180,
                "thinkingConfig": {
                    "thinkingBudget": 0,
                },
            },
        }

        try:
            response = requests.post(
                self.endpoint,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.api_key,
                },
                json=payload,
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise GeminiError("Gemini request failed.") from exc

        if response.status_code >= 400:
            raise GeminiError("Gemini returned an error response.")

        data = response.json()
        try:
            parts = data["candidates"][0]["content"]["parts"]
        except (KeyError, IndexError, TypeError) as exc:
            raise GeminiError("Gemini response was empty.") from exc

        text = "".join(part.get("text", "") for part in parts).strip()
        if not text:
            raise GeminiError("Gemini response was empty.")
        return text
