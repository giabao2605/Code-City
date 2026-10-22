# CC-003 — Windows standalone Qt WebEngine packaging spike

**Scope:** G0 / CC-003 · Master Plan v1.0.1 · [Issue #7](https://github.com/giabao2605/Code-City/issues/7) · branch `feature/CC-003-standalone-webengine-spike`.
**Status:** IN_PROGRESS until an actual independent Windows runner executes the frozen EXE and required DoD checks pass. This is **not** Code City V1, G7 release engineering or an installer.

## Packaging decision and upstream evidence

Primary builder: **Nuitka 4.1.1, --mode=standalone, --enable-plugin=pyside6**, compiled Windows x64 one-folder, with embedded Python/PySide6/Qt binaries and explicit trusted Vite static output. This uses the Nuitka engine recommended by Qt's `pyside6-deploy` wrapper, but invokes pinned Nuitka directly so there is no auto-install or uncontrolled spec-generation step. Qt 6.12 defaults to standalone for `pyside6-deploy`; Qt documentation notes Nuitka 4.1.1 as its default and `--no-install` for managing build packages explicitly.

- [Official Qt for Python pyside6-deploy documentation](https://doc.qt.io/qtforpython-6/deployment/deployment-pyside6-deploy.html)
- [Nuitka standalone mode / Qt PySide6 plugin / include-data-dir](https://nuitka.net/user-documentation/user-manual.html)
- [Qt WebEngine deployment instructions](https://doc.qt.io/qt-6/qtwebengine-deploying.html)
- [Nuitka 4.1.1 version evidence](https://pypi.org/project/Nuitka/4.1.1/)

The PySide6 Nuitka plugin is expected to package `QtWebEngineProcess.exe`, `Qt6WebEngineCore.dll`, plugins/resources/locales when the WebEngine modules are imported. This expectation must be verified from the produced package, not assumed. Nuitka can require Windows MSVC Build Tools; the build captures the runner image/compiler environment. **Nuitka has AGPL licensing; redistribution/commercial-use review is still an open G6/G7 item.** Fallback to exact-version PyInstaller onedir is allowed only if a concrete Nuitka issue is logged and tests repeated. No fallback has been asserted here.

## Exact dependency baseline

**Runtime libraries packaged:** CPython 3.12.10 x64; PySide6 6.12.0, PySide6-Addons/Essentials 6.12.0, shiboken6 6.12.0, PySide6-WebEngine and Pdf 6.12.0.140. Python dependency control: unchanged `requirements.txt` + `python-constraints.txt`; these controls pin versions, but do not yet pin wheel hashes.

**Frontend build-only:** Node.js 24.22.0, npm 11.19.1; React/ReactDOM 19.3.1, Three.js 0.186.1, Vite 8.3.4, TypeScript 5.9.3; `frontend/package-lock.json` unchanged. `npm ci` builds only trusted static assets; Node/npm are never called at end-user runtime.

**Additional build-only pinned dependencies** in `packaging/cc003-build-requirements.txt`: Nuitka 4.1.1, ordered-set 4.1.0, zstandard 0.25.0. These are not consumer requirements. Compiler/Windows runner image vary by hosted image; log exact environment. Pinning software versions does not imply byte-for-byte bit-reproducibility.

## Resource resolution and trust

`cc003_entry.py` is the Nuitka executable entry point. It invokes the existing CC-002 `spike.app`; `--smoke-test` additionally runs frozen real Qt/React/QWebChannel checks. The only customer-facing surface remains the CC-002 diagnostic application. `spike/resources.py` resolves source-mode assets relative to its own module and frozen-mode assets relative to the bundled `CodeCitySpike.exe`; it does not use current working directory, source checkout or external fallback. For packaged-mode missing assets, fail with an explicit error, not a dev HTTP server.

The `Assets` Qt custom URL scheme handler retains exact allowlisted application-owned URLs, path containment, same-origin `/qwebchannel.js` read from `:/qtwebchannel/qwebchannel.js`, CSP and profile-level scheme deny rules. No user project files are web resources. No scanner/SQLite/3D development is included.

## From fresh clone on Windows (PowerShell)

Prerequisites: Git, **CPython 3.12.10 x64**, **Node 24.22.0** (npm 11.19.1), Windows MSVC Build Tools, network for initial developer dependencies. Open PowerShell at repo root or run the script by absolute path; it resolves the root from `$PSScriptRoot`.

```powershell
git clone https://github.com/giabao2605/Code-City.git
cd Code-City
git switch feature/CC-003-standalone-webengine-spike
.\scripts\cc003-build.ps1 -PythonCommand python
```

Build script validates versions, builds a clean pinned virtual environment if missing, installs PySide6/Nuitka, runs `pip check`, frontend `npm ci`/typecheck/build, protocol/security/resource unit tests and governance. Nuitka creates `build/cc003/cc003_entry.dist/` (exact build temp name may vary); script identifies actual `*.dist` directory and copies it to the staged output. It runs structural verification and packages ZIP and SHA-256 checksum.

**Expected output (verify the actual output):**

```text
dist/cc003/
  CodeCitySpike/
    CodeCitySpike.exe
    frontend/dist/index.html
    frontend/dist/assets/*.js and *.css
    QtWebEngineProcess.exe (actual path determined by Nuitka)
    Qt WebEngine DLLs / resources (*.pak, icudtl.dat)
    platform plugin qwindows.dll and WebEngine locales
    cc003-manifest.json
  tools/
    cc003-verify-package.ps1
    cc003-smoke.ps1
  CodeCitySpike.zip
  CodeCitySpike.sha256
```

`scripts/cc003-verify-package.ps1` checks executable, React static assets, QtWebEngine helper/Core DLL, qwindows plugin, ICU, resource pack and locales; writes or validates a JSON inventory with SHA-256 hashes for important files. **Structural PASS is not runtime PASS.** The archive checksum refers to the ZIP only.

## Cross-runner verification (not a clean OS)

[GitHub Actions CC-003 workflow](https://github.com/giabao2605/Code-City/actions/workflows/cc003-standalone.yml) has two jobs with `needs`: Windows Server 2022 build on one runner and **a separate new Windows runner** to download *only the ZIP*, validate its hash, expand in an independent directory and directly launch the bundled EXE. Consumer runner performs **no checkout and no setup-python/setup-node**. It does not install extra dependencies or rely on the source tree.

Hosted Windows Server images generally already include development runtimes. **A job not calling Python/Node is NOT proof of a machine without Python/Node installed**. No Internet disconnect is enforced on hosted runner; CSP, URL policy and an actively listening test-only TCP loopback provide bounded offline-behavior evidence, not an OS-level network isolation audit. Both jobs record runner/Windows build identities. `QT_QPA_PLATFORM=offscreen` and Chromium `--disable-gpu` are CI-only environment settings, never production security bypasses.

After extracting the ZIP on an independent Windows machine, from any PowerShell directory:

```powershell
$bundle = 'C:\Path With Spaces\Extracted CC003'
& "$bundle\tools\cc003-verify-package.ps1" -PackageDir "$bundle\CodeCitySpike"
& "$bundle\tools\cc003-smoke.ps1" -PackageDir "$bundle\CodeCitySpike" -TimeoutSeconds 110 -NegativeTests
& "$bundle\CodeCitySpike\CodeCitySpike.exe"
```

The smoke script launches the **actual packaged executable** twice, with a different current working directory, validates exit code AND the explicit real UI/IPC test PASS marker, checks for new orphan `QtWebEngineProcess` PIDs, and saves stdout/stderr logs. With `-NegativeTests`, it clones the installed folder into an independent Unicode/Vietnamese path, retests portability, then tests missing frontend and missing helper on **disposable copies only**.

The bundled `--smoke-test` launches a real `QApplication` and `QWebEngineView`, confirms loaded trusted origin and React DOM mount, QWebChannel connected, unsolicited `app.ready`, three Ping/Pong pairs with matching request IDs and zero failures, invalid command rejected, CSP/HTTP(S)/WS(S)/file fetch denied (including zero accepted test-only loopback TCP), navigation/popup/download blocked, reload+new Python event+Ping working, and clean Qt lifecycle. CLI test flags have no extra QWebChannel permissions. **Never set production `--no-sandbox` or `--disable-web-security`.**

## Evidence matrix (updated only after viewing the actual Actions run)

| Check | Initial state | Required proof |
|---|---|---|
| Source unit IPC/security/resources | NOT_RUN for CC-003 branch | Build job logs |
| Frontend `npm ci`, typecheck, build | NOT_RUN for CC-003 branch | Build job logs |
| Nuitka standalone .exe | UNVERIFIED | Real produced executable in Actions artifact |
| QtWebEngine helper/resources/manifest | UNVERIFIED | Structural manifest and relevant log |
| Frozen WebEngine + React + QWebChannel | NOT_RUN | Consumer job packaged log with PASS marker |
| Three pings/events, reload/restart, negative policy | NOT_RUN | Packaged stdout/stderr and exit codes |
| Separate runner portability | NOT_RUN | Two distinct hosted job IDs/runner details |
| Runtime no developer Node/npm invocation | UNVERIFIED | No consumer-side installation, frozen process logs |
| Truly clean Windows with neither Python nor Node | UNVERIFIED | Independent VM/physical system inventory |
| Physical Windows 10 1809+ | NOT_RUN | Target OS smoke outside hosted Server 2022 |
| Physical Windows 11 | NOT_RUN | Target OS smoke outside hosted Server 2022 |
| Disconnected Internet / OS network audit | NOT_RUN | Isolated real Windows environment |
| A01–A18 final Code City V1 acceptance | NOT_RUN | Full product tasks, not CC-003 |

**Troubleshooting:** if `QtWebEngineProcess.exe`, `qwindows.dll`, `icudtl.dat`, `qtwebengine_resources.pak` or locale packs are missing, inspect Nuitka's build log and the generated file tree; do not fake structural PASS. Missing assets should raise before Qt window. Frozen `qwebchannel.js` failures often surface as bridge initialization timeouts; inspect stderr and ensure the bundled Qt resource is present. If separate-runner WebEngine hangs, retain timeout, child process logs and failed CI check; do not substitute a unit test or the build-machine smoke. When Python/Qt versions change, require change control and an ADR before upgrading pins.

**Limitations/out-of-scope:** G0 remains open for CC-004/005; physical Win10/11 standalone support, release installer, licensing/security hardening, complete offline scan/render/search product and acceptance A01–A18 are not established here. Rollback by reverting the CC-003 branch PR; it changes no user data/schema.
