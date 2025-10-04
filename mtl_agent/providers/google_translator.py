import json
from pathlib import Path

from .base_translator import BaseTranslator


class GoogleTranslator(BaseTranslator):
    def __init__(self, secrets_path: Path, source_language: str, target_language: str):
        super().__init__(secrets_path, source_language, target_language)
        with open(self.secrets_path) as f:
            self.secrets = json.load(f)

    def translate(self, lines: list[str]) -> list[str]:
        from google.cloud import translate

        client = translate.TranslationServiceClient()
        location = "us-central1"
        parent = f"projects/{self.secrets['project_id']}/locations/{location}"
        glossary = client.glossary_path(
            self.secrets["project_id"],
            "us-central1",
            self.secrets["glossary_id"],
        )
        glossary_config = translate.TranslateTextGlossaryConfig(glossary=glossary)

        response = client.translate_text(
            request={
                "parent": parent,
                "contents": lines,
                "mime_type": "text/html",
                "source_language_code": self.source_language,
                "target_language_code": self.target_language,
                "glossary_config": glossary_config,
            }
        )

        return [i.translated_text for i in response.translations]
