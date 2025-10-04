import logging
import re
from html import unescape
from itertools import chain
from pathlib import Path
from typing import Callable

import ass

from .providers.base_translator import BaseTranslator
from .providers.deepl_translator import DeepLTranslator
from .providers.google_translator import GoogleTranslator
from .video_work import extract_subtitle


def change_styles(styles):
    for style in styles:
        if any(
            x in style.fontname
            for x in ("Roboto", "Arial", "Rosario", "Open Sans", "Calibri")
        ):
            style.fontname = "Trebuchet MS"
            if style.fontsize < 21:
                style.fontsize = 22
                style.margin_v = 20
            # style.bold = True

    return styles


def translate_subtitle(
    translator: BaseTranslator,
    input_file: str | Path,
    output_file: str | Path,
    style_function: Callable,
):
    with open(input_file, encoding="utf8") as f:
        sub = ass.parse(f)

    sub.styles = style_function(sub.styles)

    lines = [x.text for x in sub.events]

    # preprocessing step to avoid mistranslation of supposedly capital case
    lines = [
        re.sub(r"\b([A-Z]+)\b", lambda x: f"{x[1].title()}", line) for line in lines
    ]

    stack = [
        re.sub(r"\{(.+?)\}", r"<\1>", line).replace(r"\N", "<c>") for line in lines
    ]

    translated = translator.translate(stack)

    # processing step to transpose the rogue commas
    stack = "stacc".join(translated)
    stack = re.sub(r"\s*(<z>|<c>)\s*([,.;:])", r"\2\1", stack)
    stack = stack.split("stacc")
    ##############

    stack = [
        re.sub(r"<(.+?)>", r"{\1}", j.replace("<c>", r"\N"))
        for j in chain.from_iterable([i.split("<z>") for i in stack])
    ]

    for i, line in enumerate(stack):
        sub.events[i].text = unescape(line)

    with open(output_file, "w", encoding="utf-8-sig") as f:
        sub.dump_file(f)

    return output_file


def translate(args):
    INPUT_FILE = Path(args.file).resolve()

    ##################### subtitle checks and translation
    if args.subtitle:
        SUBTITLE_FILE = Path(args.subtitle).resolve()
        if SUBTITLE_FILE.suffix != ".ass":
            logging.error(
                "You must use ASS (Substation Alpha) subtitle files! Exiting..."
            )
            exit(1)

    else:
        SUBTITLE_FILE = INPUT_FILE.with_stem(INPUT_FILE.stem + ".bg").with_suffix(
            ".ass"
        )

    ###################### check if subtitle exists and if not, translates it
    if SUBTITLE_FILE.exists():
        logging.info(f"Subtitle file found: {SUBTITLE_FILE.name}")
        return SUBTITLE_FILE
    ###################### no file exists
    subtitle = INPUT_FILE.with_suffix(".ass")
    if not subtitle.exists():
        subtitle = extract_subtitle(str(INPUT_FILE), str(subtitle), args.subtitle_track)
        logging.info(f"Subtitle extracted: {subtitle}")

    if args.translation_provider == "google":
        translator = GoogleTranslator(
            args.secrets, args.source_language, args.target_language
        )
    else:
        translator = DeepLTranslator(
            args.secrets, args.source_language, args.target_language
        )

    subtitle = translate_subtitle(
        translator, subtitle, SUBTITLE_FILE, change_styles
    )

    # Backup to MEGA
    backup = Path(args.backup_path) / SUBTITLE_FILE.parent.name / SUBTITLE_FILE.name
    backup.parent.mkdir(exist_ok=True)
    backup.write_text(SUBTITLE_FILE.read_text("utf-8-sig"), "utf-8-sig")
    logging.info(f"Successfully translated! Backup at {backup}")

    return SUBTITLE_FILE
