from abc import ABC, abstractmethod
from pathlib import Path


class BaseTranslator(ABC):
    def __init__(self, secrets_path: Path, source_language: str, target_language: str):
        self.secrets_path = secrets_path
        self.source_language = source_language
        self.target_language = target_language

    @abstractmethod
    def translate(self, lines: list[str]) -> list[str]:
        """Translates a list of strings"""
        pass
