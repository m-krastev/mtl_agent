import os
from pathlib import Path
import subprocess
import sys
import ffmpeg
import logging
import platform
from typing import Any, Dict

X264_DEFAULT_ARGS: Dict[str, Any] = {
    "format": "mp4",
    "vcodec": "libx264",
    "crf": "22",
    "bf": 4,
    "preset": "veryfast",
    "tune": "animation",
    "movflags": "+faststart",
    "profile:v": "high10",
    "aq-mode": 3,
}

HEVC_DEFAULT_ARGS: Dict[str, Any] = {
    "format": "mp4",
    "vcodec": "libx265",
    "crf": "25",
    "bf": 6,
    "preset": "veryfast",
}

AUDIO_DEFAULT_ARGS: Dict[str, Any] = {
    "audio_bitrate": 256_000,
}


def extract_subtitle(filepath: str, output_file: str, subtitle_track: int = 0) -> str:
    video = ffmpeg.input(filepath, loglevel=16)
    video = ffmpeg.output(video, output_file, map=f"0:s:{subtitle_track}")
    logging.info("Extracting subtitles: %s", video.get_args())
    video.run()
    return output_file


def extract_thumbnail(
    filepath: str, output_file: str, scene_threshold: float = 0.6
) -> str:
    # ffmpeg -i input.mp4 -vf "thumbnail" -frames:v 1 thumbnail.png
    input_stream = (
        ffmpeg.input(filepath, loglevel=16)
        .filter("select", f"gt(scene,{scene_threshold})")
        .output(output_file, frames=1)
        .overwrite_output()
    )
    logging.info(f"Extracting thumbnail with args: {input_stream.get_args()}")
    input_stream.run()
    return output_file


def _get_hardcode_subtitle_args(
    input_file,
    subtitle_file,
    output_file,
    codec: str,
    audio_track=None,
    extra_args=None,
):
    input_stream = ffmpeg.input(input_file)
    video_stream = ffmpeg.filter(input_stream.video, "ass", subtitle_file)

    if extra_args and "vf" in extra_args:
        user_filters = extra_args.pop("vf")
        for filter_spec in user_filters.split(","):
            parts = filter_spec.split("=", 1)
            filter_name = parts[0]
            if len(parts) > 1:
                filter_args_str = parts[1]
                args = []
                kwargs = {}
                for arg in filter_args_str.split(":"):
                    if "=" in arg:
                        key, val = arg.split("=", 1)
                        kwargs[key] = val
                    else:
                        args.append(arg)
                video_stream = video_stream.filter(filter_name, *args, **kwargs)
            else:
                video_stream = video_stream.filter(filter_name)

    # --- Audio Stream Selection and Filtering ---
    audio_stream = None
    if audio_track:
        # Select the specific audio track by language metadata
        audio_stream = input_stream[f"a:m:language:{audio_track}"]

    if extra_args and "af" in extra_args:
        if audio_stream:
            user_filters = extra_args.pop("af")
            for filter_spec in user_filters.split(","):
                parts = filter_spec.split("=", 1)
                filter_name = parts[0]
                if len(parts) > 1:
                    filter_args_str = parts[1]
                    args = []
                    kwargs = {}
                    for arg in filter_args_str.split(":"):
                        if "=" in arg:
                            key, val = arg.split("=", 1)
                            kwargs[key] = val
                        else:
                            args.append(arg)
                    audio_stream = audio_stream.filter(filter_name, *args, **kwargs)
                else:
                    audio_stream = audio_stream.filter(filter_name)
        else:
            logging.warning(
                "Audio filters ('af') provided without selecting an audio track ('--audio_track'). Filters will be ignored."
            )

    acodec = "aac_at" if platform.system() == "Darwin" else "libfdk_aac"
    audio_args = AUDIO_DEFAULT_ARGS | {"acodec": acodec}

    # --- Codec-Specific Output Configuration ---
    if codec == "x264":
        default_args = X264_DEFAULT_ARGS | audio_args
        args = default_args | (extra_args or {})

        if audio_stream:
            # Explicitly pass the selected/filtered audio stream
            args.pop("map", None)  # Remove any user-provided map to avoid conflicts
            output = ffmpeg.output(video_stream, audio_stream, output_file, **args)
        else:
            # Preserve original behavior: map all audio streams if no specific track is selected.
            args["map"] = "0:a"
            output = ffmpeg.output(video_stream, output_file, **args)

    elif codec == "hevc":
        default_args = HEVC_DEFAULT_ARGS | audio_args
        # Use the selected/filtered stream, or fall back to the default audio stream.
        final_audio_stream = audio_stream if audio_stream else input_stream.audio

        args = default_args | (extra_args or {})
        output = ffmpeg.output(video_stream, final_audio_stream, output_file, **args)
    else:
        raise ValueError(f"Unsupported codec: {codec}")

    return output.overwrite_output().get_args()



def encode(input_file: Path, subtitle_file, args):
    """
    Encoding part
    """
    output_file = input_file.with_suffix(".mp4")
    if output_file.exists() and not args.force:
        logging.info(f"Hardcoded file already exists: {output_file.name}")
        return output_file

    extra_args = {}
    if args.kwargs:
        for kwarg in args.kwargs:
            if "=" in kwarg:
                k, v = kwarg.split("=", 1)
                extra_args[k.lstrip("-")] = v
            else:
                logging.warning(
                    f"Invalid kwarg format: {kwarg}. Should be key=value. Ignoring."
                )

    ffmpeg_args = _get_hardcode_subtitle_args(
        str(input_file),
        str(subtitle_file),
        str(output_file),
        codec=args.codec,
        audio_track=args.audio_track,
        extra_args=extra_args,
    )
    ffmpeg_args = ["ffmpeg"] + ffmpeg_args
    logging.info(f"Encoding video file with config: {ffmpeg_args}")

    if args.progress_bar:
        # Use better-ffmpeg-progress for progress bar
        from better_ffmpeg_progress import FfmpegProcess
        try:
            process = FfmpegProcess(ffmpeg_args, ffmpeg_log_level="info", ffmpeg_log_file=sys.stdout)
            process.run()
            if process.return_code != 0:
                msg = f"Process did not complete successfully (Code: {process.return_code})."
                logging.error(msg)
        except Exception as e:
            # TODO: Remove once the patch is merged into better_ffmpeg_progress
            # logging.error(f"Failed to start ffmpeg process: {e}")
            # Try to recover in case better_ffmpeg_progress is not up to date
            try:
                process = FfmpegProcess(ffmpeg_args, ffmpeg_log_level="info")
                process.run()
                if process.return_code != 0:
                    msg = f"Process did not complete successfully (Code: {process.return_code})."
                    logging.error(msg)
            except Exception as e:
                logging.error(f"Failed to start ffmpeg process: {e}")
                raise e
    else:
        # Fallback to subprocess if no progress bar is needed
        try:
            result = subprocess.run(ffmpeg_args, check=True)
            if result.returncode != 0:
                msg = f"Process did not complete successfully (Code: {result.returncode})."
                logging.error(msg)
        except subprocess.CalledProcessError as e:
            logging.error(f"FFmpeg process failed: {e}")

    return output_file
