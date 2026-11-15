"""Regressions for canonical source handling and external-source publication."""

import importlib.util
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

    def test_source_paths_stay_inside_the_snapshot(self):
        for name in ("../other", "/absolute", "."):
            with self.subTest(name=name), self.assertRaises(ValueError):
                publisher.source_path(name)


if __name__ == "__main__":
    unittest.main()
