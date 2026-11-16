import os
import subprocess
from typing import Dict, List, Optional, Tuple
from app.core.config import get_settings

RESOLUTION_MAP: Dict[Tuple[str, str], Tuple[int, int]] = {
    ("16:9", "720p"): (1280, 720), ("16:9", "1080p"): (1920, 1080), ("16:9", "4k"): (3840, 2160),
    ("9:16", "720p"): (720, 1280), ("9:16", "1080p"): (1080, 1920), ("9:16", "4k"): (2160, 3840),
    ("1:1", "720p"): (720, 720), ("1:1", "1080p"): (1080, 1080), ("1:1", "4k"): (2160, 2160),
}


def render_image_to_2d_animated_clip(
    image_path: str, output_mp4: str, duration_seconds: float, width: int, height: int, fps: int = 30, camera_movement: str = "slow_zoom_in",
) -> None:
    ffmpeg = get_settings().FFMPEG_BINARY_PATH
    total_frames = max(1, int(duration_seconds * fps))
    if camera_movement == "pan_left":
        zp = f"zoompan=z='1.12':x='iw*0.12*(1-on/{total_frames})':y='ih/2-(ih/zoom/2)':d={total_frames}:s={width}x{height}:fps={fps}"
    elif camera_movement == "pan_right":
        zp = f"zoompan=z='1.12':x='iw*0.12*(on/{total_frames})':y='ih/2-(ih/zoom/2)':d={total_frames}:s={width}x{height}:fps={fps}"
    else:
        zp = f"zoompan=z='min(zoom+0.0012,1.20)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={width}x{height}:fps={fps}"

    subprocess.run([
        ffmpeg, "-y", "-loop", "1", "-i", image_path,
        "-vf", f"scale={width*2}:{height*2}:force_original_aspect_ratio=increase,crop={width*2}:{height*2},{zp},format=yuv420p",
        "-t", f"{duration_seconds:.2f}", "-c:v", "libx264", "-preset", "medium", "-crf", "20", output_mp4,
    ], capture_output=True, check=True)


def assemble_final_video(
    video_clips: List[str], audio_path: Optional[str], srt_path: Optional[str], output_mp4: str,
    aspect_ratio: str = "16:9", resolution: str = "1080p", fps: int = 30, watermark_text: Optional[str] = None,
) -> None:
    if not video_clips:
        raise ValueError("At least one video clip is required for rendering.")
    ffmpeg = get_settings().FFMPEG_BINARY_PATH
    width, height = RESOLUTION_MAP.get((aspect_ratio, resolution), (1920, 1080))
    concat_file = output_mp4 + ".concat.txt"

    normalized_clips = []
    for idx, clip in enumerate(video_clips):
        norm_path = f"{output_mp4}.norm_{idx}.mp4"
        subprocess.run([
            ffmpeg, "-y", "-i", clip,
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps={fps},format=yuv420p",
            "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "20", norm_path,
        ], capture_output=True, check=True)
        normalized_clips.append(norm_path)

    with open(concat_file, "w", encoding="utf-8") as f:
        for nc in normalized_clips:
            f.write(f"file '{os.path.abspath(nc)}'\n")

    cmd = [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", concat_file]
    if audio_path and os.path.exists(audio_path):
        cmd.extend(["-i", audio_path])

    vf_chain = []
    if srt_path and os.path.exists(srt_path):
        escaped = srt_path.replace("\\", "/").replace(":", "\\:")
        vf_chain.append(f"subtitles='{escaped}':force_style='FontName=Arial,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2'")
    if watermark_text:
        safe_wm = watermark_text.replace("'", "")
        vf_chain.append(f"drawtext=text='{safe_wm}':fontcolor=white@0.45:fontsize=24:x=w-tw-24:y=24")
    if vf_chain:
        cmd.extend(["-vf", ",".join(vf_chain)])
    if audio_path and os.path.exists(audio_path):
        cmd.extend(["-map", "0:v:0", "-map", "1:a:0", "-c:a", "aac", "-b:a", "192k", "-shortest"])

    cmd.extend(["-c:v", "libx264", "-preset", "medium", "-crf", "19", "-movflags", "+faststart", output_mp4])
    subprocess.run(cmd, capture_output=True, check=True)
