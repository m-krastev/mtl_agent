import logging
from .base import BaseProvider
from playwright.async_api import BrowserContext

class AnimesPortal(BaseProvider):
    def __init__(self, browser: BrowserContext, config):
        self.browser = browser
        self.config = config
        self.video_link = None
    
    def get_cookies(self):
        return [
            {
                "name": "ukey",
                "value": self.config["ukey"],
                "path": "/",
                "domain": "animes-portal.info",
            },
        ]
            
    async def upload(self, final_url: str, episode_num: int, animes_portal_url: str):

        final_url = f'<iframe src="{final_url}" frameborder="0" allowfullscreen></iframe>'
        page = await self.browser.new_page()
        await page.goto(animes_portal_url)

        add_button = await page.wait_for_selector(
            "#anime > main > div > article > div.rowView-content.content > section:nth-child(3) > div.heading > span"
        )
        await add_button.click()

        # input the vbox7 link
        embed_field = await page.wait_for_selector('textarea[name="players[]"]')
        await embed_field.fill(final_url)

        # input the episode no
        num_field = await page.wait_for_selector("input[name=number]")
        await num_field.fill(str(episode_num))

        # upload episode
        submit = await page.wait_for_selector(
            "#anime > div.modal.modalOverlay.modal-smaller.visible > div > div.container.rel > div > form > div.row > input.btn.btn-primary.green"
        )
        submit.click()
        logging.info("AP: Video Uploaded")



    async def upload_to_wall(
        self,
        final_url: str,
        animes_portal_wall_url="",
        post_description: str = "",
    ):
        post = post_description + "\n" + final_url

        if not animes_portal_wall_url:
            logging.warning("Animes_Portal_Wall: No URL supplied. Returning...")
            return

        page = await self.browser.new_page()
        await page.goto(animes_portal_wall_url, timeout=0, wait_until="domcontentloaded")

        await page.wait_for_selector("#comments > form > span > textarea")
        await page.eval_on_selector(
            "#comments > form > span > textarea", f"el => el.value = `{post}`"
        )

        textarea = await page.query_selector("#comments > form > span > textarea")
        await textarea.press("Enter", delay=1)

        logging.info(f"AP: {final_url} uploaded to AP wall")