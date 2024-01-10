# import asyncio
import json
from pathlib import Path
import re

from playwright.async_api import BrowserContext
import logging


async def vbox(
    browser: BrowserContext,
    filepath: str,
    title: str = "",
    description: str = "",
    tags: str = "",
    private=False,
):
    # navigate
    page = await browser.new_page()
    await page.goto("https://lupload.vbox7.com/video")

    # upload
    input_button = await page.query_selector("input[type=file]")
    await input_button.set_input_files(filepath)

    # wait for upload to finish and auto-navigation to the next page
    await page.wait_for_url("**/upload/step2*", timeout=240000)

    await page.eval_on_selector("#upload_video_name", f"el=> el.value = `{title}`")
    await page.eval_on_selector("#vdescription", f"el=> el.value = `{description}`")
    await page.eval_on_selector("#video_tags", f"el=> el.value = `{tags}`")

    # for testing, post the video privately
    if private:
        await page.eval_on_selector("#privateVideo3", "el => el.checked = true")

    # anime, animation, with_subtitles
    await page.eval_on_selector("#cat3", "el => el.checked = true")
    await page.eval_on_selector("#cat40", "el => el.checked = true")
    await page.eval_on_selector("#cat33", "el => el.checked = true")

    # upload video
    await page.click("#native > div > section > form > * > input.def-btn")

    try:
        # loading page
        final_url = await page.wait_for_selector("#post-data > p:nth-child(3) > a")
        final_url = await final_url.text_content()
    except:
        # video got uploaded immediately
        final_url = page.url

    logging.info(f"VBOX7: {title} uploaded: {final_url}")

    return final_url


async def change_vbox_thumbnail(
    browser: BrowserContext, vbox_link: str, path_to_img: str
):
    page = await browser.new_page()
    await page.goto(vbox_link)

    src = await page.eval_on_selector("#html5player", "(e) => e.src")
    if not src:
        # if await page.title() != props["title"].format(episode_num):
        await page.wait_for_url()

    await page.goto(f"https://www.vbox7.com/video/{vbox_link.rpartition(':')[-1]}/edit")

    input_field = await page.query_selector("#file_change_thumb")

    await input_field.set_input_files(path_to_img)

    await page.click("#native > div > div.major-col > form > * > input")
    await page.wait_for_url("**/play*")

    logging.info("VBOX7: Thumbnail changed.")


async def animes_portal(
    browser: BrowserContext, final_url: str, episode_num: int, animes_portal_url=""
):
    if not animes_portal_url:
        logging.warning("AP: No URL supplied. Returning...")
        return

    page = await browser.new_page()
    await page.goto(animes_portal_url)

    await page.wait_for_selector(
        "#anime > main > div > article > div.rowView-content.content > section:nth-child(3) > div.heading > span"
    )
    await page.eval_on_selector(
        "#anime > main > div > article > div.rowView-content.content > section:nth-child(3) > div.heading > span",
        "el => el.click()",
    )

    # input the vbox7 link
    await page.wait_for_selector(
        "#anime > div.modal.modalOverlay.modal-smaller.visible > div > div.container.rel > div > form > div.cl > div:nth-child(1) > input[type=text]"
    )
    await page.eval_on_selector(
        "#anime > div.modal.modalOverlay.modal-smaller.visible > div > div.container.rel > div > form > div.cl > div:nth-child(1) > input[type=text]",
        f"el => el.value = '{final_url}'",
    )

    # input the episode no
    await page.wait_for_selector(
        "#anime > div.modal.modalOverlay.modal-smaller.visible > div > div.container.rel > div > form > div.cl > div:nth-child(2) > input[type=text]"
    )
    await page.eval_on_selector(
        "#anime > div.modal.modalOverlay.modal-smaller.visible > div > div.container.rel > div > form > div.cl > div:nth-child(2) > input[type=text]",
        f"el => el.value = '{episode_num}'",
    )

    # upload episode
    await page.click(
        "#anime > div.modal.modalOverlay.modal-smaller.visible > div > div.container.rel > div > form > div.row > input.btn.btn-primary.green"
    )
    logging.info("AP: Video Uploaded")


