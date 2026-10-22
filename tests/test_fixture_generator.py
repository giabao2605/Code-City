"""CC-004 stdlib test matrix: deterministic integrity, profiles, adversarial changes."""
from __future__ import annotations
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from benchmarks import generate_fixture as gen
from benchmarks import verify_fixture as verify


class TestFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="CC004 tests ")
        cls.base = Path(cls.temp.name)
        cls.root = cls.base / "thử nghiệm với khoảng trắng"
        cls.report = gen.create(cls.root, 500, "mixed", 42, 256 * 1024 ** 2)
        cls.manifest = Path(cls.report["manifest"])

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_01_count_ignore_extensions(self):
        result = verify.verify(self.root, self.manifest)
        self.assertEqual(result["supportedFiles"], 500)
        self.assertEqual(result["ignoredFiles"], 9)
        self.assertEqual(result["unsupportedFiles"], 4)
        self.assertEqual(result["physicalFiles"], 514)
        self.assertEqual({Path(x["path"]).suffix for x in verify.inventory(self.root)
                          if x["kind"] == "supported"}, set(gen.EXTENSIONS))

    def test_02_unicode_and_spaces(self):
        entries = verify.inventory(self.root)
        self.assertTrue(any("mã nguồn" in x["path"] for x in entries))
        self.assertTrue(any("tài liệu có dấu" in x["path"] for x in entries))
        self.assertIn("thử nghiệm", str(self.root))

    def test_03_determinism_across_output_roots(self):
        r = gen.create(self.base / "clone seed", 500, "mixed", 42, 256 * 1024 ** 2)
        self.assertEqual(r["datasetDigest"], self.report["datasetDigest"])
        self.assertEqual(verify.inventory(Path(r["root"])), verify.inventory(self.root))

    def test_04_different_seed(self):
        r = gen.create(self.base / "new seed", 500, "mixed", 43, 256 * 1024 ** 2)
        self.assertNotEqual(r["datasetDigest"], self.report["datasetDigest"])
        verify.verify(Path(r["root"]), Path(r["manifest"]))

    def test_05_deep(self):
        r = gen.create(self.base / "deep", 500, "deep", 42, 256 * 1024 ** 2)
        self.assertTrue(any(len(x["path"].split("/")) >= 10 for x in verify.inventory(Path(r["root"]))))
        verify.verify(Path(r["root"]), Path(r["manifest"]))

    def test_06_tiny(self):
        r = gen.create(self.base / "tiny", 500, "tiny", 42, 256 * 1024 ** 2)
        self.assertTrue(any(x["size"] == 0 for x in verify.inventory(Path(r["root"]))))
        verify.verify(Path(r["root"]), Path(r["manifest"]))

    def test_07_large_bounded(self):
        r = gen.create(self.base / "large", 500, "large", 42, 256 * 1024 ** 2)
        self.assertGreater(max(x["size"] for x in verify.inventory(Path(r["root"]))), 1_048_576)
        self.assertLess(r["totalBytes"], 256 * 1024 ** 2)
        verify.verify(Path(r["root"]), Path(r["manifest"]))

    def test_08_existing_directory_never_overwritten(self):
        root = self.base / "existing"
        root.mkdir()
        keep = root / "keep.txt"
        keep.write_text("USER DATA", encoding="utf-8")
        with self.assertRaises(ValueError):
            gen.create(root, 500, "mixed", 42, 256 * 1024 ** 2)
        self.assertEqual(keep.read_text(encoding="utf-8"), "USER DATA")

    def test_09_bad_count_and_budget_fail_before_writing(self):
        with self.assertRaises(ValueError):
            gen.create(self.base / "bad-count", 501, "mixed", 42, 256 * 1024 ** 2)
        root = self.base / "bad-budget"
        with self.assertRaises(ValueError):
            gen.create(root, 500, "mixed", 42, 1)
        self.assertFalse(root.exists())

    def test_10_corrupt_manifest(self):
        old = self.manifest.read_bytes()
        try:
            self.manifest.write_bytes(b"{broken")
            with self.assertRaises(ValueError):
                verify.verify(self.root, self.manifest)
        finally:
            self.manifest.write_bytes(old)

    def test_11_missing_file(self):
        source = next(self.root.joinpath(*x["path"].split("/")) for x in verify.inventory(self.root) if x["kind"] == "supported")
        original = source.read_bytes()
        try:
            source.unlink()
            with self.assertRaises(ValueError):
                verify.verify(self.root, self.manifest)
        finally:
            source.write_bytes(original)

    def test_12_modified_file_same_size(self):
        source = next(self.root.joinpath(*x["path"].split("/")) for x in verify.inventory(self.root) if x["kind"] == "supported" and x["size"] > 0)
        old = source.read_bytes()
        try:
            source.write_bytes(b"z" * len(old))
            with self.assertRaises(ValueError):
                verify.verify(self.root, self.manifest)
        finally:
            source.write_bytes(old)

    def test_13_extra_supported_file(self):
        extra = self.root / "src" / "unexpected.py"
        try:
            extra.write_text("extra", encoding="utf-8")
            with self.assertRaises(ValueError):
                verify.verify(self.root, self.manifest)
        finally:
            extra.unlink()

    def test_14_manifest_count_mismatch(self):
        old = self.manifest.read_bytes()
        try:
            obj = json.loads(old)
            obj["supportedFileCount"] = 499
            self.manifest.write_text(json.dumps(obj), encoding="utf-8")
            with self.assertRaises(ValueError):
                verify.verify(self.root, self.manifest)
        finally:
            self.manifest.write_bytes(old)

    def test_15_manifest_digest_mismatch(self):
        old = self.manifest.read_bytes()
        try:
            obj = json.loads(old)
            obj["datasetDigest"] = "0" * 64
            self.manifest.write_text(json.dumps(obj), encoding="utf-8")
            with self.assertRaises(ValueError):
                verify.verify(self.root, self.manifest)
        finally:
            self.manifest.write_bytes(old)

    def test_16_metadata_not_in_source_quota(self):
        doc = json.loads(self.manifest.read_text(encoding="utf-8"))
        self.assertEqual(doc["physicalFileCount"], 514)
        self.assertFalse(self.manifest.is_relative_to(self.root))

    def test_17_unowned_cleanup_denied(self):
        root = self.base / "unowned"
        root.mkdir()
        file = root / "KEEP.txt"
        file.write_text("safe", encoding="utf-8")
        with self.assertRaises(ValueError):
            verify.cleanup(root, root.with_name(root.name + ".manifest.json"))
        self.assertTrue(file.exists())

    def test_18_owned_cleanup(self):
        r = gen.create(self.base / "owned", 500, "tiny", 42, 256 * 1024 ** 2)
        result = verify.cleanup(Path(r["root"]), Path(r["manifest"]))
        self.assertEqual(result["status"], "CLEANED")
        self.assertFalse(Path(r["root"]).exists())

    def test_19_no_import_execute_generated_source(self):
        marker = self.root / "__CC004_EXECUTION_MARKER__"
        self.assertFalse(marker.exists())
        verify.verify(self.root, self.manifest)
        self.assertFalse(marker.exists())

    def test_20_offline_generation_network_disabled(self):
        with patch.object(socket, "socket", side_effect=AssertionError("NETWORK")):
            r = gen.create(self.base / "offline", 500, "tiny", 42, 256 * 1024 ** 2)
        self.assertEqual(r["count"], 500)

    def test_21_cli_exit_codes_cwd_independent(self):
        root = self.base / "cli-test"
        cmd = [sys.executable, str(Path(gen.__file__).resolve()), "--output", str(root), "--count"]
        bad = subprocess.run(cmd + ["501"], cwd=self.base, capture_output=True, text=True)
        self.assertNotEqual(bad.returncode, 0)
        good = subprocess.run(cmd + ["500"], cwd=self.base, capture_output=True, text=True)
        self.assertEqual(good.returncode, 0, good.stderr)
        script = str(Path(verify.__file__).resolve())
        check = subprocess.run([sys.executable, script, "--root", str(root)], cwd=self.base, capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stderr)

    def test_22_case_insensitive_ignore_classification(self):
        self.assertEqual(verify.kind("MODULES/NODE_MODULES/deceptive.py"), "ignored")
        self.assertEqual(verify.kind("src/COMPONENT.TSX"), "supported")

    def test_23_cleanup_manifest_must_be_sibling(self):
        with self.assertRaises(ValueError):
            verify.cleanup(self.root, self.base / "other.json")
        self.assertTrue(self.root.exists())

    def test_24_no_network_or_exec_dependencies(self):
        import inspect
        code = inspect.getsource(gen) + inspect.getsource(verify)
        self.assertNotIn("subprocess.run(", code)
        self.assertNotIn("eval(", code)
        self.assertNotIn("exec(", code)


if __name__ == "__main__":
    unittest.main()
