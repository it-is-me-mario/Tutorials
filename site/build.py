"""Publish tutorials from their canonical repositories at recorded commits."""

from __future__ import annotations

import argparse
import hashlib
from html import escape
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import shutil
import subprocess
import sys
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

import nbformat


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
CACHE = ROOT / ".site-cache"
REPOSITORY = "it-is-me-mario/Tutorials"
DEFAULT_URL = "https://it-is-me-mario.github.io/Tutorials/"
SHA = re.compile(r"[0-9a-f]{40}")
THEME_PREFIX = "doc/source/_themes/mario/"
THEME_ASSETS = (
    "doc/source/_static/images/mario-logo.png",
    "doc/source/_static/images/mario-favicon.ico",
    "doc/source/_static/images/heatmap-background.png",
    "doc/source/_static/images/heatmap-background-dark.png",
    "doc/source/_static/external-links.js",
    "doc/source/_static/docs-versions.js",
    "doc/source/_static/docs-versions.css",
    "doc/source/_ext/mario_site.py",
)


def request_bytes(url):
    """Read public GitHub resources, using the CI token only for its API."""
    headers = {"User-Agent": "MARIO-Tutorials-site"}
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(url, headers=headers), timeout=60) as response:
        return response.read()


def github_json(path):
    return json.loads(request_bytes("https://api.github.com/" + path))


def source_path(value):
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"Invalid source path {value!r}")
    return path


def repository_source(repository, revision, filename):
    """Read committed local objects when available, then the immutable public source."""
    source_path(filename)
    if repository == REPOSITORY:
        try:
            return subprocess.check_output(
                ["git", "show", f"{revision}:{filename}"], cwd=ROOT, stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            pass
    return cached_source(repository, revision, filename)


def load_catalog(revision=None):
    payload = repository_source(REPOSITORY, revision, "site/catalog.json") if revision else \
        (SITE / "catalog.json").read_bytes()
    catalog = json.loads(payload)
    slugs = set()
    for tutorial in catalog["tutorials"]:
        slug = tutorial["slug"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) or slug in slugs:
            raise ValueError(f"Invalid or repeated tutorial slug {slug!r}")
        slugs.add(slug)
        for name in [tutorial["notebook"], *tutorial.get("materials", ())]:
            source_path(name)
        if tutorial.get("guide"):
            source_path(tutorial["guide"])
        if tutorial.get("guide_includes_downloads") and not tutorial.get("guide"):
            raise ValueError("A guide with download links requires a guide source")
        basenames = [source_path(name).name for name in [tutorial["notebook"], *tutorial.get("materials", ())]]
        if len(basenames) != len(set(basenames)) or "notebook.ipynb" in basenames:
            raise ValueError(f"Tutorial {slug!r} has conflicting download names")
        if tutorial["repository"] != REPOSITORY and not tutorial.get("ref"):
            raise ValueError(f"External tutorial {slug!r} needs a source ref")
    grouped = set()
    group_slugs = set()
    for group in catalog.get("collections", []):
        slug = group["slug"]
        members = [part["tutorial"] for part in group["parts"]]
        anchors = [part["anchor"] for part in group["parts"]]
        if (not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug)
                or slug in group_slugs or (slug in slugs and slug not in members)
                or len(members) < 2 or len(set(members)) != len(members)
                or len(set(anchors)) != len(anchors)
                or any(not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", a) for a in anchors)
                or any(member not in slugs or member in grouped for member in members)):
            raise ValueError(f"Invalid tutorial collection {slug!r}")
        group_slugs.add(slug)
        grouped.update(members)
    occupied = slugs | group_slugs | {"dev", "preview"}
    for tutorial in catalog["tutorials"]:
        aliases = tutorial.get("aliases", [])
        if not isinstance(aliases, list):
            raise ValueError("Tutorial aliases must be a list of former slugs")
        for alias in aliases:
            if (not isinstance(alias, str)
                    or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", alias)
                    or alias in occupied):
                raise ValueError(f"Invalid or conflicting tutorial alias {alias!r}")
            occupied.add(alias)
    if not SHA.fullmatch(catalog["theme"]["revision"]):
        raise ValueError("The shared theme must use a full commit SHA")
    return catalog


def catalog_entries(catalog):
    """Show each learning workflow once, retaining its independently sourced parts."""
    groups = {part["tutorial"]: group for group in catalog.get("collections", [])
              for part in group["parts"]}
    seen = set()
    for tutorial in catalog["tutorials"]:
        entry = groups.get(tutorial["slug"], tutorial)
        if entry["slug"] not in seen:
            seen.add(entry["slug"])
            yield entry


def tutorial_redirects(catalog):
    """Map former overview and companion URLs to their canonical documents."""
    return {f"{alias}/{page}": f"{tutorial['slug']}/{page}"
            for tutorial in catalog["tutorials"]
            for alias in tutorial.get("aliases", [])
            for page in ("index", "notebook")}


def tutorial_redirect_anchors(catalog):
    return {f"{alias}/{page}": anchors
            for tutorial in catalog["tutorials"]
            for alias in tutorial.get("aliases", [])
            for page, anchors in tutorial.get("anchor_aliases", {}).items()}


def resolve_sources(catalog, revision=None, external_cache=None):
    revision = revision or subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
    ).strip()
    revisions = {}
    cache = {} if external_cache is None else external_cache
    for tutorial in catalog["tutorials"]:
        repository = tutorial["repository"]
        if repository == REPOSITORY:
            continue
        key = f"{repository}@{tutorial['ref']}"
        if key not in revisions:
            ref = quote(tutorial["ref"], safe="")
            if key not in cache:
                cache[key] = github_json(f"repos/{repository}/commits/{ref}")["sha"]
            revisions[key] = cache[key]
    return {
        "site_commit": revision,
        "theme": catalog["theme"],
        "external_sources": revisions,
    }


