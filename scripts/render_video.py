#!/usr/bin/env python3
"""Render the cross-industry AI Native Vision Agents film with FFmpeg."""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "scenes.json"
BUILD = ROOT / ".render"
DIST = ROOT / "dist"
WIDTH, HEIGHT, FPS = 1280, 720, 24


def run(cmd: list[str]) -> None:
    print("+", " ".join(str(c) for c in cmd))
    subprocess.run(cmd, check=True)


def probe_duration(path: Path) -> float:
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ], text=True).strip()
    return float(out)


def font_path(bold: bool = False) -> str:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    raise SystemExit("A DejaVu or Liberation Sans font is required.")


def hex_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))


def wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textbbox((0, 0), trial, font=font)[2] <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def create_overlay(scene: dict[str, Any], index: int, count: int, output: Path) -> None:
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")
    accent = hex_rgb(scene.get("accent", "#6EE7F7"))

    # Cinematic top vignette and lower-third panel.
    draw.rectangle((0, 0, WIDTH, 86), fill=(4, 10, 24, 120))
    draw.rectangle((0, 485, WIDTH, HEIGHT), fill=(4, 10, 24, 205))
    draw.rectangle((0, 485, 8, HEIGHT), fill=(*accent, 255))
    draw.line((0, 86, WIDTH, 86), fill=(*accent, 80), width=1)

    small_bold = ImageFont.truetype(font_path(True), 22)
    tiny = ImageFont.truetype(font_path(False), 17)
    title_font = ImageFont.truetype(font_path(True), 42)
    sub_font = ImageFont.truetype(font_path(False), 22)

    badge = scene["industry"].upper()
    badge_w = draw.textbbox((0, 0), badge, font=small_bold)[2] + 36
    draw.rounded_rectangle((34, 24, 34 + badge_w, 65), radius=12, fill=(*accent, 42), outline=(*accent, 170), width=1)
    draw.text((52, 33), badge, font=small_bold, fill=(235, 248, 255, 255))

    live = "VISION AGENT  ·  LIVE"
    live_w = draw.textbbox((0, 0), live, font=tiny)[2]
    draw.ellipse((WIDTH - live_w - 79, 35, WIDTH - live_w - 67, 47), fill=(*accent, 255))
    draw.text((WIDTH - live_w - 57, 30), live, font=tiny, fill=(220, 235, 245, 230))

    title_lines = wrap(draw, scene["title"], title_font, 1010)
    y = 516
    for line in title_lines[:2]:
        draw.text((46, y), line, font=title_font, fill=(250, 252, 255, 255))
        y += 50
    sub_lines = wrap(draw, scene["subtitle"], sub_font, 1040)
    for line in sub_lines[:2]:
        draw.text((48, y + 5), line, font=sub_font, fill=(194, 211, 224, 245))
        y += 30

    # Scene progress and agent-state detail.
    progress_x0, progress_y = 1010, 675
    progress_w = 220
    draw.rounded_rectangle((progress_x0, progress_y, progress_x0 + progress_w, progress_y + 7), radius=3, fill=(255, 255, 255, 40))
    fill_w = int(progress_w * (index + 1) / count)
    draw.rounded_rectangle((progress_x0, progress_y, progress_x0 + fill_w, progress_y + 7), radius=3, fill=(*accent, 225))
    draw.text((46, 676), f"AIonOS  ·  AI NATIVE VISION AGENTS  ·  {index + 1:02d}/{count:02d}", font=tiny, fill=(160, 185, 203, 220))

    for box in scene.get("boxes", []):
        x, yb, w, h = box["x"], box["y"], box["w"], box["h"]
        # Corner-style detection box.
        corner = min(36, w // 4, h // 4)
        for x1, y1, x2, y2 in [
            (x, yb, x + corner, yb), (x, yb, x, yb + corner),
            (x + w, yb, x + w - corner, yb), (x + w, yb, x + w, yb + corner),
            (x, yb + h, x + corner, yb + h), (x, yb + h, x, yb + h - corner),
            (x + w, yb + h, x + w - corner, yb + h), (x + w, yb + h, x + w, yb + h - corner),
        ]:
            draw.line((x1, y1, x2, y2), fill=(*accent, 235), width=4)
        label = box.get("label", "DETECTED")
        label_w = draw.textbbox((0, 0), label, font=tiny)[2] + 24
        label_y = max(94, yb - 31)
        draw.rounded_rectangle((x, label_y, x + label_w, label_y + 27), radius=5, fill=(4, 10, 24, 205), outline=(*accent, 200), width=1)
        draw.text((x + 12, label_y + 4), label, font=tiny, fill=(236, 249, 255, 255))

    img.save(output)


def render_scene(scene: dict[str, Any], duration: float, overlay: Path, output: Path) -> None:
    source = ROOT / scene["source"]
    if not source.exists():
        raise SystemExit(f"Missing source video: {source}")
    start = float(scene.get("start", 0))
    vf = (
        f"[0:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},fps={FPS},setsar=1,"
        "eq=contrast=1.06:saturation=1.08:brightness=-0.015,"
        f"fade=t=in:st=0:d=0.18,fade=t=out:st={max(0.0, duration-0.18):.3f}:d=0.18,"
        "drawbox=x=0:y='mod(t*135,720)':w=1280:h=2:color=0x6EE7F7@0.10:t=fill[base];"
        "[base][1:v]overlay=0:0:shortest=1,format=yuv420p[out]"
    )
    run([
        "ffmpeg", "-y", "-stream_loop", "-1", "-ss", f"{start:.3f}", "-i", str(source),
        "-loop", "1", "-i", str(overlay), "-t", f"{duration:.3f}",
        "-filter_complex", vf, "-map", "[out]", "-an", "-r", str(FPS),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-pix_fmt", "yuv420p", str(output),
    ])


def create_srt(scenes: list[dict[str, Any]], durations: list[float], overlap: float, output: Path) -> list[dict[str, Any]]:
    def ts(seconds: float) -> str:
        ms = int(round(seconds * 1000))
        h, ms = divmod(ms, 3_600_000)
        m, ms = divmod(ms, 60_000)
        s, ms = divmod(ms, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    timeline = []
    start = 0.0
    lines = []
    for i, (scene, duration) in enumerate(zip(scenes, durations, strict=True), 1):
        end = start + duration
        timeline.append({
            "id": scene["id"], "industry": scene["industry"], "title": scene["title"],
            "start": round(start, 3), "end": round(end, 3),
        })
        lines.extend([str(i), f"{ts(start + 0.3)} --> {ts(max(start + 0.8, end - 0.3))}", scene["narration"], ""])
        start = end - overlap
    output.write_text("\n".join(lines), encoding="utf-8")
    return timeline


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--narration", type=Path, default=ROOT / "assets" / "audio" / "narration.mp3")
    parser.add_argument("--output", type=Path, default=DIST / "ai-native-vision-agents.mp4")
    parser.add_argument("--keep-build", action="store_true")
    args = parser.parse_args()

    for binary in ("ffmpeg", "ffprobe"):
        if shutil.which(binary) is None:
            raise SystemExit(f"{binary} is required")
    if not args.narration.exists():
        raise SystemExit(f"Narration file missing: {args.narration}")

    config = json.loads(DATA.read_text(encoding="utf-8"))
    scenes = config["scenes"]
    overlap = 0.0  # scene-level cinematic fades are used for robust browser/GitHub rendering
    max_duration = float(config["meta"].get("maximumDurationSeconds", 177))
    base_sum = sum(float(s["durationHint"]) for s in scenes)
    base_total = base_sum
    narration_duration = probe_duration(args.narration)
    target_total = max(base_total, narration_duration + 3.0)
    if target_total > max_duration:
        raise SystemExit(
            f"Narration is too long ({narration_duration:.1f}s). The final video would exceed "
            f"the {max_duration:.0f}s limit. Shorten assets/audio/narration.txt or increase TTS rate."
        )
    scale = target_total / base_sum
    durations = [float(s["durationHint"]) * scale for s in scenes]

    if BUILD.exists():
        shutil.rmtree(BUILD)
    (BUILD / "overlays").mkdir(parents=True)
    (BUILD / "scenes").mkdir(parents=True)
    DIST.mkdir(parents=True, exist_ok=True)

    scene_files: list[Path] = []
    for i, (scene, duration) in enumerate(zip(scenes, durations, strict=True)):
        overlay = BUILD / "overlays" / f"{scene['id']}.png"
        clip = BUILD / "scenes" / f"{scene['id']}.mp4"
        create_overlay(scene, i, len(scenes), overlay)
        render_scene(scene, duration, overlay, clip)
        scene_files.append(clip)

    # Join uniformly encoded scene clips through MPEG-TS. This avoids concat-filter
    # stalls seen on some GitHub runners when many MP4 inputs change timestamps.
    running = sum(durations)
    ts_dir = BUILD / "ts"
    ts_dir.mkdir(parents=True, exist_ok=True)
    ts_files: list[Path] = []
    for clip in scene_files:
        ts_clip = ts_dir / f"{clip.stem}.ts"
        run([
            "ffmpeg", "-y", "-i", str(clip), "-map", "0:v:0", "-an",
            "-c:v", "copy", "-bsf:v", "h264_mp4toannexb", "-f", "mpegts", str(ts_clip),
        ])
        ts_files.append(ts_clip)

    joined_ts = BUILD / "joined.ts"
    with joined_ts.open("wb") as joined:
        for ts_clip in ts_files:
            joined.write(ts_clip.read_bytes())

    visual = BUILD / "visual.mp4"
    vf = (
        f"fps={FPS},setsar=1,format=yuv420p,"
        "setparams=range=tv:color_primaries=bt709:color_trc=bt709:colorspace=bt709,"
        "fade=t=in:st=0:d=0.8,"
        f"fade=t=out:st={max(0.0, running-1.2):.3f}:d=1.2"
    )
    run([
        "ffmpeg", "-y", "-fflags", "+genpts", "-i", str(joined_ts), "-an",
        "-vf", vf, "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast",
        "-b:v", "900k", "-maxrate", "1200k", "-bufsize", "2400k",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(visual),
    ])

    timeline = create_srt(scenes, durations, overlap, DIST / "captions.srt")
    run(["ffmpeg", "-y", "-i", str(DIST / "captions.srt"), str(DIST / "captions.vtt")])
    (DIST / "timeline.json").write_text(json.dumps({"duration": round(running, 3), "scenes": timeline}, indent=2), encoding="utf-8")

    # Reuse low-volume source sound as an unobtrusive bed beneath narration.
    bed_source = ROOT / "assets" / "video" / "plane-landing.mp4"
    audio = BUILD / "mix.m4a"
    audio_filter = (
        f"[0:a]volume=0.055,atrim=0:{running:.3f},afade=t=in:st=0:d=2,"
        f"afade=t=out:st={max(0.0, running-3):.3f}:d=3[bed];"
        f"[1:a]volume=1.0,apad=pad_dur={running:.3f}[voice];"
        "[bed][voice]amix=inputs=2:duration=first:dropout_transition=2,loudnorm=I=-15:TP=-1.5:LRA=9[a]"
    )
    run([
        "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(bed_source), "-i", str(args.narration),
        "-filter_complex", audio_filter, "-map", "[a]", "-t", f"{running:.3f}",
        "-c:a", "aac", "-b:a", "96k", str(audio),
    ])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    run([
        "ffmpeg", "-y", "-i", str(visual), "-i", str(audio),
        "-map", "0:v:0", "-map", "1:a:0", "-c", "copy", "-t", f"{running:.3f}",
        "-movflags", "+faststart", str(args.output),
    ])
    run([
        "ffmpeg", "-y", "-ss", "1.5", "-i", str(args.output), "-frames:v", "1",
        "-vf", "scale=1280:-2", "-q:v", "2", str(DIST / "poster.jpg"),
    ])

    size_mb = args.output.stat().st_size / (1024 * 1024)
    print(f"Rendered {args.output} · {running:.1f}s · {size_mb:.1f} MB")
    if size_mb >= 25:
        print("WARNING: final MP4 is 25 MB or larger; lower the video bitrate for GitHub web upload.")
    if not args.keep_build:
        shutil.rmtree(BUILD, ignore_errors=True)


if __name__ == "__main__":
    main()
