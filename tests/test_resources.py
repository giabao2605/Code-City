"""Pure Python packaged resource resolution; no Qt or build tools needed."""
import os
from pathlib import Path
import tempfile
import unittest
from spike.resources import frontend_dist


class ResourceResolutionTests(unittest.TestCase):
    def test_source_tree_from_arbitrary_cwd(self):
        source = Path(__file__).resolve().parents[1] / "spike" / "resources.py"
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as d:
            try:
                os.chdir(d)
                self.assertEqual(frontend_dist(source_file=source, packaged=False),
                                 source.parents[1] / "frontend" / "dist")
            finally:
                os.chdir(previous)

    def test_bundled_unicode_and_spaced_directory(self):
        with tempfile.TemporaryDirectory() as d:
            exe = Path(d) / "Thử nghiệm Unicode có dấu" / "CodeCitySpike.exe"
            self.assertEqual(frontend_dist(executable=exe, packaged=True),
                             exe.parent / "frontend" / "dist")

    def test_no_silent_development_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            exe = Path(d) / "CodeCitySpike.exe"
            dist = frontend_dist(executable=exe)
            self.assertEqual(dist, exe.parent / "frontend" / "dist")
            self.assertFalse((dist / "index.html").exists())


if __name__ == "__main__":
    unittest.main()
