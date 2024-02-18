"""Deprecated"""

from .base import BaseProvider
from playwright.async_api import BrowserContext


class Vbox7(BaseProvider):
    def __init__(self, browser: BrowserContext, **config):
        super().__init__(config)
        self.browser = browser
        self.video_link = None

    async def upload(self,filepath: str,
    title: str = "",
    description: str = "",
    tags: str = "",
    private=False,
    ):
        # navigate
        page = await self.browser.new_page()
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
            
        self.video_link = final_url
        return final_url

    def get_cookies(self, config: dict) -> list[dict]:
        return [
            {
                "name": "vbox7remember",
                "value": config["vbox7remember"],
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
                "value": config["larabox_session"],
                "path": "/",
                "domain": ".vbox7.com",
            }
    ]
    async def get_video_url(self) -> str:
        page = await self.browser.new_page()
        await page.goto(self.video_link)

        await page.wait_for_selector("#html5player[data-src]")
        url = await page.get_attribute("#html5player", "data-src")
        url = url.replace(".mpd", "_1080.mp4")
        
        # if requests.get(url).status_code == 404:
        #     raise Exception("VBOX7: Secret link not found")

        return url

    async def change_thumbnail(self, path_to_img: str):
        
        page = await self.browser.new_page()
        await page.goto(self.video_link)

        src = await page.eval_on_selector("#html5player", "(e) => e.src")
        if not src:
            # if await page.title() != props["title"].format(episode_num):
            await page.wait_for_selector("#html5player[data-src]")

        await page.goto(f"https://www.vbox7.com/video/{self.video_link.rpartition(':')[-1]}/edit")

        input_field = await page.query_selector("#file_change_thumb")

        await input_field.set_input_files(path_to_img)

        await page.click("#native > div > div.major-col > form > * > input")
        await page.wait_for_url("**/play*")
