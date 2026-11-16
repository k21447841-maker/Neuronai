from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from fastapi import HTTPException
from app.core.config import get_settings
from app.core.security import decrypt_secret, encrypt_secret

YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly"]


def create_oauth_flow(state: Optional[str] = None) -> Flow:
    s = get_settings()
    if not s.GOOGLE_CLIENT_ID or not s.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=424, detail="Google OAuth is not configured on backend.")
    cfg = {"web": {"client_id": s.GOOGLE_CLIENT_ID, "client_secret": s.GOOGLE_CLIENT_SECRET, "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token", "redirect_uris": [s.GOOGLE_REDIRECT_URI]}}
    flow = Flow.from_client_config(cfg, scopes=YOUTUBE_SCOPES, state=state)
    flow.redirect_uri = s.GOOGLE_REDIRECT_URI
    return flow


def credentials_from_encrypted_row(token_row: Any) -> Credentials:
    s = get_settings()
    creds = Credentials(
        token=decrypt_secret(token_row.encrypted_access_token),
        refresh_token=decrypt_secret(token_row.encrypted_refresh_token) if token_row.encrypted_refresh_token else None,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=s.GOOGLE_CLIENT_ID,
        client_secret=s.GOOGLE_CLIENT_SECRET,
        scopes=YOUTUBE_SCOPES,
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_row.encrypted_access_token = encrypt_secret(creds.token)
        token_row.expires_at = creds.expiry or datetime.now(timezone.utc)
    return creds


def fetch_my_channel_info(creds: Credentials) -> Dict[str, Any]:
    yt = build("youtube", "v3", credentials=creds)
    items = yt.channels().list(part="snippet,statistics", mine=True).execute().get("items", [])
    if not items:
        raise HTTPException(status_code=404, detail="No YouTube channel found on this Google account.")
    ch = items[0]
    return {
        "youtube_channel_id": ch["id"], "channel_title": ch["snippet"]["title"],
        "channel_handle": ch["snippet"].get("customUrl"), "thumbnail_url": ch["snippet"]["thumbnails"]["default"]["url"],
        "subscriber_count": int(ch["statistics"].get("subscriberCount", 0)), "video_count": int(ch["statistics"].get("videoCount", 0)),
    }


def resumable_upload_video(
    creds: Credentials, video_file_path: str, title: str, description: str, tags: List[str],
    privacy_status: str = "private", is_short: bool = False, publish_at_iso: Optional[str] = None, thumbnail_path: Optional[str] = None,
) -> str:
    yt = build("youtube", "v3", credentials=creds)
    final_desc = f"{description}\n\n#Shorts".strip() if is_short and "#Shorts" not in description else description
    status_body: Dict[str, Any] = {"privacyStatus": privacy_status, "selfDeclaredMadeForKids": False}
    if publish_at_iso and privacy_status == "private":
        status_body["publishAt"] = publish_at_iso
    body = {"snippet": {"title": title[:100], "description": final_desc[:5000], "tags": tags[:30], "categoryId": "22"}, "status": status_body}
    req = yt.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(video_file_path, chunksize=5 * 1024 * 1024, resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    yt_id = resp["id"]
    if thumbnail_path:
        yt.thumbnails().set(videoId=yt_id, media_body=MediaFileUpload(thumbnail_path)).execute()
    return yt_id


def fetch_uploaded_video_metrics(creds: Credentials, youtube_video_ids: List[str]) -> List[Dict[str, Any]]:
    if not youtube_video_ids:
        return []
    yt = build("youtube", "v3", credentials=creds)
    resp = yt.videos().list(part="snippet,statistics,status", id=",".join(youtube_video_ids[:50])).execute()
    return [
        {"youtube_video_id": v["id"], "title": v["snippet"]["title"], "published_at": v["snippet"]["publishedAt"], "views": int(v["statistics"].get("viewCount", 0)), "likes": int(v["statistics"].get("likeCount", 0)), "comments": int(v["statistics"].get("commentCount", 0))}
        for v in resp.get("items", [])
    ]
