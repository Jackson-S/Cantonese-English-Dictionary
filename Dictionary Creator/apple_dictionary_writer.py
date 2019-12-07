import xml.etree.ElementTree as ElementTree

from typing import Set
from itertools import chain
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
        # Create the primary node
        xml_page = ElementTree.SubElement(self.root, "d:entry", {"id": page.page_id, "d:title": page.page_title})

        # Create an index for the initial character
        attribs = {"d:title": page.page_title, "d:value": page.page_title}
        ElementTree.SubElement(xml_page, "d:index", attribs)

        readings = []

        if isinstance(page, CantoneseEntry):
            readings = [x for x in page.readings]

        for reading in readings:
            attribs = {"d:yomi": reading, "d:title": page.page_title, "d:value": reading}
            ElementTree.SubElement(xml_page, "d:index", attribs)

        html_page = self.generate_page(page)

        for element in ElementTree.fromstring(html_page):
            xml_page.append(element)

    def generate_page(self, page):
        return self.templates[type(page)].render(entry=page)

    def write(self, output_location: str):
        tree = ElementTree.ElementTree(self.root)
        tree.write(output_location, "UTF-8", True)