"""Sphinx configuration for the independently published tutorial collection."""

from datetime import datetime
import json
import os
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).parent / "_ext"))


project = "MARIO Tutorials"
author = "Lorenzo Rinaldi, Mohammad Amin Tahavori, Nicolo Golinucci"
copyright = f"{datetime.now().year}, {author}"
extensions = ["nbsphinx", "sphinx.ext.mathjax"]
source_suffix = {".rst": "restructuredtext"}
root_doc = "index"
catalog = json.loads((Path(__file__).parent / "site-catalog.json").read_text())
collections = catalog.get("collections", [])
collection_for = {part["tutorial"]: group for group in collections for part in group["parts"]}
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
html_css_files = ["tutorials.css", "docs-versions.css"]
html_js_files = ["external-links.js", ("docs-versions.js", {"defer": "defer"})]
html_baseurl = os.environ.get("TUTORIALS_BASE_URL", "https://it-is-me-mario.github.io/Tutorials/")
html_show_sourcelink = False
html_copy_source = False
html_permalinks_icon = "#"
html_sidebars = {"**": []}
CHANNEL = os.environ.get("TUTORIALS_CHANNEL", "latest")
MASTER = f"https://www.marioproject.com/en/{CHANNEL}/"
EXPLORER = "https://explorer.marioproject.com/" + (CHANNEL + "/" if CHANNEL != "latest" else "")


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
        {"key": "explorer", "label": "Explorer", "url": EXPLORER, "children": [
            {"label": "Classifications", "url": EXPLORER + "resources/data-explorer/scope.html"},
            {"label": "Indicators", "url": EXPLORER + "resources/data-explorer/compare.html"},
            {"label": "Analyses", "url": EXPLORER + "resources/data-explorer/analyses.html"},
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
    hero = context["mario_page"]["hero"]
    if pagename == "index":
        hero.update(title="Tutorials",
                    text="Input-output analyses with Python notebooks and source data instructions.")
    else:
        tutorial = next((item for item in catalog["tutorials"]
                         if pagename.startswith(item["slug"] + "/")), None)
        group = next((item for item in collections if pagename == item["slug"] + "/index"), None)
        if tutorial or group:
            entry = group or tutorial
            context["title"] = entry["title"]
            hero["title"] = entry["title"]
            hero["partner"] = entry.get("partner")
            hero["breadcrumb"] = {"label": "All tutorials", "url": root}
            if group:
                hero["actions"] = []
            elif pagename.endswith("/index"):
                hero["actions"] = [{"label": "Open the notebook", "url": "notebook.html"}]
            else:
                parent = collection_for.get(tutorial["slug"], tutorial)
                hero["actions"] = [{"label": "Tutorial overview", "url": app.builder.get_relative_uri(pagename, parent["slug"] + "/index")}]
    site_root = os.environ.get("TUTORIALS_SITE_ROOT", html_baseurl).rstrip("/") + "/"
    revision = os.environ.get("TUTORIALS_SOURCE_COMMIT", "")
    context["mario_versions"] = {
        "current": CHANNEL, "label": {"latest": "Latest", "dev": "Dev", "preview": "Preview"}[CHANNEL],
        "document": pagename,
        "catalogue": root.removesuffix("index.html") + "_static/docs-versions.json",
        "revision": revision[:7],
        "source_url": "https://github.com/it-is-me-mario/Tutorials/tree/" + revision,
        "choices": [
            {"key": "latest", "label": "Latest", "url": site_root},
            {"key": "dev", "label": "Dev", "url": site_root + "dev/"},
            {"key": "preview", "label": "Preview", "url": site_root + "preview/"},
        ],
    }
    body = re.sub(r"<h1>.*?</h1>\s*", "", context.get("body", ""), count=1, flags=re.S)
    context["body"] = body.replace("<h1>", "<h2>").replace("</h1>", "</h2>")


def search_index(app, exception):
    if exception is not None:
        return
    entries = []
    for name in sorted(app.env.found_docs):
        title = app.env.titles.get(name)
        tutorial = next((item for item in catalog["tutorials"] if name.startswith(item["slug"] + "/")), None)
        group = next((item for item in collections if name == item["slug"] + "/index"), None)
        if tutorial and tutorial["slug"] in collection_for and name.endswith("/index") and not group:
            continue
        tutorial = group or tutorial
        label = tutorial["title"] + (" — Notebook" if name.endswith("/notebook") else "") if tutorial else \
            title.astext() if title else name
        entries.append({"t": label,
                        "u": app.builder.get_target_uri(name), "s": "Tutorials", "k": "page"})
    (Path(app.outdir) / "_static/mario-nav.json").write_text(json.dumps(entries))


def setup(app):
    # Reuse only the shared presentation components, without MARIO's site routing.
    import mario_site as components
    for name, directive in (("mario-cards", components.MarioCards),
                            ("mario-card", components.MarioCard),
                            ("mario-steps", components.MarioSteps),
                            ("mario-step", components.MarioStep),
                            ("mario-details", components.MarioDetails)):
        app.add_directive(name, directive)
    app.add_node(components.guide_details,
                 html=(components._visit_guide_details, components._depart_guide_details))
    app.add_js_file("mario.js", defer="defer")
    app.connect("html-page-context", page_context)
    app.connect("build-finished", search_index)

