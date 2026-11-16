from typing import Any, Dict, Type
import httpx
from fastapi import HTTPException
from app.providers.base import BaseLLMProvider, LLMResponse


class ClaudeProvider(BaseLLMProvider):
    slug = "claude"
    BASE_URL = "https://api.anthropic.com/v1/messages"

    async def test_connection(self, api_key: str, model: str, timeout: int = 30) -> Dict[str, Any]:
        resp = await self.generate_text(api_key, model, "Reply OK.", "Ping", 0.0, 16, timeout)
        return {"status": "connected", "model": resp.model}

    async def generate_text(
        self, api_key: str, model: str, system_prompt: str, user_prompt: str,
        temperature: float = 0.7, max_tokens: int = 4096, timeout: int = 60,
    ) -> LLMResponse:
        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        payload = {"model": model, "max_tokens": max_tokens, "temperature": temperature, "system": system_prompt, "messages": [{"role": "user", "content": user_prompt}]}
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(self.BASE_URL, headers=headers, json=payload)
        if r.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Claude API error ({r.status_code}): {r.text[:300]}")
        data = r.json()
        text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        usage = data.get("usage", {})
        return LLMResponse(text, data.get("model", model), usage.get("input_tokens", 0), usage.get("output_tokens", 0), data)


class DeepSeekProvider(BaseLLMProvider):
    slug = "deepseek"
    BASE_URL = "https://api.deepseek.com/chat/completions"

    async def test_connection(self, api_key: str, model: str, timeout: int = 30) -> Dict[str, Any]:
        resp = await self.generate_text(api_key, model, "Reply OK.", "Ping", 0.0, 16, timeout)
        return {"status": "connected", "model": resp.model}

    async def generate_text(
        self, api_key: str, model: str, system_prompt: str, user_prompt: str,
        temperature: float = 0.7, max_tokens: int = 4096, timeout: int = 60,
    ) -> LLMResponse:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": model, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], "temperature": temperature, "max_tokens": max_tokens}
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(self.BASE_URL, headers=headers, json=payload)
        if r.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"DeepSeek API error ({r.status_code}): {r.text[:300]}")
        data = r.json()
        usage = data.get("usage", {})
        return LLMResponse(data["choices"][0]["message"]["content"], data.get("model", model), usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0), data)


class GeminiProvider(BaseLLMProvider):
    slug = "gemini"

    async def test_connection(self, api_key: str, model: str, timeout: int = 30) -> Dict[str, Any]:
        resp = await self.generate_text(api_key, model, "Reply OK.", "Ping", 0.0, 16, timeout)
        return {"status": "connected", "model": resp.model}

    async def generate_text(
        self, api_key: str, model: str, system_prompt: str, user_prompt: str,
        temperature: float = 0.7, max_tokens: int = 4096, timeout: int = 60,
    ) -> LLMResponse:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
        payload = {"systemInstruction": {"parts": [{"text": system_prompt}]}, "contents": [{"parts": [{"text": user_prompt}]}], "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}}
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, headers=headers, json=payload)
        if r.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Gemini API error ({r.status_code}): {r.text[:300]}")
        data = r.json()
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts)
        usage = data.get("usageMetadata", {})
        return LLMResponse(text, model, usage.get("promptTokenCount", 0), usage.get("candidatesTokenCount", 0), data)


LLM_PROVIDERS: Dict[str, Type[BaseLLMProvider]] = {"claude": ClaudeProvider, "deepseek": DeepSeekProvider, "gemini": GeminiProvider}


def get_llm_provider(slug: str) -> BaseLLMProvider:
    cls = LLM_PROVIDERS.get(slug)
    if not cls:
        raise HTTPException(status_code=400, detail=f"Unsupported LLM provider: {slug}")
    return cls()
