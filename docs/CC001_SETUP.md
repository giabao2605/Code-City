# CC-001 — Windows dependency installation and verification

Preconditions: Git, **CPython 3.12.10 Windows x64** (last official installer for Python 3.12), **Node 24.22.0 Windows x64** (bundles npm **11.19.1**), a network connection to package registries for initial development install. No application or 3D shell is included in CC-001.

Official downloads: [Python 3.12.10](https://www.python.org/downloads/release/python-31210/) and [Node 24.22.0](https://nodejs.org/en/download/archive/v24.22.0).

## Clone and verify tool versions (PowerShell)

```powershell
git clone https://github.com/giabao2605/Code-City.git
cd Code-City
git switch feature/CC-001-dependency-lock
py -3.12 --version
py -3.12 -c "import sys, struct, platform; assert sys.version_info[:3] == (3,12,10); assert struct.calcsize('P')*8 == 64; print(platform.platform())"
node --version
npm --version
# Expected: Python 3.12.10 x64, v24.22.0, 11.19.1
```

If the versions mismatch, stop and install the exact versions above. A current 3.12.15 source release does not provide a standard Windows installer. This baseline is not a recommendation to ignore security fixes; Python patch/distribution migration needs approval and new testing.

## Fresh Python environment

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt -c python-constraints.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -c "import PySide6; from PySide6 import QtWebEngineWidgets, QtWebChannel; from PySide6.QtCore import qVersion; assert qVersion() == '6.12.0'; print('Qt:', qVersion(), 'WebEngine/WebChannel import OK')"
.\.venv\Scripts\python.exe -m pip list --format=freeze
```

The constraints pin the direct and five transitive PySide6 distributions to 6.12.0; only binary wheels are allowed. A clean `pip check` and imports do not prove a real Qt window launches.

## Fresh npm environment

```powershell
cd frontend
npm ci
npm ls --all
npm run verify:toolchain
node -e "const p=require('./package-lock.json'); if(p.lockfileVersion!==3) process.exit(1); console.log('npm lock v3 OK')"
cd ..
node scripts/verify_governance.mjs
```

Run `npm ci`, **not** `npm install`, for reproduction. npm installation uses the checked-in lock, including integrity metadata for transitive dependencies. The `verify:toolchain` script checks compiler/build tool CLIs only; there is no frontend source code at this gate. Do not run `vite build` expecting an app in CC-001.

## If a step fails

- **Wrong interpreter/npm/architecture:** reinstall exact x64 releases; confirm `py -0p`, `node --version` and `npm --version`. Do not alter pins silently.
- **pip cannot find a wheel:** check Python x64/3.12, `pip --version` and online registry; capture the complete error. The all-binary policy intentionally blocks unsupported builds.
- **pip conflicts:** record `pip check`, environment and package list. Use a newly created venv rather than mutating global Python.
- **npm ci lock mismatch:** this is a blocker. Do **not** hand-edit `package-lock.json`; generate it in a controlled clean environment and commit the resulting diff through PR review.
- **npm registry/network fail:** check connectivity and proxy, re-run; if offline, this is a development setup limitation, not an app runtime test.
- **Qt Windows DLL import fail:** record exact Windows build, architecture, VC++ runtime availability and traceback. Do not claim Windows supported on the basis of Linux tests.
- **Governance check fail:** preserve logs and fix tracking consistency before PR merge.

GitHub Actions windows-2022 runner may exercise installers and imports. It is **Windows Server 2022**, not an isolated clean-machine Windows 10 1809 or Windows 11 GUI/graphics smoke test.
