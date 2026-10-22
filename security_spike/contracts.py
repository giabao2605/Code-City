"""CC-005 standalone quotas and scan outcome semantics, no production scanner/DB."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto

MAX_FILES = 20_000
MAX_BYTES = 64 * 1024 * 1024
CHUNK_BYTES = 1024 * 1024
EXTENSIONS = frozenset((".py",".js",".jsx",".ts",".tsx",".html",".css",".java",
    ".cs",".cpp",".c",".go",".rs",".php",".json",".yaml",".yml"))
IGNORED_DIRS = frozenset((".git",".venv","venv","node_modules",
    "__pycache__","dist","build",".next",".idea"))

class FileTooLarge(ValueError):
    pass
class FileCountExceeded(ValueError):
    pass
class ScanStatus(Enum):
    COMPLETE = auto()
    PARTIAL = auto()
    CANCELLED = auto()
    FAILED = auto()
class ScanStage(Enum):
    VALIDATE_ROOT = auto()
    DISCOVER = auto()
    READ = auto()
    FINISH = auto()
class ErrorCode(Enum):
    INVALID_ROOT = auto()
    UNSUPPORTED_DRIVE = auto()
    IO_ERROR = auto()
    UNREADABLE_DIRECTORY = auto()
    UNREADABLE_FILE = auto()
    UNSTABLE_FILE = auto()
    FILE_COUNT_LIMIT = auto()
    FILE_SIZE_LIMIT = auto()
    PATH_COLLISION = auto()
    CONTAINMENT = auto()
    RESOURCE_EXHAUSTED = auto()
    CANCELLED = auto()
    SYSTEM_FATAL = auto()

@dataclass(frozen=True)
class Limits:
    files: int = MAX_FILES
    bytes_per_file: int = MAX_BYTES
    chunk_bytes: int = CHUNK_BYTES
    retry_count: int = 1
    workers: int = 2

    def __post_init__(self) -> None:
        if (any(type(v) is not int for v in (
                self.files,self.bytes_per_file,self.chunk_bytes,
                self.retry_count,self.workers)) or
                not 1 <= self.files <= MAX_FILES or
                not 1 <= self.bytes_per_file <= MAX_BYTES or
                not 1 <= self.chunk_bytes <= CHUNK_BYTES or
                not 0 <= self.retry_count <= 1 or
                not 1 <= self.workers <= 4):
            raise ValueError("Invalid or unsafe scanner limits")

@dataclass
class FileBudget:
    config: Limits = field(default_factory=Limits)
    supported: int = 0

    def discover(self, name: str, parents: tuple[str,...] = ()) -> bool:
        if any(p.casefold() in IGNORED_DIRS for p in parents):
            return False
        if not any(name.casefold().endswith(ext) for ext in EXTENSIONS):
            return False
        if self.supported >= self.config.files:
            raise FileCountExceeded("Supported file quota exceeded")
        self.supported += 1
        return True

    def check_size(self, size: int) -> None:
        if type(size) is not int or size < 0 or size > self.config.bytes_per_file:
            raise FileTooLarge("Unsupported/oversized source file")

@dataclass(frozen=True)
class ScanError:
    code: ErrorCode
    stage: ScanStage
    relative_path: str | None
    message: str
    retries: int = 0

    def __post_init__(self) -> None:
        if self.retries < 0 or self.retries > 1:
            raise ValueError("Retry count must be bounded")

@dataclass(frozen=True)
class ScanOutcome:
    status: ScanStatus
    stage: ScanStage
    discovered: int
    processed: int
    discovery_complete: bool
    errors: tuple[ScanError, ...] = ()
    cancelled: bool = False

    @property
    def snapshot_eligible(self) -> bool:
        return (self.status is ScanStatus.COMPLETE and
                self.discovery_complete and not self.cancelled and
                not self.errors and self.discovered == self.processed)

    def deleted_keys(self, previous: set[str], current: set[str]) -> set[str]:
        if not self.snapshot_eligible:
            raise ValueError("Incomplete scans must never calculate committed deletions")
        return previous - current

def finish(*, stage: ScanStage, discovered: int, processed: int,
           discovery_complete: bool, errors: tuple[ScanError,...] = (),
           cancelled: bool = False, fatal: bool = False) -> ScanOutcome:
    if type(discovered) is not int or type(processed) is not int or not (0 <= processed <= discovered):
        raise ValueError("Invalid discovered/processed count")
    if cancelled:
        status = ScanStatus.CANCELLED
    elif fatal or (stage is ScanStage.VALIDATE_ROOT and errors):
        status = ScanStatus.FAILED
    elif errors or not discovery_complete or processed != discovered:
        status = ScanStatus.PARTIAL
    else:
        status = ScanStatus.COMPLETE
    return ScanOutcome(status, stage, discovered, processed, discovery_complete,
                       errors, cancelled)

def retain_previous(previous_snapshot: object, outcome: ScanOutcome,
                    proposed_snapshot: object) -> object:
    """No SQLite write: pure demonstration of commit eligibility."""
    return proposed_snapshot if outcome.snapshot_eligible else previous_snapshot
