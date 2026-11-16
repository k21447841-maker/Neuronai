import asyncio
import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.config import get_settings

router = APIRouter()


@router.websocket("/ws/jobs/{job_id}")
async def job_updates_ws(websocket: WebSocket, job_id: str):
    await websocket.accept()
    r = aioredis.from_url(get_settings().REDIS_URL, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe(f"job_updates:{job_id}")
    try:
        while True:
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg and msg.get("data"):
                await websocket.send_text(msg["data"])
            await asyncio.sleep(0.2)
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(f"job_updates:{job_id}")
        await r.close()
