# CC-002 — Qt WebEngine + QWebChannel + Vite static integration spike

**Gate/task:** G0 / CC-002. **Master Plan:** 1.0.1. **Issue:** [#5](https://github.com/giabao2605/Code-City/issues/5). **PR:** [#6](https://github.com/giabao2605/Code-City/pull/6) (not merged). This is a diagnostic-only spike, not a Code City application or standalone installer.

## Architecture and trust boundary

```text
frontend/src (trusted, authored by Code City) -- npm ci / Vite build --> frontend/dist/
                                            static HTML/JS/CSS only
Python spike.app -> QApplication -> QMainWindow/QWebEngineView
  -> off-the-record QWebEngineProfile (OfflineInterceptor, Assets URL handler)
  -> LockedPage + QWebChannel(DiagnosticBridge)
  -> codecity-spike://app/index.html -> React mount
  -> codecity-spike://app/qwebchannel.js (read by QFile from Qt's bundled :/qtwebchannel/qwebchannel.js, no CDN)
  -> JS invokes Qt QObject request(JSON string) -> Python protocol validation -> pong callback
  <- Python QObject pushed signal <- QTimer app.ready on JS clientReady()
```

Only the **application-owned, built** files under `frontend/dist` are served by the custom scheme. No user-selected project, scanned file, HTTP server, browser filesystem API, shell command, arbitrary file picker, or scanner exists in this spike. `frontend/dist` must be generated from the checked-in frontend source; treat modification of installed assets as a supply-chain/integrity concern, not as untrusted project content.

## Dependency pins

Retained verbatim from CC-001: CPython 3.12.10 x64; Qt/PySide6 6.12.0; PySide6-WebEngine/Pdf 6.12.0.140; Node 24.22.0/npm 11.19.1; React/DOM 19.3.1; Three.js 0.186.1 (NOT imported for this spike); Vite 8.3.4; TypeScript 5.9.3; exact `@vitejs/plugin-react`/`@types` pins remain in the existing `frontend/package-lock.json`. **No new dependencies.**

## Run from scratch on Windows (PowerShell)

Developer machine must have Git, official x64 Python 3.12.10, Node 24.22.0 with npm 11.19.1, and network access for the **initial dependency installation only**.

```powershell
git clone https://github.com/giabao2605/Code-City.git
cd Code-City
git switch feature/CC-002-webengine-webchannel-spike
py -3.12 --version
node --version
npm --version
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt -c python-constraints.txt
.\.venv\Scripts\python.exe -m pip check
cd frontend
npm ci --no-audit --no-fund
npm run typecheck
npm run build
cd ..
.\.venv\Scripts\python.exe -m spike.app
```

**Expected:** a Qt window with React's `mounted` label, bridge `connected to Qt WebChannel`, and `app.ready` arriving in the unsolicited Python events section. Press **Send Ping**; the pong must echo the request ID and message; success counter advances. Repeat, close and relaunch. There must be **no Vite development server** and no runtime listener on localhost.

For a scripted build/unit/security/headless integration attempt, from repo root:

```powershell
.\scripts\cc002-smoke.ps1
```

Or after building, run individual tests from repo root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_protocol.py" -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_security.py" -v
$env:QT_QPA_PLATFORM="offscreen"
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_webengine.py" -v
Remove-Item Env:\QT_QPA_PLATFORM
node scripts/verify_governance.mjs
```

Do **not** use `--no-sandbox`, `--disable-web-security`, allow remote origins, or start an HTTP/WS server to make this pass. `--disable-gpu` is CI test-only, not set by production launcher.

## Implementation files

- `spike/protocol.py`: diagnostic request validation (Python stdlib).
- `spike/bridge.py`: QWebChannel QObject slot + independent signal; no privileged operations.
- `spike/security.py`: registered secure/local origin, allowlisted URL handler, request interceptor and navigation/popup policy.
- `spike/app.py`: Qt launcher, off-the-record profile, download cancellation and lifecycle logs.
- `frontend/index.html`, `src/*`, `vite.config.ts`, `tsconfig.json`: React diagnostics with enforced CSP and relative Vite base.
- `tests/test_protocol.py`, `tests/test_security.py`, `tests/test_webengine.py`: stdlib unit plus actual Qt integration/security probes.
- `scripts/cc002-smoke.ps1`, `.github/workflows/cc002-integration.yml`: PowerShell reproduction and hosted Windows CI.

## Diagnostic IPC only

Request string to QObject `request`:
```json
{"schemaVersion":1,"requestId":"ping-001","command":"diagnostics.ping","payload":{"message":"hello"}}
```
Response via **QWebChannel method callback**:
```json
{"schemaVersion":1,"requestId":"ping-001","event":"diagnostics.pong","payload":{"message":"hello","status":"ok"}}
```
Independent Qt `pushed` signal from Python:
```json
{"schemaVersion":1,"event":"app.ready","payload":{"sequence":1,"origin":"python"}}
```

Strict Python boundary: UTF-8 request length **at most 4096 bytes (4 KiB)**, message length **at most 128 UTF-8 bytes**, request IDs ASCII `[A-Za-z0-9_-]`, length 1–64, schemaVersion exactly integer 1; exact envelope keys; only `diagnostics.ping`. Invalid JSON, payloads, commands and IDs return `diagnostics.error` with a stable error code. The response includes the same valid request ID. React also validates version/event/payload, matching request ID and pong contents. These fixed diagnostic limits are conservative to prevent large objects crossing Qt's UI-thread IPC; they do **not** finalize the public V1 batch contract.

On page/reload initialization, JavaScript subscribes to `pushed` **before** calling `clientReady()`. Python queues a new `app.ready` via Qt timer on every handshake. Reload discards UI counters; a newly created WebChannel reconnects and receives a new sequence. No queued user tasks or long-running processes are used.

## Production-mode isolation and negative tests

- `codecity-spike://app/index.html` and hashed `/assets/*.js|css` only, served from canonical `frontend/dist` using a guarded `QWebEngineUrlSchemeHandler` (`SecureScheme | LocalScheme`), with host, request method, query, URL path and containment restrictions. QWebChannel JS is read from the exact Qt resource `:/qtwebchannel/qwebchannel.js` with `QFile`, then served at the exact allowlisted same-origin `/qwebchannel.js` route.
- A profile-level interceptor denies other requests, including HTTP, HTTPS, ws/wss, loopback, `file:`, unknown schemes and every direct `qrc:` URL. No network API endpoint is opened.
- `LockedPage.acceptNavigationRequest` allows just the mainframe home URL. `createWindow` refuses popups; JavaScript-created windows disabled; profile `downloadRequested` explicitly cancels.
- `QWebEngineProfile` off-the-record; `LocalContentCanAccessFileUrls` and `LocalContentCanAccessRemoteUrls` disabled; clipboard access denied; HTML CSP includes `default-src 'none'`, `connect-src 'none'`, `frame-src 'none'`, `object-src 'none'`, and limits script/style to trusted origins.
- Network negative tests use a **real test-only listening TCP loopback endpoint** and verify zero accepted connections for HTTP/HTTPS/WS/WSS; navigation, popup and file URL attempts are also tested. Unit policy tests include unknown schemes, non-app origins and path traversal. Rejections can happen at CSP/navigation/interceptor layers; these tests do not attribute an entire platform guarantee to one Qt API.

**Residual security scope:** Qt's interceptor may not observe every WebSocket flow; CSP plus deny-all network scheme policy provide defense-in-depth. A maliciously replaced `frontend/dist`, Chromium/Qt vulnerabilities, child-process traffic not mediated by the profile, and OS firewall-level isolation are not covered. An active loopback listener strengthens the denial evidence, but cannot prove all Chromium networking paths or OS-level traffic. A Qt native page-save action now probes the real profile download cancellation signal. Network capture and physical Win10/11 GPU smoke remain unverified. Do not describe this spike as the entire finished product being “offline secure.”

## Windows test evidence and states

Windows CI: [CC-002 Actions workflow](https://github.com/giabao2605/Code-City/actions/workflows/cc002-integration.yml). Verified CC-002 run [#39578515051](https://github.com/giabao2605/Code-City/actions/runs/39578515051) **SUCCESS**, 6/6 real Qt integration, Python IPC and security unit PASS, frontend typecheck/Vite build PASS, governance PASS. Workflow runs on hosted **Windows Server 2022**, which is not Windows 10/11 physical GUI/GPU smoke. A successful `npm run build` alone does not prove Chromium/QWebChannel. `tests/test_webengine.py` instantiates real Qt WebEngine after static build and interacts with JavaScript DOM/QObject; it is **not a mock**.

Early Windows runs failed on WebChannel cross-origin and Qt shutdown; corrected and retested. [Run #39578047710](https://github.com/giabao2605/Code-City/actions/runs/39578047710) **SUCCESS**: 5/5 real integration, subprocess exit code 0, Python unit/security, build, and governance PASS. Extended tests [#39578515051](https://github.com/giabao2605/Code-City/actions/runs/39578515051): **SUCCESS**. Active loopback listener accepted 0 blocked HTTP(S)/WS(S) connections; Qt `SavePage` emitted actual `downloadRequested` and cancellation was observed; six integration tests and clean process exit code 0 confirmed; **physical Windows 10 1809+/Windows 11 GUI smoke: NOT_RUN**; **standalone packaged exe: out of CC-002 scope / NOT_RUN**; **A01–A18: all NOT_RUN**. Update with confirmed run outcome, do not infer it from imports.

## Troubleshooting

- Blank/failed load: run `npm ci` and `npm run build` in `frontend`; inspect Python console (asset handler restricts file names/MIME).
- Bridge missing: inspect JavaScript console and check `/qwebchannel.js` resolves from the Qt `:/qtwebchannel/qwebchannel.js` resource at the same application origin; verify `QWebEnginePage.setWebChannel` is invoked before navigating.
- Wrong Python / missing WebEngine DLLs: ensure x64 Python 3.12.10, wheel constraints and `pip check`; consult `docs/CC001_SETUP.md`.
- Headless CI fails even though unit tests pass: report `FAIL/BLOCKED`; do not substitute mock tests as proof of actual Qt WebEngine. Reproduce on physical Windows GUI and attach console logs + OS/build/GPU details.
- Windows runtime crashes: preserve terminal log and version info; do not disable sandbox or security features.
- Test results are intentionally *not* Windows .exe packaging/release claims (CC-003).

**No ADR required:** no stack, schema for product commands, gate sequence or Master Plan changes were made.
