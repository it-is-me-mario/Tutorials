"""Publish tutorials from their canonical repositories at recorded commits."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
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
    if not SHA.fullmatch(catalog["theme"]["revision"]):
        raise ValueError("The shared theme must use a full commit SHA")
    return catalog


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
    for name in [*names, *THEME_ASSETS]:
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


def mario_web_link(source, address, channel):
    parsed = urlsplit(address)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return address
    target = mario_source_target(source, parsed.path).relative_to("doc/source")
    if target.suffix in {".rst", ".ipynb"}:
        target = target.with_suffix(".html")
    elif not target.suffix:
        target = target.with_suffix(".html")
    return (f"https://www.marioproject.com/en/{channel}/" + quote(target.as_posix())
            + ("?" + parsed.query if parsed.query else "")
            + ("#" + parsed.fragment if parsed.fragment else ""))


def rst_document_body(text):
    """Separate a full RST page's metadata/title from its reusable explanation."""
    match = re.search(r"^([^\n]+)\n[=]{3,}\s*\n", text, re.M)
    if not match:
        raise ValueError("Expected a titled MARIO RST guide")
    return match.group(1).strip(), text[match.end():].lstrip()


def prepare_mario_explanation(tutorial, revision, channel, folder, guide, notebook):
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
        return f"`{label} <{mario_web_link(tutorial['guide'], address, channel)}>`_"

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
                mario_web_link(tutorial["notebook"], address, channel)
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
                tutorial, revision, revisions.get("channel", "latest"), folder, payload,
                (folder / notebook_name).read_bytes(),
            )
            (folder / "notebook.ipynb").write_bytes(rendered)
            guide_record["assets"] = assets
        (folder / "overview.rst.inc").write_bytes(explanation)
        lines.extend([".. include:: overview.rst.inc", ""])
        guide_record["guide"] = {"path": name, "sha256": hashlib.sha256(payload).hexdigest()}
    lines.extend([
        f"Read the `source repository <https://github.com/{repository}>`_ and the",
        f"`version used for this page <{source_url}>`_.", "",
    ])
    if not tutorial.get("guide_includes_downloads"):
        lines.extend([
            "Run the tutorial", "----------------", "",
            "Download the notebook and its supporting files into one working folder.",
            "Follow the notebook's environment and source-data instructions before running it.",
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


def prepare(catalog, revisions, destination):
    destination.mkdir(parents=True, exist_ok=True)
    for name in ("conf.py", "_templates", "_static"):
        source = SITE / name
        if source.is_dir():
            shutil.copytree(source, destination / name, dirs_exist_ok=True)
        else:
            shutil.copyfile(source, destination / name)
    prepare_theme(catalog, destination)
    manifest = {**revisions, "tutorials": {}}
    lines = [
        ":summary: Worked analyses with methods, source data and downloadable notebooks.",
        "", "Tutorials", "=========", "",
        ".. raw:: html", "",
        '   <section class="tutorial-start" aria-label="Before you start"><div><span class="mario-eyebrow">New to MARIO?</span><h2>Prepare your first analysis.</h2></div>',
        '   <p>Install MARIO and learn how input-output tables, supply-use tables and scenarios fit together.</p>',
        f'   <a href="https://www.marioproject.com/en/{revisions.get("channel", "latest")}/get_started/index.html">Start with the essentials →</a></section>',
        '   <div class="tutorial-collection">',
    ]
    for tutorial in catalog["tutorials"]:
        slug = tutorial["slug"]
        manifest["tutorials"][slug] = prepare_tutorial(tutorial, revisions, destination)
        lines.extend([
            f'   <a class="tutorial-entry" href="{slug}/index.html">',
            f'   <div class="tutorial-entry__label"><span class="mario-eyebrow">{escape(tutorial.get("category", "Worked tutorial"))}</span><span class="tutorial-entry__number">{len(manifest["tutorials"]):02d}</span></div>',
            f'   <h2>{escape(tutorial["title"])}</h2>',
        ])
        if tutorial.get("partner") == "cvxlab":
            lines.extend([
                '   <div class="mario-tutorial-partner" aria-label="Joint MARIO and CVXLab tutorial"><span>Joint tutorial · MARIO ×</span>',
                '   <img class="mario-partner-logo--light" src="_static/cvxlab-logo-light.png" alt="CVXLab" width="104" height="30">',
                '   <img class="mario-partner-logo--dark" src="_static/cvxlab-logo-dark.png" alt="CVXLab" width="104" height="30"></div>',
            ])
        companion = "Notebook + supporting materials" if tutorial.get("materials") else "Notebook + worked guide"
        lines.extend([
            f'   <p>{escape(tutorial["summary"])}</p>',
            f'   <div class="tutorial-entry__foot"><span>{companion}</span><span>Open tutorial ↗</span></div>',
            '   </a>',
        ])
    lines.extend(['   </div>', "", ".. toctree::", "   :hidden:", ""])
    for tutorial in catalog["tutorials"]:
        lines.append(f"   {tutorial['title']} <{tutorial['slug']}/index>")
    channel = revisions.get("channel", "latest")
    lines.extend(["", "The tutorials cover real databases and complete exercises. For individual operations,",
                  f"use the `MARIO documentation <https://www.marioproject.com/en/{channel}/user_guide/index.html>`_.", ""])
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
    if set(definitions) != {"latest", "dev", "preview"}:
        raise ValueError("Configure the Latest, Dev and Preview source refs")
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
        if channel != "preview":
            catalog["theme"] = theme
        plan["versions"][channel] = {**resolve_sources(catalog, revision, cache), "ref": ref, "channel": channel}
    return plan


def preview_renderer(revision):
    """Read the proposed presentation from the same immutable source as its content."""
    destination = ROOT / "_build/presentation" / revision
    for name in ("site/build.py", "site/conf.py", "site/_static/tutorials.css",
                 "site/_templates/partials/footer.html"):
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(repository_source(REPOSITORY, revision, name))
    spec = importlib.util.spec_from_file_location("preview_presentation", destination / "site/build.py")
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    renderer.ROOT, renderer.CACHE = ROOT, CACHE
    return renderer


def build_channel(catalog, revisions, output, base_url, root_url):
    channel = revisions["channel"]
    work = ROOT / "_build/source" / channel
    if work.exists():
        shutil.rmtree(work)
    prepare_source = preview_renderer(revisions["site_commit"]).prepare if channel == "preview" else prepare
    manifest = prepare_source(catalog, revisions, work)
    env = {
        **os.environ, "TUTORIALS_BASE_URL": base_url,
        "TUTORIALS_CHANNEL": channel, "TUTORIALS_SOURCE_COMMIT": revisions["site_commit"],
        "TUTORIALS_SITE_ROOT": root_url,
    }
    subprocess.run([sys.executable, "-m", "sphinx", "-b", "html", "-W", "--keep-going",
                    str(work), str(output)], check=True, cwd=ROOT, env=env)
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
        build_channel(catalog, revisions, destination, url, root_url)
        documents = {}
        for page in sorted(destination.rglob("*.html")):
            if channel == "latest" and page.relative_to(destination).parts[0] in {"dev", "preview"}:
                continue
            soup = BeautifulSoup(page.read_text(), "html.parser")
            documents[page.relative_to(destination).with_suffix("").as_posix()] = [
                element["id"] for element in soup.select("[id]")
            ]
        versions["versions"][channel] = {"url": url, "commit": revisions["site_commit"], "documents": documents}
    payload = json.dumps(versions, separators=(",", ":")) + "\n"
    for channel in plan["versions"]:
        destination = output if channel == "latest" else output / channel
        (destination / "_static/docs-versions.json").write_text(payload)
    (output / "docs-versions.json").write_text(payload)
    (output / "versions-manifest.json").write_text(json.dumps(plan, indent=2) + "\n")
    (output / ".nojekyll").touch()
    subprocess.run([sys.executable, str(SITE / "check.py"), str(output)], check=True)
    print(f"Built Latest, Dev and Preview tutorials at {output}")


if __name__ == "__main__":
    main()
