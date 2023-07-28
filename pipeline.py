import os
import pyppeteer
from video_work import extract_subtitle, hardcode_ass_subtitle_hevc, hardcode_ass_subtitle_x264
from translate_subtitle import translate_subtitle_deepl, change_roboto_to_trebuchet, translate_subtitle_google
from upload_videos import animes_portal_wall, vbox, animes_portal, change_vbox_thumbnail
import asyncio
import json

import argparse
from pathlib import Path


SECRETS = Path(r"secrets.json")
TRANSLATIONS_PATH = SECRETS.parent / "Translations"

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="File to translate", type=str)
    parser.add_argument("--upload", action="store_true")
    parser.add_argument("--thumb", action="store_true")
    args = parser.parse_args()

    INPUT_FILE = Path(args.file)
    OUTPUT_FILE = INPUT_FILE.with_suffix(".mp4")
    SUBTITLE_FILE = INPUT_FILE.with_stem(INPUT_FILE.stem + "_translated").with_suffix(".ass")
    
    if not SUBTITLE_FILE.exists():
        subtitle = INPUT_FILE.with_suffix(".ass")
        if not subtitle.exists():
            subtitle = extract_subtitle(str(INPUT_FILE), str(subtitle))
            print("Subtitle extracted:", subtitle)

        # subtitle = translate_subtitle_google(subtitle, SUBTITLE_FILE, change_roboto_to_trebuchet, path_to_secrets= SECRETS)
        subtitle = translate_subtitle_deepl(subtitle, SUBTITLE_FILE, change_roboto_to_trebuchet, path_to_secrets=SECRETS)
        
        # Backup to MEGA
        backup = TRANSLATIONS_PATH / subtitle.parts[-2] / subtitle.name
        backup.parent.mkdir(exist_ok=True)
        backup.write_text(subtitle.read_text())
        print("Successfully translated!")

    if not OUTPUT_FILE.exists():
        os.chdir(SUBTITLE_FILE.parent)
        out, err = hardcode_ass_subtitle_x264(str(INPUT_FILE), str(SUBTITLE_FILE.name), str(OUTPUT_FILE))
        if err is not None:
            print("Stdout:" , out, "\nStderr:" , err)
            print("Error has been established. Exiting...")
            exit()
    else:
        print("File already exists...")

    if args.upload:
        print("Uploading...", OUTPUT_FILE)
        # browser = await pyppeteer.launch(headless=False, executablePath=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        # print(Browser.wsEndpoint)

        browser = await pyppeteer.connect(browserURL="http://127.0.0.1:9222")

        with open(INPUT_FILE.parent / "upload_properties.json", encoding="utf8") as f:
            props = json.load(f)

        import re

        file = args.file
        episode_num = int(re.search(props["episode_parser"], file)[1])
        
        title:str = props["title"].format(episode_num)
        if "Jujutsu Kaisen" in title:
            title = "Jujutsu Kaisen / Джуджуцу войни - {:0>2} / S2 E{:0>2} [ Bg Mtl Sub ]".format(episode_num, episode_num - 24)

        final_url = await vbox(
            browser,
            OUTPUT_FILE,
            title,
            props["description"],
            props["tags"],
            # private=True
        )
        print("Final URL:", final_url)

        # final_url = "https://www.vbox7.com/play:e93fbf6e1a"
        if args.thumb:
            await change_vbox_thumbnail(browser, final_url, props["thumbnail_path"])

        await animes_portal(browser, final_url, episode_num, props["animes_portal"])
        await animes_portal_wall(browser, final_url, "https://animes-portal.info/otakus/otaku-122609", title)


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
