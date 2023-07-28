# %%
# get_subtitle_file
# "ffmpeg -i "[Erai-raws] Zom 100 - Zombie ni Naru made ni Shitai 100 no Koto - 01 [1080p][HEVC][Multiple Subtitle][E5FE755A].mkv" -t 0:2 subtitle.ass"

from typing import Callable
import ass
import ass_tag_parser
import json
from html import unescape
import re
from requests import post
from itertools import chain

def parse_assline(line):
    return ass_tag_parser.parse_ass(line)


def convert_assline(_list):
    return ass_tag_parser.compose_ass(_list)

def change_roboto_to_trebuchet(styles):
    for style in styles:
        if any(x in style.fontname for x in ("Roboto", "Arial")):
            style.fontname = "Trebuchet MS"
            # style.bold = True
    return styles


def translate_subtitle_google(filepath: str, output_file: str, styling_function: Callable, path_to_secrets):
    with open(filepath) as f:
        sub = ass.parse(f)
    lines = [x.text for x in sub.events]

    # styling changes
    sub.styles = styling_function(sub.styles)

    # create the lines for the translation
    stack = []
    for line in lines:
        stack.append(re.sub(r"\{(.+?)\}", r"<\1>", line).replace(r"\N", "<c>"))
        # line = parse_assline(line)
        # stack_2 = []
        # for x in line:
        #     if not isinstance(x, ass_tag_parser.AssText):
        #         continue

        #     stack_2.append(x.text)
        # stack.append("".join(stack_2).replace(r'\N','<code>0</code>'))

    # stack = ["<br><br>".join(stack)]

    # translate
    with open(path_to_secrets) as f:
        secrets = json.load(f)
        
    from google.cloud import translate


    def translate_lines_google(
        text: list[str],
        project_id: str = "YOUR_PROJECT_ID",
        glossary_id: str = "YOUR_GLOSSARY_ID",
    ) -> translate.TranslationServiceClient:
        """Translating Text."""

        client = translate.TranslationServiceClient()

        location = "us-central1"
        parent = f"projects/{project_id}/locations/{location}"

        glossary = client.glossary_path(
            project_id, "us-central1", glossary_id  # The location of the glossary
        )

        glossary_config = translate.TranslateTextGlossaryConfig(glossary=glossary)

        # Translate text from English to French
        # Detail on supported types can be found here:
        response = client.translate_text(
            request={
                "parent": parent,
                "contents": text,
                "mime_type": "text/html",  # mime types: text/plain, text/html
                "source_language_code": "en",
                "target_language_code": "bg",
                "glossary_config": glossary_config,
            }
        )

        # Display the translation for each input text provided
        # for translation in response.translations:
        #     print(f"Translated text: {translation.translated_text}")

        return response

    translations = translate_lines_google(
        stack, secrets["project_id"], secrets["glossary_id"]
    )
    #####

    # convert back to ass file
    stack_translated = [i.translated_text for i in translations.translations]
    # stack_translated = translations.translations[0].translated_text.split("<br><br>")
    print(stack_translated)
    # stack_translated = lines
    # i = 0
    for j, line in enumerate(stack_translated):
        sub.events[j].text = re.sub(
            r"<(.+?)>", r"{\1}", unescape(line).replace("<c>", r"\N")
        )

        # fragmented = parse_assline(line)

        # flag = False
        # for x in fragmented:
        #     if flag is True:
        #         if isinstance(x, ass_tag_parser.AssText):
        #             x.text = ""
        #             continue
        #     if not isinstance(x, ass_tag_parser.AssText):
        #         continue
        #     x.text = stack_translated[j].replace("<code></code>", r'\N')
        #     flag = True
        #     i += 1

        # line = convert_assline(fragmented)

        # sub.events[j].text = line

    with open(output_file, "w", encoding="utf8") as f:
        sub.dump_file(f)
    return output_file



def translate_subtitle_deepl(input_file, output_file, style_function: Callable, path_to_secrets):
    with open(input_file, encoding="utf8") as f:
        sub = ass.parse(f)

    sub.styles = style_function(sub.styles)

    lines = [x.text for x in sub.events]
    
    # preprocessing step to avoid mistranslation of supposedly capital case
    lines = [re.sub(r'\b([A-Z]+)\b', lambda x: f"{x[1].title()}", line) for line in lines]

    stack = [
        re.sub(r"\{(.+?)\}", r"<\1>", line).replace(r"\N", "<c>") for line in lines
    ]

    batchsize = 32
    stack = ["<z>".join(stack[i : i + batchsize]) for i in range(0, len(stack), batchsize)]


    with open(path_to_secrets) as f:
        secrets = json.load(f)

    def deepl_translate(text: list[str], deepl_auth_key):
        body = {
            "text": text,
            "source_lang": "EN",
            "target_lang": "BG",
            "preserve_formatting": True,
            "non_splitting_tags": [
                "code",
                "c",
                "i",
                "an",
                "b",
                "an2",
                "an8",
                "z",
            ],
            "tag_handling": "xml",
            "outline_detection": False,
            "split_sentences": "nonewlines",
        }
        response = post(
            "https://api-free.deepl.com/v2/translate",
            json=body,
            headers={
                "Authorization": f"DeepL-Auth-Key {deepl_auth_key}",
                "Content-Type": "application/json",
            },
        )
        # print(response)
        if response.status_code != 200:
            raise Exception("Translation unsuccessful")
        # print(response.json())

        return response.json()

    deepl_auth_key = secrets["deepl_auth_key"]
    translated = deepl_translate(stack, deepl_auth_key)
    
    # processing step to transpose the rogue commas
    stack =  "stacc".join([i["text"] for i in translated["translations"]])
    stack = re.sub(r'\s*(<z>|<c>)\s*([,.;:])', r'\2\1', stack)
    stack = stack.split("stacc")
    ##############


    stack = [
        re.sub(r"<(.+?)>", r"{\1}", j.replace("<c>", r"\N"))
        for j in chain.from_iterable([i.split("<z>") for i in stack])
    ]

    for i, line in enumerate(stack):
        sub.events[i].text = line

    with open(output_file, "w",encoding="utf8") as f:
        sub.dump_file(f)
    
    return output_file

if __name__ == "__main__":
    translate_subtitle_google(
        r"C:\Users\matey\Videos\Content\SukinaKo\[SubsPlease] Suki na Ko ga Megane wo Wasureta - 03 (1080p) [BFE26D78].ass", 
        change_roboto_to_trebuchet,   
        r"C:\MEGA\Subtitles\[Scripts]\mtl_agent\secrets.json")
    pass
