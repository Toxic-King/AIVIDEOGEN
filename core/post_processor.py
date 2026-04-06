"""
core/post_processor.py — Applies color grading, transitions, sharpening
"""

import shutil
import subprocess
from pathlib import Path

from utils.logger import setup_logger

logger = setup_logger("PostProcessor")

# FFmpeg filter chains per quality level
QUALITY_FILTERS = {
    "low": (
        "unsharp=3:3:0.5:3:3:0.0"
    ),
    "medium": (
        "unsharp=5:5:0.8:5:5:0.0,"
        "eq=contrast=1.05:brightness=0.02:saturation=1.1"
    ),
    "high": (
        "unsharp=7:7:1.0:7:7:0.0,"
        "eq=contrast=1.1:brightness=0.03:saturation=1.15,"
        "hqdn3d=1.5:1.5:6:6"
    ),
}

# Subtle cinematic color grade (film look)
CINEMATIC_GRADE = (
    "curves=r='0/0 0.2/0.18 0.8/0.82 1/1':"
    "g='0/0 0.2/0.19 0.8/0.81 1/1':"
    "b='0/0.02 0.2/0.21 0.8/0.79 1/0.98'"
)

FADE_DURATION = 0.5   # seconds for fade-in at start


class PostProcessor:
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.ffmpeg = shutil.which("ffmpeg") or "ffmpeg"

    # ------------------------------------------------------------------
    def process(self, raw_video: Path, quality: str) -> Path:
        final_path = self.output_dir / "final_video.mp4"
        logger.info(f"Post-processing: quality={quality}")

        sharpen = QUALITY_FILTERS.get(quality, QUALITY_FILTERS["medium"])
        vf = f"fade=t=in:st=0:d={FADE_DURATION},{sharpen},{CINEMATIC_GRADE}"

        cmd = [
            self.ffmpeg, "-y",
            "-i", str(raw_video),
            "-vf", vf,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-crf", "18",
            "-movflags", "+faststart",
            str(final_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Post-process failed: {result.stderr[-300:]}")
            # Fallback: just copy
            shutil.copy(raw_video, final_path)
            logger.info("  Copied raw video as fallback")
        else:
            logger.info(f"✅ Post-processed → {final_path.name}")

        self._print_video_info(final_path)
        return final_path

    # ------------------------------------------------------------------
    def _print_video_info(self, path: Path):
        try:
            import json
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json",
                 "-show_streams", "-show_format", str(path)],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                fmt = data.get("format", {})
                duration = float(fmt.get("duration", 0))
                size_mb = int(fmt.get("size", 0)) / 1024 / 1024
                logger.info(
                    f"  📊 Duration: {duration:.1f}s | Size: {size_mb:.1f} MB"
                )
        except Exception:
            pass
