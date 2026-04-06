# 🎬 AIVideoGen CLI

> **Text → Cinematic AI Video** — Fully local, zero API cost, CLI-first.

---

## ✨ What It Does

Give it one text prompt. It returns a fully edited `.mp4` video with:
- 🎨 AI-generated cinematic visuals (Stable Diffusion)
- 🎞️ Animated scenes (AnimateDiff or Ken Burns fallback)
- 🔊 Natural voice narration (Microsoft Edge TTS)
- ✂️ Auto-synced audio + video
- 🎨 Color grading + post-processing

All locally. No GPU cloud credits. No GUI needed.

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
# Clone / download the project
cd AIVideoGen

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate      # macOS / Linux
venv\Scripts\activate         # Windows

# Install Python packages
pip install -r requirements.txt
```

### 2. Install FFmpeg

| Platform | Command |
|----------|---------|
| macOS    | `brew install ffmpeg` |
| Ubuntu   | `sudo apt install ffmpeg` |
| Windows  | Download from https://ffmpeg.org/download.html |

### 3. Run

```bash
python app.py --text "A lone astronaut walking on Mars at sunset"
```

---

## 💻 CLI Usage

```
python app.py --text "your prompt" [options]
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--text` | *required* | Input text prompt |
| `--voice` | `en-US-AriaNeural` | Edge TTS voice |
| `--fps` | `24` | Frame rate (24 or 30) |
| `--quality` | `medium` | `low` / `medium` / `high` |
| `--resolution` | `720p` | `720p` / `1080p` |
| `--output` | `output` | Output directory |
| `--no-animation` | `False` | Skip AnimateDiff (faster) |
| `--debug` | `False` | Verbose logs |

---

## 📖 Examples

```bash
# Simple scene
python app.py --text "Ocean waves crashing at sunset"

# Multi-scene (splits on 'then', commas, etc.)
python app.py --text "A boy walking in rain, then smiling at sunrise"

# Epic cinematic
python app.py --text "Dragon flying over a medieval city at night" \
  --quality high --resolution 1080p --fps 30

# Custom voice
python app.py --text "A futuristic city in 2150" --voice en-US-GuyNeural

# Fast draft
python app.py --text "Forest in autumn" --quality low --no-animation
```

---

## 🏗 Architecture

```
User Prompt
   │
   ▼
┌─────────────────────┐
│  PromptAnalyzer     │  Extracts: subject, mood, weather, time, style
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  SceneGenerator     │  Splits text into logical scenes
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  PromptEnhancer     │  "boy walking" → "cinematic shot of boy, 4k..."
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  ImageGenerator     │  Stable Diffusion → PNG frames per scene
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  AnimationEngine    │  AnimateDiff → MP4  (Ken Burns fallback)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  VoiceGenerator     │  Edge TTS → MP3 narration
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  AudioSyncEngine    │  Matches scene duration to audio length
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  VideoComposer      │  FFmpeg: frames + audio → scenes → full video
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  PostProcessor      │  Color grade, sharpen, fade-in, fast-start
└──────────┬──────────┘
           │
           ▼
    final_video.mp4 🎬
```

---

## 📁 Output Structure

```
output/
├── frames/              # Raw generated images
│   ├── scene_00/
│   └── scene_01/
├── animated/            # Per-scene video clips
├── audio/               # TTS narration files
├── composed/            # Assembled clips
└── final_video.mp4      # ← Your video

logs/
└── aivideogen.log       # Full debug log
```

---

## ⚡ Performance Notes

| Hardware | Quality | Speed (3 scenes) |
|----------|---------|-----------------|
| M2 Mac (MPS) | medium | ~4–8 min |
| NVIDIA RTX 3090 | medium | ~2–4 min |
| CPU only | low | ~15–30 min |

Use `--quality low --no-animation` for fast drafts.

---

## 🎙️ Available Voices

Popular Edge TTS voices:

| Voice | Style |
|-------|-------|
| `en-US-AriaNeural` | Female, natural (default) |
| `en-US-GuyNeural` | Male, natural |
| `en-US-JennyNeural` | Female, friendly |
| `en-GB-SoniaNeural` | Female, British |
| `en-AU-NatashaNeural` | Female, Australian |

Find all voices: `python -c "import asyncio, edge_tts; asyncio.run(edge_tts.list_voices())" | grep ShortName`

---

## 🛠 Troubleshooting

**`ModuleNotFoundError: diffusers`**
```bash
pip install diffusers transformers accelerate
```

**`ffmpeg: command not found`**
```bash
brew install ffmpeg  # macOS
sudo apt install ffmpeg  # Ubuntu
```

**AnimateDiff slow / OOM**
```bash
python app.py --text "..." --no-animation
```

**Force CPU (no GPU)**
```python
# In core/image_generator.py, change:
device = "cpu"
```

---

## 📦 Project Structure

```
AIVideoGen/
├── app.py                    # Entry point / CLI
├── requirements.txt
├── setup.py
├── core/
│   ├── pipeline.py           # Master orchestrator
│   ├── prompt_analyzer.py    # NLP metadata extraction
│   ├── scene_generator.py    # Scene splitting
│   ├── prompt_enhancer.py    # Cinematic prompt crafting
│   ├── image_generator.py    # Stable Diffusion wrapper
│   ├── animation_engine.py   # AnimateDiff / Ken Burns
│   ├── voice_generator.py    # Edge TTS
│   ├── audio_sync.py         # Duration alignment
│   ├── video_composer.py     # FFmpeg composition
│   └── post_processor.py     # Color grade / polish
└── utils/
    ├── logger.py             # Logging setup
    └── helpers.py            # Shared utilities
```

---

## 📝 License

MIT — use freely, build on it.
