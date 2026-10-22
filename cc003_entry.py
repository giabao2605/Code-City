"""Nuitka entry point for CC-003 standalone integration spike, not the V1 application."""
import sys
from spike.app import main

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--smoke-test":
        from spike.packaged_smoke import smoke
        raise SystemExit(smoke())
    if len(sys.argv) != 1:
        print("Usage: CodeCitySpike.exe [--smoke-test]", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main())
