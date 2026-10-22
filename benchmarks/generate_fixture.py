#!/usr/bin/env python3
"""CC-004 deterministic synthetic project fixture writer (stdlib-only, offline)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time

VERSION = "1"
OWNER = ".codecity-fixture-owner"
MAGIC = "codecity-cc004-fixture-v1"
EXTENSIONS = (".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css",
              ".java", ".cs", ".cpp", ".c", ".go", ".rs", ".php",
              ".json", ".yaml", ".yml")
IGNORED = (".git", ".venv", "venv", "node_modules", "__pycache__",
           "dist", "build", ".next", ".idea")
COUNTS = (500, 1000, 5000, 10000)
PROFILES = ("mixed", "tiny", "deep", "large")
ROOTS = ("src", "packages", "apps", "tests", "lib", "tools",
         "examples", "mã nguồn", "tài liệu có dấu", "Components")
NAMES = ("service", "model", "handler", "view", "index", "utils", "widget", "schema")


def canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def junction_or_link(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def assert_safe_output(output: Path) -> Path:
    # Do not silently resolve a user-supplied junction into another directory.
    target = Path(os.path.abspath(output))
    if target.exists() or target.is_symlink():
        raise ValueError("Output already exists; never overwrite a directory or link")
    if target == target.parent or target == Path.home() or target == Path.cwd():
        raise ValueError("Unsafe output root")
    if not target.parent.is_dir():
        raise ValueError("Parent directory must already exist")
    for part in (target.parent, *target.parent.parents):
        if junction_or_link(part):
            raise ValueError("Output ancestor is a symlink/junction")
    if os.name == "nt" and len(str(target)) > 150:
        raise ValueError("Output root too long for portable Windows fixture paths")
    return target


def relative_path(i: int, profile: str, seed: int) -> str:
    ext = EXTENSIONS[(i + seed) % len(EXTENSIONS)]
    top = ROOTS[((i // 13) + seed) % len(ROOTS)]
    section = f"area_{((i // 73) + seed) % 29:02d}"
    module = f"module_{(i // 17) % 31:02d}"
    if profile == "deep":
        depths = [f"branch_{((i // (11 ** j)) + seed) % 9:02d}" for j in range(8)]
        parts = [top, section, *depths, module]
    else:
        parts = [top, section, module]
    name = f"{NAMES[(i + seed) % len(NAMES)]}_{i:05d}{ext}"
    return "/".join((*parts, name))


def size_for(i: int, profile: str, seed: int) -> int:
    h = hashlib.sha256(f"{VERSION}:{profile}:{seed}:{i}".encode("ascii")).digest()
    x = int.from_bytes(h[:4], "big")
    if profile == "tiny":
        return (0, 4, 16, 32, 63, 120, 400)[x % 7]
    if profile == "deep":
        return 50 + x % 300
    if profile == "large":
        # A few larger files, not thousands of 64 MiB blobs.
        if i % 500 == 0:
            return 1_048_576 + (x % 8192)
        if i % 50 == 0:
            return 131_072 + (x % 4096)
        return 80 + x % 350
    if i % 100 == 0:
        return 16_384 + x % 4096
    if i % 7 == 0:
        return 1024 + x % 8192
    return 60 + x % 700


def write_bytes(path: Path, size: int, seed: int, rel: str) -> tuple[str, int]:
    digest = hashlib.sha256()
    signature = hashlib.sha256(f"{VERSION}:{seed}:{rel}".encode("utf-8")).hexdigest()
    line = (f"// synthetic Code City fixture {signature} path={rel}\n").encode("utf-8")
    # A dormant execution marker to make future tests catch accidental imports.
    if rel.endswith(".py") and rel.rsplit("_", 1)[-1].startswith("000"):
        line = (b'from pathlib import Path\n'
                b'Path("__CC004_EXECUTION_MARKER__").write_text("executed")\n') + line
    block = (line * max(1, 8192 // len(line) + 1))[:8192]
    remaining = size
    with path.open("xb") as out:
        while remaining:
            chunk = block[:min(remaining, len(block))]
            out.write(chunk)
            digest.update(chunk)
            remaining -= len(chunk)
    return digest.hexdigest(), size


def dataset_digest(entries: list[dict]) -> str:
    stable = [[e["path"], e["size"], e["sha256"], e["kind"]] for e in
              sorted(entries, key=lambda item: item["path"])]
    return hashlib.sha256(canonical(stable)).hexdigest()


def create(output: Path, count: int, profile: str, seed: int,
           max_bytes: int) -> dict:
    if count not in COUNTS or profile not in PROFILES:
        raise ValueError("Unsupported count or profile")
    if max_bytes < 1 or max_bytes > 2 * 1024 ** 3:
        raise ValueError("max-bytes must be between 1 and 2147483648")
    root = assert_safe_output(output)
    manifest_path = root.with_name(root.name + ".manifest.json")
    if manifest_path.exists() or manifest_path.is_symlink():
        raise ValueError("External manifest path exists; refusing overwrite")
    owner_bytes = canonical({"magic": MAGIC, "generatorVersion": VERSION,
                             "count": count, "profile": profile, "seed": seed}) + b"\n"
    ignored_entries = [(f"{d}/decoy_{i:02d}{EXTENSIONS[i % len(EXTENSIONS)]}",
                        "ignored", 64) for i, d in enumerate(IGNORED)]
    other_entries = [(f"assets/unsupported_{i:02d}.{ext}", "unsupported", 48)
                     for i, ext in enumerate(("txt", "md", "svg", "lock"))]
    expected_bytes = (len(owner_bytes) + sum(size_for(i, profile, seed)
                      for i in range(count)) + sum(s for _, _, s in
                      ignored_entries + other_entries))
    if expected_bytes > max_bytes:
        raise ValueError(f"Disk budget exceeded: {expected_bytes} > {max_bytes}")
    free = shutil.disk_usage(root.parent).free
    if expected_bytes + 16 * 1024 ** 2 > free:
        raise ValueError("Insufficient available disk space (+16 MiB reserve)")
    root.mkdir()
    started = time.perf_counter()
    entries: list[dict] = []
    try:
        owner_path = root / OWNER
        owner_path.write_bytes(owner_bytes)
        entries.append({"path": OWNER, "kind": "metadata", "size": len(owner_bytes),
                        "sha256": hashlib.sha256(owner_bytes).hexdigest()})
        plan = ((relative_path(i, profile, seed), "supported",
                 size_for(i, profile, seed)) for i in range(count))
        # Write and hash one file at a time; never hold large source bytes in RAM.
        for index, (rel, kind, size) in enumerate(
                list(ignored_entries + other_entries) +
                list(plan)):
            path = root.joinpath(*rel.split("/"))
            if os.name == "nt" and len(str(path)) > 240:
                raise ValueError(f"Windows path exceeds portable limit: {rel}")
            path.parent.mkdir(parents=True, exist_ok=True)
            sha, size = write_bytes(path, size, seed, rel)
            entries.append({"path": rel, "kind": kind, "size": size, "sha256": sha})
            if (index + 1) % 1000 == 0:
                print(f"generated {index + 1}/{count + 13}", file=sys.stderr)
        entries.sort(key=lambda e: e["path"])
        doc = {
            "schemaVersion": 1, "generatorVersion": VERSION,
            "seed": seed, "profile": profile, "count": count,
            "supportedFileCount": count,
            "ignoredFileCount": len(ignored_entries),
            "unsupportedFileCount": len(other_entries),
            "metadataFileCount": 1,
            "physicalFileCount": len(entries),
            "totalBytes": sum(e["size"] for e in entries),
            "datasetDigest": dataset_digest(entries),
            "files": entries,
        }
        # Manifest is outside fixture root, thus never counted as source.
        with manifest_path.open("xb") as handle:
            handle.write(json.dumps(doc, ensure_ascii=False, sort_keys=True,
                                    indent=2).encode("utf-8") + b"\n")
        elapsed = round(time.perf_counter() - started, 6)
        return {"status": "PASS", "root": str(root),
                "manifest": str(manifest_path), "count": count,
                "physicalFiles": len(entries), "totalBytes": doc["totalBytes"],
                "datasetDigest": doc["datasetDigest"],
                "generationSeconds": elapsed}
    except Exception:
        # Fail closed: preserve partial output, never delete user data automatically.
        print(f"PARTIAL fixture left at {root}; inspect before manual cleanup",
              file=sys.stderr)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count", type=int, required=True, choices=COUNTS)
    parser.add_argument("--profile", choices=PROFILES, default="mixed")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-bytes", type=int, default=256 * 1024 ** 2)
    args = parser.parse_args()
    try:
        result = create(args.output, args.count, args.profile, args.seed,
                        args.max_bytes)
    except (OSError, ValueError) as exc:
        print(f"CC004_GENERATION_ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
