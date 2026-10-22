"""CC-005 isolated Windows filesystem security feasibility probe, NOT the product scanner.

Reject reparse points, require local fixed disks and validate the opened handle's
actual path and volume before reading. This is NOT an atomic ancestor walk.
"""
from __future__ import annotations

from dataclasses import dataclass
import ctypes
from ctypes import wintypes
import hashlib
import ntpath
import os
from pathlib import Path
import stat
import sys
import unicodedata
from typing import Callable

from security_spike.contracts import FileTooLarge, MAX_BYTES

WIN = sys.platform == "win32"
REPARSE = 0x400
INVALID_HANDLE = ctypes.c_void_p(-1).value
READ = 0x80000000
SHARE_ALL = 0x00000001 | 0x00000002 | 0x00000004
OPEN_EXISTING = 3
OPEN_REPARSE = 0x00200000
BACKUP = 0x02000000
SEQUENTIAL = 0x08000000
REMOTE = 4
FIXED = 3

class UnsafePath(ValueError):
    """Untrusted filesystem path, link, escaping target or unsupported drive."""

class UnstableFile(OSError):
    """A file or selected project root changed during a validation/read."""

@dataclass(frozen=True)
class ReadEvidence:
    sha256: str
    bytes_read: int
    max_chunk: int
    chunks: int

if WIN:
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD,
        wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD,
        wintypes.HANDLE]
    k32.CreateFileW.restype = wintypes.HANDLE
    k32.GetDriveTypeW.argtypes = [wintypes.LPCWSTR]
    k32.GetDriveTypeW.restype = wintypes.UINT
    k32.GetFinalPathNameByHandleW.argtypes = [wintypes.HANDLE,
        wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD]
    k32.GetFinalPathNameByHandleW.restype = wintypes.DWORD
    k32.GetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
    k32.GetFileInformationByHandle.restype = wintypes.BOOL
    k32.ReadFile.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
    k32.ReadFile.restype = wintypes.BOOL
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    k32.CloseHandle.restype = wintypes.BOOL

    class FileTime(ctypes.Structure):
        _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]

    class HandleInfo(ctypes.Structure):
        _fields_ = [
            ("attributes", wintypes.DWORD),
            ("created", FileTime),
            ("accessed", FileTime),
            ("written", FileTime),
            ("serial", wintypes.DWORD),
            ("size_high", wintypes.DWORD),
            ("size_low", wintypes.DWORD),
            ("links", wintypes.DWORD),
            ("file_index_high", wintypes.DWORD),
            ("file_index_low", wintypes.DWORD),
        ]

def require_windows() -> None:
    if not WIN:
        raise OSError("CC-005 handle experiment requires actual Windows")

def is_reparse(path: Path) -> bool:
    info = path.lstat()
    return bool(getattr(info, "st_file_attributes", 0) & REPARSE) or (
        path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())
    )

def relative_parts(value: str) -> tuple[str, ...]:
    """Refuse absolute, traversal, ADS and Win32 ambiguous components."""
    if not isinstance(value, str) or not value or "\x00" in value:
        raise UnsafePath("Empty or invalid relative path")
    if value.startswith(("/", "\\")) or "\\" in value or ":" in value:
        raise UnsafePath("Absolute, backslash or ADS path")
    parts = tuple(value.split("/"))
    devices = {"CON", "PRN", "AUX", "NUL",
               *(f"COM{i}" for i in range(1, 10)),
               *(f"LPT{i}" for i in range(1, 10))}
    for part in parts:
        if (part in ("", ".", "..") or part[-1:] in (" ", ".") or
                part.split(".")[0].upper() in devices or
                any(ord(c) < 32 for c in part)):
            raise UnsafePath("Traversal or ambiguous Win32 component")
    return parts

def path_key(relative: str) -> str:
    return unicodedata.normalize("NFC", "/".join(relative_parts(relative))).casefold()

def reject_collisions(paths: list[str]) -> None:
    seen: set[str] = set()
    for path in paths:
        key = path_key(path)
        if key in seen:
            raise UnsafePath("Unicode/casefold relative path collision")
        seen.add(key)

def validate_root(root: str | Path) -> Path:
    require_windows()
    selected = Path(root)
    if not selected.is_absolute():
        raise UnsafePath("Root must be an absolute user-selected directory")
    if str(selected).startswith("\\\\") or selected.drive.startswith("\\\\"):
        raise UnsafePath("UNC roots unsupported in V1")
    if is_reparse(selected):
        raise UnsafePath("Root is a reparse point")
    if not selected.is_dir():
        raise UnsafePath("Root is not a directory")
    canonical = selected.resolve(strict=True)
    if str(canonical).startswith("\\\\") or canonical.drive.startswith("\\\\"):
        raise UnsafePath("Resolved UNC path unsupported")
    drive_root = canonical.drive + "\\"
    if not canonical.drive or k32.GetDriveTypeW(drive_root) != FIXED:
        raise UnsafePath("Only local fixed volumes supported")
    if is_reparse(canonical):
        raise UnsafePath("Canonical root is a reparse point")
    return canonical

