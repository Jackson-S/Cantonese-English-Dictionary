'''
This is a modified version of https://github.com/Jackson-S/Wiktionary-Translation-Extractor that outputs only
Cantonese (yue) entries.

Takes an XML backup of English Wiktionary (all articles and pages) and outputs an
SQLite database of all translations with the schema:

CREATE TABLE EnglishTranslations (
    english TEXT NOT NULL, -- English Translation
    meaning TEXT NOT NULL, -- Any further explanation of en translation i.e. "distant to speaker and listener"
    translation TEXT NOT NULL, -- Chinese Word
    transliteration TEXT, -- Cantonese (Jyutping) transliteration of the Chinese characters
    alternate TEXT, -- Alternate forms of the word
    literal TEXT, -- Literal meaning of the translation
    qualifier TEXT -- Any extra information
)

The progress bar only offers an approximation of the time taken, based on the size of the 2019/11/20 Wiktionary dump.
Dumps can be obtained from here https://dumps.wikimedia.org/enwiktionary/

Note that wiktionary dumps are huge (>6gb of pure text) and will probably break any text editor that tries to open them.
'''

from typing import List, Optional, Dict
from collections import defaultdict
from dataclasses import dataclass

import sqlite3
import html
import sys
import os
import re


# Define the input and output database name
DATABASE_NAME = "database.db"


@dataclass
class Translation:
    language_code: str
    translation: str
    is_equivalent_term: bool = True
    gender: Optional[str] = None
    script_code: Optional[str] = None
    transliteration: Optional[str] = None
    alternate_form: Optional[str] = None
    literal_translation: Optional[str] = None
    qualifier: Optional[str] = None


@dataclass
class TranslationGroup:
    meaning: str
    translations: List[Translation]


def generate_arguments(arguments: List[str]) -> (List[str], Dict[str, str]):
    '''
    Parse arguments from the Wiktionary translation template format
    '''
    positional_arguments = list()
    keyword_arguments = dict()
    
    # Track if any positional arguments occur after keyword arguments (illegal)
    keywords = False
    
    for argument in map(html.unescape, arguments):
        if "=" in argument:
            keywords = True
            split_index = argument.index("=")
            keyword_arguments[argument[:split_index]] = argument[split_index+1:]
        elif not keywords:
            positional_arguments.append(argument)
        else:
            raise TypeError("arguments is not of correct format")

    return positional_arguments, keyword_arguments


def decode_term(arguments: List[str]) -> Translation:
    '''
    Take in an argument of format [t, jp, 日本語, ...] given by doing .split("|") 
    on the input and return a collection of outputs
    '''
    type = arguments[0]

    if type not in ["t", "t+", "t-simple", "tt", "tt+"]:
        raise TypeError("Incorrect list type")

    positional, keyword = generate_arguments(arguments[1:])

    equivalent_term = True
    
    if len(positional) < 2:
        raise TypeError("Missing required positional arguments")

    # Check to see if the given translation is a phrase, with individually linked words
    if "[[" and "]]" in positional[1]:
        equivalent_term = False
    
    positional = [*map(lambda x: x.replace("[[", "").replace("]]", ""), positional)]
    keyword = {a: b.replace("[[", "").replace("]]", "") for a, b in keyword.items()}

    result = Translation(positional[0], positional[1], equivalent_term)

    # Add gender
    if len(positional) >= 3:
        result.gender = positional[2]

    # Add keyword arguments
    if "sc" in keyword:
        result.script_code = keyword["sc"]
    if "tr" in keyword:
        result.transliteration = keyword["tr"]
    if "alt" in keyword:
        result.alternate_form = keyword["alt"]
    if "lit" in keyword:
        result.literal_translation = keyword["lit"]
    if "g" in keyword:
        result.gender = keyword["g"]

    return result


# Check for correct argument count
if len(sys.argv) < 2:
    print(f"USAGE: python3 {sys.argv[0]} INPUT_FILE.xml")
    sys.exit(1)


db = sqlite3.connect(DATABASE_NAME)
cursor = db.cursor()

