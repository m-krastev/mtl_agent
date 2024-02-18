from playwright.async_api import BrowserContext
from .base import BaseProvider

class TubeBG(BaseProvider):
    upload_url = "https://www.tubebg.com/upload"
    def __init__(self, browser: BrowserContext, session_id: str, user: str):
        self.browser = browser
        self.session_id = session_id
        self.user = user
        
    def get_cookies(self):
        return [{
                "name": "PHPSESSID",
                "value": self.session_id,
                "path": "/",
                "domain": "www.tubebg.com"
        }]
     
    async def upload(self, file_path, title, description = "", tags = "", categories= []):
        """Uploads a video to TubeBG. """
        page = await self.browser.new_page()
        await page.goto(self.upload_url)
        
        uploader = await page.wait_for_selector("#file")
        await uploader.set_input_files(file_path)
        
        
        
        _title = await page.wait_for_selector("#title")
        await _title.fill(title)
        
        _description = await page.wait_for_selector("#description")
        await _description.fill(description)
        
        _tags = await page.wait_for_selector("#tags")
        await _tags.fill(tags)
        
        if categories:
            _categories = await page.wait_for_selector("select")
            await _categories.select_option(categories)
        
        _submit_button = await page.wait_for_selector("input[name=upload-video]")
        # Ignore any obstructions to the click
        await _submit_button.dispatch_event("click")

    async def get_secret_link(self):
        page = await self.browser.new_page()
        await page.goto(f"https://www.tubebg.com/users/{self.user}")
        
        video_url = await page.query_selector("div.music_video:nth-child(1) > div:nth-child(1) > a:nth-child(1)")
        video_url = await video_url.get_attribute("href")

        identifier = video_url.split("/")[-2]

        return "https://www.tubebg.com" + video_url, f'https://www.tubebg.com/embed/{identifier}'
