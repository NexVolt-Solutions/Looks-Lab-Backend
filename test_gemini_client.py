import json
import types

import pytest

from app.ai import gemini_client


def test_clean_json_response_replaces_ranges():
    raw = "```json\n{\"a\": 1, \"b\": {\"confidence\": 0-100}, \"c\": \"ok\"}\n```"
    cleaned = gemini_client._clean_json_response(raw)
    # After cleaning the invalid 0-100 range should be replaced so json.loads succeeds
    data = json.loads(cleaned)
    assert data["a"] == 1
    # confidence should be normalized to an integer (0)
    assert isinstance(data["b"]["confidence"], int)


class DummyModel:
    def __init__(self, *_a, **_kw):
        pass

    def generate_content(self, *_a, **_kw):
        raise Exception("simulated API failure")


def test_run_gemini_json_safe_returns_fallback(monkeypatch):
    # Monkeypatch the genai GenerativeModel to raise so run_gemini_json_safe returns fallback
    monkeypatch.setattr(gemini_client.genai, "GenerativeModel", DummyModel)

    fallback = {"x": 1}
    out = gemini_client.run_gemini_json_safe("prompt", domain="diet", fallback=fallback)
    assert out == fallback
