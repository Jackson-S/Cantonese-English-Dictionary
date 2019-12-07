"""
Takes CC-CEDICT and CC-Canto and combines them into a single database containing only Cantonese 
readings with the schema

CREATE TABLE Entries (
    id INT PRIMARY KEY,
    traditional STRING, -- Traditional character representation
    simplified STRING   -- Simplified character representation
)

CREATE TABLE Definitions (
    id INT REFERENCES Entries,
    definition STRING   -- A single definition relating to the entry at id
)

CREATE TABLE Readings (
    id INT REFERENCES Entries,
    reading STRING      -- A single Cantonese reading relating to the entry at id
)

-- Provides a combined view of all the tables
CREATE VIEW Translations AS
  SELECT id, traditional, simplified, definition, reading FROM
    Definitions
    NATURAL JOIN Readings
    NATURAL JOIN Entries;

Files to use with this converter can be found at:
CC-Canto & CC-Canto readings: http://cccanto.org/download.html
CC-CEDICT: https://www.mdbg.net/chinese/dictionary?page=cc-cedict
"""

import sqlite3

DATABASE_NAME = "database.db"

db = sqlite3.connect(DATABASE_NAME)
cursor = db.cursor()

# Prepare the Database
cursor.execute("""
CREATE TABLE Entries (
    id INT PRIMARY KEY,
    traditional STRING, -- Traditional character representation
    simplified STRING   -- Simplified character representation
)
""")

cursor.execute("""
CREATE TABLE Definitions (
    id INT REFERENCES Entries,
    definition STRING   -- A single definition relating to the entry at id
)
""")

cursor.execute("""
CREATE TABLE Readings (
    id INT REFERENCES Entries,
    reading STRING      -- A single Cantonese reading relating to the entry at id
)
""")

cursor.execute("""
CREATE VIEW Translations AS
 SELECT id, traditional, simplified, definition, reading FROM
  Definitions
  NATURAL JOIN Readings
  NATURAL JOIN Entries;
""")

# Create a map of entries and their entry id
word_mappings = {}
index_counter = 0

# Parse the CEDict file
with open("cedict_1_0_ts_utf-8_mdbg.txt") as in_file:
    for line in in_file:
        # Ignore commented out lines
        if line.startswith("#"):
            continue

        # Parse lines of the format 
        # traditional simplified [Mandarin] /def1/def2/.../defn/
        traditional, simplified = line.split(" ")[:2]
        mandarin = line[line.index("[")+1:line.index("]")]
        # Filter out cross references
        definitions = filter(lambda x: "CL:" not in x, line[line.index("/")+1:-2].split("/"))

        index_counter += 1
        word_mappings[(traditional, simplified, mandarin)] = index_counter

        cursor.execute("INSERT INTO Entries VALUES (?, ?, ?)", (index_counter, traditional, simplified))
        for definition in definitions:
            cursor.execute("INSERT INTO Definitions VALUES (?, ?)", (index_counter, definition))

with open("cccedict-canto-readings-150923.txt") as in_file:
    for line in in_file:
        # Ignore commented out lines
        if line.startswith("#"):
            continue

        # Parse lines of the format
        # traditional simplified [mandarin] {cantonese}
        traditional, simplified = line.split(" ")[:2]
        mandarin = line[line.index("[")+1:line.index("]")]
        cantonese = line[line.index("{")+1:line.index("}")]

        try:
            translation_id = word_mappings[(traditional, simplified, mandarin)]
        except KeyError:
            continue

        cursor.execute("INSERT INTO Readings VALUES (?, ?)", (translation_id, cantonese))

with open("cccanto-webdist.txt") as in_file:
    for line in in_file:
        # Ignore commented out lines
        if line.startswith("#"):
            continue

        if "#" in line:
            line = line[:line.index("#")].strip()

        # Parse lines of the format 
        # traditional simplified [Mandarin] /def1/def2/.../defn/
        traditional, simplified = line.split(" ")[:2]
        mandarin = line[line.index("[")+1:line.index("]")]
        cantonese = line[line.index("{")+1:line.index("}")]
        # Filter out cross references
        definitions = filter(lambda x: " M: " not in x, line[line.index("/")+1:-2].split("/"))
        # Remove whitespace from definitions
        definitions = map(lambda x: x.strip(), definitions)

        if (traditional, simplified, mandarin) in word_mappings:
            definition_id = word_mappings[(traditional, simplified, mandarin)]
            for definition in definitions:
                cursor.execute("INSERT INTO Definitions VALUES (?, ?)", (definition_id, definition))
        else:
            index_counter += 1
            cursor.execute("INSERT INTO Entries VALUES (?, ?, ?)", (index_counter, traditional, simplified))
            cursor.execute("INSERT INTO Readings VALUES (?, ?)", (index_counter, cantonese))
            
            for definition in definitions:
                cursor.execute("INSERT INTO Definitions VALUES (?, ?)", (index_counter, definition))


cursor.close()
db.commit()
db.close()