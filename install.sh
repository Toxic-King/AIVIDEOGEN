#!/usr/bin/env bash
# install.sh — One-click setup for AIVideoGen

set -e

echo ""
echo "======================================"
echo "  🎬  AIVideoGen — Setup Script"
echo "======================================"
echo ""

# Check Python
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✔ Python: $python_version"

# Check FFmpeg
if command -v ffmpeg &> /dev/null; then
    ffmpeg_version=$(ffmpeg -version 2>&1 | head -1 | awk '{print $3}')
    echo "✔ FFmpeg: $ffmpeg_version"
else
    echo "⚠  FFmpeg not found."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  Installing via Homebrew…"
        brew install ffmpeg
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "  Installing via apt…"
        sudo apt-get update -qq && sudo apt-get install -y ffmpeg
    else
        echo "  ➡ Install FFmpeg manually: https://ffmpeg.org/download.html"
    fi
fi

# Create virtualenv
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment…"
    python3 -m venv venv
fi

# Activate
source venv/bin/activate

echo ""
echo "Installing Python packages…"
pip install --upgrade pip -q
pip install -r requirements.txt

echo ""
echo "======================================"
echo "  ✅  Setup complete!"
echo "======================================"
echo ""
echo "Run your first video:"
echo ""
echo "  source venv/bin/activate"
echo "  python app.py --text \"A sunset over the ocean\" --quality low"
echo ""
