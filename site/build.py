"""Publish tutorials from their canonical repositories at recorded commits."""

from __future__ import annotations

import argparse
import hashlib
from html import escape
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
from urllib.error import HTTPError
from urllib.parse import quote
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


def load_catalog():
    catalog = json.loads((SITE / "catalog.json").read_text())
    slugs = set()
    for tutorial in catalog["tutorials"]:
        slug = tutorial["slug"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) or slug in slugs:
            raise ValueError(f"Invalid or repeated tutorial slug {slug!r}")
        slugs.add(slug)
        for name in [tutorial["notebook"], *tutorial.get("materials", ())]:
            source_path(name)
        basenames = [source_path(name).name for name in [tutorial["notebook"], *tutorial.get("materials", ())]]
        if len(basenames) != len(set(basenames)) or "notebook.ipynb" in basenames:
            raise ValueError(f"Tutorial {slug!r} has conflicting download names")
        if tutorial["repository"] != REPOSITORY and not tutorial.get("ref"):
            raise ValueError(f"External tutorial {slug!r} needs a source ref")
    if not SHA.fullmatch(catalog["theme"]["revision"]):
        raise ValueError("The shared theme must use a full commit SHA")
    return catalog


def resolve_sources(catalog):
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
    ).strip()
    revisions = {}
    for tutorial in catalog["tutorials"]:
        repository = tutorial["repository"]
        if repository == REPOSITORY:
            continue
        key = f"{repository}@{tutorial['ref']}"
        if key not in revisions:
            ref = quote(tutorial["ref"], safe="")
            revisions[key] = github_json(f"repos/{repository}/commits/{ref}")["sha"]
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
        payload = (ROOT / source_path(name)).read_bytes() if repository == REPOSITORY else \
            cached_source(repository, revision, name)
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
        f"Read the `source repository <https://github.com/{repository}>`_ and the",
        f"`version used for this page <{source_url}>`_.", "",
        "Run the tutorial", "----------------", "",
        "Download the notebook and its supporting files into one working folder.",
        "Follow the notebook's environment and source-data instructions before running it.",
        "",
        f"* :download:`Notebook <{notebook_name}>`",
    ]
    for name in tutorial.get("materials", ()):
        basename = source_path(name).name
        lines.append(f"* :download:`{basename} <{basename}>`")
    if tutorial.get("instructions"):
        path = quote(tutorial["instructions"])
        instructions = f"https://github.com/{repository}/blob/{revision}/{path}"
        lines.extend(["", f"`Repository instructions <{instructions}>`_ supply the original setup notes."])
    lines.extend(["", ".. toctree::", "   :maxdepth: 2", "", "   Notebook <notebook>", ""])
    (folder / "index.rst").write_text("\n".join(lines))
    return {**provenance, "files": files}


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
        ":summary: Follow MARIO tutorials and download the materials from their source repositories.",
        "", "Tutorials", "=========", "",
        "Follow complete exercises with MARIO, source data and model inputs.",
        "Each tutorial provides a readable notebook, downloadable materials and its source revision.", "",
        ".. raw:: html", "", '   <div class="mario-cards mario-cards--2 mario-cards--links">',
    ]
    for tutorial in catalog["tutorials"]:
        slug = tutorial["slug"]
        manifest["tutorials"][slug] = prepare_tutorial(tutorial, revisions, destination)
        lines.extend([
            '   <section class="mario-card">',
            f'   <h2 class="mario-card__title"><a href="{slug}/index.html">{escape(tutorial["title"])}</a></h2>',
            f'   <div class="mario-card__body"><p>{escape(tutorial["summary"])}</p></div>',
            '   </section>',
        ])
    lines.extend(['   </div>', "", ".. toctree::", "   :hidden:", ""])
    for tutorial in catalog["tutorials"]:
        lines.append(f"   {tutorial['title']} <{tutorial['slug']}/index>")
    lines.extend(["", "The tutorials cover real databases and complete exercises. For individual operations,",
                  "use the `MARIO documentation <https://www.marioproject.com/en/latest/user_guide/index.html>`_.", ""])
    (destination / "index.rst").write_text("\n".join(lines))
    (destination / "site-catalog.json").write_text(json.dumps(catalog))
    return manifest


def updates_needed(revisions, base_url):
    try:
        published = json.loads(request_bytes(base_url.rstrip("/") + "/source-manifest.json"))
    except HTTPError as error:
        if error.code == 404:
            return True
        raise
    return any(published.get(key) != value for key, value in revisions.items())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "_site")
    parser.add_argument("--base-url", default=os.environ.get("TUTORIALS_BASE_URL", DEFAULT_URL))
    parser.add_argument("--check-updates", action="store_true")
    parser.add_argument("--resolved-sources", type=Path)
    args = parser.parse_args()
    catalog = load_catalog()
    revisions = json.loads(args.resolved_sources.read_text()) if args.resolved_sources else resolve_sources(catalog)
    if args.check_updates:
        changed = updates_needed(revisions, args.base_url)
        print(f"changed={str(changed).lower()}")
        if os.environ.get("GITHUB_OUTPUT"):
            with Path(os.environ["GITHUB_OUTPUT"]).open("a") as output:
                output.write(f"changed={str(changed).lower()}\n")
        return
    work = ROOT / "_build/source"
    if work.exists():
        shutil.rmtree(work)
    manifest = prepare(catalog, revisions, work)
    output = args.output.resolve()
    if ROOT.is_relative_to(output) or output in (SITE, CACHE) or (output / ".git").exists():
        raise ValueError("The HTML output must be a dedicated build directory")
    if output.exists():
        shutil.rmtree(output)
    env = {**os.environ, "TUTORIALS_BASE_URL": args.base_url}
    subprocess.run([sys.executable, "-m", "sphinx", "-b", "html", "-W", "--keep-going",
                    str(work), str(args.output)], check=True, cwd=ROOT, env=env)
    (args.output / "source-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (args.output / ".nojekyll").touch()
    subprocess.run([sys.executable, str(SITE / "check.py"), str(args.output)], check=True)
    print(f"Built {len(catalog['tutorials'])} tutorials at {args.output}")


if __name__ == "__main__":
    main()
