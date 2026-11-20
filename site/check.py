"""Check generated pages, source provenance and downloadable companions."""

import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup
import nbformat


def check_channel(output, *, skip=()):
    output = output.resolve()
    manifest = json.loads((output / "source-manifest.json").read_text())
    downloads = {}
    count = 0
    for path in output.rglob("*.html"):
        if path.relative_to(output).parts[0] in skip:
            continue
        soup = BeautifulSoup(path.read_text(), "html.parser")
        if path.name not in {"search.html", "genindex.html"}:
            assert len(soup.select("h1")) == 1, f"Expected one page heading in {path}"
        for element in soup.select("a[href], script[src], img[src], link[href]"):
            address = element.get("href", element.get("src", ""))
            parsed = urlsplit(address)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (path.parent / unquote(parsed.path)).resolve()
            if not target.is_relative_to(output):
                raise AssertionError(f"Link leaves the site {path}: {address}")
            if target.is_dir():
                target = target / "index.html"
            assert target.is_file(), f"Missing target {path}: {address}"
            if "_downloads" in target.parts:
                downloads.setdefault(target.name, set()).add(target)
            count += 1
    for old, target in manifest.get("redirects", {}).items():
        assert (output / (target + ".html")).is_file(), f"Missing redirect target: {target}"
        soup = BeautifulSoup((output / (old + ".html")).read_text(), "html.parser")
        canonical = soup.find("link", rel="canonical")["href"]
        assert urlsplit(canonical).path.endswith("/" + target + ".html")
        assert soup.find("meta", attrs={"http-equiv": "refresh"})["content"] == "0;url=" + canonical
        assert soup.find("meta", attrs={"name": "robots"})["content"] == "noindex"
        assert soup.find("a")["href"] == canonical
    for slug, source in manifest["tutorials"].items():
        assert (output / slug / "index.html").is_file()
        assert (output / slug / "notebook.html").is_file()
        for filename, record in source["files"].items():
            candidates = downloads.get(Path(filename).name, set())
            path = next((p for p in candidates if hashlib.sha256(p.read_bytes()).hexdigest() == record["download_sha256"]), None)
            assert path is not None, f"Missing or changed download: {slug}/{filename}"
            if path.suffix == ".ipynb":
                notebook = nbformat.read(path, as_version=4)
                assert notebook.metadata["mario_tutorial_source"]["commit"] == source["commit"]
                for cell in notebook.cells:
                    if cell.cell_type == "code":
                        assert not cell.outputs and cell.execution_count is None
    for group in manifest.get("collections", []):
        page = output / group["slug"] / "index.html"
        soup = BeautifulSoup(page.read_text(), "html.parser")
        for part in group["parts"]:
            assert soup.find(id=part["anchor"]), f"Missing tutorial part: {part}"
            if part["tutorial"] != group["slug"]:
                old = BeautifulSoup((output / part["tutorial"] / "index.html").read_text(), "html.parser")
                refresh = old.find("meta", attrs={"http-equiv": "refresh"})
                assert refresh and (group["slug"] + "/index.html#" + part["anchor"]) in refresh["content"]
    print(f"PASS {len(manifest['tutorials'])} source notebooks, {count} local links and all downloads")


def check(output):
    if (output / "versions-manifest.json").is_file():
        check_channel(output, skip=("dev", "preview"))
        check_channel(output / "dev")
    else:
        check_channel(output)


if __name__ == "__main__":
    check(Path(sys.argv[1]))