async def animes_portal_wall(
    browser: BrowserContext,
    final_url: str,
    animes_portal_wall_url="",
    post_description: str = "",
):
    post = post_description + "\n" + final_url

    if not animes_portal_wall_url:
        logging.warning("Animes_Portal_Wall: No URL supplied. Returning...")
        return

    page = await browser.new_page()
    await page.goto(animes_portal_wall_url)

    await page.wait_for_selector("#comments > form > span > textarea")
    await page.eval_on_selector(
        "#comments > form > span > textarea", f"el => el.value = `{post}`"
    )

    textarea = await page.query_selector("#comments > form > span > textarea")
    await textarea.press("Enter", delay=1)

    logging.info(f"AP: {final_url} uploaded to AP wall")


from playwright.async_api import async_playwright


async def upload(file: Path, args):
    playwright = await async_playwright().start()

    _browser = await playwright.chromium.launch(headless=False)
    browser = await _browser.new_context()

    with open(args.profile_path) as f:
        profile = json.load(f)

    await browser.add_cookies(
        [
            {
                "name": "vbox7remember",
                "value": profile["vbox7remember"],
                "domain": ".vbox7.com",
                "path": "/",
            },
            {
                "name": "euconsent-v2",
                "value": "CP36MEAP36MEAAHABBENAhEsAP_gAEPAAAIwGMwHIAFAAWAA0ACAAFYAOAA6ACAAFQALQAZAA0ACKAEwALYAYYBAAEDAIMAhABFADgAKQAmkBR4CpAFXALhAXKAukBeYDGQLzgGQAKAAsACoAHAAQAAyABoAEwALYAhAFHgKkAXmAAAA.f_wACHgAAAAA",
                "path": "/",
                "domain": ".vbox7.com",
            },
            {
                "name": "larabox_session",
                "value": profile["larabox_session"],
                "path": "/",
                "domain": ".vbox7.com",
            },
            {
                "name": "ukey",
                "value": profile["ukey"],
                "path": "/",
                "domain": "animes-portal.info",
            },
        ]
    )

    # process = await asyncio.create_subprocess_exec(
    #     "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    #     "--remote-debugging-port=9222",
    # )
    # await asyncio.sleep(3)

    # NOTE: Has issues uploading files bigger than 50mb
    # _browser = await playwright.chromium.connect_over_cdp("http://127.0.0.1:9222")
    # browser = _browser.contexts[0]

    browser.set_default_timeout(300000)

    logging.info(f"Uploading... {file}")

    # NOTE: Upload properties must be in the same folder as the file
    with open(file.parent / "upload_properties.json", encoding="utf8") as f:
        props = json.load(f)
    logging.info(f"Upload Properties found with: {props}")

    # parse episode number
    episode_num = int(re.search(props["episode_parser"], file.stem)[1])
    title = props["title"].format(episode_num)
    description = props.get("description", "")
    tags = props.get("tags", "")

    final_url = args.video_url or await vbox(
        browser, file, title, description, tags
    )

    if args.thumb and props.get("thumbnail_path"):
        if props.get("thumbnail_font"):
            from .thumbnail import generate_thumbnail, default_config

            default_config.update(props["thumbnail_font"])
            _, thumbnail_path = generate_thumbnail(
                props["thumbnail_path"], episode_num, **default_config
            )

            await change_vbox_thumbnail(browser, final_url, thumbnail_path)
            Path(thumbnail_path).unlink()

        else:
            await change_vbox_thumbnail(browser, final_url, props["thumbnail_path"])

    if props.get("animes_portal"):
        await animes_portal(browser, final_url, episode_num, props["animes_portal"])

    if props.get("animes_portal_wall"):
        await animes_portal_wall(
            browser,
            final_url,
            props["animes_portal_wall"],
            title + "\n" + description,
        )

    await browser.close()
    await _browser.close()
    await playwright.stop()

    return final_url