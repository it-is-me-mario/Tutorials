"""Sphinx configuration for the independently published tutorial collection."""

from datetime import datetime
import json
import os
from pathlib import Path
import re


project = "MARIO Tutorials"
copyright = f"{datetime.now().year}, MARIO contributors"
extensions = ["nbsphinx", "sphinx.ext.mathjax"]
source_suffix = {".rst": "restructuredtext"}
root_doc = "index"
catalog = json.loads((Path(__file__).parent / "site-catalog.json").read_text())
exclude_patterns = ["site-catalog.json"] + [
    f"{item['slug']}/{Path(item['notebook']).name}" for item in catalog["tutorials"]
]
nbsphinx_execute = "never"
nbsphinx_requirejs_path = ""
nbsphinx_prolog = ""
html_theme = "mario"
html_theme_path = ["_themes"]
templates_path = ["_templates"]
html_static_path = ["_static"]
html_title = "MARIO Tutorials"
html_favicon = "_static/images/mario-favicon.ico"
html_css_files = ["tutorials.css"]
html_js_files = ["external-links.js"]
html_baseurl = os.environ.get("TUTORIALS_BASE_URL", "https://it-is-me-mario.github.io/Tutorials/")
html_show_sourcelink = False
html_copy_source = False
html_permalinks_icon = "#"
html_sidebars = {"**": []}
MASTER = "https://www.marioproject.com/en/latest/"


def page_context(app, pagename, templatename, context, doctree):
    root = app.builder.get_relative_uri(pagename, "index")
    nav = [
        {"key": "get_started", "label": "Get started", "url": MASTER + "get_started/index.html", "children": [
            {"label": "Installation", "url": MASTER + "get_started/index.html"},
            {"label": "Table formats", "url": MASTER + "get_started/table_formats.html"},
            {"label": "Scenarios", "url": MASTER + "get_started/scenarios.html"},
        ]},
        {"key": "docs", "label": "Docs", "url": MASTER + "user_guide/index.html", "children": [
            {"label": "Data sources", "url": MASTER + "user_guide/parsers/index.html"},
            {"label": "Inspecting and exporting", "url": MASTER + "user_guide/inspection/index.html"},
            {"label": "Transformations", "url": MASTER + "user_guide/transformations/index.html"},
        ]},
        {"key": "explorer", "label": "Database explorer", "url": "https://explorer.marioproject.com/", "children": [
            {"label": "Classifications", "url": "https://explorer.marioproject.com/resources/data-explorer/scope.html"},
            {"label": "Compare databases", "url": "https://explorer.marioproject.com/resources/data-explorer/compare.html"},
            {"label": "Analyses", "url": "https://explorer.marioproject.com/resources/data-explorer/analyses.html"},
        ]},
        {"key": "resources", "label": "Resources", "url": root, "active": True, "children": [
            {"label": "Tutorials", "url": root, "active": True},
            {"label": "Teaching", "url": MASTER + "resources/teaching.html"},
            {"label": "Projects & Publications", "url": MASTER + "resources/projects_publications.html"},
            {"label": "Downloadable material", "url": MASTER + "resources/material.html"},
        ]},
    ]
    metadata = app.env.metadata.get(pagename, {})
    context["mario_page"] = {
        "nav": nav, "layout": "plain", "section_key": "tutorials", "group_key": "tutorials",
        "hero": {"title": context.get("title", "Tutorials"), "text": metadata.get("summary", ""), "install": False},
        "tabs": [], "sidebar": [], "local_toc": [], "home_url": MASTER,
        "github": "https://github.com/it-is-me-mario/Tutorials", "pypi": "", "install": "",
        "ai_notice": "", "closing": None, "topic_navigation": False,
        "changelog_url": MASTER + "changelog.html",
    }
    body = re.sub(r"<h1>.*?</h1>\s*", "", context.get("body", ""), count=1, flags=re.S)
    context["body"] = body.replace("<h1>", "<h2>").replace("</h1>", "</h2>")


def search_index(app, exception):
    if exception is not None:
        return
    entries = []
    for name in sorted(app.env.found_docs):
        title = app.env.titles.get(name)
        entries.append({"t": title.astext() if title else name,
                        "u": app.builder.get_target_uri(name), "s": "Tutorials", "k": "page"})
    (Path(app.outdir) / "_static/mario-nav.json").write_text(json.dumps(entries))


def setup(app):
    app.add_js_file("mario.js", defer="defer")
    app.connect("html-page-context", page_context)
    app.connect("build-finished", search_index)

