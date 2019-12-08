import xml.etree.ElementTree as ElementTree

from typing import Set
from jinja2 import Environment, FileSystemLoader, select_autoescape
from datatypes import *


class AppleDictionaryWriter:
    def __init__(self, pages: Set[Entry]):
        dict_entries = filter(lambda x: isinstance(x, CantoneseEntry), pages)
        self.full_entries = set(map(lambda x: x.page_title, dict_entries))

        self.root: ElementTree.Element = ElementTree.Element(
            "d:dictionary",
            {
                "xmlns": "http://www.w3.org/1999/xhtml",
                "xmlns:d": "http://www.apple.com/DTDs/DictionaryService-1.0.rng"
            }
        )

        self.environment = Environment(
            loader=FileSystemLoader("assets"),
            autoescape=select_autoescape(enabled_extensions=('html', 'xml'), default_for_string=True)
        )

        self.templates = {
            CantoneseEntry: self.environment.get_template("cantonese_entry.html"),
            EnglishEntry: self.environment.get_template("english_entry.html")
        }

        for page in pages:
            self.generate_entry(page)

    def generate_entry(self, page: Entry):
        entry_node = None

        if isinstance(page, CantoneseEntry):
            entry_node = ElementTree.SubElement(self.root, "d:entry", {"id": page.page_id, "d:title": page.traditional})

            ElementTree.SubElement(entry_node, "d:index", {"d:title": page.traditional, "d:value": page.traditional})
            # Add an index for the simplified character variant if there is one
            if page.traditional != page.simplified:
                ElementTree.SubElement(entry_node, "d:index", {"d:title": page.traditional, "d:value": page.simplified})

            # Add readings
            for reading in page.readings:
                ElementTree.SubElement(entry_node, "d:index", {"d:yomi": reading, "d:title": page.traditional, "d:value": reading})

        elif isinstance(page, EnglishEntry):
            entry_node = ElementTree.SubElement(self.root, "d:entry", {"id": page.page_id, "d:title": page.page_title})
            ElementTree.SubElement(entry_node, "d:index", {"d:title": page.page_title, "d:value": page.page_title})

        # Create the page body using Jinja2
        entry_html = self.templates[type(page)].render(entry=page)

        # Append all page body elements onto the entry XML node
        for element in ElementTree.fromstring(entry_html):
            entry_node.append(element)

    def write(self, output_location: str):
        tree = ElementTree.ElementTree(self.root)
        tree.write(output_location, "UTF-8", True)
