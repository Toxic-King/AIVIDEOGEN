"""
core/prompt_enhancer.py — Converts simple descriptions to cinematic prompts
"""

from typing import List
from utils.logger import setup_logger
from core.scene_generator import Scene
from core.prompt_analyzer import PromptAnalysis

logger = setup_logger("PromptEnhancer")

# ── Cinematic style templates per mood ───────────────────────────────────
MOOD_STYLE = {
    "happy":    "warm golden lighting, vibrant colors, joyful atmosphere, 8k",
    "sad":      "desaturated colors, soft rain, moody shadows, emotional depth",
    "epic":     "dramatic lighting, high contrast, dust particles, awe-inspiring scale",
    "calm":     "soft diffused lighting, pastel tones, peaceful atmosphere, bokeh",
    "tense":    "harsh shadows, cold blue tones, high contrast, suspenseful mood",
    "romantic": "warm orange tones, soft bokeh, golden hour, dreamy atmosphere",
    "neutral":  "balanced lighting, natural colors, cinematic depth of field",
}

# ── Negative prompt base ─────────────────────────────────────────────────
BASE_NEGATIVE = (
    "ugly, blurry, low quality, watermark, text, deformed, distorted, "
    "bad anatomy, worst quality, jpeg artifacts, noise, grainy, overexposed"
)

# ── Camera directions ────────────────────────────────────────────────────
CAMERA_BY_PACE = {
    "slow":   "slow pan, smooth dolly shot,",
    "medium": "medium tracking shot,",
    "fast":   "dynamic handheld camera, quick cuts,",
}

QUALITY_SUFFIX = ", 4k ultra detailed, professional color grading, hyperrealistic"


class PromptEnhancer:
    def enhance_all(self, scenes: List[Scene], analysis: PromptAnalysis) -> List[Scene]:
        for scene in scenes:
            scene.enhanced_prompt = self._enhance(scene, analysis)
            scene.negative_prompt = BASE_NEGATIVE
            logger.debug(f"Scene {scene.index} prompt: {scene.enhanced_prompt[:80]}...")
        return scenes

    # ------------------------------------------------------------------
    def _enhance(self, scene: Scene, analysis: PromptAnalysis) -> str:
        base = scene.raw_description
        mood_style = MOOD_STYLE.get(scene.mood, MOOD_STYLE["neutral"])
        camera = CAMERA_BY_PACE.get(analysis.pace, "")
        env_hint = self._environment_hint(analysis.environment)
        time_hint = self._time_hint(analysis.time_of_day)
        weather_hint = self._weather_hint(analysis.weather)
        style_hint = self._style_hint(analysis.style)

        parts = [
            "cinematic shot of",
            base,
            env_hint,
            time_hint,
            weather_hint,
            camera,
            mood_style,
            style_hint,
            QUALITY_SUFFIX,
        ]

        # Filter empty and join
        prompt = ", ".join(p for p in parts if p.strip())
        # Clean up double commas
        import re
        prompt = re.sub(r",\s*,", ",", prompt)
        return prompt.strip(", ")

    def _environment_hint(self, env: str) -> str:
        hints = {
            "forest":   "lush forest background, towering trees",
            "ocean":    "vast ocean, crashing waves, sea horizon",
            "city":     "urban cityscape, glowing windows, bustling streets",
            "desert":   "endless desert dunes, shimmering heat haze",
            "mountain": "majestic mountain peaks, rugged terrain",
            "space":    "infinite cosmos, nebula, distant galaxies",
            "indoor":   "beautifully lit interior, architectural details",
        }
        return hints.get(env, "")

    def _time_hint(self, time: str) -> str:
        hints = {
            "dawn":  "magical dawn light, pastel sky",
            "day":   "natural daylight, clear sky",
            "dusk":  "stunning golden hour, orange sky",
            "night": "night time, moonlit, city lights",
        }
        return hints.get(time, "")

    def _weather_hint(self, weather: str) -> str:
        hints = {
            "rain":   "heavy rain, raindrops, wet ground reflections",
            "snow":   "falling snow, frosty breath, winter landscape",
            "fog":    "thick fog, misty atmosphere, ethereal light",
            "sunny":  "bright sunshine, lens flare, golden light",
            "cloudy": "overcast sky, dramatic clouds, diffused light",
        }
        return hints.get(weather, "")

    def _style_hint(self, style: str) -> str:
        hints = {
            "anime":     "anime style, studio ghibli inspired, detailed cel shading",
            "realistic": "photorealistic, DSLR quality, natural textures",
            "fantasy":   "fantasy art, magical particles, ethereal glow",
            "sci-fi":    "futuristic sci-fi, neon accents, chrome surfaces",
            "cinematic": "film grain, anamorphic lens flare, movie poster quality",
        }
        return hints.get(style, "cinematic film quality")
