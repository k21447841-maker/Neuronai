from typing import Any, Dict, List
import httpx
from fastapi import HTTPException


class ElevenLabsAdapter:
    BASE_URL = "https://api.elevenlabs.io/v1"

    async def test_and_get_subscription(self, api_key: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(f"{self.BASE_URL}/user/subscription", headers={"xi-api-key": api_key})
        if r.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"ElevenLabs auth failed ({r.status_code}): {r.text[:250]}")
        data = r.json()
        return {"status": "connected", "tier": data.get("tier"), "character_count": data.get("character_count", 0), "character_limit": data.get("character_limit", 0)}

    async def list_voices(self, api_key: str) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(f"{self.BASE_URL}/voices", headers={"xi-api-key": api_key})
        if r.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Failed to load voices: {r.text[:250]}")
        return [
            {"voice_id": v["voice_id"], "name": v["name"], "category": v.get("category", "premade"), "labels": v.get("labels", {}), "preview_url": v.get("preview_url")}
            for v in r.json().get("voices", [])
        ]

    async def synthesize(
        self, api_key: str, voice_id: str, text: str, model_id: str = "eleven_multilingual_v2",
        stability: float = 0.5, similarity_boost: float = 0.75, style: float = 0.0, speed: float = 1.0,
    ) -> bytes:
        payload = {"text": text, "model_id": model_id, "voice_settings": {"stability": stability, "similarity_boost": similarity_boost, "style": style, "use_speaker_boost": True, "speed": speed}}
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(
                f"{self.BASE_URL}/text-to-speech/{voice_id}",
                headers={"xi-api-key": api_key, "Accept": "audio/mpeg", "Content-Type": "application/json"},
                json=payload,
            )
        if r.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"ElevenLabs synthesis error ({r.status_code}): {r.text[:300]}")
        return r.content
