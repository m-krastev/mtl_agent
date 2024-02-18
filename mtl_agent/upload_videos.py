# import asyncio
from asyncio import sleep
import json
from pathlib import Path
import re

import logging
from .providers.animes_portal import AnimesPortal

from playwright.async_api import async_playwright
from .providers.tubebg import TubeBG

async def upload(file: Path, args):
    print('Dev: here')
    playwright = await async_playwright().start()

    _browser = await playwright.chromium.launch(headless=False)
    browser = await _browser.new_context()
    browser.set_default_timeout(3000000)

    with open(args.profile_path) as f:
        profile = json.load(f)
    tubebg = TubeBG(browser, **profile["TUBEBG"])
    await browser.add_cookies(tubebg.get_cookies())

    logging.info(f"Uploading... {file}")

    # NOTE: Upload properties must be in the same folder as the file
    with open(file.parent / "upload_properties.json", encoding="utf8") as f:
        props = json.load(f)
    logging.info(f"Upload Properties found with: {props}")

    # parse and set episode number
    episode_num = int(re.search(props["episode_parser"], file.stem)[1])
    title = props["title"].format(episode_num)
    description = props.get("description", "")
    tags = props.get("tags", "")
    categories = props.get("categories", "")
    
    # Upload videos
    await tubebg.upload(file, title, description, tags, categories)
    
    # Close and reopen browser to avoid CloudFlare checks.
    await browser.close() 
    browser = await _browser.new_context()
    
    # Wait for 5 seconds for the video to be processed
    await sleep(60)
    tubebg = TubeBG(browser, **profile["TUBEBG"])
    if args.video_url:
        embed_url = args.video_url
        public_url = args.video_url
    else:
        public_url, embed_url = await tubebg.get_secret_link()

    # if args.thumb and props.get("thumbnail_path"):
    #     if props.get("thumbnail_font"):
    #         from .thumbnail import generate_thumbnail, default_config

    #         default_config.update(props["thumbnail_font"])
    #         _, thumbnail_path = generate_thumbnail(
    #             props["thumbnail_path"], episode_num, **default_config
    #         )

    #         await change_vbox_thumbnail(browser, final_url, thumbnail_path)
    #         Path(thumbnail_path).unlink()

    #     else:
    #         await change_vbox_thumbnail(browser, final_url, props["thumbnail_path"])

    if props.get("animes_portal"):
        ap = AnimesPortal(browser, profile["ANIMES_PORTAL"])
        await browser.add_cookies(ap.get_cookies())

        await ap.upload(embed_url, episode_num, props["animes_portal"])

    if props.get("animes_portal_wall"):
        ap = AnimesPortal(browser, profile["ANIMES_PORTAL"])
        await browser.add_cookies(ap.get_cookies())

        await ap.upload_to_wall(public_url, props["animes_portal_wall"], title + "\n" + description)

    await sleep(60)
    # Clean up
    await browser.close()
    await _browser.close()
    await playwright.stop()

    return public_url