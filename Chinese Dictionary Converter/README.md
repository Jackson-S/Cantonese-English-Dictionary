# CC-CEDICT/CC-Canto Combiner

## Description
Takes CC-CEDICT and CC-Canto and combines them into a single database containing only Cantonese 
readings.

## Instructions
Files to use with this converter can be found at:
- CC-Canto & CC-Canto readings: http://cccanto.org/download.html
- CC-CEDICT: https://www.mdbg.net/chinese/dictionary?page=cc-cedict

Decompress and place them into the same directory as the script and modify line 96 (at time of writing) to reflect the actual name of the Cantonese readings file you have (or just rename the file as the line below shows).
``` python
with open("cccedict-canto-readings-150923.txt") as in_file:
```

## Output Schema
```SQL
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
```
