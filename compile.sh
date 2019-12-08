#! /usr/bin/env bash

# Remove old directories if they exist
rm -rf build

echo "1. Have you have installed the necessary packages in pip3?"
echo "2. Have you placed all the input files in the necessary locations?"

cd "Chinese Dictionary Converter"
rm database.db

echo "Converting CCEDICT and CC-Canto to database..."
python3 cantonese_cedict_combiner.py
echo "Done"

# Move the database file into the Wiktionary converter
cd ..
mv "Chinese Dictionary Converter/database.db" "Wiktionary Converter/database.db"
cd "Wiktionary Converter"

echo "Converting Wiktionary pages. Hold tight (~3-5 minutes)..."
python3 wiktionary_translation_extractor.py enwiktionary-20191120-pages-articles.xml
echo "Done"

cd ..
mv "Wiktionary Converter/database.db" "Dictionary Creator/database.db"
cd "Dictionary Creator"

echo "Generating Apple Dictionary app XML..."
python3 dictionary_creator.py database.db -o CantoneseDictionary.xml
echo "Done"

cd ..
echo "Setting up build directory"
mkdir build
mkdir build/OtherResources
mkdir build/OtherResources/Images
mv "Dictionary Creator/CantoneseDictionary.xml" build/CantoneseDictionary.xml
cp "Dictionary Creator/assets/Makefile" build/Makefile
cp "Dictionary Creator/assets/info.plist" build/CantoneseDictionary.plist
cp "Dictionary Creator/assets/style.css" build/CantoneseDictionary.css
cp "Dictionary Creator/assets/prefs.html" build/OtherResources/CantoneseDictionary_prefs.html
echo "Done"

cd build

# Compress the dictionary down, removing all spaces in the file (Reduces final compiled size)
xmllint CantoneseDictionary.xml --noblanks > compressed.xml
mv compressed.xml CantoneseDictionary.xml

make
make install
