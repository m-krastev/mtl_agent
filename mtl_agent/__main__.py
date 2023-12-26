from mtl_agent.video_work import encode
from mtl_agent.translate_subtitle import translate
from mtl_agent.upload_videos import upload
import asyncio
import logging

import argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent
TRANSLATIONS_PATH = ROOT / "Translations"

logging.basicConfig(
    handlers=[logging.FileHandler(ROOT / "debug.log"), logging.StreamHandler()],
    level=logging.INFO,
    format="[%(asctime)s][%(levelname)-8s] %(name)s - %(message)s",
)


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--headless",
        help="Whether to run in headless mode. Must specify root folder. If the folder does not appear in the PATH of FILE, the program exits.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Whether to run in debug mode. If present, will not delete temporary files",
    )

    # Translate Parser
    subparsers = parser.add_subparsers(required=True)

    translate_parser = subparsers.add_parser("translate")
    translate_parser.add_argument("file", help="File to process", type=str)
    translate_parser.add_argument(
        "--subtitle", "-s", help="Ready-made subtitle file to use"
    )
    translate_parser.add_argument(
        "--subtitle_track",
        "-st",
        default=0,
        help="Subtitle track (English) to use for translation. Default is 0",
    )
    translate_parser.add_argument(
        "--translation_provider",
        "-sp",
        default="deepl",
        choices=["deepl", "google"],
        help="Translation API provider to use",
    )
    translate_parser.add_argument(
        "--backup_path",
        default=TRANSLATIONS_PATH,
        help="Path to backup translated file",
    )
    translate_parser.add_argument(
        "--secrets",
        default=ROOT / "secrets.json",
        help="Path to secrets file (contains API keys for DeepL and/or Google Translate)",
    )

    translate_parser.set_defaults(func=translate)

    encode_parser = subparsers.add_parser("encode")
    encode_parser.add_argument("file", help="File to process", type=str)
    encode_parser.add_argument(
        "--subtitle", "-s", help="Ready-made subtitle file to use"
    )
    encode_parser.add_argument(
        "--audio_track",
        "-a",
        type=str,
        default=None,
        help="Audio track to use. If not specified, will output all available audio tracks. Otherwise, must use the language code (e.g. jpn)",
    )

    encode_parser.add_argument(
        "--codec",
        "-c",
        type=str,
        default="x264",
        choices=["hevc", "x264"],
        help="Codec to use for encoding",
    )

    encode_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Whether to force the encoding process even if the file already exists",
    )
    encode_parser.set_defaults(func=encode)

    upload_parser = subparsers.add_parser("upload")
    upload_parser.add_argument("file", help="File to process", type=str)
    upload_parser.add_argument(
        "--video_url",
        "-u",
        help="If present, skips the vbox upload and uses the specified URL instead",
    )
    upload_parser.add_argument(
        "--thumb",
        "--thumbnail",
        "-t",
        action="store_true",
        help="If present, changes the thumbnail of the video during the upload.",
    )
    upload_parser.set_defaults(func=upload)
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    INPUT_FILE = Path(args.file).resolve()

    if INPUT_FILE.is_dir():
        logging.info("Program called with folder instead of a file")
        exit(1)

    if args.headless and args.headless not in INPUT_FILE.parts:
        print("Headless mode invoked in non-automatically managed folder. Exiting...")
        exit(1)

    match args.func.__name__:
        case "translate":
            out = translate(args)
            print(out)

        case "encode":
            subtitle_file = Path(args.subtitle).resolve()
            out = asyncio.run(encode(INPUT_FILE, subtitle_file, args))
            print(out)

        case "upload":
            output_file = Path(args.file).resolve()
            out = asyncio.run(upload(output_file, args))
            print(out)


if __name__ == "__main__":
    main()
