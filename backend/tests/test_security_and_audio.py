from cryptography.fernet import Fernet
from app.core.security import decrypt_secret, encrypt_secret, mask_api_key
from app.video.subtitles import export_srt, export_vtt, format_srt_timestamp


def test_secret_roundtrip(monkeypatch):
    monkeypatch.setenv("CREDENTIAL_ENCRYPTION_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "jwt-secret")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

    raw = "sk-ant-api03-test-secret-123456"
    enc = encrypt_secret(raw)
    assert enc != raw
    assert decrypt_secret(enc) == raw
    assert mask_api_key(raw) == "sk-a...3456"


def test_subtitle_exports():
    segs = [{"start": 0.5, "end": 2.25, "text": "Welcome to Neuroflow AI."}]
    assert format_srt_timestamp(0.5) == "00:00:00,500"
    assert "00:00:00,500 --> 00:00:02,250" in export_srt(segs)
    assert "WEBVTT" in export_vtt(segs)
