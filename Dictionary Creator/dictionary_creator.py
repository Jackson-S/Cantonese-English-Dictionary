import argparse
import sqlite3

from dataclasses import dataclass
from typing import List, Dict, Optional
from datatypes import *
from apple_dictionary_writer import AppleDictionaryWriter


def get_stats(pages):
    entries = {
        "english": 0,
        "cantonese": 0,
        "other": 0
    }

    for entry in pages:
        if isinstance(entry, CantoneseEntry):
            entries["cantonese"] += 1
        elif isinstance(entry, EnglishEntry):
            entries["english"] += 1
        else:
            entries["other"] += 1

    print(f"Created:\n{entries['cantonese']} cantonese entries\n{entries['english']} english entries\n{entries['other']} other entries")


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=str)
    parser.add_argument("-o", type=str)
    return parser.parse_args()


def create_cantonese_entries(database_path: str) -> List[CantoneseEntry]:
    db = sqlite3.connect(database_path)
    cursor = db.cursor()

    pages = {}

    entry_query = cursor.execute("SELECT id, traditional, simplified FROM Entries")
    for id, traditional, simplified in entry_query.fetchall():
        pages[id] = CantoneseEntry(id, traditional, simplified)

    definition_query = cursor.execute("SELECT id, definition FROM Definitions")
    for id, definition in definition_query.fetchall():
        pages[id].add_definition(definition)


    reading_query = cursor.execute("SELECT id, reading FROM Readings")
    for id, reading in reading_query.fetchall():
        pages[id].add_reading(reading)
    
    pages = [*filter(lambda x: x.is_worth_adding(), pages.values())]

    return pages


def create_english_pages(database_path: str) -> List[EnglishEntry]:
    db = sqlite3.connect(database_path)
    cursor = db.cursor()

    result: Dict[str, EnglishEntry] = dict()

    query = cursor.execute("SELECT * FROM EnglishTranslations")

    for en, mean, trans, translit, alt, lit, qual in query.fetchall():
        if en not in result:
            result[en] = EnglishEntry(en)
        
        result[en].add_translation(mean, trans, alt, lit, qual, translit)

    return list(result.values())


def main():
    args = get_arguments()

    # This will contain all the pages for the dictionary as they are added
    pages: Dict[str, Entry] = dict()

    pages = set([
        *create_cantonese_entries(args.database),
        *create_english_pages(args.database)
    ])

    dictionary = AppleDictionaryWriter(pages)
    dictionary.write(args.o)

    get_stats(pages)


if __name__ == "__main__":
    main()
