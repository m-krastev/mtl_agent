from .video_work import encode
from .translate_subtitle import translate
from .upload_videos import upload
import asyncio
import logging

import argparse
from pathlib import Path

ROOT = Path.home() / ".config" / "mtl_agent"

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

    parser.add_argument(
        "--root",
        default=ROOT,
        help="Root folder to use for credentials, logs, backup files. Default is the $HOME/.config/mtl_agent",
    )

    ####################### TRANSLATE PARSER #######################
    subparsers = parser.add_subparsers(required=True)

    translate_parser = subparsers.add_parser("translate")
    translate_parser.add_argument("file", help="File to process", type=str)
    translate_parser.add_argument("--subtitle", "-s", help="Subtitle file to use")
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
        default=None,
        help="Path to backup translated file",
    )
    translate_parser.add_argument(
        "--secrets",
        default=None,
        help="Path to secrets.json file for translation API",
    )

    translate_parser.set_defaults(func=translate)
    ####################### TRANSLATE PARSER #######################

    ####################### ENCODE PARSER #######################
    encode_parser = subparsers.add_parser("encode")
    encode_parser.add_argument("file", help="File to process", type=str)
    encode_parser.add_argument(
        "--subtitle", "-s", help="Ready-made subtitle file to use", required=True
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
    ####################### ENCODE PARSER #######################

    ####################### UPLOAD PARSER #######################
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
    upload_parser.add_argument(
        "--profile_path",
        "-pp",
        default=None,
        help="Path to profile to use for uploading",
    )
    upload_parser.set_defaults(func=upload)
    ####################### UPLOAD PARSER #######################
    
    ####################### PIPELINE PARSER #######################
    
    pipeline_parser = subparsers.add_parser("pipeline")
    pipeline_parser.add_argument("file", help="File to process", type=str)
    pipeline_parser.add_argument(
        "--subtitle", "-s", help="Ready-made subtitle file to use", 
    )
    pipeline_parser.add_argument(
        "--audio_track",
        "-a",
        type=str,
        default=None,
        help="Audio track to use. If not specified, will output all available audio tracks. Otherwise, must use the language code (e.g. jpn)",
    )
    pipeline_parser.add_argument("--profile_path", "-pp", default=None, help="Path to profile to use for uploading")
    pipeline_parser.add_argument("--secrets", default=None, help="Path to secrets.json file for translation API")
    pipeline_parser.add_argument("--backup_path", default=None, help="Path to backup translated file")
    pipeline_parser.add_argument("--translation_provider", "-sp", default="deepl", choices=["deepl", "google"], help="Translation API provider to use")
    pipeline_parser.add_argument("--subtitle_track", "-st", default=0, help="Subtitle track (English) to use for translation. Default is 0")
    pipeline_parser.add_argument("--codec", "-c", type=str, default="x264", choices=["hevc", "x264"], help="Codec to use for encoding")
    pipeline_parser.add_argument("--force", "-f", action="store_true", help="Whether to force the encoding process even if the file already exists")
    
    pipeline_parser.add_argument("--video_url", "-v", help="If present, skips the vbox upload and uses the specified URL instead")
    pipeline_parser.add_argument("--upload", "-u", action="store_true", help="Whether to upload to Vbox7, Animes-Portal etc.")
    pipeline_parser.add_argument("--thumb", "-t", action="store_true", help="If present, changes the thumbnail of the video during the upload.")
    pipeline_parser.set_defaults(func=pipeline)
    ####################### PIPELINE PARSER #######################
    
    return parser

async def pipeline(INPUT_FILE, args):
    sub = translate(args)
    out = await encode(INPUT_FILE, sub, args)
    if args.upload:
        out = await upload(out, args)
    return out
    

def main():
    parser = get_parser()
    args = parser.parse_args()

    args.root = Path(args.root).resolve()
    if not args.root.exists():
        args.root.mkdir(parents=True)

    logging.basicConfig(
        handlers=[logging.FileHandler(args.root / "debug.log"), logging.StreamHandler()],
        level=logging.INFO,
        format="[%(asctime)s][%(levelname)-8s] %(name)s - %(message)s",
    )

    INPUT_FILE = Path(args.file).resolve()

    if INPUT_FILE.is_dir():
        logging.info("Program called with folder instead of a file")
        exit(1)

    if args.headless and args.headless not in INPUT_FILE.parts:
        print("Headless mode invoked in non-automatically managed folder. Exiting...")
        exit(1)

    match args.func.__name__:
        case "translate":
            args.backup_path = args.backup_path or args.root / "Translations"
            args.secrets = args.secrets or args.root / "secrets.json"
            out = translate(args)
            print(out)

        case "encode":
            subtitle_file = Path(args.subtitle).resolve()
            out = asyncio.run(encode(INPUT_FILE, subtitle_file, args))
            print(out)

        case "upload":
            args.profile_path = args.profile_path or args.root / "profile_default.json"

            output_file = Path(args.file).resolve()
            out = asyncio.run(upload(output_file, args))
            print(out)

        case "pipeline":
            args.profile_path = args.profile_path or args.root / "profile_default.json"
            args.profile_path = Path(args.profile_path).resolve()
            args.backup_path = args.backup_path or args.root / "Translations"
            args.backup_path = Path(args.backup_path).resolve()
            args.secrets = args.secrets or args.root / "secrets.json"
            args.secrets = Path(args.secrets).resolve()
            out = asyncio.run(pipeline(INPUT_FILE, args))
            print(out)

if __name__ == "__main__":
    main()
