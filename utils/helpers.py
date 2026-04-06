"""utils/helpers.py — Shared utility functions"""

import os
import shutil
import subprocess
from pathlib import Path


def check_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def get_video_duration(path: str) -> float:
    try:
        import json
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", path],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return float(json.loads(result.stdout)["format"]["duration"])
    except Exception:
        pass
    return 0.0


def ensure_dir(path: Path) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def clean_output_dir(output_dir: Path):
    """Remove intermediate files, keep only final video."""
    keep = {"final_video.mp4"}
    for item in output_dir.iterdir():
        if item.name not in keep and item.is_dir():
            shutil.rmtree(item, ignore_errors=True)


def estimate_generation_time(n_scenes: int, quality: str, use_animation: bool) -> str:
    base = {"low": 30, "medium": 90, "high": 180}[quality]
    total = base * n_scenes
    if use_animation:
        total *= 1.5
    mins = total // 60
    secs = total % 60
    if mins > 0:
        return f"~{mins}m {secs}s"
    return f"~{secs}s"
