"""CC-005 isolated negative/security tests. Windows-only tests run on actual Actions host."""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from security_spike.contracts import (
    Limits, FileBudget, FileCountExceeded, FileTooLarge,
    ScanError, ScanStage, ScanStatus, ErrorCode, finish, retain_previous,
    MAX_BYTES, MAX_FILES
)
from security_spike.windows_paths import (
    WIN, UnsafePath, UnstableFile, relative_parts, path_key,
    reject_collisions, validate_root, read_probe
)

class ContractTests(unittest.TestCase):
    def test_relative_path_rejection(self):
        for bad in ("", ".", "../secret.py", "a/../b.py", "/etc/passwd",
                    "C:/secret.py", "a\\b.py", "a//b.py", "file.py:secret",
                    "x./file.py", "NUL.txt", "AUX", "CON.py", "foo/.",
                    "a/ ", "a/ending."):
            with self.subTest(bad=bad), self.assertRaises(UnsafePath):
                relative_parts(bad)
        self.assertEqual(relative_parts("mã nguồn/test.py"), ("mã nguồn", "test.py"))

    def test_unicode_casefold_collision(self):
        with self.assertRaises(UnsafePath):
            reject_collisions(["Dir/Test.PY", "dir/test.py"])
        with self.assertRaises(UnsafePath):
            reject_collisions(["café/file.py", "cafe\u0301/file.py"])
        self.assertEqual(path_key("mã/File.PY"), path_key("mã/file.py"))

    def test_counts_and_ignored_unsupported(self):
        quota = FileBudget()
        self.assertFalse(quota.discover("README.md"))
        self.assertFalse(quota.discover("a.py", parents=("NODE_MODULES",)))
        self.assertFalse(quota.discover("a.py", parents=(".GIT",)))
        self.assertEqual(quota.supported, 0)
        self.assertEqual(len(__import__("security_spike.contracts", fromlist=["EXTENSIONS"]).EXTENSIONS), 17)
        for _ in range(MAX_FILES):
            self.assertTrue(quota.discover("a.py"))
        self.assertEqual(quota.supported, 20_000)
        with self.assertRaises(FileCountExceeded):
            quota.discover("overflow.py")
        self.assertEqual(quota.supported, 20_000)

    def test_limit_boundary(self):
        b = FileBudget()
        for n in (0, 1, MAX_BYTES):
            b.check_size(n)
        for n in (-1, MAX_BYTES+1, 2*MAX_BYTES):
            with self.assertRaises(FileTooLarge):
                b.check_size(n)

    def test_invalid_config(self):
        for kwargs in ({"files":0},{"files":20001},{"files":-1},
                       {"files":True},{"bytes_per_file":MAX_BYTES+1},
                       {"bytes_per_file":0},{"chunk_bytes":0},
                       {"chunk_bytes":2*1024*1024},
                       {"retry_count":2},{"retry_count":-1},
                       {"workers":0},{"workers":5}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Limits(**kwargs)

    def test_complete_and_genuine_deleted(self):
        valid = finish(stage=ScanStage.FINISH, discovered=1, processed=1,
                       discovery_complete=True)
        self.assertEqual(valid.status, ScanStatus.COMPLETE)
        self.assertTrue(valid.snapshot_eligible)
        self.assertEqual(valid.deleted_keys({"old","keep"},{"keep"}), {"old"})
        zero = finish(stage=ScanStage.FINISH, discovered=0, processed=0,
                      discovery_complete=True)
        self.assertTrue(zero.snapshot_eligible)

    def test_partial_and_no_false_deleted(self):
        for code,stage in (
            (ErrorCode.UNREADABLE_DIRECTORY,ScanStage.DISCOVER),
            (ErrorCode.UNREADABLE_FILE,ScanStage.READ),
            (ErrorCode.UNSTABLE_FILE,ScanStage.READ),
            (ErrorCode.FILE_COUNT_LIMIT,ScanStage.DISCOVER),
            (ErrorCode.FILE_SIZE_LIMIT,ScanStage.READ),
            (ErrorCode.PATH_COLLISION,ScanStage.DISCOVER),
            (ErrorCode.CONTAINMENT,ScanStage.READ),
        ):
            with self.subTest(code=code):
                error = ScanError(code, stage, "src/old.py", code.name, retries=1)
                result = finish(stage=stage, discovered=4, processed=3,
                                discovery_complete=False, errors=(error,))
                self.assertEqual(result.status, ScanStatus.PARTIAL)
                self.assertFalse(result.snapshot_eligible)
                self.assertEqual(retain_previous("old-snapshot",result,"new"), "old-snapshot")
                with self.assertRaises(ValueError):
                    result.deleted_keys({"old"},set())

    def test_deleted_during_scan_and_directory_failure(self):
        for stage in (ScanStage.READ, ScanStage.DISCOVER):
            result = finish(stage=stage, discovered=2, processed=1,
                            discovery_complete=stage is ScanStage.READ)
            self.assertEqual(result.status,ScanStatus.PARTIAL)
            with self.assertRaises(ValueError):
                result.deleted_keys({"deleted"},set())

    def test_cancel_and_failed_root(self):
        cancelled = finish(stage=ScanStage.READ,discovered=2,processed=1,
                           discovery_complete=False,cancelled=True)
        self.assertEqual(cancelled.status,ScanStatus.CANCELLED)
        self.assertFalse(cancelled.snapshot_eligible)
        failed = finish(stage=ScanStage.VALIDATE_ROOT,discovered=0,processed=0,
                        discovery_complete=False,errors=(ScanError(
                            ErrorCode.INVALID_ROOT, ScanStage.VALIDATE_ROOT,
                            None,"Root missing"),))
        self.assertEqual(failed.status,ScanStatus.FAILED)
        self.assertFalse(failed.snapshot_eligible)

    def test_bounded_retries_and_invalid_counters(self):
        with self.assertRaises(ValueError):
            ScanError(ErrorCode.IO_ERROR,ScanStage.READ,"f.py","bad",retries=3)
        for d,p in ((-1,0),(1,2),(1,-1)):
            with self.assertRaises(ValueError):
                finish(stage=ScanStage.FINISH,discovered=d,processed=p,
                       discovery_complete=True)

    def test_deep_path_key_iterative_not_real_windows_path(self):
        value="/".join(["folder"]*4000+["f.py"])
        self.assertEqual(len(relative_parts(value)),4001)
        self.assertTrue(path_key(value).endswith("/f.py"))

@unittest.skipUnless(WIN, "Win32 API tests require a real Windows runner")
class WindowsProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="CC005 Security ")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base/"inside root tiếng Việt"
        self.root.mkdir()
        self.outside = self.base/"outside root"
        self.outside.mkdir()
        self.inside_file = self.root/"hello.py"
        self.inside_file.write_bytes(b"SAFE INSIDE\n")
        self.outside_file = self.outside/"secret.py"
        self.outside_file.write_bytes(b"EXTERNAL MARKER MUST NOT BE READ\n")

    def _junction(self, path: Path, target: Path):
        p = subprocess.run(["cmd","/c","mklink","/J",str(path),str(target)],
                           capture_output=True,text=True,check=False)
        if p.returncode != 0:
            self.skipTest("Junction creation unavailable: "+(p.stderr or p.stdout)[:200])

    def _symlink(self, path: Path, target: Path, directory=False):
        try:
            os.symlink(target, path, target_is_directory=directory)
        except (OSError,NotImplementedError) as exc:
            self.skipTest("Symlink privilege unavailable: "+str(exc))

    def test_local_root_and_handle_hash_no_execution(self):
        self.assertEqual(validate_root(self.root),self.root.resolve())
        marker = self.root/"EXECUTED"
        malicious = ("from pathlib import Path\nPath("+
                     repr(str(marker))+").write_text('ran')\n").encode()
        self.inside_file.write_bytes(malicious)
        with patch.object(socket.socket,"connect",side_effect=AssertionError("Network forbidden")):
            data = read_probe(self.root,"hello.py",chunk_size=9)
        self.assertEqual(data.sha256,hashlib.sha256(malicious).hexdigest())
        self.assertEqual(data.bytes_read,len(malicious))
        self.assertLessEqual(data.max_chunk,9)
        self.assertFalse(marker.exists())

    def test_missing_and_file_roots(self):
        with self.assertRaises((UnsafePath,OSError)):
            validate_root(self.base/"missing")
        with self.assertRaises(UnsafePath):
            validate_root(self.inside_file)

    def test_unc_refused_before_access(self):
        with self.assertRaises(UnsafePath):
            validate_root(r"\\server\share\project")

    def test_root_symlink_rejected(self):
        link = self.base/"linked root"
        self._symlink(link,self.root,directory=True)
        with self.assertRaises(UnsafePath):
            validate_root(link)

    def test_root_junction_rejected(self):
        link = self.base/"junction root"
        self._junction(link,self.root)
        with self.assertRaises(UnsafePath):
            validate_root(link)

    def test_nested_file_symlink_not_followed(self):
        link = self.root/"link.py"
        self._symlink(link,self.outside_file)
        with self.assertRaises(UnsafePath):
            read_probe(self.root,"link.py")

    def test_nested_directory_symlink_not_followed(self):
        link = self.root/"linkdir"
        self._symlink(link,self.outside,directory=True)
        with self.assertRaises(UnsafePath):
            read_probe(self.root,"linkdir/secret.py")

    def test_nested_junction_not_followed(self):
        link = self.root/"junction"
        self._junction(link,self.outside)
        with self.assertRaises(UnsafePath):
            read_probe(self.root,"junction/secret.py")

    def test_prefix_confusion(self):
        peer = self.base/(self.root.name+"-copy")
        peer.mkdir()
        (peer/"other.py").write_bytes(b"OUTSIDE")
        with self.assertRaises(UnsafePath):
            read_probe(self.root,"../"+peer.name+"/other.py")
        with self.assertRaises(UnsafePath):
            read_probe(self.root,str(peer/"other.py"))

    def test_before_open_file_changed(self):
        replacement = self.root/"other.py"
        replacement.write_bytes(b"CHANGED TARGET BUT INSIDE")
        def swap():
            os.replace(replacement,self.inside_file)
        with self.assertRaises((UnstableFile,UnsafePath,OSError)):
            read_probe(self.root,"hello.py",before_open=swap)

    def test_before_open_symlink_points_outside(self):
        replacement = self.root/"outside-link.py"
        self._symlink(replacement,self.outside_file)
        def swap():
            os.replace(replacement,self.inside_file)
        with self.assertRaises((UnsafePath,UnstableFile,OSError)):
            evidence = read_probe(self.root,"hello.py",before_open=swap)
            self.assertNotEqual(evidence.sha256,
                                hashlib.sha256(self.outside_file.read_bytes()).hexdigest())

    def test_before_open_junction_swap_to_outside(self):
        folder = self.root/"module"
        folder.mkdir()
        (folder/"secret.py").write_bytes(b"INNER")
        renamed = self.root/"held-module"
        def swap():
            os.rename(folder,renamed)
            self._junction(folder,self.outside)
        try:
            with self.assertRaises((UnsafePath,UnstableFile,OSError)):
                evidence = read_probe(self.root,"module/secret.py",before_open=swap)
                self.assertNotEqual(evidence.sha256,
                                    hashlib.sha256(self.outside_file.read_bytes()).hexdigest())
        finally:
            if folder.exists() and folder.is_junction():
                folder.rmdir()
            if renamed.exists():
                renamed.rename(folder)

    def test_truncated_during_preopen(self):
        def truncate():
            self.inside_file.write_bytes(b"x")
        with self.assertRaises(UnstableFile):
            read_probe(self.root,"hello.py",before_open=truncate)

    def test_growing_past_quota_before_open(self):
        def grow():
            with self.inside_file.open("ab") as f:
                f.write(b"x"*64)
        with self.assertRaises(FileTooLarge):
            read_probe(self.root,"hello.py",max_bytes=20,before_open=grow)

    def test_streaming_64_mib_boundary_sparse(self):
        large = self.root/"big.py"
        with large.open("wb") as f:
            f.truncate(MAX_BYTES)
        read = read_probe(self.root,"big.py")
        self.assertEqual(read.bytes_read,MAX_BYTES)
        self.assertEqual(read.max_chunk,1024*1024)
        with large.open("ab") as f:
            f.write(b"x")
        with self.assertRaises(FileTooLarge):
            read_probe(self.root,"big.py")

    def test_mapped_network_drive_when_available(self):
        from security_spike.windows_paths import k32, REMOTE
        drives = [f"{letter}:\\" for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                  if k32.GetDriveTypeW(f"{letter}:\\") == REMOTE]
        if not drives:
            self.skipTest("No mapped network drive on hosted runner; policy checked in code")
        for drive in drives:
            with self.assertRaises((UnsafePath,OSError)):
                validate_root(Path(drive))

if __name__ == "__main__":
    unittest.main()
