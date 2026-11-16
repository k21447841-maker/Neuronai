from typing import Any, Dict, List
from faster_whisper import WhisperModel
from app.core.config import get_settings


def format_srt_timestamp(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"


def format_vtt_timestamp(seconds: float) -> str:
    return format_srt_timestamp(seconds).replace(",", ".")


def transcribe_audio_with_whisper(audio_path: str, language: str = None) -> List[Dict[str, Any]]:
    model = WhisperModel(get_settings().WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio_path, language=language, word_timestamps=True)
    results: List[Dict[str, Any]] = []
    for idx, seg in enumerate(segments, start=1):
        words = [{"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)} for w in (seg.words or [])]
        results.append({"index": idx, "start": round(seg.start, 3), "end": round(seg.end, 3), "text": seg.text.strip(), "words": words})
    return results


def export_srt(segments: List[Dict[str, Any]]) -> str:
    lines = []
    for i, s in enumerate(segments, start=1):
        lines.extend([str(i), f"{format_srt_timestamp(s['start'])} --> {format_srt_timestamp(s['end'])}", s["text"], ""])
    return "\n".join(lines)


def export_vtt(segments: List[Dict[str, Any]]) -> str:
    lines = ["WEBVTT", ""]
    for s in segments:
        lines.extend([f"{format_vtt_timestamp(s['start'])} --> {format_vtt_timestamp(s['end'])}", s["text"], ""])
    return "\n".join(lines)
