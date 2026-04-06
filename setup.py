"""setup.py — Optional package installation"""
from setuptools import setup, find_packages

setup(
    name="aivideogen",
    version="1.0.0",
    description="CLI tool: Text → Cinematic AI Video",
    author="AIVideoGen",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        "torch>=2.1.0",
        "diffusers>=0.25.0",
        "transformers>=4.35.0",
        "accelerate>=0.25.0",
        "Pillow>=10.0.0",
        "edge-tts>=6.1.9",
        "tqdm>=4.66.0",
        "numpy>=1.24.0",
    ],
    entry_points={
        "console_scripts": [
            "aivideogen=app:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
