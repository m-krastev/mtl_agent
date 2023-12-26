from PIL import Image, ImageDraw, ImageFont

default_config = {
    "font_name": "Roboto-Black",
    "stroke_width": 1,
    "stroke_fill": "black",
    "text_fill": "white",
    "font_weight": 0,
    "factor": 0.25,
}

def generate_thumbnail(
    thumbnail_path: str,
    episode_num: int,
    font_name: str = "Impact",
    factor: float = 0.25,
    stroke_width: int = 10,
    stroke_fill: str = "white",
    text_fill: str = "black",
    font_weight: int = 0,
    x=0,
    y=0,
    **kwargs,
):

    with Image.open(thumbnail_path) as im:
        draw = ImageDraw.Draw(im)
        episode_num = f"{episode_num:0>2}"
        font = ImageFont.truetype(
            font_name, size=int(im.height * factor), index=font_weight
        )
        font_length = font.getlength(episode_num)
        font_ascent, font_descent = font.getmetrics()
        draw.text(
            (
                (0.95 - font_length / im.width) * im.width - x,
                (1 - (font_descent + font_ascent) / im.height) * im.height - y,
            ),
            episode_num,
            font=font,
            fill=text_fill,
            stroke_width=stroke_width,
            stroke_fill=stroke_fill,
            **kwargs,
        )

        im.save(f"{thumbnail_path[:-4]}_{episode_num}.png", "PNG")
        return im, f"{thumbnail_path[:-4]}_{episode_num}.png"
