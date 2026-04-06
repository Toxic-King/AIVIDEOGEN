"""
core/prompt_analyzer.py — Extracts structured metadata from raw user prompt
"""

import re
from dataclasses import dataclass, field
from typing import List
from utils.logger import setup_logger

logger = setup_logger("PromptAnalyzer")


@dataclass
class PromptAnalysis:
    subject: str = ""
    environment: str = ""
    mood: str = "neutral"
    actions: List[str] = field(default_factory=list)
    time_of_day: str = "day"
    weather: str = "clear"
    style: str = "cinematic"
    emotion: str = "neutral"
    pace: str = "medium"          # slow / medium / fast
    raw: str = ""


# Simple keyword maps (no external NLP dependency)
MOOD_KEYWORDS = {
    "happy":   ["happy", "joy", "smile", "laugh", "cheerful", "sunny", "bright", "celebrate"],
    "sad":     ["sad", "cry", "tears", "lonely", "dark", "gloomy", "rain", "sorrow"],
    "epic":    ["epic", "battle", "war", "hero", "dragon", "mountain", "thunder", "storm"],
    "calm":    ["calm", "peaceful", "quiet", "serene", "gentle", "soft", "relax"],
    "tense":   ["tense", "scary", "horror", "danger", "chase", "fear", "suspense"],
    "romantic":["love", "romance", "kiss", "heart", "sunset", "couple", "together"],
}

TIME_KEYWORDS = {
    "dawn":    ["dawn", "sunrise", "morning", "early"],
    "day":     ["day", "afternoon", "noon", "sunlight"],
    "dusk":    ["dusk", "sunset", "evening", "twilight"],
    "night":   ["night", "dark", "midnight", "stars", "moon"],
}

WEATHER_KEYWORDS = {
    "rain":    ["rain", "rainy", "storm", "drizzle", "wet"],
    "snow":    ["snow", "snowy", "blizzard", "winter", "frost"],
    "fog":     ["fog", "mist", "misty", "haze"],
    "sunny":   ["sunny", "sun", "clear sky", "bright"],
    "cloudy":  ["cloud", "overcast", "grey sky"],
}

ENVIRONMENT_KEYWORDS = {
    "forest":  ["forest", "jungle", "woods", "trees"],
    "ocean":   ["ocean", "sea", "beach", "waves", "shore"],
    "city":    ["city", "street", "urban", "building", "town"],
    "desert":  ["desert", "sand", "dune", "arid"],
    "mountain":["mountain", "cliff", "peak", "valley", "hill"],
    "space":   ["space", "galaxy", "stars", "cosmos", "universe"],
    "indoor":  ["room", "house", "office", "indoor", "inside"],
}

STYLE_KEYWORDS = {
    "anime":   ["anime", "manga", "cartoon", "animated"],
    "realistic":["realistic", "photo", "real", "photorealistic"],
    "fantasy": ["fantasy", "magical", "fairy", "mythical"],
    "sci-fi":  ["sci-fi", "futuristic", "robot", "cyber", "neon"],
    "cinematic":["cinematic", "movie", "film", "dramatic"],
}


class PromptAnalyzer:
    def analyze(self, text: str) -> PromptAnalysis:
        lower = text.lower()
        analysis = PromptAnalysis(raw=text)

        analysis.mood       = self._match(lower, MOOD_KEYWORDS, "neutral")
        analysis.time_of_day = self._match(lower, TIME_KEYWORDS, "day")
        analysis.weather    = self._match(lower, WEATHER_KEYWORDS, "clear")
        analysis.environment = self._match(lower, ENVIRONMENT_KEYWORDS, "outdoor")
        analysis.style      = self._match(lower, STYLE_KEYWORDS, "cinematic")
        analysis.subject    = self._extract_subject(text)
        analysis.actions    = self._extract_actions(text)
        analysis.emotion    = analysis.mood
        analysis.pace       = self._infer_pace(lower)

        logger.debug(f"Analysis result: {analysis}")
        return analysis

    # ------------------------------------------------------------------
    def _match(self, text: str, keyword_map: dict, default: str) -> str:
        scores = {}
        for label, keywords in keyword_map.items():
            scores[label] = sum(1 for kw in keywords if kw in text)
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else default

    def _extract_subject(self, text: str) -> str:
        # Grab first noun phrase heuristically (first few words)
        words = text.split()
        stop = {"a", "an", "the", "in", "on", "at", "is", "are", "with", "and"}
        subject_words = []
        for w in words[:6]:
            clean = re.sub(r"[^a-zA-Z]", "", w)
            if clean.lower() not in stop and clean:
                subject_words.append(clean)
            if len(subject_words) == 3:
                break
        return " ".join(subject_words) or "scene"

    def _extract_actions(self, text: str) -> List[str]:
        # Very simple: split on commas/then/and to find action phrases
        parts = re.split(r",\s*|\s+then\s+|\s+and\s+", text, flags=re.IGNORECASE)
        return [p.strip() for p in parts if p.strip()]

    def _infer_pace(self, text: str) -> str:
        if any(w in text for w in ["fast", "quick", "rush", "race", "chase", "rapid"]):
            return "fast"
        if any(w in text for w in ["slow", "gentle", "calm", "peaceful", "serene"]):
            return "slow"
        return "medium"
