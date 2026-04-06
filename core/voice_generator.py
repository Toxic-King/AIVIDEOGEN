"""
core/voice_generator.py — Generates narration using Microsoft Edge TTS
"""

import asyncio
import os
from pathlib import Path
from typing import List

from utils.logger import setup_logger
from core.scene_generator import Scene

logger = setup_logger("VoiceGenerator")

# Emotion → voice style mapping (Edge TTS SSML styles)
MOOD_VOICE_STYLE = {
    "happy":    "cheerful",
    "sad":      "sad",
    "epic":     "excited",
    "calm":     "calm",
    "tense":    "fearful",
    "romantic": "gentle",
    "neutral":  "general",
}

# Pace → rate mapping
PACE_RATE = {
    "slow":   "-10%",
    "medium": "+0%",
    "fast":   "+15%",
}


class VoiceGenerator:
    def __init__(self, output_dir: Path, voice: str = "en-US-AriaNeural"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.voice = voice

    # ------------------------------------------------------------------
    def generate_all(self, scenes: List[Scene]) -> List[Scene]:
        for scene in scenes:
            logger.info(f"  Generating voice for scene {scene.index}…")
            scene.audio_path = self._generate(scene)
            if scene.audio_path:
                scene.audio_duration = self._get_duration(scene.audio_path)
        return scenes

    # ------------------------------------------------------------------
    def _generate(self, scene: Scene) -> str:
        out_path = self.output_dir / f"scene_{scene.index:02d}.mp3"

        if out_path.exists():
            logger.debug(f"  Audio cached: {out_path.name}")
            return str(out_path)

        text = scene.narration_text or scene.raw_description
        if not text:
            return ""

        try:
            asyncio.run(self._tts_async(text, scene.mood, str(out_path)))
            logger.info(f"  ✅ Audio → {out_path.name}")
            return str(out_path)
        except ImportError:
            logger.error("edge-tts not installed. Run: pip install edge-tts")
            return self._silent_audio(str(out_path), 4.0)
        except Exception as e:
            logger.error(f"  TTS failed for scene {scene.index}: {e}")
            return self._silent_audio(str(out_path), 4.0)

    async def _tts_async(self, text: str, mood: str, out_path: str):
        import edge_tts

        style = MOOD_VOICE_STYLE.get(mood, "general")
        rate  = "+0%"  # default

        # Build SSML for emotion + pacing
        ssml = self._build_ssml(text, style, rate)

        communicate = edge_tts.Communicate(ssml, self.voice, rate=rate)
        await communicate.save(out_path)

    def _build_ssml(self, text: str, style: str, rate: str) -> str:
        # Simple text is fine; Edge TTS handles it
        return text

    # ------------------------------------------------------------------
    def _get_duration(self, audio_path: str) -> float:
        try:
            import subprocess
            import json
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json",
                 "-show_format", audio_path],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return float(data["format"]["duration"])
        except Exception:
            pass

        # Fallback: estimate by text length
        words = len(audio_path.split())
        return max(2.0, words * 0.4)

    def _silent_audio(self, out_path: str, duration: float) -> str:
        """Generate a silent audio file as placeholder."""
        import subprocess
        import shutil
        ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
        cmd = [
            ffmpeg, "-y",
            "-f", "lavfi",
            "-i", f"anullsrc=r=44100:cl=stereo",
            "-t", str(duration),
            "-acodec", "mp3",
            out_path,
        ]
        subprocess.run(cmd, capture_output=True)
        return out_path
