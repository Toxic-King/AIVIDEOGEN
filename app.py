#!/usr/bin/env python3
"""
AIVideoGen CLI - Text to Cinematic Video Generator
Usage: python app.py --text "your prompt" --voice en-US-AriaNeural
"""

import argparse
import sys
import time
from pathlib import Path

from core.pipeline import VideoPipeline
from utils.logger import setup_logger

logger = setup_logger("AIVideoGen")


def parse_args():
    parser = argparse.ArgumentParser(
        description="🎬 AIVideoGen - Convert text to cinematic AI video",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app.py --text "A boy walking in rain, then smiling at sunrise"
  python app.py --text "Ocean waves at sunset" --voice en-US-GuyNeural --quality high
  python app.py --text "City at night" --fps 30 --resolution 1080p
        """
    )

    parser.add_argument("--text", required=True, help="Input text prompt for video generation")
    parser.add_argument("--voice", default="en-US-AriaNeural", help="Edge TTS voice name")
    parser.add_argument("--fps", type=int, default=24, choices=[24, 30], help="Frame rate")
    parser.add_argument("--quality", default="medium", choices=["low", "medium", "high"], help="Generation quality")
    parser.add_argument("--duration", default="auto", help="Video duration per scene (auto or seconds)")
    parser.add_argument("--resolution", default="720p", choices=["720p", "1080p"], help="Output resolution")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument("--no-animation", action="store_true", help="Skip animation, use static frames")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    return parser.parse_args()


def main():
    args = parse_args()

    if args.debug:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)

    print("\n" + "="*60)
    print("🎬  AIVideoGen CLI  —  Text → Cinematic Video")
    print("="*60)
    print(f"📝 Prompt   : {args.text}")
    print(f"🎙️  Voice    : {args.voice}")
    print(f"🎞️  FPS      : {args.fps}")
    print(f"⚡ Quality  : {args.quality}")
    print(f"📺 Resolution: {args.resolution}")
    print("="*60 + "\n")

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    start_time = time.time()

    try:
        pipeline = VideoPipeline(
            text=args.text,
            voice=args.voice,
            fps=args.fps,
            quality=args.quality,
            resolution=args.resolution,
            duration=args.duration,
            output_dir=output_dir,
            use_animation=not args.no_animation,
        )

        output_path = pipeline.run()

        elapsed = time.time() - start_time
        print("\n" + "="*60)
        print(f"✅  Video generated successfully!")
        print(f"📁  Output: {output_path}")
        print(f"⏱️  Time  : {elapsed:.1f}s")
        print("="*60 + "\n")

    except KeyboardInterrupt:
        print("\n⚠️  Generation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        print(f"\n❌  Error: {e}")
        print("Run with --debug for detailed logs.")
        sys.exit(1)


if __name__ == "__main__":
    main()
