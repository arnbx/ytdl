import os
import re
import unittest
from html.parser import HTMLParser

class IDCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.duplicates = []
        self.css_links = []
        self.js_scripts = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if "id" in attr_dict:
            id_val = attr_dict["id"]
            if id_val in self.ids:
                self.duplicates.append(id_val)
            else:
                self.ids.append(id_val)
        if tag == "link" and attr_dict.get("rel") == "stylesheet":
            self.css_links.append(attr_dict.get("href", ""))
        if tag == "script" and attr_dict.get("src"):
            self.js_scripts.append(attr_dict.get("src", ""))

class TestHtmlDomValidation(unittest.TestCase):
    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.html_path = os.path.join(self.root_dir, "src", "web", "index.html")
        self.css_dir = os.path.join(self.root_dir, "src", "web", "css")
        self.js_dir = os.path.join(self.root_dir, "src", "web", "js")

    def test_01_html_exists_and_parses(self):
        self.assertTrue(os.path.exists(self.html_path), "index.html does not exist!")
        with open(self.html_path, "r", encoding="utf-8") as f:
            content = f.read()
        parser = IDCollector()
        parser.feed(content)
        self.assertEqual(len(parser.duplicates), 0, f"Duplicate IDs found in index.html: {parser.duplicates}")

    def test_02_css_links_exist(self):
        with open(self.html_path, "r", encoding="utf-8") as f:
            content = f.read()
        parser = IDCollector()
        parser.feed(content)
        for link in parser.css_links:
            if link.startswith("http://") or link.startswith("https://") or link.startswith("//"):
                continue
            clean_link = link.split("?")[0]
            full_path = os.path.join(self.root_dir, "src", "web", clean_link)
            self.assertTrue(os.path.exists(full_path), f"Linked CSS file missing: {link}")

    def test_03_js_scripts_exist(self):
        with open(self.html_path, "r", encoding="utf-8") as f:
            content = f.read()
        parser = IDCollector()
        parser.feed(content)
        for script in parser.js_scripts:
            clean_script = script.split("?")[0]
            full_path = os.path.join(self.root_dir, "src", "web", clean_script)
            self.assertTrue(os.path.exists(full_path), f"Linked JS script missing: {script}")

    def test_04_js_dom_ids_present_in_html(self):
        with open(self.html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        parser = IDCollector()
        parser.feed(html_content)
        html_ids = set(parser.ids)

        # Dynamic IDs created or checked in JS that are not static in HTML
        dynamic_or_optional_ids = {
            "btn-remove-tier",
            "chk-sel-0",
            "chk-sel-1",
            "group-card-0"
        }

        for root, dirs, files in os.walk(self.js_dir):
            for file in files:
                if file.endswith(".js"):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        js_content = f.read()
                    matches = re.findall(r'document\.getElementById\(\s*["\']([^"\']+)["\']\s*\)', js_content)
                    for dom_id in matches:
                        if dom_id not in dynamic_or_optional_ids and not dom_id.startswith("chk-sel-"):
                            self.assertIn(
                                dom_id,
                                html_ids,
                                f"DOM ID '{dom_id}' referenced in {file} was not found in index.html!"
                            )

if __name__ == "__main__":
    unittest.main()