def _open(path: Path, directory: bool) -> wintypes.HANDLE:
    flags = OPEN_REPARSE | (BACKUP if directory else SEQUENTIAL)
    h = k32.CreateFileW(str(path), READ, SHARE_ALL, None, OPEN_EXISTING, flags, None)
    if h is None or h == INVALID_HANDLE:
        raise ctypes.WinError(ctypes.get_last_error())
    return h

def _info(handle: wintypes.HANDLE) -> HandleInfo:
    data = HandleInfo()
    if not k32.GetFileInformationByHandle(handle, ctypes.byref(data)):
        raise ctypes.WinError(ctypes.get_last_error())
    if data.attributes & REPARSE:
        raise UnsafePath("Opened handle is reparse point")
    return data

def _final_path(handle: wintypes.HANDLE) -> str:
    buf = ctypes.create_unicode_buffer(32768)
    size = k32.GetFinalPathNameByHandleW(handle, buf, len(buf), 0)
    if size == 0 or size >= len(buf):
        raise OSError("GetFinalPathNameByHandleW unavailable/too long")
    return ntpath.normcase(ntpath.normpath(buf.value))

def _fingerprint(info: HandleInfo) -> tuple[int, ...]:
    return (info.serial, info.file_index_high, info.file_index_low,
            info.size_high, info.size_low, info.written.high, info.written.low)

def _stat_fingerprint(path: Path) -> tuple[int, ...]:
    st = path.stat(follow_symlinks=False)
    return st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns

def _preflight(root: Path, parts: tuple[str, ...]) -> Path:
    path = root
    for index, component in enumerate(parts):
        path = path / component
        if is_reparse(path):
            raise UnsafePath("Link/junction/reparse point in path")
        mode = path.lstat().st_mode
        if index < len(parts) - 1 and not stat.S_ISDIR(mode):
            raise UnsafePath("Non-directory ancestor")
        if index == len(parts) - 1 and not stat.S_ISREG(mode):
            raise UnsafePath("Not a regular source file")
    resolved = path.resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise UnsafePath("Resolved target escapes root") from exc
    return path

def read_probe(root: Path, relative: str, *,
               before_open: Callable[[], None] | None = None,
               after_first_chunk: Callable[[], None] | None = None,
               chunk_size: int = 1024 * 1024,
               max_bytes: int = MAX_BYTES) -> ReadEvidence:
    """Experimental handle-pinned streaming hash, with deterministic race hook.

    Never returns source bytes; rejects uncertain results. Windows-only.
    """
    if type(chunk_size) is not int or not (1 <= chunk_size <= 1024 * 1024):
        raise ValueError("chunk_size must be 1..1048576")
    if type(max_bytes) is not int or not 1 <= max_bytes <= MAX_BYTES:
        raise ValueError("max_bytes must be a positive integer")
    trusted_root = validate_root(root)
    parts = relative_parts(relative)
    candidate = _preflight(trusted_root, parts)
    old_file = _stat_fingerprint(candidate)
    old_root = _stat_fingerprint(trusted_root)
    if old_file[2] > max_bytes:
        raise FileTooLarge("Preflight file exceeds per-file quota")
    if before_open:
        before_open()
    root_handle = _open(trusted_root, True)
    try:
        root_info = _info(root_handle)
        root_final = _final_path(root_handle)
        file_handle = _open(candidate, False)
        try:
            file_info = _info(file_handle)
            file_final = _final_path(file_handle)
            # A string prefix alone is unsafe (root vs root-copy). Also compare volume.
            if (file_info.serial != root_info.serial or
                    not file_final.startswith(root_final.rstrip("\\") + "\\")):
                raise UnsafePath("Opened target is outside pinned root handle")
            actual_size = (file_info.size_high << 32) | file_info.size_low
            if actual_size > max_bytes:
                raise FileTooLarge("Opened file exceeds quota")
            if actual_size != old_file[2]:
                raise UnstableFile("File size changed before handle opened")
            digest = hashlib.sha256()
            total = chunks = largest = 0
            buffer = ctypes.create_string_buffer(chunk_size)
            while True:
                got = wintypes.DWORD()
                if not k32.ReadFile(file_handle, buffer, chunk_size,
                                   ctypes.byref(got), None):
                    raise ctypes.WinError(ctypes.get_last_error())
                if not got.value:
                    break
                total += got.value
                if total > max_bytes:
                    raise FileTooLarge("File grew above quota while streaming")
                digest.update(buffer.raw[:got.value])
                chunks += 1
                largest = max(largest, got.value)
                if chunks == 1 and after_first_chunk:
                    after_first_chunk()
            end_info = _info(file_handle)
            if (total != actual_size or
                    _fingerprint(file_info) != _fingerprint(end_info) or
                    old_file != _stat_fingerprint(candidate) or
                    old_root != _stat_fingerprint(trusted_root) or
                    is_reparse(candidate) or
                    _final_path(file_handle) != file_final or
                    _final_path(root_handle) != root_final):
                raise UnstableFile("Filesystem changed across validation/read")
            return ReadEvidence(digest.hexdigest(), total, largest, chunks)
        finally:
            k32.CloseHandle(file_handle)
    finally:
        k32.CloseHandle(root_handle)
