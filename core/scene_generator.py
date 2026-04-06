"""
core/scene_generator.py — Splits analyzed prompt into logical video scenes
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional
from utils.logger import setup_logger
from core.prompt_analyzer import PromptAnalysis

logger = setup_logger("SceneGenerator")


@dataclass
class Scene:
    index: int
    raw_description: str
    enhanced_prompt: str = ""
    negative_prompt: str = ""
    mood: str = "neutral"
    duration_sec: float = 4.0

    # Populated later by downstream stages
    image_paths: List[str] = field(default_factory=list)
    video_path: Optional[str] = None
    audio_path: Optional[str] = None
    narration_text: str = ""
    audio_duration: float = 0.0


# Transition words that imply a scene change
SCENE_SPLIT_PATTERNS = [
    r",\s*then\s+",
    r"\.\s+",
    r";\s*",
    r"\s+then\s+",
    r"\s+after\s+(that|which)\s+",
    r"\s+suddenly\s+",
    r"\s+meanwhile\s+",
    r"\s+later\s+",
    r"\s+finally\s+",
    r"\s+as\s+the\s+",
]


class SceneGenerator:
    MAX_SCENES = 6   # prevent extremely long videos

    def generate(self, text: str, analysis: PromptAnalysis) -> List[Scene]:
        parts = self._split_text(text)

        if len(parts) > self.MAX_SCENES:
            logger.warning(f"Truncating to {self.MAX_SCENES} scenes (got {len(parts)})")
            parts = parts[:self.MAX_SCENES]

        scenes = []
        for i, part in enumerate(parts):
            part = part.strip().strip(",").strip()
            if not part:
                continue

            scene = Scene(
                index=i,
                raw_description=part,
                mood=self._infer_scene_mood(part, analysis),
                narration_text=self._make_narration(part),
            )
            scenes.append(scene)
            logger.info(f"  Scene {i}: '{part[:60]}...' mood={scene.mood}")

        if not scenes:
            # Fallback: treat entire text as one scene
            scenes.append(Scene(index=0, raw_description=text,
                                mood=analysis.mood,
                                narration_text=self._make_narration(text)))

        logger.info(f"Generated {len(scenes)} scene(s)")
        return scenes

    # ------------------------------------------------------------------
    def _split_text(self, text: str) -> List[str]:
        pattern = "|".join(SCENE_SPLIT_PATTERNS)
        parts = re.split(pattern, text, flags=re.IGNORECASE)
        return [p.strip() for p in parts if p.strip()]

    def _infer_scene_mood(self, text: str, analysis: PromptAnalysis) -> str:
        lower = text.lower()
        mood_hints = {
            "happy":    ["smile", "laugh", "happy", "joy", "sunrise", "bright"],
            "sad":      ["rain", "cry", "sad", "dark", "lonely", "tears"],
            "epic":     ["battle", "fight", "hero", "storm", "thunder", "climax"],
            "calm":     ["calm", "peace", "quiet", "gentle", "soft"],
            "tense":    ["scary", "danger", "chase", "fear", "night", "shadow"],
            "romantic": ["love", "sunset", "together", "heart", "kiss"],
        }
        for mood, hints in mood_hints.items():
            if any(h in lower for h in hints):
                return mood
        return analysis.mood

    def _make_narration(self, text: str) -> str:
        """Create natural narration text from scene description."""
        text = text.strip()
        # Capitalize first letter, ensure ends with period
        text = text[0].upper() + text[1:] if text else text
        if not text.endswith((".", "!", "?")):
            text += "."
        return text
