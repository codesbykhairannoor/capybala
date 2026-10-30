"""
capybala.models.supervisor
~~~~~~~~~~~~~~~~~~~~~~~~~~
Lightweight Doctor/Supervisor model integrations (Llama 3.2 1B, OpenRouter, Ollama, Llama Stack).
"""

import urllib.request
import json
from abc import ABC, abstractmethod
from typing import Optional


class BaseSupervisorClient(ABC):
    @abstractmethod
    def generate(self, model: str, prompt: str, max_tokens: int = 150) -> str:
        """Generates supervisor intervention directives."""
        pass


class OpenRouterSupervisorClient(BaseSupervisorClient):
    """
    Lightweight OpenRouter client for ultra-cheap supervisor models (Llama 3.2 1B, GPT-4o-mini).
    Uses standard library urllib - 0 external dependencies!
    """

    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1/chat/completions"):
        self.api_key = api_key
        self.base_url = base_url

    def generate(self, model: str, prompt: str, max_tokens: int = 150) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/capybala/capybala",
            "X-Title": "Capybala Doctor Supervisor"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.3
        }
        req = urllib.request.Request(self.base_url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]


class OllamaSupervisorClient(BaseSupervisorClient):
    """
    Local on-device supervisor client via Ollama (e.g., Llama-3.2:1b).
    """

    def __init__(self, host: str = "http://localhost:11434"):
        self.endpoint = f"{host.rstrip('/')}/api/generate"

    def generate(self, model: str, prompt: str, max_tokens: int = 150) -> str:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.3}
        }
        req = urllib.request.Request(self.endpoint, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "")


class MockSupervisorClient(BaseSupervisorClient):
    """
    Deterministic supervisor for unit testing and offline environments.
    """

    def __init__(self, return_text: str = "Pivot to inspecting module imports and configuration."):
        self.return_text = return_text

    def generate(self, model: str, prompt: str, max_tokens: int = 150) -> str:
        return self.return_text

