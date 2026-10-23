import json
from dataclasses import dataclass, field
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from app.modules.guidance.script import SYSTEM_PROMPT
from app.modules.guidance.settings import GuidanceSettings


@dataclass(frozen=True)
class ProviderResult:
    segments: object
    response: dict
    suggestions: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)


class Organizer(Protocol):
    def organize(
        self, question: str, answer: str, *, context: dict[str, str] | None = None
    ) -> ProviderResult: ...


class ProviderFailure(Exception):
    def __init__(self, code: str, *, http_status: int | None = None):
        super().__init__(code)
        self.http_status = http_status


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class GeminiOrganizer:
    def __init__(self, settings: GuidanceSettings):
        self.settings = settings

    def organize(
        self, question: str, answer: str, *, context: dict[str, str] | None = None
    ) -> ProviderResult:
        key = self.settings.gemini_api_key
        if key is None:
            raise ProviderFailure("unconfigured")
        payload = {
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": json.dumps(
                                {"question": question, "answer": answer, "context": context or {}},
                                ensure_ascii=False,
                            )
                        }
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0,
                "maxOutputTokens": 2048,
                "responseMimeType": "application/json",
                "responseJsonSchema": {
                    "type": "object",
                    "properties": {
                        "segments": {
                            "description": "Texto desenvolvido a partir da ideia informada.",
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 1,
                            "maxItems": 12,
                        },
                        "suggestions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "maxItems": 4,
                            "description": "Possibilidades a avaliar, sem adoção automática.",
                        },
                        "open_questions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "maxItems": 3,
                            "description": "Lacunas específicas, sem substituir o roteiro fixo.",
                        },
                    },
                    "required": ["segments", "suggestions", "open_questions"],
                    "additionalProperties": False,
                },
            },
        }
        # Fixed provider host; no user URL, redirect, tool, file or web grounding.
        request = Request(
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.settings.guidance_model}:generateContent",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": key.get_secret_value()},
            method="POST",
        )
        try:
            with build_opener(NoRedirect()).open(
                request, timeout=self.settings.guidance_timeout_seconds
            ) as response:
                body = response.read(131073)
            if len(body) > 131072:
                raise ProviderFailure("oversized_response")
            result = json.loads(body)
            candidate = result["candidates"][0]
            if candidate.get("finishReason") != "STOP":
                raise ProviderFailure("incomplete_response")
            text = "".join(part.get("text", "") for part in candidate["content"]["parts"])
            value = json.loads(text)
            if not isinstance(value, dict) or set(value) != {
                "segments",
                "suggestions",
                "open_questions",
            }:
                raise ProviderFailure("invalid_response")
            return ProviderResult(
                value["segments"],
                {"text": text, "usage": result.get("usageMetadata")},
                value["suggestions"],
                value["open_questions"],
            )
        except HTTPError as error:
            # Keep only the status; upstream bodies may contain private provider metadata.
            raise ProviderFailure("provider_unavailable", http_status=error.code) from error
        except (
            URLError,
            TimeoutError,
            OSError,
            ValueError,
            KeyError,
            IndexError,
            TypeError,
        ) as error:
            raise ProviderFailure("provider_unavailable") from error
