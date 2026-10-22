"""Bound CI headless WebEngine test; always emit diagnostics rather than hanging."""
import subprocess
import sys

command = [sys.executable, "-u", "-m", "unittest", "discover", "-s",
           "tests", "-p", "test_webengine.py", "-v"]
print("CC-002 running REAL Qt WebEngine (hosted Windows, offscreen)", flush=True)
try:
    completed = subprocess.run(command, timeout=90, check=False)
except subprocess.TimeoutExpired:
    print("FAIL: real WebEngine integration exceeded 90 seconds on hosted CI; "
          "do NOT count imports/mocks as an integration PASS.", file=sys.stderr, flush=True)
    sys.exit(124)
print(f"REAL_WEBENGINE_PROCESS_RETURN_CODE={completed.returncode}", flush=True)
sys.exit(completed.returncode)
