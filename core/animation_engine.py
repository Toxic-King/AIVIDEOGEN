"""
core/animation_engine.py — Animates frames using AnimateDiff or frame interpolation
"""

import os
from pathlib import Path
from typing import List

from utils.logger import setup_logger
from core.scene_generator import Scene

logger = setup_logger("AnimationEngine")


class AnimationEngine:
    def __init__(self, output_dir: Path, fps: int = 24):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.fps = fps
        self._animatediff_available = None

    # ------------------------------------------------------------------
    def animate_all(self, scenes: List[Scene]) -> List[Scene]:
        for scene in scenes:
            if not scene.image_paths:
                logger.warning(f"Scene {scene.index}: no images to animate")
                continue
            logger.info(f"  Animating scene {scene.index}…")
            scene.video_path = self._animate_scene(scene)
        return scenes

    # ------------------------------------------------------------------
    def _animate_scene(self, scene: Scene) -> str:
        out_path = self.output_dir / f"scene_{scene.index:02d}.mp4"

        if out_path.exists():
            logger.debug(f"  Scene {scene.index} animation cached")
            return str(out_path)

        # Try AnimateDiff first
        if self._try_animatediff(scene, out_path):
            return str(out_path)

        # Fallback: smooth interpolation
        logger.info(f"  Using frame-interpolation fallback for scene {scene.index}")
        self._interpolation_fallback(scene, out_path)
        return str(out_path)

    # ------------------------------------------------------------------
    def _try_animatediff(self, scene: Scene, out_path: Path) -> bool:
        if self._animatediff_available is False:
            return False
        try:
            import torch
            from diffusers import AnimateDiffPipeline, MotionAdapter, DDIMScheduler
            from diffusers.utils import export_to_video
            from PIL import Image

            if self._animatediff_available is None:
                logger.info("  Loading AnimateDiff…")

            adapter = MotionAdapter.from_pretrained(
                "guoyww/animatediff-motion-adapter-v1-5-2",
                torch_dtype=torch.float16,
            )

            if torch.backends.mps.is_available():
                device = "mps"
                dtype = torch.float16
            elif torch.cuda.is_available():
                device = "cuda"
                dtype = torch.float16
            else:
                device = "cpu"
                dtype = torch.float32

            pipe = AnimateDiffPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                motion_adapter=adapter,
                torch_dtype=dtype,
            )
            pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config,
                                                        beta_schedule="linear",
                                                        clip_sample=False,
                                                        timestep_spacing="linspace",
                                                        steps_offset=1)
            pipe = pipe.to(device)

            result = pipe(
                prompt=scene.enhanced_prompt,
                negative_prompt=scene.negative_prompt,
                num_frames=16,
                guidance_scale=7.5,
                num_inference_steps=20,
                generator=torch.Generator(device=device).manual_seed(42 + scene.index),
            )

            frames = result.frames[0]  # list of PIL Images
            export_to_video(frames, str(out_path), fps=self.fps)

            self._animatediff_available = True
            logger.info(f"  ✅ AnimateDiff video → {out_path.name}")
            return True

        except Exception as e:
            if self._animatediff_available is None:
                logger.warning(f"  AnimateDiff unavailable: {e}. Using fallback.")
            self._animatediff_available = False
            return False

    # ------------------------------------------------------------------
    def _interpolation_fallback(self, scene: Scene, out_path: Path):
        """
        Smooth zoom/pan effect on static images using FFmpeg.
        Each image gets subtle Ken Burns effect to simulate motion.
        """
        import subprocess
        import shutil
        from PIL import Image

        if not scene.image_paths:
            return

        tmp_dir = self.output_dir / f"tmp_scene_{scene.index:02d}"
        tmp_dir.mkdir(exist_ok=True)

        images = scene.image_paths
        total_frames = max(24, self.fps * 4)  # 4 seconds per scene minimum
        frames_per_image = total_frames // len(images)

        generated_frames = []

        for img_idx, img_path in enumerate(images):
            try:
                img = Image.open(img_path).convert("RGB")
                w, h = img.size

                for f in range(frames_per_image):
                    # Ken Burns: subtle zoom in
                    progress = f / max(frames_per_image - 1, 1)
                    scale = 1.0 + 0.05 * progress  # 0% → 5% zoom
                    new_w = int(w * scale)
                    new_h = int(h * scale)

                    # Center crop back to original size
                    resized = img.resize((new_w, new_h), Image.LANCZOS)
                    left = (new_w - w) // 2
                    top = (new_h - h) // 2
                    cropped = resized.crop((left, top, left + w, top + h))

                    frame_num = img_idx * frames_per_image + f
                    frame_path = tmp_dir / f"frame_{frame_num:05d}.png"
                    cropped.save(str(frame_path))
                    generated_frames.append(str(frame_path))

            except Exception as e:
                logger.warning(f"  Frame interpolation error: {e}")

        if not generated_frames:
            return

        # Use FFmpeg to assemble
        ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
        cmd = [
            ffmpeg, "-y",
            "-framerate", str(self.fps),
            "-i", str(tmp_dir / "frame_%05d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            "-crf", "23",
            str(out_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"  FFmpeg error: {result.stderr[:200]}")
        else:
            logger.info(f"  ✅ Interpolated video → {out_path.name}")

        # Cleanup tmp frames
        shutil.rmtree(tmp_dir, ignore_errors=True)
