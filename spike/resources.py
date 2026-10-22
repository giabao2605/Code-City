"""Resolve application-owned Vite outputs; no CWD, user paths, URLs or dev servers."""
import sys
from pathlib import Path


def frontend_dist(*, executable=None, source_file=None, packaged=None):
    exe = Path(executable or sys.executable).resolve()
    source = Path(source_file or __file__).resolve()
    if packaged is None:
        # Nuitka marks compiled modules; the fixed exe name is an additional
        # guard against silently searching source on broken packaged installs.
        packaged = (getattr(sys, "frozen", False)
                    or "__compiled__" in globals()
                    or exe.name.casefold() == "codecityspike.exe")
    if packaged:
        return exe.parent / "frontend" / "dist"
    return source.parents[1] / "frontend" / "dist"
