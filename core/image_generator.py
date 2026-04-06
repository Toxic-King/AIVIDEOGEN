"""
core/image_generator.py — Generates images using HuggingFace Diffusers (MPS optimized)
"""

import os
import time
from pathlib import Path
from typing import List

from utils.logger import setup_logger
from core.scene_generator import Scene

logger = setup_logger("ImageGenerator")


class ImageGenerator:
    def __init__(self, output_dir: Path, steps: int, guidance: float,
                 width: int = 1280, height: int = 720):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.steps = steps
        self.guidance = guidance
        self.width = width
        self.height = height
        self._pipe = None

    # ------------------------------------------------------------------
    def _load_pipeline(self):
        if self._pipe is not None:
            return
        logger.info("Loading Stable Diffusion pipeline…")
        try:
            import torch
            from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler

            model_id = "runwayml/stable-diffusion-v1-5"

            # Detect best device
            if torch.backends.mps.is_available():
                device = "mps"
                dtype = torch.float16
                logger.info("🍎 Using Apple MPS (Metal GPU)")
            elif torch.cuda.is_available():
                device = "cuda"
                dtype = torch.float16
                logger.info("🟢 Using CUDA GPU")
            else:
                device = "cpu"
                dtype = torch.float32
                logger.info("⚠️  Using CPU (slow)")

            pipe = StableDiffusionPipeline.from_pretrained(
                model_id,
                torch_dtype=dtype,
                safety_checker=None,
                requires_safety_checker=False,
            )

            # Fast scheduler
            pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
            pipe = pipe.to(device)

            if device != "cpu":
                try:
                    pipe.enable_attention_slicing()
                except Exception:
                    pass

            self._pipe = pipe
            self._device = device
            logger.info("✅ Pipeline loaded")

        except ImportError as e:
            logger.error(f"Missing dependency: {e}")
            raise RuntimeError(
                "Install diffusers: pip install diffusers transformers accelerate"
            ) from e

    # ------------------------------------------------------------------
    def generate_all(self, scenes: List[Scene], frames_per_scene: int) -> List[Scene]:
        self._load_pipeline()
        for scene in scenes:
            logger.info(f"  Generating images for scene {scene.index}…")
            scene.image_paths = self._generate_scene_frames(
                scene, frames_per_scene
            )
        return scenes

    def _generate_scene_frames(self, scene: Scene, n_frames: int) -> List[str]:
        import torch
        scene_dir = self.output_dir / f"scene_{scene.index:02d}"
        scene_dir.mkdir(parents=True, exist_ok=True)

        paths = []
        for i in range(n_frames):
            out_path = scene_dir / f"frame_{i:04d}.png"
            if out_path.exists():
                logger.debug(f"    Frame {i} cached, skipping")
                paths.append(str(out_path))
                continue

            try:
                # Vary seed per frame for subtle diversity
                generator = torch.Generator(device=self._device).manual_seed(
                    hash(scene.enhanced_prompt) % (2**32) + i
                )

                result = self._pipe(
                    prompt=scene.enhanced_prompt,
                    negative_prompt=scene.negative_prompt,
                    width=min(self.width, 768),   # SD 1.5 works best ≤ 768
                    height=min(self.height, 432),
                    num_inference_steps=self.steps,
                    guidance_scale=self.guidance,
                    generator=generator,
                    num_images_per_prompt=1,
                )

                image = result.images[0]

                # Upscale to target resolution if needed
                if image.width != self.width or image.height != self.height:
                    from PIL import Image
                    image = image.resize((self.width, self.height), Image.LANCZOS)

                image.save(str(out_path))
                paths.append(str(out_path))
                logger.debug(f"    ✔ Frame {i} saved → {out_path.name}")

            except Exception as e:
                logger.error(f"    Frame {i} generation failed: {e}")
                # Create placeholder frame
                placeholder = self._placeholder_frame(scene, i)
                placeholder.save(str(out_path))
                paths.append(str(out_path))

        return paths

    def _placeholder_frame(self, scene: Scene, frame_idx: int):
        """Create a simple colored placeholder when generation fails."""
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (self.width, self.height), color=(20, 20, 40))
        draw = ImageDraw.Draw(img)
        text = f"Scene {scene.index} | Frame {frame_idx}\n{scene.raw_description[:50]}..."
        draw.text((50, self.height // 2 - 20), text, fill=(200, 200, 200))
        return img
