# CC-001 — Dependency matrix (G0, Master Plan v1.0.1)

**Date:** 2026-10-21 UTC. **State:** IN_PROGRESS, pending install + reproducibility evidence. **Target:** Windows 10 1809+ x64 and Windows 11 x64. **Scope:** dependency baseline only. **Issue:** https://github.com/giabao2605/Code-City/issues/1

## Evidence codes
- **VERIFIED:** command/install/test actually executed, with OS, command, outcome and linked CI/log.
- **DOCUMENTED:** upstream documentation, package registry release files or metadata, *not* a successful local install.
- **UNVERIFIED:** insufficient evidence for this particular combination/platform.
- **BLOCKED:** unable to continue a specific test because an obstacle has been identified.

## Matrix

| Component | Exact version | Role / compatibility | Evidence status and source | Risk / open validation |
|---|---|---|---|---|
| Python (CPython x64) | **3.12.10** | Local scanner/backend and venv; last Python 3.12 with official 64-bit Windows installer | **DOCUMENTED** [Python 3.12.10 release](https://www.python.org/downloads/release/python-31210/) | 3.12.15 security source release is newer **without** official Windows installers. Security patches absent from 3.12.10; re-evaluate a secure Windows Python 3.12 distribution before release. |
| PySide6 / Qt | **6.12.0** | Desktop Qt binding, Qt6 WebEngine/WebChannel baseline; `cp310-abi3-win_amd64` published, usable by CPython 3.12 under abi3 | **DOCUMENTED** [PySide6 release](https://pypi.org/project/PySide6/6.12.0/) and [Qt 6.12 Windows](https://doc.qt.io/qt-6.12/windows.html) | DLL load, display/GPU, Qt packaging and actual Win10/Win11 startup unverified. |
| PySide6-Addons | **6.12.0** | Provides QtWebEngineWidgets and QtWebChannel bindings | **DOCUMENTED** [wheels](https://pypi.org/project/PySide6-Addons/6.12.0/) | Runtime imports still require test; wheel includes Qt WebEngine libraries, not proof of clean-machine startup. |
| PySide6-Essentials | **6.12.0** | QtCore/QtWidgets core bindings | **DOCUMENTED** [wheels](https://pypi.org/project/PySide6-Essentials/6.12.0/) | Native DLL loading and redistribution verification pending. |
| shiboken6 | **6.12.0** | Required PySide6 binding runtime | **DOCUMENTED** [release](https://pypi.org/project/shiboken6/6.12.0/) | Must match PySide6 patch exactly. |
| Qt WebEngine | **Qt 6.12.0** | Embedded Chromium view from PySide6-Addons, *not* a separately pinned pip package | **DOCUMENTED** [Qt for Windows](https://doc.qt.io/qt-6.12/windows.html) | Browser startup and bundled subprocess/resources are CC-002/CC-003, NOT_RUN. |
| Qt WebChannel | **Qt 6.12.0** | Native ↔ web IPC module from PySide6-Addons, *not* a separately pinned pip package | **DOCUMENTED** [Qt for Python](https://doc.qt.io/qtforpython-6/) | Ping/pong is CC-002, NOT_RUN. |
| Node.js x64 | **24.22.0 LTS** | Build-only frontend runtime, no dependency for end-user offline app | **DOCUMENTED** [Node archive incl. Windows x64](https://nodejs.org/en/download/archive/v24.22.0) and [releases](https://nodejs.org/en/about/previous-releases) | Actual CLI test required on Windows CI. |
| npm | **11.19.1** | npm bundled with Node 24.22.0, package lock v3 and `npm ci` | **DOCUMENTED** [Node archive](https://nodejs.org/en/download/archive/v24.22.0) | Verify `npm --version` on CI. |
| React | **19.3.1** | Declarative UI, exact same patch as react-dom | **DOCUMENTED** [npm React](https://www.npmjs.com/package/react) | No React app at CC-001, runtime render NOT_RUN. |
| React DOM | **19.3.1** | React browser renderer, aligned with React | **DOCUMENTED** [npm React DOM](https://www.npmjs.com/package/react-dom) | No browser/UI smoke until CC-002. |
| Three.js | **0.186.1** | WebGL instancing/3D, ESM build import | **DOCUMENTED** [three release](https://www.npmjs.com/package/three) and [upstream releases](https://github.com/mrdoob/three.js/releases) | WebGL hardware, OrbitControls, Raycaster integration NOT_RUN. |
| Vite | **8.3.4** | Build-time static assets tool, no runtime localhost/CDN required | **DOCUMENTED** [npm Vite](https://www.npmjs.com/package/vite) | CLI version check first; static asset delivery CC-002. Vite 8 uses Rolldown; optional binaries differ by OS. |
| TypeScript | **5.9.3** | Conservative mature TS compiler version; avoids untested TypeScript 7 migration | **DOCUMENTED** [TypeScript npm](https://www.npmjs.com/package/typescript) | Full typecheck deferred until app TS sources exist; run tsc CLI now. |
| @vitejs/plugin-react | **6.1.2** | Vite React plugin for later frontend integration | **DOCUMENTED** [npm plugin](https://www.npmjs.com/package/@vitejs/plugin-react) | Validate npm peer dependency tree. |
| @types/react / react-dom | **19.3.0 / 19.3.0** | Type declarations matching React major | **DOCUMENTED** [React types](https://www.npmjs.com/package/@types/react), [DOM types](https://www.npmjs.com/package/@types/react-dom) | Typecheck of actual app deferred. |
| @types/three | **0.186.0** | Type declarations matching Three r186 | **DOCUMENTED** [Three types](https://www.npmjs.com/package/@types/three) | Extra transitive type-only libraries pulled in; `npm ls` and lock needed. |

**Documented OS support ≠ Windows verification.** Qt lists Windows 10 (1809+) x64 and Windows 11 x64 for Qt 6.12, noting it is the last Qt release supporting Win10. This does not certify QtWebEngine start-up on those OSes, physical Win10/Win11 smoke or packaged app behavior.

## Pinning policy
- Python: `.python-version` chooses exact interpreter; `requirements.txt` contains one direct package; `python-constraints.txt` pins **all four** packages in PySide6 dependency tree (without hashes). `--only-binary=:all:` prevents source builds. This controls resolution, not wheel-byte integrity; hash-pinned per-platform wheels are a later hardening item.
- Frontend: `.node-version`, `engines`, `.npmrc` and exact manifest dependencies; lockfile v3 expected from **actual npm on Windows**. `npm ci` must succeed from checked-in lock; otherwise state stays IN_PROGRESS.
- Never depend on CDN/Internet at packaged application runtime. Registry access during developer/CI installation is distinct from user-runtime offline requirement.
- This task intentionally does not scaffold Vite app, Qt desktop window or release exe.

## CI evidence ledger
At first commit, documentation and release artifacts are **DOCUMENTED**, not VERIFIED. GitHub Actions job `cc001-windows-dependencies` must record fresh package lock generation, `npm ci`, `npm ls --all`, Python 3.12 x64, `pip check`, PySide6 imports and toolchain versions. Update this section with actual run URL and PASS/FAIL after checking logs.

**Untested (out of scope):** Qt window + QWebChannel ping/pong, QtWebEngine local assets, app packaging, physical Win10/Win11 smoke, GPU, offline app, scanner tests and acceptance A01–A18.
