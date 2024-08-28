from pathlib import Path
import ffmpeg
import logging


def extract_subtitle(filepath, output_file, subtitle_track=0):
    video = ffmpeg.input(filepath, loglevel=16)
    video = ffmpeg.output(video, output_file, map=f"0:s:{subtitle_track}")
    logging.info("Extracting subtitles: %s", video.get_args())
    video.run()
    return output_file


def extract_thumbnail(filepath, output_file):
    # ffmpeg -i input.mp4 -vf "thumbnail" -frames:v 1 thumbnail.png
    input = (
        ffmpeg.input(filepath, loglevel=16)
        .filter("select", "gt(scene,0.6)")
        .output(output_file, frames=1)
        .overwrite_output()
    )
    logging.info(f"Extracting thumbnail with args: {input.get_args()}")
    input.run()
    return output_file


def hardcode_ass_subtitle_hevc(
    input_file, subtitle, output_file, get_args: bool = True, **kwargs
):
    import platform
    input = ffmpeg.input(input_file)
    video = ffmpeg.filter(input.video, "ass", subtitle)

    input = ffmpeg.output(
        video,
        input.audio,
        output_file,
        # https://trac.ffmpeg.org/wiki/Encode/AAC
        acodec="aac_at" if platform.system() == "Darwin" else "libfdk_aac",
        audio_bitrate=128,
        format="mp4",
        vcodec="libx265",
        crf="25",
        bf=6,
        preset="veryfast",
        **kwargs
    ).overwrite_output()

    if get_args is True:
        return input.get_args()

    try:
        input.run()

    except ffmpeg.Error as e:
        if e.stdout:
            logging.error("stdout: %s", e.stdout.decode("utf8"))
        if e.stderr:
            logging.error("stderr: %s", e.stderr.decode("utf8"))

        raise e


def hardcode_ass_subtitle_x264(
    input_file, subtitle, output_file, get_args: bool = True, audio_track=None, **kwargs
):

    import platform
    input = ffmpeg.input(input_file)
    video = ffmpeg.filter(input.video, "ass", subtitle)

    audio_map = f"0:a:m:language:{audio_track}" if audio_track else "0:a"
    # map="0:a:m:language:jpn"
    input = ffmpeg.output(
        video,
        output_file,
        map=audio_map,
        format="mp4",
        vcodec="libx264",
        # https://trac.ffmpeg.org/wiki/Encode/AAC
        acodec="aac_at" if platform.system() == "Darwin" else "libfdk_aac",
        audio_bitrate=128,
        crf="22",
        bf=4,
        preset="veryfast",
        tune="animation",
        movflags="+faststart",
        **{"profile:v": "high10"},
        **{"aq-mode": 3},
        **kwargs
    ).overwrite_output()

    if get_args is True:
        return input.get_args()

    try:
        input.run()

    except ffmpeg.Error as e:
        if e.stdout:
            logging.error("stdout: %s", e.stdout.decode("utf8"))
        if e.stderr:
            logging.error("stderr: %s", e.stderr.decode("utf8"))

        raise e


async def encode(input_file: Path, subtitle_file, args):
    """
    Encoding part
    """
    ################################# encoding part
    output_file = input_file.with_suffix(".mp4")
    if output_file.exists() and not args.force:
        logging.info(f"Hardcoded file already exists: {output_file.name}")
        return output_file

    kwargs = {k:v for k,v in [x.split('=') for x in args.kwargs.split()]} if args.kwargs else {}
    ffmpeg_args = (
        hardcode_ass_subtitle_x264(
            str(input_file),
            str(subtitle_file),
            str(output_file),
            audio_track=args.audio_track,
            **kwargs
        )
        if args.codec == "x264"
        else hardcode_ass_subtitle_hevc(
            str(input_file), str(subtitle_file), str(output_file), **kwargs
        )
    )
    logging.info(f"Encoding video file with config: {ffmpeg_args}")

    from asyncio import subprocess

    process = await subprocess.create_subprocess_exec(
        "ffmpeg", *ffmpeg_args, stderr=subprocess.STDOUT
    )
    result = await process.wait()

    if result != 0:
        logging.error(
            f"Process did not complete successfully (Code: {result}). Exiting..."
        )
        exit(1)

    return output_file
