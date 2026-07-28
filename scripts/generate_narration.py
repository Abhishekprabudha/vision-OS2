#!/usr/bin/env python3
"""Generate narration with Microsoft Edge neural TTS or an offline eSpeak fallback."""
from __future__ import annotations

import argparse
import asyncio
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT = ROOT / "assets" / "audio" / "narration.txt"


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


async def edge_tts_generate(text: str, output: Path, voice: str, rate: str) -> None:
    try:
        import edge_tts
    except ImportError as exc:
        raise SystemExit("edge-tts is not installed. Run: pip install -r requirements.txt") from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    communicator = edge_tts.Communicate(text, voice, rate=rate)
    await communicator.save(str(output))
    if not output.exists() or output.stat().st_size == 0:
        raise RuntimeError("Edge TTS did not create a non-empty narration file")


def espeak_generate(text_path: Path, output: Path, speed: int) -> None:
    if shutil.which("espeak") is None:
        raise SystemExit("eSpeak is not installed; use --engine edge instead.")
    wav = output.with_suffix(".wav")
    wav.parent.mkdir(parents=True, exist_ok=True)
    run([
        "espeak", "-v", "en-us+f3", "-s", str(speed), "-p", "43", "-a", "150",
        "-w", str(wav), "-f", str(text_path),
    ])
    if output.suffix.lower() == ".wav":
        if output != wav:
            wav.replace(output)
        return
    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg is required to convert the eSpeak WAV to MP3.")
    run([
        "ffmpeg", "-y", "-i", str(wav),
        "-af", "highpass=f=85,lowpass=f=11000,acompressor=threshold=-18dB:ratio=2.5:attack=10:release=180,loudnorm=I=-16:TP=-1.5:LRA=8",
        "-c:a", "libmp3lame", "-b:a", "128k", str(output),
    ])
    wav.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", choices=("edge", "espeak"), default="edge")
    parser.add_argument("--voice", default="en-GB-RyanNeural")
    parser.add_argument("--rate", default="+2%")
    parser.add_argument("--speed", type=int, default=190, help="eSpeak words per minute")
    parser.add_argument("--output", type=Path, default=ROOT / "assets" / "audio" / "narration.mp3")
    args = parser.parse_args()

    text = TEXT.read_text(encoding="utf-8").strip()
    if not text:
        raise SystemExit(f"Narration text is empty: {TEXT}")

    if args.engine == "edge":
        asyncio.run(edge_tts_generate(text, args.output, args.voice, args.rate))
    else:
        espeak_generate(TEXT, args.output, args.speed)
    print(f"Narration written to {args.output}")


if __name__ == "__main__":
    main()
