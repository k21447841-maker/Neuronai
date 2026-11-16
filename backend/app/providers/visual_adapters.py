import base64
from typing import Dict
import httpx
from fastapi import HTTPException


class VisualGenerationAdapter:
    async def generate_image(self, provider_slug: str, api_key: str, model: str, prompt: str, width: int, height: int) -> bytes:
        if provider_slug == "openai_images":
            size = "1024x1024"
            if width > height:
                size = "1536x1024" if model == "gpt-image-1" else "1792x1024"
            elif height > width:
                size = "1024x1536" if model == "gpt-image-1" else "1024x1792"
            async with httpx.AsyncClient(timeout=120) as client:
                r = await client.post(
                    "https://api.openai.com/v1/images/generations",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={"model": model, "prompt": prompt, "size": size, "n": 1},
                )
            if r.status_code >= 400:
                raise HTTPException(status_code=502, detail=f"OpenAI Image API error: {r.text[:300]}")
            item = r.json()["data"][0]
            if "b64_json" in item:
                return base64.b64decode(item["b64_json"])
            return httpx.get(item["url"], timeout=60).content

        if provider_slug == "stability":
            async with httpx.AsyncClient(timeout=120) as client:
                r = await client.post(
                    "https://api.stability.ai/v2beta/stable-image/generate/sd3",
                    headers={"Authorization": f"Bearer {api_key}", "Accept": "image/*"},
                    files={"none": ("", "")},
                    data={"prompt": prompt, "model": model, "output_format": "png"},
                )
            if r.status_code >= 400:
                raise HTTPException(status_code=502, detail=f"Stability AI error: {r.text[:300]}")
            return r.content

        raise HTTPException(status_code=424, detail=f"Visual provider '{provider_slug}' requires a configured visual adapter.")

    async def test_connection(self, provider_slug: str, api_key: str) -> Dict[str, str]:
        if provider_slug == "openai_images":
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get("https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {api_key}"})
            if r.status_code >= 400:
                raise HTTPException(status_code=502, detail="Invalid OpenAI API key")
            return {"status": "connected"}
        if provider_slug == "stability":
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get("https://api.stability.ai/v1/user/account", headers={"Authorization": f"Bearer {api_key}"})
            if r.status_code >= 400:
                raise HTTPException(status_code=502, detail="Invalid Stability AI key")
            return {"status": "connected"}
        raise HTTPException(status_code=400, detail=f"Unknown visual provider: {provider_slug}")
