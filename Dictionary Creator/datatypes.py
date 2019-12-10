from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class EnglishTranslation:
    translation: str
    qualifier: Optional[str] = None
    alternate_form: Optional[str] = None
    literal_meaning: Optional[str] = None
    transliteration: Optional[str] = None


@dataclass
class EnglishTranslationSense:
    meaning: str
    translations: List[EnglishTranslation]


class Entry:
    def __init__(self, page_title: str, language: str, entry_type: str):
        self.page_title: str = page_title
        self.page_id: str = "{}_{}_{}".format(language, entry_type, page_title)


class CantoneseEntry(Entry):
    def __init__(self, id: int, traditional: str, simplified: str):
        super().__init__(str(id), "yue", "dictionary")
        # Manually set the page title in parent, as otherwise it's set to the id
        self.page_title = traditional
        
        self.traditional = traditional
        self.simplified = simplified
        self.readings: List[str] = []
        self.definitions: List[str] = []

    def add_definition(self, definition: str):
        # Needed as SQLite "helpfully" makes numeric definitions int type regardless of schema
        definition = str(definition).strip()
        if definition != "" and definition not in self.definitions:
            self.definitions.append(definition)

    def add_reading(self, reading: str):
        reading = reading.strip()
        if reading != "" and reading not in self.readings:
            self.readings.append(reading)

    def is_worth_adding(self) -> bool:
        return len(self.readings) > 0 and len(self.definitions) > 0


class EnglishEntry(Entry):
    def __init__(self, root_word: str):
        super().__init__(root_word, "en", "dictionary")
        self.translations: List[EnglishTranslationSense] = []
        self._translation_guide: Dict[str, EnglishTranslationSense] = dict()

    def add_translation(self, meaning: str, translation: str, alternate: Optional[str], literal: Optional[str], qualifier: Optional[str], transliteration: Optional[str]):
        if meaning not in self._translation_guide:
            new_sense = EnglishTranslationSense(meaning, [])
            self.translations.append(new_sense)
            self._translation_guide[meaning] = new_sense
        
        new_translation = EnglishTranslation(translation, alternate, literal, qualifier, transliteration)
        self._translation_guide[meaning].translations.append(new_translation)