"""Adapter pattern — bridge between incompatible interfaces.

Use when: wrapping third-party APIs, hardware drivers, or legacy code so the
         rest of the codebase sees a consistent interface (Ollama, HF, OpenAI).
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class CompletionRequest:
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.1


@dataclass
class CompletionResponse:
    text: str
    model: str
    tokens_used: int = 0


class InferenceBackend(ABC):
    """Unified interface all adapters must implement."""
    @abstractmethod
    def complete(self, req: CompletionRequest) -> CompletionResponse: ...

    @abstractmethod
    def is_available(self) -> bool: ...


class OllamaAdapter(InferenceBackend):
    def __init__(self, model: str = "qwen2.5-coder:7b", base_url: str = "http://localhost:11434") -> None:
        self.model = model
        self.base_url = base_url

    def complete(self, req: CompletionRequest) -> CompletionResponse:
        import requests
        resp = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": req.prompt, "stream": False,
                  "options": {"temperature": req.temperature, "num_predict": req.max_tokens}},
            timeout=120,
        )
        resp.raise_for_status()
        body = resp.json()
        return CompletionResponse(text=body["response"], model=self.model)

    def is_available(self) -> bool:
        try:
            import requests
            return requests.get(f"{self.base_url}/api/tags", timeout=2).ok
        except Exception:
            return False


class FallbackBackend(InferenceBackend):
    """Try primary, fall back to secondary if primary fails."""
    def __init__(self, primary: InferenceBackend, secondary: InferenceBackend) -> None:
        self.primary = primary
        self.secondary = secondary

    def complete(self, req: CompletionRequest) -> CompletionResponse:
        if self.primary.is_available():
            try:
                return self.primary.complete(req)
            except Exception:
                pass
        return self.secondary.complete(req)

    def is_available(self) -> bool:
        return self.primary.is_available() or self.secondary.is_available()
