# CC-003 — Windows standalone Qt WebEngine packaging spike

**Scope:** G0 / CC-003 · Master Plan v1.0.1 · [Issue #7](https://github.com/giabao2605/Code-City/issues/7) · branch `feature/CC-003-standalone-webengine-spike`.
**Status:** VERIFIED in G0/CC-003 packaging feasibility scope after two independent Windows Server 2022 workflows with actual frozen runtime tests, pending owner PR review. Physical Windows 10/11 and truly clean no-Python/Node VM acceptance remain NOT_RUN/UNVERIFIED. This is **not** Code City V1, G7 release engineering or an installer.

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

**Additional build-only pinned dependencies** in `packaging/cc003-build-requirements.txt`: Nuitka 4.1.1, ordered-set 4.1.0, zstandard 0.25.0. These are not consumer requirements. Compiler/Windows runner image vary by hosted image; log exact environment. **Observed packaging blocker:** Actions [run #39709854048](https://github.com/giabao2605/Code-City/actions/runs/39709854048) succeeded on all 15 unit tests, Qt/frontend dependency installation, `pip check`, frontend typecheck/build and governance, but Nuitka failed before EXE generation because Dependency Walker was missing and the non-interactive prompt defaulted to No. Added `--assume-yes-for-downloads` to the **pinned Nuitka** invocation, allowing the pinned compiler to download its fixed `https://dependencywalker.com/depends22_x64.zip` build-time binary into Nuitka's cache. This is not an unpinned pip/npm package, but its byte hash has not been independently locked; this is an explicit reproducibility/supply-chain limitation for CC-003 pending a captured checksum. Never ship or download it at consumer runtime. [Nuitka caching documentation](https://nuitka.net/user-documentation/tips.html). Pinning software versions does not imply byte-for-byte bit-reproducibility.

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

The smoke script launches the **actual packaged executable** twice, with a different current working directory, validates exit code AND the explicit real UI/IPC test PASS marker, checks for new orphan `QtWebEngineProcess` PIDs, and saves stdout/stderr logs. With `-NegativeTests`, it clones the installed folder into an independent Unicode/Vietnamese path, retests portability, then tests missing frontend, missing Qt WebEngine helper, and missing Chromium resource pack on **disposable copies only**.

The bundled `--smoke-test` launches a real `QApplication` and `QWebEngineView`, confirms loaded trusted origin and React DOM mount, QWebChannel connected, unsolicited `app.ready`, three Ping/Pong pairs with matching request IDs and zero failures, invalid command rejected, CSP/HTTP(S)/WS(S)/file fetch denied (including zero accepted test-only loopback TCP), navigation/popup/download blocked, reload+new Python event+Ping working, and clean Qt lifecycle. CLI test flags have no extra QWebChannel permissions. **Never set production `--no-sandbox` or `--disable-web-security`.**

## Evidence matrix — verified hosted Windows runs

**Two complete, independent build + consumer runs:** [push #39710663609](https://github.com/giabao2605/Code-City/actions/runs/39710663609) **SUCCESS** and [PR #39710667523](https://github.com/giabao2605/Code-City/actions/runs/39710667523) **SUCCESS**. Both have separate build/consumer jobs and `needs` barriers, without checkout or Python/Node setup on consumer.

| Check | Actual result and evidence |
|---|---|
| Source protocol/security/resources unit | **PASS:** 8/8 + 4/4 + 3/3 in each Windows build |
| Pinned Python toolchain, `pip check` | **PASS:** CPython 3.12.10 x64, PySide6 6.12.0, Nuitka 4.1.1, MSVC cl14.3 |
| Frontend `npm ci`, typecheck and Vite build | **PASS:** Node 24.22.0/npm 11.19.1, TypeScript/Vite static build |
| Nuitka frozen Windows executable | **PASS:** `CodeCitySpike.exe` built (5,689,856 bytes); onedir, no source checkout |
| Helper/Qt resources/Vite/static/manifest | **PASS:** 452 packaged files, helper `QtWebEngineProcess.exe`, 1 WebEngineCore DLL, `qwindows.dll`, ICU, Chromium `.pak`, 53 locale files, bundled HTML/JS/CSS |
| Artifact SHA-256 validated after separate-runner download | **PASS:** consumer extracted and matched ZIP hash |
| Frozen Qt WebEngine + React + QWebChannel | **PASS:** actual `CodeCitySpike.exe --smoke-test` loads static origin, mounts DOM, connects QWebChannel |
| Three ping/pong with matching IDs, Python `app.ready` | **PASS:** JS↔Python IPC, independent event, no response failures |
| Packaged security negative | **PASS:** malformed/unauthorized IPC, HTTP/HTTPS/WS/WSS/file fetch, external navigation, popup/download rejected, active TCP loopback accepted 0 connections |
| Reload/reconnect/new Python event | **PASS** |
| Restart, working directory and Unicode relocation | **PASS:** two independent successful launches; moved installed folder into a Vietnamese Unicode path, launched again |
| Missing frontend `index.html` | **PASS expected failure:** diagnostic exit 1 on disposable copy |
| Missing QtWebEngineProcess / Chromium resource pack | **PASS expected failure:** both launch attempts fail with nonzero process exit. Currently result is a native process crash, not a friendly error dialog; preserve as limitation |
| No new orphan helper after process exit | **PASS** |
| Separate hosted Windows build and consumer runners | **PASS:** run #39710663609 builder `GitHub Actions 1000001023`, consumer `1000001027`; run #39710667523 builder `1000001024`, consumer `1000001028`, Windows Server 2022 build 10.0.20348, image 20261012.333.1 |
| No runtime developer install / source checkout on consumer | **PASS for workflow design:** no setup/checkout, execute only ZIP-provided exe/scripts. This does not prove a truly clean host absent preinstalled runtimes |
| Physical clean Windows 10 1809+ | **NOT_RUN** |
| Physical clean Windows 11 | **NOT_RUN** |
| Truly clean machine with no Python/Node installed | **UNVERIFIED:** GitHub-hosted image may already have them |
| Disconnected Internet / OS-level network audit | **NOT_RUN:** CSP/network policy probes are bounded, not full OS isolation |
| Complete V1 A01–A18 | **NOT_RUN:** CC-003 does not count as product acceptance |

**Archived evidence:**
- [Push workflow artifact](https://github.com/giabao2605/Code-City/actions/runs/39710663609/artifacts/12397440833) · [consumer logs](https://github.com/giabao2605/Code-City/actions/runs/39710663609/artifacts/12396902917)
- [PR workflow artifact](https://github.com/giabao2605/Code-City/actions/runs/39710667523/artifacts/12397485278) · [consumer logs](https://github.com/giabao2605/Code-City/actions/runs/39710667523/artifacts/12396588127)
- Push run `CodeCitySpike.zip` **SHA-256**: `1c6f91d5ac63c5a29e34541f6222a7d6282faa0c003dd86c7fd7279f78e88ee1`.
- PR run `CodeCitySpike.zip` **SHA-256**: `a253a2913eb1d967c2283802a6fe01c00f54fd2f6ee4af6f2f39eec3a566534b`.
- Differences between the two successful ZIP digests are real and show this is a reproducible *process*, **not yet byte-for-byte deterministic output**.
- Both consumer jobs log `CC003_ALL_PACKAGED_SMOKE=PASS`, with normal/restart/relocation exit 0, and missing-assets/helper/resource negatives exit nonzero. Check archived stderr and process exit codes for exact details.

**Troubleshooting:** if `QtWebEngineProcess.exe`, `qwindows.dll`, `icudtl.dat`, `qtwebengine_resources.pak` or locale packs are missing, inspect Nuitka's build log and the generated file tree; do not fake structural PASS. Missing assets should raise before Qt window. Frozen `qwebchannel.js` failures often surface as bridge initialization timeouts; inspect stderr and ensure the bundled Qt resource is present. If separate-runner WebEngine hangs, retain timeout, child process logs and failed CI check; do not substitute a unit test or the build-machine smoke. When Python/Qt versions change, require change control and an ADR before upgrading pins.

**Limitations/out-of-scope:** G0 remains open for CC-004/005; physical Win10/11 standalone support, release installer, licensing/security hardening, complete offline scan/render/search product and acceptance A01–A18 are not established here. Rollback by reverting the CC-003 branch PR; it changes no user data/schema.