readings_query = cursor.execute("SELECT traditional, simplified, reading FROM Readings NATURAL JOIN Entries")
cantonese_readings = {}
for traditional, simplified, reading in readings_query.fetchall():
    if traditional in cantonese_readings and reading not in cantonese_readings[traditional]:
        cantonese_readings[traditional].append(reading)
    elif traditional not in cantonese_readings:
        cantonese_readings[traditional] = [reading]

    if simplified in cantonese_readings and reading not in cantonese_readings[simplified]:
        cantonese_readings[simplified].append(reading)
    elif simplified not in cantonese_readings:
        cantonese_readings[simplified] = [reading]

translations = defaultdict(list)

with open(sys.argv[1]) as in_file:
    page_title = None
    recording = False
    group = None

    for line in in_file:
        if "<title>" in line:
            # Get the page title
            page_title = line.strip()[7:-8]
            # Special handling for translation pages (common for pages with many translations)
            if page_title.endswith("/translations"):
                page_title = page_title[:-13]

        elif "{{trans-top" in line:
            # Begin parsing translations and get the meaning
            recording = True
            parameters = line.strip()[:-2].split("|")
            parameters = [html.unescape(x) for x in parameters]
            meaning = ""
            if len(parameters) > 2 and parameters[1].startswith("id="):
                meaning = parameters[2]
            elif len(parameters) > 1:
                meaning = parameters[1]
            group = TranslationGroup(meaning, [])

        elif "{{trans-bottom}}" in line:
            # Finish parsing translations
            recording = False
            if group.translations:
                # Check if there was a Cantonese translation recorded for the group
                cantonese_translations = {x.translation for x in group.translations if x.language_code == "yue"}

                # If there are no Cantonese translations append as is, otherwise filter out Mandarin translations before appending
                if cantonese_translations:
                    group.translations = [x for x in group.translations if x.language_code == "yue"]
            
            translations[page_title].append(group)
        
        elif "{{trans-mid}}" in line:
            # Mid is useless to us, defines layout on Wiktionary
            pass

        elif recording:
            qualifier = None
            
            # Find all the Lua codeblocks in the line, split them and remove the enclosing {{ }}
            for codeblock in map(lambda x: x.group(0)[2:-2].split("|"), re.finditer(r"{{.*?}}", line)):
                if codeblock[0] == "qualifier" and len(codeblock) > 1:
                    # Run a join just in case the qualifier included a "|" for some reason...
                    qualifier = "|".join(codeblock[1:])
                else:
                    try:
                        new_entry = decode_term(codeblock)
                    except TypeError as e:
                        continue
                    new_entry.qualifier = qualifier
                    # Check if the new entry is Mandarin, and if so check it has a Cantonese reading
                    if new_entry.language_code == "cmn":
                        if new_entry.translation in cantonese_readings:
                            # TODO Handle entries with multiple readings
                            new_entry.transliteration = cantonese_readings[new_entry.translation][0]
                            group.translations.append(new_entry)
                    elif new_entry.language_code == "yue":
                        group.translations.append(new_entry)

cursor.execute("""
CREATE TABLE EnglishTranslations (
    english TEXT NOT NULL, -- English Translation
    meaning TEXT NOT NULL, -- Any further explanation of en translation i.e. "distant to speaker and listener"
    translation TEXT NOT NULL, -- Chinese Word
    transliteration TEXT, -- Cantonese (Jyutping) transliteration of the Chinese characters
    alternate TEXT, -- Alternate forms of the word
    literal TEXT, -- Literal meaning of the translation
    qualifier TEXT -- Any extra information
)
""")

for word, meaning_group in translations.items():
    for group in meaning_group:
        for translation in group.translations:
            parameters = (
                word,
                group.meaning,
                translation.translation,
                translation.transliteration,
                translation.alternate_form,
                translation.literal_translation,
                translation.qualifier
            )
            cursor.execute("INSERT INTO EnglishTranslations VALUES (?, ?, ?, ?, ?, ?, ?)", parameters)

cursor.close()
db.commit()
db.close()
