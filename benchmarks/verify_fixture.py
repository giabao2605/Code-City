#!/usr/bin/env python3
"""CC-004 independent filesystem inventory and integrity verifier / safe cleanup."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys
import time

# Intentionally independent of generate_fixture.py: verify from the filesystem.
EXTENSIONS = frozenset((".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css",
                        ".java", ".cs", ".cpp", ".c", ".go", ".rs", ".php",
                        ".json", ".yaml", ".yml"))
IGNORE_NAMES = frozenset((".git", ".venv", "venv", "node_modules", "__pycache__",
                          "dist", "build", ".next", ".idea"))
OWNER = ".codecity-fixture-owner"
MAGIC = "codecity-cc004-fixture-v1"


def link(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def kind(rel: str) -> str:
    parts = rel.split("/")
    if rel == OWNER:
        return "metadata"
    if any(name.casefold() in IGNORE_NAMES for name in parts[:-1]):
        return "ignored"
    if Path(parts[-1]).suffix.lower() in EXTENSIONS:
        return "supported"
    return "unsupported"


def fingerprint(files: list[dict]) -> str:
    rows = [[x["path"], x["size"], x["sha256"], x["kind"]]
            for x in sorted(files, key=lambda e: e["path"])]
    return hashlib.sha256(canonical(rows)).hexdigest()


def inventory(root: Path) -> list[dict]:
    if not root.is_dir() or link(root):
        raise ValueError("Fixture root missing or link/junction")
    results = []
    for folder, dirs, names in os.walk(root, topdown=True, followlinks=False):
        parent = Path(folder)
        if link(parent):
            raise ValueError("Directory is a link/junction")
        for dirname in dirs:
            if link(parent / dirname):
                raise ValueError("Fixture contains directory link/junction")
        dirs.sort()
        for name in sorted(names):
            path = parent / name
            if link(path) or not path.is_file():
                raise ValueError("Fixture contains linked or non-regular file")
            rel = path.relative_to(root).as_posix()
            digest = hashlib.sha256()
            length = 0
            with path.open("rb") as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b""):
                    length += len(block)
                    digest.update(block)
            results.append({"path": rel, "size": length,
                            "sha256": digest.hexdigest(), "kind": kind(rel)})
    return sorted(results, key=lambda e: e["path"])


def verify(root: Path, manifest: Path) -> dict:
    started = time.perf_counter()
    root = Path(os.path.abspath(root))
    manifest = Path(os.path.abspath(manifest))
    if link(manifest) or not manifest.is_file():
        raise ValueError("Manifest missing or linked")
    try:
        doc = json.loads(manifest.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Manifest invalid JSON") from exc
    if not isinstance(doc, dict) or doc.get("schemaVersion") != 1:
        raise ValueError("Invalid manifest schema")
    expected = doc.get("files")
    if not isinstance(expected, list) or len(expected) != doc.get("physicalFileCount"):
        raise ValueError("Manifest physical count inconsistent")
    seen = set()
    for e in expected:
        if (not isinstance(e, dict) or set(e) !=
                {"path", "size", "sha256", "kind"}):
            raise ValueError("Invalid manifest file record")
        rel = e["path"]
        if (not isinstance(rel, str) or not rel or rel.startswith("/") or
                "\\" in rel or any(part in ("", ".", "..") for part in rel.split("/"))):
            raise ValueError("Unsafe manifest relative path")
        key = rel.casefold()
        if key in seen:
            raise ValueError("Manifest path casefold collision")
        seen.add(key)
        if kind(rel) != e["kind"]:
            raise ValueError("Manifest file category mismatch")
        if not isinstance(e["size"], int) or e["size"] < 0:
            raise ValueError("Invalid manifest file size")
        if not isinstance(e["sha256"], str) or len(e["sha256"]) != 64:
            raise ValueError("Invalid manifest checksum")
    actual = inventory(root)
    actual_keys = [e["path"].casefold() for e in actual]
    if len(set(actual_keys)) != len(actual_keys):
        raise ValueError("Case-insensitive filename collision")
    if actual != sorted(expected, key=lambda e: e["path"]):
        missing = set(e["path"] for e in expected) - set(e["path"] for e in actual)
        extra = set(e["path"] for e in actual) - set(e["path"] for e in expected)
        raise ValueError(f"Filesystem/manifest mismatch: missing={len(missing)} extra={len(extra)} or content changed")
    counts = Counter(e["kind"] for e in actual)
    for field, classification in [
            ("supportedFileCount", "supported"),
            ("ignoredFileCount", "ignored"),
            ("unsupportedFileCount", "unsupported"),
            ("metadataFileCount", "metadata")]:
        if counts[classification] != doc.get(field):
            raise ValueError(f"Count mismatch: {field}")
    if doc.get("count") != counts["supported"] or doc.get("count") not in (500, 1000, 5000, 10000):
        raise ValueError("Supported quota mismatch")
    if doc.get("totalBytes") != sum(e["size"] for e in actual):
        raise ValueError("Byte total mismatch")
    if doc.get("datasetDigest") != fingerprint(actual):
        raise ValueError("Dataset SHA-256 mismatch")
    supported_extensions = {Path(e["path"]).suffix.lower()
                            for e in actual if e["kind"] == "supported"}
    if supported_extensions != EXTENSIONS:
        raise ValueError("Missing or unsupported source extension")
    ignored_dirs = {e["path"].split("/")[0].casefold()
                    for e in actual if e["kind"] == "ignored"}
    if ignored_dirs != IGNORE_NAMES:
        raise ValueError("Incomplete ignored-dir decoy coverage")
    owner_rec = next((e for e in actual if e["path"] == OWNER), None)
    if owner_rec is None:
        raise ValueError("Missing ownership marker")
    try:
        marker = json.loads((root / OWNER).read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid ownership marker") from exc
    if (marker.get("magic") != MAGIC or marker.get("generatorVersion") != doc.get("generatorVersion") or
            marker.get("count") != doc.get("count") or marker.get("profile") != doc.get("profile") or
            marker.get("seed") != doc.get("seed")):
        raise ValueError("Ownership marker does not match manifest")
    return {"status": "PASS", "root": str(root), "manifest": str(manifest),
            "supportedFiles": counts["supported"], "ignoredFiles": counts["ignored"],
            "unsupportedFiles": counts["unsupported"],
            "physicalFiles": len(actual), "totalBytes": doc["totalBytes"],
            "datasetDigest": doc["datasetDigest"],
            "verificationSeconds": round(time.perf_counter() - started, 6)}


def cleanup(root: Path, manifest: Path) -> dict:
    root = Path(os.path.abspath(root))
    manifest = Path(os.path.abspath(manifest))
    if (manifest != root.with_name(root.name + ".manifest.json") or
            root == root.parent or root == Path.home() or root == Path.cwd() or
            link(root) or link(manifest)):
        raise ValueError("Unsafe cleanup target")
    for ancestor in (root.parent, *root.parent.parents):
        if link(ancestor):
            raise ValueError("Cleanup path includes a link/junction")
    # Full validation before any destructive operation. No rmtree, no following links.
    evidence = verify(root, manifest)
    actual = inventory(root)
    for entry in actual:
        file = root.joinpath(*entry["path"].split("/"))
        if link(file):
            raise ValueError("Linked file during cleanup")
        file.unlink()
    directories = []
    for folder, subdirs, _ in os.walk(root, topdown=False, followlinks=False):
        for name in subdirs:
            directories.append(Path(folder) / name)
    for directory in sorted(directories, key=lambda d: len(d.parts), reverse=True):
        if link(directory):
            raise ValueError("Linked directory during cleanup")
        directory.rmdir()
    root.rmdir()
    manifest.unlink()
    return {"status": "CLEANED", "supportedFiles": evidence["supportedFiles"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--cleanup", action="store_true",
                        help="Delete only a fully validated owned fixture and sibling manifest")
    args = parser.parse_args()
    manifest = args.manifest or args.root.with_name(args.root.name + ".manifest.json")
    try:
        result = cleanup(args.root, manifest) if args.cleanup else verify(args.root, manifest)
    except (ValueError, OSError, TypeError, KeyError) as exc:
        print(f"CC004_VERIFICATION_ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
