import asyncio
import json
from pathlib import Path
import re
import pyppeteer
from pyppeteer.browser import Browser
import logging

async def vbox(
    browser: Browser,
    filepath: str,
    title: str = "",
    description: str = "",
    tags: str = "",
    private=False,
):
    page = await browser.newPage()

    await page.goto("https://lupload.vbox7.com/video")

    input_button = await page.querySelector("input[type=file]")
    await input_button.uploadFile(filepath)

    await page.waitForNavigation(timeout=0)

    await page.Jeval("#upload_video_name", f"el=> el.value = `{title}`")
    await page.Jeval("#vdescription", f"el=> el.value = `{description}`")
    await page.Jeval("#video_tags", f"el=> el.value = `{tags}`")

    # for testing, post the video privately
    if private:
        await page.Jeval("#privateVideo3", "el => el.checked = true")

    await page.Jeval("#cat3", "el => el.checked = true")
    await page.Jeval("#cat40", "el => el.checked = true")
    await page.Jeval("#cat33", "el => el.checked = true")

    await page.click("#native > div > section > form > * > input.def-btn")

    await page.waitForNavigation(timeout=0)

    try:
        # loading page
        final_url = await page.Jeval(
            "#post-data > p:nth-child(3) > a", "a => a.textContent"
        )
    except:
        # video got uploaded immediately
        final_url = page.url

    # await page.close()

    logging.info(f"VBOX7: {title} uploaded: {final_url}")

    return final_url


async def change_vbox_thumbnail(browser: Browser, vbox_link: str, path_to_img: str):
    page = await browser.newPage()
    await page.goto(vbox_link)

    src = await page.Jeval("#html5player", "(e) => e.src")
    if src == "":
        # if await page.title() != props["title"].format(episode_num):
        await page.waitForNavigation(timeout=0)

    await page.goto(f"https://www.vbox7.com/video/{vbox_link.split(':')[-1]}/edit")

    input_field = await page.J("#file_change_thumb")

    await input_field.uploadFile(path_to_img)

    await page.click("#native > div > div.major-col > form > * > input")
    await page.waitForNavigation(timeout=0)

    logging.info("VBOX7: Thumbnail changed.")


async def animes_portal(
    browser: Browser, final_url: str, episode_num: int, animes_portal_url=""
):
    if animes_portal_url == "":
        logging.warning("AP: No URL supplied. Returning...")
        return

    page = await browser.newPage()

    await page.goto(animes_portal_url)

    await page.waitForSelector(
        "#anime > main > div > article > div.rowView-content.content > section:nth-child(3) > div.heading > span"
    )
    await page.Jeval(
        "#anime > main > div > article > div.rowView-content.content > section:nth-child(3) > div.heading > span",
        "el => el.click()",
    )

    # input the vbox7 link
    await page.waitForSelector(
        "#anime > div.modal.modalOverlay.modal-smaller.visible > div > div.container.rel > div > form > div.cl > div:nth-child(1) > input[type=text]"
    )
    await page.Jeval(
        "#anime > div.modal.modalOverlay.modal-smaller.visible > div > div.container.rel > div > form > div.cl > div:nth-child(1) > input[type=text]",
        f"el => el.value = '{final_url}'",
    )

    # input the episode no
    await page.waitForSelector(
        "#anime > div.modal.modalOverlay.modal-smaller.visible > div > div.container.rel > div > form > div.cl > div:nth-child(2) > input[type=text]"
    )
    await page.Jeval(
        "#anime > div.modal.modalOverlay.modal-smaller.visible > div > div.container.rel > div > form > div.cl > div:nth-child(2) > input[type=text]",
        f"el => el.value = '{episode_num}'",
    )

    # upload episode
    await page.click(
        "#anime > div.modal.modalOverlay.modal-smaller.visible > div > div.container.rel > div > form > div.row > input.btn.btn-primary.green"
    )
    print("File uploaded to animes-portal")

    logging.info("AP: Video Uploaded")

    # await page.close()


async def animes_portal_wall(
    browser: Browser,
    final_url: str,
    animes_portal_wall_url="",
    post_description: str = "",
):
    if animes_portal_wall_url == "":
        logging.warning("Animes_Portal: No URL supplied. Returning...")
        return

    page = await browser.newPage()

    await page.setViewport({"width": 1000, "height": 700})

    await page.goto(animes_portal_wall_url)

    await page.waitForSelector("#comments > form > span > textarea")

    post = post_description + "\n" + final_url

    await page.Jeval("#comments > form > span > textarea", f"el => el.value = `{post}`")

    textarea = await page.J("#comments > form > span > textarea")
    await textarea.press("Enter", delay=1)

    logging.info(f"AP: {final_url} uploaded to AP wall")

    # await page.close()


async def upload(file: Path, args):
    logging.info(f"Uploading... {file}")
    # spawn a browser instance
    # NOTE: Must be logged into the relevant accounts for the ones requiring CAPTCHA
    process = await asyncio.subprocess.create_subprocess_exec(
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "--remote-debugging-port=9222",
    )
    browser = await pyppeteer.connect(browserURL="http://127.0.0.1:9222")

    # NOTE: Upload properties must be in the same folder as the file
    with open(file.parent / "upload_properties.json", encoding="utf8") as f:
        props = json.load(f)
    logging.info(f"Upload Properties found with: {props}")

    # parse episode number
    episode_num = int(re.search(props["episode_parser"], file.stem)[1])
    title = props["title"].format(episode_num)
    
    final_url = args.video_url or await vbox(
            browser, file, title, props["description"], props["tags"], private=False
        )

    if args.thumb and props.get("thumbnail_path"):
        if props.get("thumbnail_font"):
            from mtl_agent.thumbnail import generate_thumbnail, default_config

            font_options = props["thumbnail_font"]
            default_config.update(font_options)
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
            title + "\n" + props["description"],
        )

    # process.kill()

    return final_url