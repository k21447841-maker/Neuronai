import json
import os
import re
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Tuple
from app.core.config import get_settings


@dataclass
class SilenceSegment:
    start: float
    end: float
    duration: float


def probe_duration(file_path: str) -> float:
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", file_path]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(json.loads(res.stdout)["format"]["duration"])


def detect_silences(file_path: str, threshold_db: float = -35.0, min_duration: float = 0.45) -> List[SilenceSegment]:
    ffmpeg = get_settings().FFMPEG_BINARY_PATH
    res = subprocess.run(
        [ffmpeg, "-i", file_path, "-af", f"silencedetect=noise={threshold_db}dB:d={min_duration}", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    segments: List[SilenceSegment] = []
    current_start: Optional[float] = None
    for line in res.stderr.splitlines():
        m_start = re.search(r"silence_start:\s*([0-9.]+)", line)
        m_end = re.search(r"silence_end:\s*([0-9.]+)\s*\|\s*silence_duration:\s*([0-9.]+)", line)
        if m_start:
            current_start = float(m_start.group(1))
        elif m_end and current_start is not None:
            segments.append(SilenceSegment(current_start, float(m_end.group(1)), float(m_end.group(2))))
            current_start = None
    return segments


def process_voice_audio(
    input_path: str, output_path: str, threshold_db: float = -35.0, min_silence_duration: float = 0.45,
    retain_pause_seconds: float = 0.18, normalize_loudness: bool = True, noise_reduction: bool = True,
    fade_in_seconds: float = 0.1, fade_out_seconds: float = 0.25, bgm_path: Optional[str] = None, bgm_volume: float = 0.15,
) -> Tuple[float, float, List[SilenceSegment]]:
    ffmpeg = get_settings().FFMPEG_BINARY_PATH
    orig_duration = probe_duration(input_path)
    silences = detect_silences(input_path, threshold_db=threshold_db, min_duration=min_silence_duration)

    keep_intervals = []
    cursor = 0.0
    for s in silences:
        half_retain = min(retain_pause_seconds / 2.0, s.duration / 2.0)
        keep_end = min(s.start + half_retain, s.end)
        if keep_end > cursor:
            keep_intervals.append((cursor, keep_end))
        cursor = max(cursor, s.end - half_retain)
    if cursor < orig_duration:
        keep_intervals.append((cursor, orig_duration))
    if not keep_intervals:
        keep_intervals = [(0.0, orig_duration)]

    filter_parts, concat_inputs = [], []
    for idx, (st, en) in enumerate(keep_intervals):
        filter_parts.append(f"[0:a]atrim=start={st:.3f}:end={en:.3f},asetpts=PTS-STARTPTS[a{idx}]")
        concat_inputs.append(f"[a{idx}]")
    filter_parts.append(f"{''.join(concat_inputs)}concat=n={len(keep_intervals)}:v=0:a=1[spliced]")

    post = []
    if noise_reduction:
        post.append("highpass=f=80,afftdn=nf=-25")
    if normalize_loudness:
        post.append("loudnorm=I=-16:TP=-1.5:LRA=11")
    if fade_in_seconds > 0:
        post.append(f"afade=t=in:st=0:d={fade_in_seconds:.2f}")

    if post:
        filter_parts.append(f"[spliced]{','.join(post)}[voiceclean]")
        voice_label = "[voiceclean]"
    else:
        voice_label = "[spliced]"

    cmd = [ffmpeg, "-y", "-i", input_path]
    if bgm_path and os.path.exists(bgm_path):
        cmd.extend(["-stream_loop", "-1", "-i", bgm_path])
        filter_parts.append(f"[1:a]volume={bgm_volume:.2f}[bgm]")
        filter_parts.append(f"{voice_label}[bgm]amix=inputs=2:duration=first:dropout_transition=2[outa]")
        map_label = "[outa]"
    else:
        map_label = voice_label

    cmd.extend(["-filter_complex", ";".join(filter_parts), "-map", map_label, "-c:a", "libmp3lame", "-b:a", "192k", output_path])
    subprocess.run(cmd, capture_output=True, check=True)

    new_duration = probe_duration(output_path)
    if fade_out_seconds > 0 and new_duration > fade_out_seconds + 0.2:
        faded_tmp = output_path + ".fade.mp3"
        st_fade = max(0.0, new_duration - fade_out_seconds)
        subprocess.run([ffmpeg, "-y", "-i", output_path, "-af", f"afade=t=out:st={st_fade:.2f}:d={fade_out_seconds:.2f}", faded_tmp], capture_output=True, check=True)
        os.replace(faded_tmp, output_path)

    return new_duration, max(0.0, orig_duration - new_duration), silences
