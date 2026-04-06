"""
core/pipeline.py — Master pipeline orchestrating all stages
"""

import time
from pathlib import Path

from utils.logger import setup_logger
from core.prompt_analyzer import PromptAnalyzer
from core.scene_generator import SceneGenerator
from core.prompt_enhancer import PromptEnhancer
from core.image_generator import ImageGenerator
from core.animation_engine import AnimationEngine
from core.voice_generator import VoiceGenerator
from core.audio_sync import AudioSyncEngine
from core.video_composer import VideoComposer
from core.post_processor import PostProcessor

logger = setup_logger("Pipeline")


class VideoPipeline:
    """
    End-to-end pipeline:
      text → scenes → images → animation → voice → sync → video
    """

    def __init__(self, text, voice, fps, quality, resolution,
                 duration, output_dir, use_animation=True):
        self.text = text
        self.voice = voice
        self.fps = fps
        self.quality = quality
        self.resolution = resolution
        self.duration = duration
        self.output_dir = Path(output_dir)
        self.use_animation = use_animation

        # Quality presets
        self.quality_cfg = {
            "low":    {"steps": 15, "frames_per_scene": 8,  "guidance": 6.0},
            "medium": {"steps": 25, "frames_per_scene": 16, "guidance": 7.5},
            "high":   {"steps": 40, "frames_per_scene": 24, "guidance": 8.0},
        }[quality]

        # Resolution map
        self.res_map = {"720p": (1280, 720), "1080p": (1920, 1080)}
        self.width, self.height = self.res_map[resolution]

    # ------------------------------------------------------------------
    def run(self) -> Path:
        logger.info("🚀 Pipeline started")
        t0 = time.time()

        # ── Stage 1: Analyze prompt ──────────────────────────────────
        self._stage("1/9", "Analyzing prompt")
        analyzer = PromptAnalyzer()
        analysis = analyzer.analyze(self.text)
        logger.info(f"Analysis: {analysis}")

        # ── Stage 2: Generate scenes ─────────────────────────────────
        self._stage("2/9", "Generating scenes")
        scene_gen = SceneGenerator()
        scenes = scene_gen.generate(self.text, analysis)
        logger.info(f"Scenes: {len(scenes)}")

        # ── Stage 3: Enhance prompts ─────────────────────────────────
        self._stage("3/9", "Enhancing prompts cinematically")
        enhancer = PromptEnhancer()
        scenes = enhancer.enhance_all(scenes, analysis)

        # ── Stage 4: Generate images ─────────────────────────────────
        self._stage("4/9", "Generating AI images")
        img_gen = ImageGenerator(
            output_dir=self.output_dir / "frames",
            steps=self.quality_cfg["steps"],
            guidance=self.quality_cfg["guidance"],
            width=self.width,
            height=self.height,
        )
        scenes = img_gen.generate_all(scenes, self.quality_cfg["frames_per_scene"])

        # ── Stage 5: Animate frames ──────────────────────────────────
        if self.use_animation:
            self._stage("5/9", "Animating scenes")
            anim = AnimationEngine(output_dir=self.output_dir / "animated", fps=self.fps)
            scenes = anim.animate_all(scenes)
        else:
            logger.info("⏭  Animation skipped (--no-animation)")

        # ── Stage 6: Generate voice ──────────────────────────────────
        self._stage("6/9", "Generating voice narration")
        voice_gen = VoiceGenerator(
            output_dir=self.output_dir / "audio",
            voice=self.voice,
        )
        scenes = voice_gen.generate_all(scenes)

        # ── Stage 7: Sync audio ──────────────────────────────────────
        self._stage("7/9", "Syncing audio with scenes")
        sync = AudioSyncEngine(fps=self.fps)
        scenes = sync.sync(scenes)

        # ── Stage 8: Compose video ───────────────────────────────────
        self._stage("8/9", "Composing final video")
        composer = VideoComposer(
            output_dir=self.output_dir / "composed",
            fps=self.fps,
            width=self.width,
            height=self.height,
        )
        raw_video = composer.compose(scenes)

        # ── Stage 9: Post-process ────────────────────────────────────
        self._stage("9/9", "Post-processing & polishing")
        pp = PostProcessor(output_dir=self.output_dir)
        final_video = pp.process(raw_video, self.quality)

        elapsed = time.time() - t0
        logger.info(f"✅ Pipeline complete in {elapsed:.1f}s → {final_video}")
        return final_video

    # ------------------------------------------------------------------
    def _stage(self, num, label):
        bar = "─" * 40
        print(f"\n{bar}")
        print(f"  Stage {num}  ▶  {label}")
        print(bar)
        logger.info(f"[Stage {num}] {label}")
