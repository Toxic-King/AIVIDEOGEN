"""
core/audio_sync.py — Aligns scene durations with narration length
"""

from typing import List
from utils.logger import setup_logger
from core.scene_generator import Scene

logger = setup_logger("AudioSync")

MIN_SCENE_DURATION = 2.0   # seconds
MAX_SCENE_DURATION = 15.0  # seconds
DEFAULT_DURATION   = 4.0


class AudioSyncEngine:
    def __init__(self, fps: int = 24):
        self.fps = fps

    def sync(self, scenes: List[Scene]) -> List[Scene]:
        for scene in scenes:
            audio_dur = scene.audio_duration or self._estimate(scene)
            # Give video a bit of padding around narration
            scene.duration_sec = max(
                MIN_SCENE_DURATION,
                min(MAX_SCENE_DURATION, audio_dur + 0.5)
            )
            logger.info(
                f"  Scene {scene.index}: audio={audio_dur:.1f}s "
                f"→ video duration={scene.duration_sec:.1f}s"
            )
        return scenes

    def _estimate(self, scene: Scene) -> float:
        words = len(scene.narration_text.split())
        # Average speaking pace: ~130 words/minute → ~0.46s per word
        return max(DEFAULT_DURATION, words * 0.46)
