"""SEO, GitHub, and AI-discovery contract tests."""

from html.parser import HTMLParser
from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CANONICAL = "https://openglaze.com"
SEO_PAGES = [
    "ceramic-glaze-calculator.html",
    "umf-calculator.html",
    "glaze-recipe-calculator.html",
    "cte-glaze-calculator.html",
    "glazy-alternative.html",
    "digitalfire-companion.html",
    "open-source-pottery-software.html",
    "self-hosted-glaze-software.html",
]


class HeadParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self._in_title = False
        self.meta = {}
        self.links = {}
        self.json_ld = []
        self._script_type = None
        self._script_chunks = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            key = attrs.get("name") or attrs.get("property")
            if key:
                self.meta[key] = attrs.get("content", "")
        if tag == "link" and attrs.get("rel"):
            self.links[attrs["rel"]] = attrs.get("href", "")
        if tag == "script":
            self._script_type = attrs.get("type")
            self._script_chunks = []

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._script_type == "application/ld+json":
            self._script_chunks.append(data)

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag == "script" and self._script_type == "application/ld+json":
            self.json_ld.append("".join(self._script_chunks).strip())
            self._script_type = None
            self._script_chunks = []


def parse_html(path: Path) -> HeadParser:
    parser = HeadParser()
    parser.feed(path.read_text())
    return parser


def test_seo_landing_pages_have_indexable_metadata_and_schema():
    for page in SEO_PAGES:
        path = DOCS / page
        assert path.exists(), f"missing {page}"
        html = path.read_text()
        parsed = parse_html(path)

        assert "<h1" in html
        assert "OpenGlaze" in html
        assert "github.com/Pastorsimon1798/openglaze" in html
        assert parsed.title and len(parsed.title) <= 70
        assert 120 <= len(parsed.meta.get("description", "")) <= 170
        assert parsed.links.get("canonical") == f"{CANONICAL}/{page}"
        assert parsed.meta.get("og:title")
        assert parsed.meta.get("twitter:card") == "summary_large_image"
        assert parsed.json_ld, f"missing JSON-LD in {page}"
        for blob in parsed.json_ld:
            json.loads(blob)


def test_homepage_links_to_all_search_intent_pages():
    homepage = (DOCS / "index.html").read_text()
    for page in SEO_PAGES:
        assert page in homepage


def test_sitemap_lists_all_discovery_pages_with_current_lastmod():
    xml = ET.parse(DOCS / "sitemap.xml")
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    entries = {
        loc.text: lastmod.text
        for loc, lastmod in [
            (url.find("sm:loc", ns), url.find("sm:lastmod", ns))
            for url in xml.findall("sm:url", ns)
        ]
    }
    for page in SEO_PAGES:
        assert entries[f"{CANONICAL}/{page}"] == "2026-04-26"


def test_ai_files_are_truthful_and_answer_engine_ready():
    ai = (DOCS / "ai.txt").read_text()
    llms = (DOCS / "llms.txt").read_text()
    llms_full = (DOCS / "llms-full.txt").read_text()

    for content in (ai, llms, llms_full):
        assert "126 automated tests" in content
        assert "PostgreSQL" not in content or "experimental" in content
        assert "SQLite or PostgreSQL" not in content
        assert "ceramic glaze calculator" in content.lower()
        assert "https://github.com/Pastorsimon1798/openglaze" in content

    assert "## Answer Snippets" in llms_full
    assert "What is OpenGlaze?" in llms_full


def test_repository_growth_metadata_exists():
    citation = ROOT / "CITATION.cff"
    dependabot = ROOT / ".github/dependabot.yml"
    social_svg = DOCS / "social-preview.svg"
    social_png = DOCS / "social-preview.png"

    assert citation.exists()
    assert "title: OpenGlaze" in citation.read_text()
    assert dependabot.exists()
    assert "pip" in dependabot.read_text()
    assert social_svg.exists()
    assert re.search(r"<svg[^>]+viewBox=\"0 0 1280 640\"", social_svg.read_text())
    assert social_png.exists()
    assert social_png.stat().st_size < 1_000_000
