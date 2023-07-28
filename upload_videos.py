from pyppeteer.browser import Browser

async def vbox(browser: Browser, filepath: str, title: str = "", description: str = "", tags: str = "", private=False):
    page = await browser.newPage()

    await page.goto("https://lupload.vbox7.com/video")

    input_button = await page.querySelector("input[type=file]")
    await input_button.uploadFile(filepath)

    await page.waitForNavigation(timeout=0)

    await page.Jeval("#upload_video_name", f"el=> el.value = '{title}'")
    await page.Jeval("#vdescription", f"el=> el.value = `{description}`")
    await page.Jeval("#video_tags", f"el=> el.value = '{tags}'")

    # for testing, post the video privately
    if private:
        await page.Jeval("#privateVideo3", "el => el.checked = true")

    await page.Jeval("#cat3", "el => el.checked = true")
    await page.Jeval("#cat40", "el => el.checked = true")
    await page.Jeval("#cat33", "el => el.checked = true")

    await page.click(
        "#native > div > section > form > * > input.def-btn"
    )

    await page.waitForNavigation(timeout=0)

    try:
        # loading page
        final_url = await page.Jeval(
            "#post-data > p:nth-child(3) > a", "a => a.textContent"
        )
    except:
        # video got uploaded immediately
        final_url = page.url

    await page.close()

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
    
    await page.close()
    


async def animes_portal(browser: Browser, final_url: str, episode_num: int, animes_portal_url = ""):
    if animes_portal_url == "":
        print("LOG: Animes_Portal: No URL supplied. Returning...")
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
    await page.click("#anime > div.modal.modalOverlay.modal-smaller.visible > div > div.container.rel > div > form > div.row > input.btn.btn-primary.green")
    print("File uploaded to animes-portal")
    

async def animes_portal_wall(browser: Browser, final_url: str, animes_portal_wall_url = "", post_description: str = ""):
    if animes_portal_wall_url == "":
        print("LOG: Animes_Portal: No URL supplied. Returning...")
        return
    
    page = await browser.newPage()
    
    await page.setViewport({"width":1000, "height": 700})

    await page.goto(animes_portal_wall_url)

    await page.waitForSelector(
        "#comments > form > span > textarea"
    )
    
    post = post_description + "\n" + final_url
    
    await page.Jeval(
        "#comments > form > span > textarea",
        f"el => el.value = `{post}`")
    
    textarea = await page.J("#comments > form > span > textarea")
    await textarea.press("Enter", delay=1)
