"""Regressions for canonical source handling and external-source publication."""

import importlib.util
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

import nbformat


SPEC = importlib.util.spec_from_file_location("publisher", Path(__file__).parents[1] / "build.py")
publisher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publisher)


class PublisherTests(unittest.TestCase):
    def test_collection_combines_guides_and_keeps_original_notebooks_and_routes(self):
        tutorials = [{"slug": slug, "title": title, "summary": "Case study.",
                      "repository": "owner/source", "ref": "main", "notebook": slug + ".ipynb",
                      "guide": slug + ".rst", "guide_includes_downloads": True}
                     for slug, title in [("nickel", "Nickel"), ("vehicles", "Motor vehicles")]]
        group = {"slug": "supply-chains", "title": "Trace supply chains", "summary": "Two cases.",
                 "intro": "Trade and structural paths.", "parts": [
                     {"tutorial": "nickel", "title": "Nickel", "anchor": "nickel"},
                     {"tutorial": "vehicles", "title": "Motor vehicles", "anchor": "vehicles"}]}
        catalog = {"tutorials": tutorials, "collections": [group]}
        book = nbformat.writes(nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell("value = 3")])).encode()
        def source(repo, revision, path):
            if path.endswith(".ipynb"):
                return book
            slug = Path(path).stem
            return (f"Inputs\n------\n\nUnique {slug} explanation.\n\n"
                    f":download:`Notebook <{slug}.ipynb>`\n\n"
                    ".. figure:: assets/result.png\n\n:doc:`Read notebook <notebook>`\n").encode()
        revisions = {"site_commit": "a" * 40, "external_sources": {"owner/source@main": "b" * 40}}
        with TemporaryDirectory() as directory, patch.object(publisher, "repository_source", side_effect=source):
            root = Path(directory)
            for tutorial in tutorials:
                publisher.prepare_tutorial(tutorial, revisions, root)
            before = {slug: (root / slug / (slug + ".ipynb")).read_bytes() for slug in ["nickel", "vehicles"]}
            publisher.prepare_collection(group, catalog, root)
            page = (root / "supply-chains/index.rst").read_text()
            for slug in ["nickel", "vehicles"]:
                self.assertIn(f"Unique {slug} explanation.", page)
                self.assertIn(f"<{ '../' + slug }/{slug}.ipynb>", page)
                self.assertIn(f".. figure:: ../{slug}/assets/result.png", page)
                self.assertEqual(before[slug], (root / slug / (slug + ".ipynb")).read_bytes())
                self.assertIn(f"../supply-chains/index.html#{slug}", (root / slug / "index.rst").read_text())
            self.assertEqual([item["slug"] for item in publisher.catalog_entries(catalog)], ["supply-chains"])

    def test_collection_can_retain_a_members_existing_url(self):
        catalog = {"tutorials": [{"slug": "bonsai"}, {"slug": "import"}], "collections": [
            {"slug": "bonsai", "parts": [{"tutorial": "import"}, {"tutorial": "bonsai"}]}]}
        self.assertEqual([item["slug"] for item in publisher.catalog_entries(catalog)], ["bonsai"])

    def test_mario_tutorial_moves_links_and_images_but_preserves_downloaded_cells(self):
        source = "doc/source/user_guide/examples/example"
        markdown = "# Original title\n\n[Guide](../analysis/method.rst#units)\n\n![Result](../../_static/images/result.png)"
        notebook = nbformat.writes(nbformat.v4.new_notebook(cells=[
            nbformat.v4.new_markdown_cell(markdown),
            nbformat.v4.new_code_cell("result = model.calculate()"),
        ])).encode()
        guide = (":page-type: Worked example\n\nOriginal title\n==============\n\n"
                 ":doc:`Method <../analysis/method>`\n\n"
                 ".. figure:: ../../_static/images/result.png\n"
                 "   :alt: A result.\n\n"
                 ":download:`Notebook <example.ipynb>`\n").encode()
        tutorial = {"slug": "example", "title": "Published title", "summary": "A worked analysis.",
                    "repository": "it-is-me-mario/MARIO", "ref": "source", "notebook": source + ".ipynb",
                    "guide": source + ".rst", "guide_includes_downloads": True, "source_format": "mario"}
        payloads = {source + ".ipynb": notebook, source + ".rst": guide,
                    "doc/source/_static/images/result.png": b"source-image"}
        revisions = {"site_commit": "a" * 40, "channel": "preview",
                     "external_sources": {"it-is-me-mario/MARIO@source": "b" * 40}}
        with TemporaryDirectory() as directory, patch.object(publisher, "repository_source",
                side_effect=lambda repository, revision, path: payloads[path]):
            folder = Path(directory) / "example"
            record = publisher.prepare_tutorial(tutorial, revisions, Path(directory))
            downloaded = nbformat.read(folder / "example.ipynb", as_version=4)
            rendered = nbformat.read(folder / "notebook.ipynb", as_version=4)
            self.assertEqual(downloaded.cells[0].source, markdown)
            self.assertEqual(rendered.cells[1].source, downloaded.cells[1].source)
            self.assertIn("https://www.marioproject.com/en/preview/user_guide/analysis/method.html#units", rendered.cells[0].source)
            self.assertIn("![Result](assets/result.png)", rendered.cells[0].source)
            explanation = (folder / "overview.rst.inc").read_text()
            self.assertNotIn("Original title", explanation)
            self.assertIn(".. figure:: assets/result.png\n   :alt: A result.", explanation)
            self.assertIn("https://www.marioproject.com/en/preview/user_guide/analysis/method.html", explanation)
            self.assertEqual((folder / "assets/result.png").read_bytes(), b"source-image")
            self.assertEqual(record["assets"]["doc/source/_static/images/result.png"]["sha256"],
                             hashlib.sha256(b"source-image").hexdigest())

    def test_mario_links_preserve_external_targets_and_reject_root_escape(self):
        source = "doc/source/user_guide/examples/example.rst"
        for target in ["https://example.org/guide", "#local-section"]:
            self.assertEqual(publisher.mario_web_link(source, target, "preview"), target)
        with self.assertRaises(ValueError):
            publisher.mario_web_link(source, "../../../../private.rst", "preview")

    def test_periodic_refresh_has_its_own_workflow(self):
        workflows = Path(__file__).parents[2] / ".github/workflows"
        self.assertNotIn("  schedule:", (workflows / "pages.yml").read_text())
        self.assertIn("  schedule:", (workflows / "refresh.yml").read_text())

    def test_clean_notebook_preserves_source_and_is_reproducible(self):
        payload = json.dumps({
            "nbformat": 4, "nbformat_minor": 2, "metadata": {}, "cells": [{
                "cell_type": "code", "metadata": {"execution": {"time": "local"}},
                "source": ["path = # fill in the original placeholder\n", "db = mario.parse_from_excel(path)"],
                "execution_count": 2,
                "outputs": [{"output_type": "stream", "name": "stdout", "text": "stored output"}],
            }],
        }).encode()
        provenance = {"repository": "owner/source", "commit": "a" * 40, "path": "example.ipynb"}
        first = publisher.clean_notebook(payload, provenance)
        self.assertEqual(first, publisher.clean_notebook(payload, provenance))
        notebook = nbformat.reads(first.decode(), as_version=4)
        self.assertEqual(notebook.cells[0].source, "".join(json.loads(payload)["cells"][0]["source"]))
        self.assertEqual(notebook.cells[0].outputs, [])
        self.assertIsNone(notebook.cells[0].execution_count)
        self.assertEqual(notebook.metadata.mario_tutorial_source, provenance)

    def test_external_tutorial_uses_one_recorded_commit_for_all_files(self):
        notebook = nbformat.writes(nbformat.v4.new_notebook(cells=[
            nbformat.v4.new_code_cell("result = 1"),
        ])).encode()
        tutorial = {"slug": "example", "title": "Example", "summary": "An example.",
                    "repository": "owner/source", "ref": "main", "notebook": "run.ipynb",
                    "materials": ["inventory.xlsx"]}
        revisions = {"site_commit": "a" * 40, "external_sources": {"owner/source@main": "b" * 40}}
        with TemporaryDirectory() as folder, patch.object(publisher, "cached_source") as fetch:
            fetch.side_effect = [notebook, b"spreadsheet"]
            manifest = publisher.prepare_tutorial(tutorial, revisions, Path(folder))
            self.assertEqual([call.args[1] for call in fetch.call_args_list], ["b" * 40] * 2)
            self.assertEqual(manifest["commit"], "b" * 40)
            self.assertEqual((Path(folder) / "example/inventory.xlsx").read_bytes(), b"spreadsheet")
            self.assertTrue((Path(folder) / "example/notebook.ipynb").is_file())

    def test_external_change_requests_publication(self):
        revisions = {"site_commit": "a", "theme": {}, "external_sources": {"source@main": "new"}}
        previous = {**revisions, "external_sources": {"source@main": "old"}}
        with patch.object(publisher, "request_bytes", return_value=json.dumps(previous).encode()):
            self.assertTrue(publisher.updates_needed(revisions, "https://tutorials.example"))
        with patch.object(publisher, "request_bytes", return_value=json.dumps(revisions).encode()):
            self.assertFalse(publisher.updates_needed(revisions, "https://tutorials.example"))

    def test_only_missing_publication_is_treated_as_initial_build(self):
        with patch.object(publisher, "request_bytes", side_effect=HTTPError("url", 404, "missing", {}, None)):
            self.assertTrue(publisher.updates_needed({}, "https://tutorials.example"))
        with patch.object(publisher, "request_bytes", side_effect=HTTPError("url", 503, "unavailable", {}, None)):
            with self.assertRaises(HTTPError):
                publisher.updates_needed({}, "https://tutorials.example")

    def test_guide_comes_from_the_notebook_source_revision(self):
        notebook = nbformat.writes(nbformat.v4.new_notebook()).encode()
        guide = b"Reference system\n----------------\n\nA worked explanation.\n"
        tutorial = {"slug": "example", "title": "Example", "summary": "An example.",
                    "repository": "owner/source", "ref": "main", "notebook": "run.ipynb",
                    "guide": "overview.rst", "guide_includes_downloads": True}
        revisions = {"site_commit": "a" * 40, "external_sources": {"owner/source@main": "b" * 40}}
        with TemporaryDirectory() as folder, patch.object(publisher, "cached_source") as fetch:
            fetch.side_effect = [notebook, guide]
            manifest = publisher.prepare_tutorial(tutorial, revisions, Path(folder))
            self.assertEqual([call.args[1] for call in fetch.call_args_list], ["b" * 40] * 2)
            self.assertEqual(manifest["guide"], {"path": "overview.rst", "sha256": hashlib.sha256(guide).hexdigest()})
            page = Path(folder) / "example"
            self.assertEqual((page / "overview.rst.inc").read_bytes(), guide)
            self.assertIn(".. include:: overview.rst.inc", (page / "index.rst").read_text())
            self.assertNotIn("Run the tutorial", (page / "index.rst").read_text())
            self.assertIn("   :hidden:", (page / "index.rst").read_text())

    def test_source_paths_stay_inside_the_snapshot(self):
        for name in ("../other", "/absolute", "."):
            with self.subTest(name=name), self.assertRaises(ValueError):
                publisher.source_path(name)

    def test_local_snapshot_reads_committed_content(self):
        with patch.object(publisher.subprocess, "check_output", return_value=b"committed") as git:
            self.assertEqual(publisher.repository_source(publisher.REPOSITORY, "a" * 40, "run.ipynb"), b"committed")
            self.assertEqual(git.call_args.args[0], ["git", "show", "a" * 40 + ":run.ipynb"])

    def test_channels_share_one_resolution_of_an_external_ref(self):
        catalog = {"theme": {}, "tutorials": [{"repository": "owner/source", "ref": "main"}]}
        cache = {}
        with patch.object(publisher, "github_json", return_value={"sha": "b" * 40}) as github:
            first = publisher.resolve_sources(catalog, "a" * 40, cache)
            second = publisher.resolve_sources(catalog, "c" * 40, cache)
            self.assertEqual(first["external_sources"], second["external_sources"])
            self.assertEqual(github.call_count, 1)


if __name__ == "__main__":
    unittest.main()
