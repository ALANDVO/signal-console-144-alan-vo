
"""LLM provider adapters for evaluation execution."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import json
import httpx
from app.core.config import get_settings


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""
    content: str
    raw_response: Dict[str, Any]
    model: str
    usage: Optional[Dict[str, int]] = None


class LLMAdapter(ABC):
    """Abstract base class for LLM provider adapters."""

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Execute a completion request."""
        pass

    @abstractmethod
    async def complete_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """Execute a completion request expecting JSON output matching schema."""
        pass


class OpenAICompatibleAdapter(LLMAdapter):
    """Adapter for OpenAI-compatible APIs (OpenAI, LiteLLM, OpenRouter, Ollama)."""

    def __init__(self, api_key: str, base_url: str, model: str, timeout: float = 30.0):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        content = data["choices"][0]["message"]["content"]
        return LLMResponse(
            content=content,
            raw_response=data,
            model=data.get("model", self.model),
            usage=data.get("usage"),
        )

    async def complete_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        json_system = (
            (system_prompt or "") + "\n\nYou must respond with valid JSON matching the provided schema. No extra text."
        )
        response = await self.complete(prompt, system_prompt=json_system, temperature=temperature)
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            match = re.search(r"\{.*\}", response.content, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise


class AnthropicAdapter(LLMAdapter):
    """Adapter for Anthropic Messages API."""

    def __init__(self, api_key: str, model: str, base_url: Optional[str] = None, timeout: float = 30.0):
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url or "https://api.anthropic.com").rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
        }
        if system_prompt:
            payload["system"] = system_prompt

        response = await self.client.post(
            f"{self.base_url}/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        content = data["content"][0]["text"]
        return LLMResponse(
            content=content,
            raw_response=data,
            model=data.get("model", self.model),
            usage={
                "prompt_tokens": data.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": data.get("usage", {}).get("output_tokens", 0),
            },
        )

    async def complete_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        json_system = (
            (system_prompt or "") + "\n\nYou must respond with valid JSON matching the provided schema. No extra text."
        )
        response = await self.complete(prompt, system_prompt=json_system, temperature=temperature)
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\{.*\}", response.content, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise


class GeminiAdapter(LLMAdapter):
    """Adapter for Google Gemini generateContent API."""

    def __init__(self, api_key: str, model: str, base_url: Optional[str] = None, timeout: float = 30.0):
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url or "https://generativelanguage.googleapis.com").rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        parts = []
        if system_prompt:
            parts.append({"text": system_prompt})
        parts.append({"text": prompt})

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens or 4096,
            },
        }

        response = await self.client.post(
            f"{self.base_url}/v1beta/models/{self.model}:generateContent",
            headers={"Content-Type": "application/json"},
            params={"key": self.api_key},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        content = data["candidates"][0]["content"]["parts"][0]["text"]
        return LLMResponse(
            content=content,
            raw_response=data,
            model=self.model,
            usage=data.get("usageMetadata"),
        )

    async def complete_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        json_system = (
            (system_prompt or "") + "\n\nYou must respond with valid JSON matching the provided schema. No extra text."
        )
        response = await self.complete(prompt, system_prompt=json_system, temperature=temperature)
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\{.*\}", response.content, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise


class OllamaNativeAdapter(LLMAdapter):
    """Adapter for Ollama native API."""

    def __init__(self, model: str, base_url: str = "http://localhost:11434", timeout: float = 30.0):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt or "",
            "temperature": temperature,
            "stream": False,
        }
        if max_tokens:
            payload["num_predict"] = max_tokens

        response = await self.client.post(
            f"{self.base_url}/api/generate",
            headers={"Content-Type": "application/json"},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        content = data.get("response", "")
        return LLMResponse(
            content=content,
            raw_response=data,
            model=data.get("model", self.model),
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            },
        )

    async def complete_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        json_system = (
            (system_prompt or "") + "\n\nYou must respond with valid JSON matching the provided schema. No extra text."
        )
        response = await self.complete(prompt, system_prompt=json_system, temperature=temperature)
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\{.*\}", response.content, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise


def get_llm_adapter() -> Optional[LLMAdapter]:
    """Factory function to create the appropriate LLM adapter from settings."""
    settings = get_settings()
    
    if not settings.llm_api_key and settings.llm_provider != "ollama":
        return None
    
    if settings.llm_provider == "openai-compatible":
        base_url = settings.llm_base_url or "https://api.openai.com/v1"
        return OpenAICompatibleAdapter(
            api_key=settings.llm_api_key or "",
            base_url=base_url,
            model=settings.llm_model,
            timeout=settings.llm_timeout,
        )
    elif settings.llm_provider == "anthropic":
        return AnthropicAdapter(
            api_key=settings.llm_api_key or "",
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            timeout=settings.llm_timeout,
        )
    elif settings.llm_provider == "gemini":
        return GeminiAdapter(
            api_key=settings.llm_api_key or "",
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            timeout=settings.llm_timeout,
        )
    elif settings.llm_provider == "ollama":
        base_url = settings.llm_base_url or "http://localhost:11434"
        return OllamaNativeAdapter(
            model=settings.llm_model,
            base_url=base_url,
            timeout=settings.llm_timeout,
        )
    return None

