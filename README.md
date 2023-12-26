# MTL Agent for Media Processing

This repository contains the code for a Machine Translation (MTL) agent that can perform automatic translation, subtitle extraction, video encoding, and thumbnail generation.
Contrary to its name, it does not contain code for MTL, it only interacts with DeepL's API service to perform the translation.

## Features

- **Automatic Translation**: Translates text from one language (usually English) to another (Bulgarian).
- **Subtitle Extraction**: Uses FFMPEG to extract subtitles from video files.
- **Video Encoding**: Encodes videos in different formats.
- **Thumbnail Generation**: Automatically generates thumbnails from videos.

To get a feel for it, run `python pipeline.py --help`

Currently a hobby project that automates away translation needs!