def cached_source(repository, revision, filename):
    path = CACHE / repository / revision / source_path(filename)
    if not path.is_file():
        url = f"https://raw.githubusercontent.com/{repository}/{revision}/{quote(filename)}"
        payload = request_bytes(url)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    return path.read_bytes()


def prepare_theme(catalog, destination):
    theme = catalog["theme"]
    repository, revision = theme["repository"], theme["revision"]
    tree_path = CACHE / repository / revision / "theme-tree.json"
    if not tree_path.is_file():
        tree = github_json(f"repos/{repository}/git/trees/{revision}?recursive=1")
        if tree.get("truncated"):
            raise ValueError("The shared-theme source tree is incomplete")
        tree_path.parent.mkdir(parents=True, exist_ok=True)
        tree_path.write_text(json.dumps(tree))
    tree = json.loads(tree_path.read_text())
    names = [entry["path"] for entry in tree["tree"]
             if entry["type"] == "blob" and entry["path"].startswith(THEME_PREFIX)]
    if not any(name.endswith("/theme.toml") for name in names):
        raise ValueError("The shared-theme source has no theme.toml")
    logo_assets = [
        "doc/source/_static/images/logos/" + source_path(database["logo"]).as_posix()
        for database in catalog.get("databases", {}).values() if database.get("logo")
    ]
    if logo_assets:
        logo_assets.append("doc/source/_static/images/logos/CREDITS.md")
    for name in [*names, *THEME_ASSETS, *logo_assets]:
        payload = cached_source(repository, revision, name)
        target = destination / name.removeprefix("doc/source/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)


def clean_notebook(payload, provenance):
    """Retain all source cells and remove stored results from published copies."""
    raw = json.loads(payload)
    for position, cell in enumerate(raw["cells"]):
        cell.setdefault("id", f"source-{position + 1}")
    raw["nbformat_minor"] = max(raw.get("nbformat_minor", 0), 5)
    notebook = nbformat.from_dict(raw)
    for cell in notebook.cells:
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None
        cell.metadata = {}
    notebook.metadata.pop("widgets", None)
    notebook.metadata["mario_tutorial_source"] = provenance
    nbformat.validate(notebook)
    return nbformat.writes(notebook).encode("utf-8")


def mario_source_target(source, address):
    """Resolve a relative documentation target inside its committed source tree."""
    path = PurePosixPath(posixpath.normpath(str(PurePosixPath(source).parent / address)))
    if not path.is_relative_to("doc/source"):
        raise ValueError(f"Documentation link leaves its source root: {address!r}")
    return path


def mario_web_link(source, address):
    parsed = urlsplit(address)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return address
    target = mario_source_target(source, parsed.path).relative_to("doc/source")
    if target.suffix in {".rst", ".ipynb"}:
        target = target.with_suffix(".html")
    elif not target.suffix:
        target = target.with_suffix(".html")
    return ("https://www.marioproject.com/en/latest/" + quote(target.as_posix())
            + ("?" + parsed.query if parsed.query else "")
            + ("#" + parsed.fragment if parsed.fragment else ""))


def rst_document_body(text):
    """Separate a full RST page's metadata/title from its reusable explanation."""
    match = re.search(r"^([^\n]+)\n[=]{3,}\s*\n", text, re.M)
    if not match:
        raise ValueError("Expected a titled MARIO RST guide")
    return match.group(1).strip(), text[match.end():].lstrip()


def prepare_mario_explanation(tutorial, revision, folder, guide, notebook):
    """Relocate presentation links and figures without changing downloadable cells."""
    repository = tutorial["repository"]
    assets = {}

    def image_link(source, address):
        parsed = urlsplit(address)
        if parsed.scheme or parsed.netloc:
            return address
        target = mario_source_target(source, parsed.path).as_posix()
        relative = "assets/" + PurePosixPath(target).name
        payload = repository_source(repository, revision, target)
        path = folder / relative
        path.parent.mkdir(exist_ok=True)
        if path.exists() and path.read_bytes() != payload:
            raise ValueError(f"Conflicting tutorial image basename: {relative}")
        path.write_bytes(payload)
        assets[target] = {"sha256": hashlib.sha256(payload).hexdigest(), "path": relative}
        return relative

    def doc_link(match):
        value = match.group(1)
        named = re.fullmatch(r"(.+?)\s*<([^>]+)>", value)
        label, address = named.groups() if named else (None, value)
        if label is None:
            path = mario_source_target(tutorial["guide"], urlsplit(address).path).with_suffix(".rst")
            label, _ = rst_document_body(repository_source(repository, revision, path.as_posix()).decode())
        return f"`{label} <{mario_web_link(tutorial['guide'], address)}>`_"

    _, body = rst_document_body(guide.decode())
    body = re.sub(r":doc:`([^`]+)`", doc_link, body)
    body = re.sub(r"(?m)^([ \t]*\.\. (?:figure|image)::[ \t]+)(\S+)[ \t]*$",
                  lambda m: m[1] + image_link(tutorial["guide"], m[2]), body)
    rendered = nbformat.reads(notebook.decode(), as_version=4)
    for cell in rendered.cells:
        if cell.cell_type != "markdown":
            continue
        def markdown_link(match):
            prefix, address = match[1], match[2]
            link = image_link(tutorial["notebook"], address) if prefix.startswith("!") else \
                mario_web_link(tutorial["notebook"], address)
            return prefix + link + ")"
        cell.source = re.sub(r"(!?\[[^\]]*\]\()([^\s)]+)\)", markdown_link, cell.source)
    return body.encode(), nbformat.writes(rendered).encode(), assets


def prepare_tutorial(tutorial, revisions, destination):
    repository = tutorial["repository"]
    revision = revisions["site_commit"] if repository == REPOSITORY else \
        revisions["external_sources"][f"{repository}@{tutorial['ref']}"]
    folder = destination / tutorial["slug"]
    folder.mkdir(parents=True)
    files = {}
    provenance = {"repository": repository, "commit": revision, "path": tutorial["notebook"]}
    names = [tutorial["notebook"], *tutorial.get("materials", ())]
    for name in names:
        payload = repository_source(repository, revision, name)
        files[name] = {"sha256": hashlib.sha256(payload).hexdigest()}
        target = folder / source_path(name).name
        target.write_bytes(clean_notebook(payload, provenance) if name == tutorial["notebook"] else payload)
        files[name]["download_sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
    # nbsphinx reads this generated copy. The downloadable companion keeps its source filename.
    notebook_name = source_path(tutorial["notebook"]).name
    shutil.copyfile(folder / notebook_name, folder / "notebook.ipynb")
    source_url = f"https://github.com/{repository}/tree/{revision}"
    lines = [
        ":page-type: Tutorial", f":summary: {tutorial['summary']}", "",
        tutorial["title"], "=" * len(tutorial["title"]), "",
    ]
    if tutorial.get("intro"):
        lines.extend([tutorial["intro"], ""])
    guide_record = {}
    if tutorial.get("guide"):
        name = tutorial["guide"]
        payload = repository_source(repository, revision, name)
        explanation = payload
        if tutorial.get("source_format") == "mario":
            explanation, rendered, assets = prepare_mario_explanation(
                tutorial, revision, folder, payload,
                (folder / notebook_name).read_bytes(),
            )
            (folder / "notebook.ipynb").write_bytes(rendered)
            guide_record["assets"] = assets
        (folder / "overview.rst.inc").write_bytes(explanation)
        lines.extend([".. include:: overview.rst.inc", ""])
        guide_record["guide"] = {"path": name, "sha256": hashlib.sha256(payload).hexdigest()}
    lines.extend([
        f"`Source and revision <{source_url}>`__.", "",
    ])
    if not tutorial.get("guide_includes_downloads"):
        lines.extend([
            "Run the tutorial", "----------------", "",
            "Download the notebook and its supporting files into one working folder.",
            "The notebook specifies the environment and source data.",
            "", f"* :download:`Notebook <{notebook_name}>`",
        ])
        for name in tutorial.get("materials", ()):
            basename = source_path(name).name
            lines.append(f"* :download:`{basename} <{basename}>`")
    if tutorial.get("instructions"):
        path = quote(tutorial["instructions"])
        instructions = f"https://github.com/{repository}/blob/{revision}/{path}"
        lines.extend(["", f"`Repository instructions <{instructions}>`_ supply the original setup notes."])
    lines.extend(["", ".. toctree::", "   :maxdepth: 2", "   :hidden:"])
    lines.extend(["", "   Notebook <notebook>", ""])
    (folder / "index.rst").write_text("\n".join(lines))
    return {**provenance, "files": files, **guide_record}


def prepare_collection(group, catalog, destination):
    """Combine explanations on one page without copying or editing source notebooks."""
    tutorials = {item["slug"]: item for item in catalog["tutorials"]}
    folder = destination / group["slug"]
    folder.mkdir(exist_ok=True)
    lines = [":page-type: Tutorial", f":summary: {group['summary']}", "",
             group["title"], "=" * len(group["title"]), "", group["intro"], ""]
    parts = []
    for part in group["parts"]:
        slug = part["tutorial"]
        tutorial = tutorials[slug]
        _, body = rst_document_body((destination / slug / "index.rst").read_text())
        body = body.split(".. toctree::", 1)[0]
        include = destination / slug / "overview.rst.inc"
        if include.exists():
            body = body.replace(".. include:: overview.rst.inc", include.read_text())
        prefix = posixpath.relpath(slug, group["slug"])
        def relative_link(match):
            role, value = match[1], match[2]
            named = re.fullmatch(r"(.+?)\s*<([^>]+)>", value)
            label, target = named.groups() if named else (value, value)
            if not urlsplit(target).scheme and not target.startswith("/"):
                target = posixpath.normpath(prefix + "/" + target)
            return f":{role}:`{label} <{target}>`"
        body = re.sub(r":(download|doc):`([^`]+)`", relative_link, body)
        body = re.sub(r"(?m)^([ \t]*\.\. (?:figure|image)::[ \t]+)(assets/\S+)",
                      lambda m: m[1] + posixpath.normpath(prefix + "/" + m[2]), body)
        # The source's section headings become subsections of this part.
        body = re.sub(r"(?m)^(-{3,})$", lambda m: "~" * len(m[1]), body)
        parts.append((part, slug, body))
    for part, slug, body in parts:
        lines.extend([f".. _{part['anchor']}:", "", part["title"],
                      "-" * len(part["title"]), "", body.rstrip(), "",
                      f":doc:`Read this notebook <{posixpath.relpath(slug, group['slug'])}/notebook>`", ""])
    lines.extend([".. toctree::", "   :hidden:", ""])
    for part, slug, _ in parts:
        lines.append(f"   {part['title']} <{posixpath.relpath(slug, group['slug'])}/notebook>")
        if slug != group["slug"]:
            target = posixpath.relpath(group["slug"], slug) + "/index.html#" + part["anchor"]
            (destination / slug / "index.rst").write_text(
                ":orphan:\n\n" + tutorials[slug]["title"] + "\n" + "=" * len(tutorials[slug]["title"]) +
                f"\n\nThis section is part of `{group['title']} <{target}>`_.\n\n.. raw:: html\n\n"
                f'   <meta http-equiv="refresh" content="0;url={target}">\n')
    (folder / "index.rst").write_text("\n".join(lines) + "\n")


def prepare(catalog, revisions, destination):
    destination.mkdir(parents=True, exist_ok=True)
    for name in ("conf.py", "_templates", "_static"):
        source = SITE / name
        if source.is_dir():
            shutil.copytree(source, destination / name, dirs_exist_ok=True)
        else:
            shutil.copyfile(source, destination / name)
    prepare_theme(catalog, destination)
    manifest = {**revisions, "tutorials": {}, "collections": catalog.get("collections", []),
                "redirects": tutorial_redirects(catalog),
                "redirect_anchors": tutorial_redirect_anchors(catalog)}
    for tutorial in catalog["tutorials"]:
        manifest["tutorials"][tutorial["slug"]] = prepare_tutorial(tutorial, revisions, destination)
    for group in catalog.get("collections", []):
        prepare_collection(group, catalog, destination)
    entries = list(catalog_entries(catalog))
    lines = [
        ":summary: Input-output analyses with Python notebooks and source data instructions.",
        "", "Tutorials", "=========", "",
        ".. raw:: html", "",
        '   <section class="tutorial-start" aria-label="Before you start"><div><h2>Before you start</h2></div>',
        '   <p>Install MARIO before running the notebooks. Each tutorial lists its data and any additional dependencies.</p>',
        '   <a href="https://www.marioproject.com/en/latest/get_started/index.html">Installation →</a></section>',
        '   <div class="tutorial-collection">',
    ]
    for number, tutorial in enumerate(entries, 1):
        slug = tutorial["slug"]
        lines.extend([
            f'   <a class="tutorial-entry" href="{slug}/index.html">',
            f'   <div class="tutorial-entry__label"><span>{escape(tutorial.get("category", "Tutorial"))}</span><span class="tutorial-entry__number">{number:02d}</span></div>',
            f'   <h2>{escape(tutorial["title"])}</h2>',
        ])
        if tutorial.get("partner") == "cvxlab":
            lines.extend([
                '   <div class="mario-tutorial-partner" aria-label="Joint MARIO and CVXLab tutorial"><span>Joint tutorial · MARIO ×</span>',
                '   <img class="mario-partner-logo--light" src="_static/cvxlab-logo-light.png" alt="CVXLab" width="104" height="30">',
                '   <img class="mario-partner-logo--dark" src="_static/cvxlab-logo-dark.png" alt="CVXLab" width="104" height="30"></div>',
            ])
        lines.append(f'   <p>{escape(tutorial["summary"])}</p>')
        members = [next(item for item in catalog["tutorials"] if item["slug"] == part["tutorial"])
                   for part in tutorial["parts"]] if tutorial.get("parts") else [tutorial]
        databases = dict.fromkeys(database for member in members for database in member.get("databases", []))
        if databases:
            lines.append('   <div class="tutorial-entry__databases"><span class="tutorial-entry__databases-label">Databases</span>')
            for key in databases:
                database = catalog["databases"][key]
                lines.append('   <span class="tutorial-entry__database">')
                if database.get("logo"):
                    logo = quote(database["logo"])
                    lines.append(f'   <span class="tutorial-entry__database-logo"><img src="_static/images/logos/{logo}" alt="" loading="lazy"></span>')
                lines.append(f'   <span>{escape(database["name"])}</span></span>')
            lines.append('   </div>')
        lines.extend([
            '   <div class="tutorial-entry__foot"><span>Open tutorial →</span></div>',
            '   </a>',
        ])
    lines.extend(['   </div>', "", ".. toctree::", "   :hidden:", ""])
    for tutorial in entries:
        lines.append(f"   {tutorial['title']} <{tutorial['slug']}/index>")
    lines.append("")
    (destination / "index.rst").write_text("\n".join(lines))
    (destination / "site-catalog.json").write_text(json.dumps(catalog))
    return manifest


def updates_needed(revisions, base_url, manifest="source-manifest.json"):
    try:
        published = json.loads(request_bytes(base_url.rstrip("/") + "/" + manifest))
    except HTTPError as error:
        if error.code == 404:
            return True
        raise
    return any(published.get(key) != value for key, value in revisions.items())


def resolve_channels(latest_ref=None):
    definitions = json.loads((SITE / "versions.json").read_text())
    if set(definitions) != {"latest", "dev"}:
        raise ValueError("Configure the Latest and Dev source refs")
    publisher = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    theme = load_catalog()["theme"]
    plan = {"publisher_commit": publisher, "theme": theme, "versions": {}}
    cache = {}
    for channel, definition in definitions.items():
        ref = latest_ref if channel == "latest" and latest_ref else definition["ref"]
        revision = publisher if ref == "HEAD" else github_json(
            f"repos/{REPOSITORY}/commits/{quote(ref, safe='')}"
        )["sha"]
        catalog = load_catalog(revision)
        catalog["theme"] = theme
        plan["versions"][channel] = {**resolve_sources(catalog, revision, cache), "ref": ref, "channel": channel}
    return plan



def write_moved_page(path, target, anchors=None):
    """Write a native fallback and preserve query strings and anchors in browsers."""
    path.parent.mkdir(parents=True, exist_ok=True)
    address = escape(target, quote=True)
    path.write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="robots" content="noindex">'
        '<title>MARIO · Page moved</title><link rel="canonical" href="' + address + '">'
        '<meta http-equiv="refresh" content="0;url=' + address + '">'
        '<script>const target = new URL(' + json.dumps(target) + ');'
        'const anchors = ' + json.dumps(anchors or {}) + ';'
        'const fragment = location.hash.slice(1); target.search = location.search;'
        'target.hash = Object.hasOwn(anchors, fragment) ? anchors[fragment] : location.hash;'
        'location.replace(target.href);</script></head><body><h1>Page moved</h1>'
        '<p>This page has moved. <a href="' + address + '">Continue to MARIO</a>.</p>'
        '</body></html>')


def write_tutorial_redirects(output, redirects, base_url, anchors=None):
    for old, target in redirects.items():
        write_moved_page(output / (old + ".html"), base_url + target + ".html",
                         (anchors or {}).get(old))


def write_preview_redirects(output, catalogue):
    """Retire Preview while preserving its page URLs, query strings and anchors."""
    destinations = {}
    # Prefer Latest; a page available only in Dev keeps its working counterpart.
    for channel in ("dev", "latest"):
        version = catalogue["versions"][channel]
        for document in version["documents"]:
            destinations[document] = (version["url"] + document + ".html", {})
        for old, target in version.get("redirects", {}).items():
            destinations[old] = (version["url"] + target + ".html",
                                 version.get("redirect_anchors", {}).get(old))
    for document, (target, anchors) in destinations.items():
        path = output / "preview" / (document + ".html")
        write_moved_page(path, target, anchors)


def build_channel(catalog, revisions, output, base_url, root_url):
    channel = revisions["channel"]
    work = ROOT / "_build/source" / channel
    if work.exists():
        shutil.rmtree(work)
    manifest = prepare(catalog, revisions, work)
    env = {
        **os.environ, "TUTORIALS_BASE_URL": base_url,
        "TUTORIALS_CHANNEL": channel, "TUTORIALS_SOURCE_COMMIT": revisions["site_commit"],
        "TUTORIALS_SITE_ROOT": root_url,
    }
    subprocess.run([sys.executable, "-m", "sphinx", "-b", "html", "-W", "--keep-going",
                    str(work), str(output)], check=True, cwd=ROOT, env=env)
    write_tutorial_redirects(output, manifest["redirects"], base_url, manifest["redirect_anchors"])
    (output / "source-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "_site")
    parser.add_argument("--base-url", default=os.environ.get("TUTORIALS_BASE_URL", DEFAULT_URL))
    parser.add_argument("--check-updates", action="store_true")
    parser.add_argument("--resolved-sources", type=Path)
    parser.add_argument("--latest-ref")
    args = parser.parse_args()
    plan = json.loads(args.resolved_sources.read_text()) if args.resolved_sources else resolve_channels(args.latest_ref)
    if args.check_updates:
        changed = updates_needed(plan, args.base_url, "versions-manifest.json")
        print(f"changed={str(changed).lower()}")
        if os.environ.get("GITHUB_OUTPUT"):
            with Path(os.environ["GITHUB_OUTPUT"]).open("a") as output:
                output.write(f"changed={str(changed).lower()}\n")
        return
    output = args.output.resolve()
    if ROOT.is_relative_to(output) or output in (SITE, CACHE) or (output / ".git").exists():
        raise ValueError("The HTML output must be a dedicated build directory")
    if output.exists():
        shutil.rmtree(output)
    from bs4 import BeautifulSoup
    root_url = args.base_url.rstrip("/") + "/"
    versions = {"versions": {}}
    for channel, revisions in plan["versions"].items():
        destination = output if channel == "latest" else output / channel
        url = root_url if channel == "latest" else root_url + channel + "/"
        catalog = load_catalog(revisions["site_commit"])
        catalog["theme"] = revisions["theme"]
        manifest = build_channel(catalog, revisions, destination, url, root_url)
        documents = {}
        for page in sorted(destination.rglob("*.html")):
            if channel == "latest" and page.relative_to(destination).parts[0] in {"dev", "preview"}:
                continue
            document = page.relative_to(destination).with_suffix("").as_posix()
            if document in manifest["redirects"]:
                continue
            soup = BeautifulSoup(page.read_text(), "html.parser")
            documents[document] = [
                element["id"] for element in soup.select("[id]")
            ]
        versions["versions"][channel] = {"url": url, "commit": revisions["site_commit"],
                                          "documents": documents, "redirects": manifest["redirects"],
                                          "redirect_anchors": manifest["redirect_anchors"]}
    payload = json.dumps(versions, separators=(",", ":")) + "\n"
    for channel in plan["versions"]:
        destination = output if channel == "latest" else output / channel
        (destination / "_static/docs-versions.json").write_text(payload)
    (output / "docs-versions.json").write_text(payload)
    write_preview_redirects(output, versions)
    (output / "versions-manifest.json").write_text(json.dumps(plan, indent=2) + "\n")
    (output / ".nojekyll").touch()
    subprocess.run([sys.executable, str(SITE / "check.py"), str(output)], check=True)
    print(f"Built Latest and Dev tutorials at {output}")


if __name__ == "__main__":
    main()
