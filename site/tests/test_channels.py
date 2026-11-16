"""Keep the two channels' same-named downloads independent."""
import hashlib
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import nbformat

SPEC = importlib.util.spec_from_file_location("checker", Path(__file__).parents[1] / "check.py")
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


class ChannelChecks(unittest.TestCase):
    def test_each_channel_checks_its_own_download_hash(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            for output, revision in [(root, "a" * 40), (root / "dev", "b" * 40)]:
                (output / "example").mkdir(parents=True)
                (output / "_downloads").mkdir()
                book = nbformat.v4.new_notebook(metadata={"mario_tutorial_source": {"commit": revision}})
                payload = nbformat.writes(book).encode()
                (output / "_downloads/run.ipynb").write_bytes(payload)
                (output / "index.html").write_text('<h1>Tutorials</h1><a href="example/index.html">Example</a>')
                (output / "example/index.html").write_text('<h1>Example</h1><a href="../_downloads/run.ipynb">Download</a>')
                (output / "example/notebook.html").write_text('<h1>Notebook</h1>')
                manifest = {"tutorials": {"example": {"commit": revision, "files": {
                    "run.ipynb": {"download_sha256": hashlib.sha256(payload).hexdigest()},
                }}}}
                (output / "source-manifest.json").write_text(json.dumps(manifest))
            (root / "versions-manifest.json").write_text('{}')
            checker.check(root)
