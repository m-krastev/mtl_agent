#!/Users/Matey/miniconda3/envs/uncle-google/bin/python3

import argparse
import asyncio
import logging
from pathlib import Path
from mtl_agent.translate_subtitle import translate
from mtl_agent.video_work import encode
from mtl_agent.upload_videos import upload

ROOT = Path(__file__).parent.parent
TRANSLATIONS_PATH = ROOT / "Translations"

logging.basicConfig(
    handlers=[logging.FileHandler(ROOT / "debug.log"), logging.StreamHandler()],
    level=logging.INFO,
    format="[%(asctime)s][%(levelname)-8s] %(name)s - %(message)s",
)

async def _main():
    parser = argparse.ArgumentParser()

    parser.add_argument("file", help="File to process", type=str)

    parser.add_argument(
        "--headless",
        help="Whether to run in headless mode. Must specify root folder. If the folder does not appear in the PATH of FILE, the program exits.",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Whether to run in debug mode. If present, will not delete temporary files",
    )
    parser.add_argument(
        "--video_url", help="Video URL to use when uploading to Animes-Portal etc."
    )
    parser.add_argument(
        "--thumb", action="store_true", help="Whether to upload thumbnail"
    )

    parser.add_argument("--subtitle", "-s", help="Ready-made subtitle file to use")
    parser.add_argument("--subtitle_track", help="Subtitle track to use", default=0)
    parser.add_argument("--audio_track", "-a", help="Audio track to use", default=None)

    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Whether to force the encoding process even if the file already exists",
    )

    parser.add_argument(
        "--translation_provider",
        "-sp",
        default="deepl",
        choices=["deepl", "google"],
        help="Translation API provider to use",
    )

    parser.add_argument(
        "--secrets",
        default=ROOT / "secrets.json",
        help="Path to secrets file (contains API keys for DeepL and/or Google Translate)",
    )

    parser.add_argument(
        "--backup_path",
        default=TRANSLATIONS_PATH,
        help="Path to backup translated file",
    )
    
    parser.add_argument(
        "--upload", "-u", action="store_true", help="Whether to upload to Vbox7, Animes-Portal etc."
    )
    parser.add_argument(
        "--codec", "-c", default="x264", help="Codec to use for encoding", choices=["x264", "hevc"]
    )

    args = parser.parse_args()
    logging.info(f"Program called with args: {args}")

    INPUT_FILE = Path(args.file).resolve()

    if args.headless and args.headless not in INPUT_FILE.parent.parent.name:
        print("Headless mode invoked in non-automatically managed folder. Exiting...")
        exit(1)

    sub = translate(args)
    out = await encode(INPUT_FILE, sub, args)
    if args.upload:
        out = await upload(out, args)
    return out

def main():
    asyncio.run(_main())

if __name__ == "__main__":
    main()
