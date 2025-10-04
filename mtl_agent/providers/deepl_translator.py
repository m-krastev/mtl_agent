import json
import logging
from itertools import chain
from pathlib import Path

from requests import post

from .base_translator import BaseTranslator


class DeepLTranslator(BaseTranslator):
    def __init__(self, secrets_path: Path, source_language: str, target_language: str):
        super().__init__(secrets_path, source_language, target_language)
        with open(self.secrets_path) as f:
            self.secrets = json.load(f)

    def translate(self, lines: list[str]) -> list[str]:
        batchsize = 32
        stack = [
            "<z>".join(lines[i : i + batchsize])
            for i in range(0, len(lines), batchsize)
        ]

        body = {
            "text": stack,
            "source_lang": self.source_language.upper(),
            "target_lang": self.target_language.upper(),
            "preserve_formatting": True,
            "non_splitting_tags": [
                "code",
                "c",
                "2c",
                "3c",
                "4c",
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
            # "model_type": "quality_optimized",
        }
        response = post(
            "https://api-free.deepl.com/v2/translate",
            json=body,
            headers={
                "Authorization": f"DeepL-Auth-Key {self.secrets['deepl_auth_key']}",
                "Content-Type": "application/json",
            },
        )

        if response.status_code != 200:
            logging.exception(
                f"Translation failed with response {response.status_code} and data: {response.text}"
            )
            raise Exception("Translation unsuccessful")

        translated = response.json()
        return list(
            chain.from_iterable(
                i["text"].split("<z>") for i in translated["translations"]
            )
        )
