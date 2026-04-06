"""
core/video_composer.py — Merges animated scenes + audio into a single video
"""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

from utils.logger import setup_logger
from core.scene_generator import Scene

logger = setup_logger("VideoComposer")


class VideoComposer:
    def __init__(self, output_dir: Path, fps: int, width: int, height: int):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.fps = fps
        self.width = width
        self.height = height
        self.ffmpeg = shutil.which("ffmpeg") or "ffmpeg"

    # ------------------------------------------------------------------
    def compose(self, scenes: List[Scene]) -> Path:
        """Combine all scenes into a single video with audio."""
        logger.info(f"Composing {len(scenes)} scene(s)…")

        scene_clips = []
        for scene in scenes:
            clip = self._prepare_scene_clip(scene)
            if clip:
                scene_clips.append(clip)

        if not scene_clips:
            raise RuntimeError("No scene clips to compose")

        # Concatenate all clips
        out_path = self.output_dir / "composed_raw.mp4"
        self._concatenate(scene_clips, out_path)
        logger.info(f"✅ Composed → {out_path.name}")
        return out_path

    # ------------------------------------------------------------------
    def _prepare_scene_clip(self, scene: Scene) -> Optional[Path]:
        """
        Creates a video clip for one scene: video track + audio track,
        padded/trimmed to scene.duration_sec.
        """
        out_path = self.output_dir / f"clip_{scene.index:02d}.mp4"

        if out_path.exists():
            return out_path

        video_src = scene.video_path
        audio_src = scene.audio_path
        duration  = scene.duration_sec

        if not video_src or not Path(video_src).exists():
            logger.warning(f"  Scene {scene.index}: no video file, creating from images")
            video_src = self._images_to_video(scene)

        if not video_src:
            logger.error(f"  Scene {scene.index}: cannot create clip, skipping")
            return None

        cmd = [self.ffmpeg, "-y"]

        # Input: video (looped/trimmed to duration)
        cmd += ["-stream_loop", "-1",
                "-t", str(duration),
                "-i", str(video_src)]

        # Input: audio (if exists)
        if audio_src and Path(audio_src).exists():
            cmd += ["-i", str(audio_src)]
            cmd += ["-map", "0:v:0", "-map", "1:a:0"]
            cmd += ["-shortest"]
        else:
            # Silent audio
            cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
            cmd += ["-map", "0:v:0", "-map", "1:a:0"]
            cmd += ["-t", str(duration)]

        # Scale to target resolution
        cmd += [
            "-vf", f"scale={self.width}:{self.height}:force_original_aspect_ratio=decrease,"
                   f"pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2,setsar=1",
            "-r", str(self.fps),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            "-crf", "20",
            str(out_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"  FFmpeg clip error: {result.stderr[-300:]}")
            return None

        logger.info(f"  ✅ Clip {scene.index} → {out_path.name} ({duration:.1f}s)")
        return out_path

    # ------------------------------------------------------------------
    def _images_to_video(self, scene: Scene) -> Optional[str]:
        if not scene.image_paths:
            return None

        tmp_dir = self.output_dir / f"img_video_{scene.index}"
        tmp_dir.mkdir(exist_ok=True)

        # Copy images with sequential names
        for i, img_path in enumerate(scene.image_paths):
            dst = tmp_dir / f"frame_{i:05d}.png"
            shutil.copy(img_path, dst)

        out_video = self.output_dir / f"img_video_{scene.index}.mp4"
        cmd = [
            self.ffmpeg, "-y",
            "-framerate", str(max(1, len(scene.image_paths) // 4)),
            "-i", str(tmp_dir / "frame_%05d.png"),
            "-vf", f"scale={self.width}:{self.height}",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-t", str(scene.duration_sec),
            str(out_video),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        shutil.rmtree(tmp_dir, ignore_errors=True)

        if result.returncode == 0:
            return str(out_video)
        return None

    # ------------------------------------------------------------------
    def _concatenate(self, clips: List[Path], out_path: Path):
        """Use FFmpeg concat demuxer to join clips seamlessly."""
        list_file = self.output_dir / "concat_list.txt"
        with open(list_file, "w") as f:
            for clip in clips:
                f.write(f"file '{clip.resolve()}'\n")

        cmd = [
            self.ffmpeg, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(out_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            # Fallback: re-encode on concat
            logger.warning("Copy concat failed, re-encoding…")
            cmd[-3:-1] = ["-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg concat failed: {result.stderr[-400:]}")
