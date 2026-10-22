# WORK LOG — Nhật ký bàn giao theo phiên

> **Append-only.** Thêm entry mới ở đầu danh sách, không sửa/xóa lịch sử để che lỗi. Mỗi entry cần ngày UTC, CC task/gate, hành động thực tế, bằng chứng commit/PR, kiểm thử đã chạy/chưa chạy, blockers, next task. Khi thay đổi một entry cũ để sửa lỗi thông tin, thêm ghi chú correction có ngày.

## 2026-10-22 — CC-003 VERIFIED after two real Windows standalone cross-runner smoke runs

- **Gate/task/next:** G0 remains IN_PROGRESS; CC-003 **VERIFIED in packaging spike scope**, next task CC-004 TODO **not authorized**; CC-001/002 VERIFIED, CC-005 TODO, G1–G8 LOCKED, A01–A18 NOT_RUN. CC-003 PR #8 unmerged pending owner.
- **GitHub evidence:** [push Actions #39710663609](https://github.com/giabao2605/Code-City/actions/runs/39710663609) and [PR Actions #39710667523](https://github.com/giabao2605/Code-City/actions/runs/39710667523) both **SUCCESS** with build and independent hosted consumer smoke jobs. [Issue #7](https://github.com/giabao2605/Code-City/issues/7), [draft PR #8](https://github.com/giabao2605/Code-City/pull/8); review/merge by owner only. Source protocol 8, security 4, resources 3 all PASS, npm ci/typecheck/Vite build, pip check and code governance PASS.
- **Actual artifact:** Nuitka 4.1.1, CPython 3.12.10 x64, PySide6/Qt 6.12.0, one-folder `CodeCitySpike.exe`, QtWebEngineProcess/Core DLL, qwindows, ICU/Chromium pack, 53 WebEngine locale paks and static React Vite assets. 452 files structural PASS. SHA256 ZIP **push** `1c6f91d5ac63c5a29e34541f6222a7d6282faa0c003dd86c7fd7279f78e88ee1`, **PR** `a253a2913eb1d967c2283802a6fe01c00f54fd2f6ee4af6f2f39eec3a566534b`. Byte-for-byte reproducibility NOT claimed.
- **Cross-runner:** hosted Windows Server 2022 10.0.20348; run push build runner 1000001023 / consumer 1000001027, PR build 1000001024 / consumer 1000001028. Consumer without checkout/setup Python/Node downloaded and checksum-verified zipped package, directly launched standalone EXE. Real Qt WebEngine loaded React; WebChannel connected, three Ping/Pong request IDs matched, Python unsolicited `app.ready`, request negative, CSP/HTTP(S)/WS(S)/file denied, loopback 0 accepted connections, popup/navigation/download blocked; reload/reconnect, restart, Unicode path relocation, no new orphan helper. `CC003_ALL_PACKAGED_SMOKE=PASS` twice, exit codes 0 on 3 expected-success launches in each run, nonzero on three deliberately broken copies. Archived packaged [PR logs](https://github.com/giabao2605/Code-City/actions/runs/39710667523/artifacts/12396588127).
- **Limitations:** runner image already includes developer tooling; genuinely clean OS no Python/Node UNVERIFIED. Physical Windows 10/11 GUI and disconnected-Internet/OS network audit NOT_RUN, acceptance A14/A15/A02/A18 not promoted. Missing Qt helper/resources cause native process failure rather than user-friendly preflight. Nuitka auxiliary Dependency Walker uses fixed upstream URL but downloaded byte hash not pinned: supply-chain hardening pending future gate. Nuitka runtime exception and third-party notices/license review needed before product release. No code beyond CC-003, no ADR or architecture change.
- **Governance/PR:** Master Plan unchanged, PROGRESS and README synchronized to next CC-004 after actual evidence. Final CI on documentation/status update head still needs validation; DO NOT merge without final required checks and owner review.

## 2026-10-22 — CC-003 actual Nuitka Windows artifact built; consumer workflow guard false failure

- **Build evidence:** [run #39710283408](https://github.com/giabao2605/Code-City/actions/runs/39710283408) build job SUCCESS: actual `CodeCitySpike.exe` 5,689,856 bytes, structural PASS 452 bundled files, QtWebEngineProcess.exe, qt6webenginecore.dll, qwindows.dll, 53 locale packs, Vite assets, ZIP/checksum/manifest. ZIP SHA256 `225bcaf6ce860d67a116d28b2aa01f591584e80dd1aa6b1e3d91696792161fe7`; [artifact](https://github.com/giabao2605/Code-City/actions/runs/39710283408/artifacts/12396354969). Python 8 protocol + 4 security + 3 resources tests, frontend Vite build, governance PASS.
- **Separate-runner evidence:** consumer Windows Server 2022 `GitHub Actions 1000001021` downloaded artifact with no checkout or Python/Node setup, verified matching ZIP SHA-256, structure PASS (453 files including manifest). It incorrectly failed **before executing EXE** because a shell wrapper inspected stale `$LASTEXITCODE` after a successful PowerShell verifier. No UI/IPC runtime PASS claimed. Build and smoke are separate hosted runners; physical clean Win10/11 still NOT_RUN.
- **Corrective action:** remove `$LASTEXITCODE` checks after PowerShell scripts (they throw on failure), keep exit code assertions inside the frozen-executable smoke. Add missing WebEngine resource pack negative on disposable clone. Next CI run must prove real packed Windows execution before status VERIFIED. G0/CC003 remain IN_PROGRESS.
- **Previous failed attempt:** [run #39709854048](https://github.com/giabao2605/Code-City/actions/runs/39709854048) failed at noninteractive Dependency Walker prompt, addressed by Nuitka build-time flag.

## 2026-10-22 — CC-003 failed Nuitka tool bootstrap, explicit build-time dependency fix

- **Observed failure:** [CC-003 PR build #39709854048](https://github.com/giabao2605/Code-City/actions/runs/39709854048) FAIL on real hosted Windows Server 2022: CPython 3.12.10 x64, Qt dependencies, pinned Nuitka 4.1.1, MSVC cl14.3, npm ci/typecheck/Vite build PASS; 8 protocol, 4 security and 3 resource tests PASS; local governance PASS. Nuitka recognized PySide6 Qt WebEngine and logged that it would include QtWebEngineProcess; no standalone output produced because Windows Dependency Walker missing and a non-interactive permission prompt defaulted to No. Consumer job SKIPPED, no cross-runner evidence.
- **Fix on feature branch:** authorize Nuitka 4.1.1's **build-time-only** `--assume-yes-for-downloads` for dependency walker (`https://dependencywalker.com/depends22_x64.zip`), preserve exact original product stack, document tool URL and unpinned downloaded binary digest as residual supply-chain concern. Must inspect new run logs; no claim of PASS. No PyInstaller fallback yet and no bypass of browser security.
- **Progress:** CC-003 IN_PROGRESS, G0 IN_PROGRESS, Next CC-003; no Windows physical Win10/Win11 smoke, no A01–A18 PASS.

## 2026-10-22 — CC-003 implementation started, packaging CI verification pending

- **Gate/task:** G0 / CC-003 IN_PROGRESS; Next task CC-003; CC-001/002 remain VERIFIED, CC-004/005 TODO, G1–G8 LOCKED, A01–A18 NOT_RUN. Owner explicitly authorized only CC-003.
- **GitHub source of truth:** main `d1b93cd66eb44530f65fa0965509891c1773e47f` after merged PR #6; main branch ruleset active and required `plan-progress-consistency` operational. [Issue #7](https://github.com/giabao2605/Code-City/issues/7), `feature/CC-003-standalone-webengine-spike`. Previous WORK_LOG statements that PR #6 was unmerged are historical checkpoints.
- **Code/scripts committed:** frozen `cc003_entry.py`, source/frozen `spike/resources.py`, source resource tests, standalone self-contained `spike/packaged_smoke.py`; pinned Nuitka 4.1.1, ordered-set 4.1.0, zstandard 0.25.0 build-only requirements; Windows PowerShell `cc003-build.ps1`, `cc003-verify-package.ps1`, `cc003-smoke.ps1`; `.github/workflows/cc003-standalone.yml` with independent build/consumer runners; `docs/CC003_PACKAGING.md`. Existing CC-002 network/IPC/CSP policies retained. No stack/architecture change or ADR; no CC-004/G1 implementation.
- **Evidence status at entry creation:** automated build-trigger [workflow](https://github.com/giabao2605/Code-City/actions/workflows/cc003-standalone.yml) dispatched from branch push; real Windows packaging, resource layout, ZIP SHA256, frozen Qt UI and cross-runner smoke **NOT_YET_VERIFIED** pending full CI logs. Linux local environment cannot execute Windows EXE; no false PASS claim. Python/source unit and frontend typecheck on **CC-003 head** also pending CI.
- **Expected cross-runner evidence:** independent Windows Server 2022 jobs, consumer no checkout/setup-python/setup-node, archived logs, explicit packaged smoke marker and exit codes. Hosted image may have Python/Node preinstalled; physical Win10/11 clean no-runtime and disconnected-Internet tests: NOT_RUN/UNVERIFIED. A14/A15 NOT_RUN, no V1 acceptance promoted.
- **Governance:** required validator is invoked by build script and protected PR workflow; PASS on final PR head must be checked after last commit. Owner decides merge, agent must NOT merge. Rollback by reverting PR with no user data migration.
- **Next:** inspect build and consumer job logs and fixes, update evidence/limits and PR body with actual outcomes. If clean runner check not proven, leave CC-003 IN_PROGRESS/BLOCKED, do not start CC-004.

## 2026-10-21 — CC-002 DoD verified on hosted Windows (PR unmerged)

- **UTC date:** 2026-10-21, **gate/task:** G0 / CC-002 **VERIFIED** in integration spike scope. **Next task by plan:** CC-003 TODO / **NOT AUTHORIZED**; G0 remains IN_PROGRESS and G1+ LOCKED.
- **GitHub:** [Issue #5](https://github.com/giabao2605/Code-City/issues/5), [PR #6](https://github.com/giabao2605/Code-City/pull/6) still **NOT MERGED**, branch `feature/CC-002-webengine-webchannel-spike`, final test implementation commit `39745e03bcab4e05fc74e922064c07a1b7bc34b4`; documentation status commit available on PR. No direct main commit and no bypass.
- **Windows Server 2022 hosted CI:** [PR integration run #39578515051](https://github.com/giabao2605/Code-City/actions/runs/39578515051) and [branch integration run #39578508910](https://github.com/giabao2605/Code-City/actions/runs/39578508910): **SUCCESS**; real QApplication/QWebEngineView loaded built Vite React assets; `QWebChannel` JS→Python ping/Python→JS callback/independent host `app.ready` signal; requestId/malformed validation; reload; no server at production; clean Qt shutdown `REAL_WEBENGINE_PROCESS_RETURN_CODE=0`. All six integration tests PASS.
- **Security evidence:** CSP denied HTTP, HTTPS, ws, wss and file fetch; test-only listening TCP loopback accepted **0** connections; external navigation and popup rejected; native Qt SavePage emitted downloadRequested, cancelled; untrusted URL schemes and local asset containment checked. Python protocol 8/8 PASS and URL policy tests 4/4 PASS.
- **Frontend/dependencies:** Python 3.12.10 x64 + six pinned PySide6 distributions / `pip check` PASS; Node 24.22.0/npm 11.19.1; `npm ci --no-audit --no-fund`, TS typecheck and `vite build` PASS; npm lock and Python constraints unchanged. No external runtime CDN, TCP server, scanner or code execution.
- **Governance:** [PR governance #39578515062](https://github.com/giabao2605/Code-City/actions/runs/39578515062) SUCCESS, `node scripts/verify_governance.mjs` PASS; README/PROGRESS are being changed to Next CC-003 in this final evidence commit and require fresh CI verification on final PR head.
- **NOT_RUN / limitations:** real physical Windows 10 1809+/Win11 GUI/GPU smoke NOT_RUN, standalone executable and clean-machine packaging CC-003 NOT_RUN, complete app offline acceptance NOT_RUN, acceptance **A01–A18 remain NOT_RUN**. Hosted Windows offscreen `--disable-gpu` has GLES diagnostic errors but all direct IPC/DOM tests PASS. This does not prove OS network isolation/zero child-process traffic; no release security signoff claimed.
- **Changed files:** Python spike, React TS/Vite static UI, tests, Windows workflow/PowerShell script, `docs/CC002_SPIKE.md`, PROGRESS/README/WORK_LOG. **No ADR or stack change.**
- **Decision:** CC-002 DoD passed within spike scope, ready for owner review/merge once final CI green; do not auto-merge or start CC-003.

## 2026-10-21 — CC-002 hosted Windows E2E clean process and extra security coverage

- **Evidence:** [Windows CI #39578047710](https://github.com/giabao2605/Code-City/actions/runs/39578047710) SUCCESS: five real Qt WebEngine integration tests, `REAL_WEBENGINE_PROCESS_RETURN_CODE=0`; 8 Python protocol tests PASS, 4 URL policy tests PASS, npm ci/typecheck/Vite build and governance PASS. [Second Windows CI #39578042402](https://github.com/giabao2605/Code-City/actions/runs/39578042402) and [standalone governance #39578047600](https://github.com/giabao2605/Code-City/actions/runs/39578047600) SUCCESS.
- **Verified fix:** Qt page/profile lifetime and DeferredDelete; React static frontend, WebChannel ping/pong, Python event, reject invalid IPC, network requests, popup/navigation and reload now work in hosted Windows offscreen.
- **Added tests pending:** test-only **active listening loopback** asserts no HTTP(S)/WS(S) TCP connection; Qt SavePage attempts an actual download and checks the profile cancellation signal. Do not count these as PASS until next CI results.
- **Still NOT_RUN:** physical Win10 1809+/Win11 GUI/GPU smoke; standalone exe (CC-003); A01–A18. PR #6 draft/unmerged; CC-002 IN_PROGRESS until expanded tests reviewed.

## 2026-10-21 — CC-002 WebChannel E2E PASS, teardown exit still failing

- **Evidence:** [Windows Server 2022 run #39577555655](https://github.com/giabao2605/Code-City/actions/runs/39577555655): actual Qt WebEngine + React + QWebChannel **5/5 integration methods report OK** after serving Qt's qwebchannel.js through same-origin handler; ping/pong, unsolicited event, negative IPC, CSP HTTP/HTTPS/WS/WSS/file fetch, external navigation/popup, reload/reconnect all exercised. Python unit 8/8, policy unit 4/4, `npm ci`/typecheck/Vite build all PASS.
- **Remaining failure:** workflow process exit code 1 after unittest reported OK, so **overall CI FAIL**, CC-002 remains IN_PROGRESS. The test also exposed a spurious `loadFinished(False)` dialog from intentionally denied navigation.
- **Follow-up code:** reorder Qt QObject parent creation to release QWebEngineView/page before off-the-record profile; flush DeferredDelete events explicitly in test teardown; suppress false load-error dialog for known blocked navigation; print test subprocess exit code for diagnosis. These changes must themselves be retested; no claim yet that CI is green.
- **Scope/decision:** no dependencies changed, no security downgrade, no ADR or CC-003. Physical Win10/Win11 GUI smoke NOT_RUN; A01–A18 NOT_RUN; PR #6 remains unmerged.

## 2026-10-21 — CC-002 real Windows bridge regression and same-origin Qt resource fix

- **Gate/task:** G0/CC-002 remains IN_PROGRESS, PR [#6](https://github.com/giabao2605/Code-City/pull/6) draft and unmerged; next CC-002.
- **Evidence:** [Windows run #39577058869](https://github.com/giabao2605/Code-City/actions/runs/39577058869) **FAIL** (not a mock): Vite static frontend React mounted and typecheck/build succeeded; Python protocol tests 8/8 PASS, security policy unit tests 4/4 PASS, WebEngine resource load succeeded; WebChannel bridge initialization/ping/reload failed. Browser CSP/network fetch and navigation/popup probes passed in that run, but this does not establish full isolation with active network listeners.
- **Root cause hypothesis:** directly loading qrc WebChannel JS from the secure custom-scheme page caused cross-scheme access issues. Implemented exact `/qwebchannel.js` same-origin route backed by Qt's bundled `:/qtwebchannel/qwebchannel.js` resource; tightened CSP to same-origin only, updated negative URL tests, retest required before PASS.
- **Test control:** headless integration now executed with 90-second subprocess timeout so failures cannot indefinitely hang CI; no sandbox or browser web-security bypass. GPU context errors recorded in hosted Windows Server logs, no physical Win10/Win11 GPU claim.
- **Dependencies:** no stack change or added package. **Next:** verify same-origin Qt resource availability and actual ping/pong on Windows CI, fix confirmed failures; no CC-003 and no merge.

## 2026-10-21 — CC-002 code spike and Windows verification initiated (unmerged)

- **UTC date:** 2026-10-21; **Gate/task:** G0 / CC-002 IN_PROGRESS; Next task CC-002 until DoD is evidenced.
- **Scope:** build Qt WebEngine with allowlisted trusted Vite static assets, QWebChannel diagnostic ping/pong + unsolicited Python event, off-the-record isolation, rejection policies and tests. No scanner/SQLite/Three renderer/standalone exe.
- **Issue/branch/PR:** [Issue #5](https://github.com/giabao2605/Code-City/issues/5), `feature/CC-002-webengine-webchannel-spike`, [draft PR #6](https://github.com/giabao2605/Code-City/pull/6), **NOT MERGED**.
- **Source commits:** `be3369dfd6bda02f505bbaaf390a2cc79cdb4fe0` (Python + unit tests), `ab9daef1a03025e48763aacce6c0c9d3da4b22f7` (React/Vite), `8a91db4116d4028c04dea15e1828a9dc47c84abc` (real Qt tests + Windows CI); this tracking/doc commit will be linked by the PR.
- **Files added/changed:** `spike/*`, `tests/*`, `frontend/index.html`, `frontend/src/*`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, frontend package scripts, `.github/workflows/cc002-integration.yml`, `scripts/cc002-smoke.ps1`, `docs/CC002_SPIKE.md`, README/PROGRESS/WORK_LOG. Locked Python constraints and npm lock unchanged.
- **Dependencies:** exact CC-001 baseline retained; no packages added. No public V1 command/schema change, no ADR.
- **Tests:** Windows hosted run [#39576528135](https://github.com/giabao2605/Code-City/actions/runs/39576528135) triggered; final status must be checked. Python protocol/security tests, `npm ci`, `npm run typecheck`, `npm run build`, real Qt WebEngine integration and governance are CI steps, not claimed PASS before logs confirm. Physical Windows 10/11 GUI smoke: NOT_RUN. Standalone packaging CC-003: NOT_RUN.
- **Security:** designed CSP deny network, URL scheme-handler allowlist, profile request interception, restricted navigation/popup/download and file access. Network/WS/navigation outcomes require real runtime evidence; an implemented policy alone does not equal verified guarantee.
- **IPC:** diagnostic envelope validation/unit tests and real WebChannel E2E included; actual JavaScript→Python→JavaScript success remains pending CI evidence.
- **Acceptance:** A01–A18 remain NOT_RUN; do not treat spike tests as final product acceptance.
- **Risk / next:** review Windows Qt offscreen integration logs, fix real failures, document CI pass/fail, run governance on final PR head; owner alone decides merge. Do not start CC-003.

## 2026-10-21 — Documentation handoff guard verified in PR #4

- **Gate/task:** G0, governance correction for CC-002 handoff. CC-001 VERIFIED; CC-002 TODO (authorized in new task prompt, implementation not started). No G1 unlock.
- **Issue / PR:** [Issue #3](https://github.com/giabao2605/Code-City/issues/3), [PR #4](https://github.com/giabao2605/Code-City/pull/4) (OPEN at this checkpoint; not merged). Branch `docs/G0-cc002-handoff-consistency`; source commit `c149398236d1685d681e74570ca40b26925c3beb`, regression test commit `21a629713a1bd936206ee2ed37e6484bf3480c65`.
- **Tests PASS:** [GitHub Actions governance run #39574386673](https://github.com/giabao2605/Code-City/actions/runs/39574386673) on Ubuntu: `node scripts/verify_governance.mjs` passes with consistent README/PROGRESS; intentional README Next task replacement with `CC-999` is rejected with expected error `README Next task differs from PROGRESS`. `git restore README.md` follows in regression step. Previous PR run [#39574156275](https://github.com/giabao2605/Code-City/actions/runs/39574156275) also PASSED the positive validator.
- **Tests NOT_RUN:** Qt/WebEngine ping-pong, GUI/Windows hardware smoke, network isolation, 3D, packaging, scanner, A01–A18. PR contains only governance docs/script/workflow changes.
- **Risk/next:** required checks must be revalidated on final PR head after this log addition; owner review/merge is needed before CC-002 agent can proceed. Do not merge autonomously or implement CC-002 in this docs PR.

## 2026-10-21 — Correction: G0/CC-002 handoff documents drifted after CC-001 merge

- **Mục tiêu / gate:** sửa lỗi đồng bộ trạng thái, không triển khai mã CC-002. Issue [#3](https://github.com/giabao2605/Code-City/issues/3). Main khi phát hiện: `38d091e6539f524337414807a72612fcebec5748` ([PR #2](https://github.com/giabao2605/Code-City/pull/2) đã squash merge).
- **Mâu thuẫn xác nhận:** `PROGRESS.md` báo G0/CC-002 TODO, CC-001 VERIFIED nhưng `README.md` còn ghi PLANNING/CC-001 đang thực hiện. `AGENTS.md` mô tả baseline DOCS_ONLY lịch sử không phân biệt với quyền ở phiên mới. `PROGRESS.md` còn lệnh 'CC-002 chưa được cấp phép', trong khi chủ dự án đã gửi prompt cấp phép CC-002 ở phiên triển khai mới.
- **Sửa trong branch:** đồng bộ README Phase/Current gate/Next task; giải thích baseline authorization là lịch sử trong AGENTS; cập nhật Authorization/G0 note/Blockers trong PROGRESS. Bổ sung guard kiểm tra README metadata so với PROGRESS để giảm khả năng tái diễn; không sửa Master Plan/stack/schema/acceptance.
- **Trạng thái:** CC-001 vẫn VERIFIED; CC-002 vẫn TODO (được cấp quyền nhưng chưa code); G0 IN_PROGRESS, các gate sau LOCKED; A01–A18 vẫn NOT_RUN.
- **Tests:** `node scripts/verify_governance.mjs` và required CI `plan-progress-consistency` sẽ được kiểm tra trên PR tài liệu; ở thời điểm ghi entry này: **NOT_RUN**, không nhận bừa PASS. Không thực hiện Qt/WebEngine/Windows/GPU smoke.
- **Risk / rollback:** thay đổi chỉ tài liệu và governance guard; rollback qua revert PR nếu validator có lỗi. GitHub PR cần review, không tự merge.
- **Next:** sau khi docs PR đã merge và CI xanh, phiên triển khai mới xác minh HEAD và thực hiện duy nhất CC-002 theo quyền đã cấp; CC-003 không được phép tự bắt đầu.

## 2026-10-21 — CC-001 DoD signed off for merge (owner authorization)

- **Task/gate:** G0 / CC-001 becomes **VERIFIED**; G0 remains IN_PROGRESS (CC-002–CC-005 TODO). **Next task:** CC-002, not yet authorized to implement.
- **Owner authorization:** project owner explicitly requested merge of [PR #2](https://github.com/giabao2605/Code-City/pull/2) on 2026-10-21. This entry was committed to the PR branch **before merge**; the actual merge SHA must be verified from GitHub, not assumed.
- **Evidence (Windows Server 2022 x64):** [lock-only CI #39571168925](https://github.com/giabao2605/Code-City/actions/runs/39571168925), [latest PR dependency run #39571641134](https://github.com/giabao2605/Code-City/actions/runs/39571641134) and [required PR governance #39571641218](https://github.com/giabao2605/Code-City/actions/runs/39571641218) **PASS**. Commands: Python 3.12.10 x64 assertion, pip install with exact six-package constraints, pip check, PySide6 QtWebEngineWidgets/QtWebChannel imports (Qt 6.12.0), Node 24.22.0/npm 11.19.1 assertions, npm ci from committed v3 lockfile, npm ls --all, Vite/tsc CLIs, node scripts/verify_governance.mjs.
- **Files in PR:** pinned Python dependencies/constraints; frontend manifest and npm-generated lock; toolchain pins; dependency matrix, Windows setup guide, read-only CI workflow; PROGRESS/WORK_LOG/README. No desktop shell, renderer, IPC spike, standalone packaging or new release.
- **Tests NOT RUN:** Qt WebEngine window or ping/pong (CC-002), exe packaging (CC-003), physical Windows 10 1809+/Windows 11 smoke, offline app run, GPU/WebGL, acceptance A01–A18. These are **not** asserted to PASS.
- **Residual risks:** Python 3.12.10 security patch gap vs source-only 3.12.15; Qt Windows 10 GPU/WebEngine runtime and packaging require separate proof. No architecture deviation or ADR.
- **Next action:** merge only after governance and dependency checks rerun successfully for the new commit. Merge through protected PR, then check main contains PROGRESS VERIFIED/Next CC-002. Owner approval to merge is **not** authorization to begin CC-002.

## 2026-10-21 — CC-001 PR and read-only Windows CI checkpoint

- **Task / status:** G0 / CC-001 **IN_PROGRESS**, next task CC-001 pending owner PR review/approval, not CC-002. PR [#2](https://github.com/giabao2605/Code-City/pull/2) open into main, **not merged**. Branch `feature/CC-001-dependency-lock`.
- **Verification evidence:** [Windows runner read-only locked reinstallation #39571168925](https://github.com/giabao2605/Code-City/actions/runs/39571168925) **SUCCESS**; [PR Windows dependencies #39571280503](https://github.com/giabao2605/Code-City/actions/runs/39571280503) **SUCCESS**; [PR required governance #39571280882](https://github.com/giabao2605/Code-City/actions/runs/39571280882) `plan-progress-consistency` **SUCCESS**. Pull Request review showed `mergeable_state=clean` before this final evidence update. `node scripts/verify_governance.mjs` PASS within Windows CI.
- **Test commands (Windows Server 2022 x64):** Python 3.12.10/64-bit assertion PASS; `pip install --only-binary=:all: -r requirements.txt -c python-constraints.txt` PASS; `python -m pip check` PASS; PySide6 WebEngineWidgets and WebChannel import / Qt 6.12.0 PASS; Node/npm 24.22.0/11.19.1 assertions PASS; `npm ci --no-audit --no-fund` from committed npm lock PASS; `npm ls --all` PASS; `npm run verify:toolchain` PASS; npm lock v3 assertion PASS; governance PASS.
- **Changed files in CC-001 PR:** `requirements.txt`, `python-constraints.txt`, `.python-version`, `.node-version`, `.gitignore`, `frontend/.npmrc`, `frontend/package.json`, `frontend/package-lock.json`, `docs/DEPENDENCY_MATRIX.md`, `docs/CC001_SETUP.md`, `.github/workflows/cc001-dependencies.yml`, `PROGRESS.md`, `README.md`, `docs/WORK_LOG.md`.
- **NOT_RUN:** local standalone on physical Win10 1809+/Win11, GPU/WebGL, Qt WebEngine page/ping-pong, static Vite assets, CodeCity.exe build, benchmarks, acceptance A01–A18. These require later CC tasks; CI hosted server is not a clean consumer OS smoke.
- **Risks/decision:** Python 3.12.10 last Windows installer vs 3.12.15 source-only security patches; monitor and seek owner agreement for patch/distribution hardening. GitHub Actions Node 20 action deprecation warning from `checkout@v4`/`setup-node@v4`/`setup-python@v5`, functional now but migration needed when hardening CI. No architecture change or ADR currently.
- **Next:** owner reviews PR #2 and approves merge separately. Do not merge autonomously. Gate G0 still IN_PROGRESS; CC-002 is NOT authorized.

## 2026-10-21 — CC-001 Windows first verification and dependency-tree correction

- **GitHub Actions:** [run #39570639921](https://github.com/giabao2605/Code-City/actions/runs/39570639921), Windows Server 2022 x64, job `cc001-windows-dependencies`, **SUCCESS**.
- **PASS:** `python --version` 3.12.10 + 64-bit assertion; `pip install --only-binary=:all: -r requirements.txt -c python-constraints.txt`; `python -m pip check` (No broken requirements found); `import PySide6; from PySide6 import QtWebEngineWidgets, QtWebChannel`; Qt version 6.12.0; Node 24.22.0/npm 11.19.1; `npm ci --no-audit --no-fund`; `npm ls --all`; `npm run verify:toolchain`; npm lock v3; `node scripts/verify_governance.mjs`.
- **Evidence-derived correction:** pip resolved six Python packages, not four. Also pin `PySide6_WebEngine==6.12.0.140` and `PySide6_Pdf==6.12.0.140`; WebEngine bindings reside in dedicated 131.7 MB wheel. `frontend/package-lock.json` was generated from npm 11.19.1 and committed by GitHub Actions bot (commit `ebab98d3a1f16fc872086096b2ac3c3141e4a4d5`), 57 entries / lock v3.
- **Hardening:** move npm engine-strict to `frontend/.npmrc`, remove one-time Actions lock generator after lock exists, CI contents permission becomes read-only. Follow-on run must confirm clean install using committed lock.
- **NOT_RUN:** physical Windows 10 1809+/Windows 11 GUI smoke, offline app runtime, WebEngine page/process, standalone packaging, and A01–A18.
- **Risks:** official Python 3.12.10 installer is behind security-source 3.12.15; Github Actions action versions currently use deprecated Node 20-based actions shim (warning, despite successful run); revisit under CI hardening. **Next:** PR checks and reviewer approval before merge; never CC-002 without authorization.

## 2026-10-21 — CC-001 dependency baseline initiated (feature branch)

- **Gate/task:** G0 / CC-001 IN_PROGRESS; authorized by owner; issue [#1](https://github.com/giabao2605/Code-City/issues/1).
- **Environment:** GitHub connector + public package metadata research; local sandbox is Linux Python 3.13.5 / Node 22.16.0, no external network. Local execution is **not** a test of target Windows stack.
- **Pinned:** Python 3.12.10 x64; PySide6/Qt, Addons, Essentials, shiboken6 6.12.0; Node 24.22.0/npm 11.19.1; React/DOM 19.3.1; Three 0.186.1; Vite 8.3.4; TypeScript 5.9.3; types/plugin see dependency matrix.
- **Files:** `requirements.txt`, `python-constraints.txt`, `.python-version`, `.node-version`, `.npmrc`, `.gitignore`, `frontend/package.json`, `docs/DEPENDENCY_MATRIX.md`, `docs/CC001_SETUP.md`, CI dependency verification workflow, `PROGRESS.md`, this log. `frontend/package-lock.json` to be generated by Windows CI and committed only if installation succeeds.
- **Tests at initiation:** Python Windows imports, pip check, npm ci/npm ls, frontend toolchain, governance: **NOT_RUN pending Actions result**. No physical Windows 10/11 or GPU smoke performed. Do not claim VERIFIED until checks reviewed.
- **Risk:** Python 3.12.10 has official installer but misses 3.12.15 security fixes; Qt Windows support documented but not tested; Actions is Windows Server 2022, not clean consumer Windows.
- **Next:** review Windows dependency workflow and lockfile, confirm `plan-progress-consistency` after PR, resolve any blocker; CC-002 remains TODO and unauthorized.

## 2026-10-21 — Governance verification checkpoint (docs only)

- **Gate/task:** G0 / CC-001 vẫn TODO; phase PLANNING_ONLY.
- **Tài liệu đã lưu:** `PROGRESS.md`, `AGENTS.md`, `docs/WORK_LOG.md`, `docs/ADR_TEMPLATE.md`, `.github/pull_request_template.md`, `scripts/verify_governance.mjs`, `.github/workflows/governance.yml`; `README.md` đã liên kết các tài liệu.
- **Kiểm tra tự động:** GitHub Actions [Governance guard run #39551417792](https://github.com/giabao2605/Code-City/actions/runs/39551417792) hoàn thành **SUCCESS** trên commit `238910af1920ed1526f833a85c9144b1602d6887`.
- **Kiểm tra phản chứng:** 5 trường hợp giả lập được validator phát hiện: thiếu task, VERIFIED không evidence, nhảy gate, sai version Master Plan, acceptance PASS không evidence. Kiểm tra thực hiện với cùng hàm validation được lưu trong script.
- **Giới hạn bằng chứng:** governance CI chỉ kiểm tra consistency tài liệu, không chứng minh ứng dụng/Windows/WebGL đã chạy. Các commit tài liệu bổ sung sau checkpoint sẽ tạo run CI mới và cần xác minh riêng.
- **Next:** chờ chủ dự án cho phép bắt đầu G0 / CC-001.

## 2026-10-21 — Governance bootstrap (docs only)

- **Gate/task:** G0 / CC-001 vẫn TODO. Chưa bắt đầu lập trình.
- **Mục tiêu phiên:** tạo cơ chế chống quên/chệch Master Plan theo yêu cầu chủ dự án.
- **Thực hiện:** lập `PROGRESS.md` với 9 gate, 43 task, 18 acceptance; `AGENTS.md` quy định cho AI; tài liệu bàn giao/ADR/PR template; script và workflow kiểm tra consistency.
- **Nguồn:** `MASTER_PLAN.md` v1.0.1; không thay đổi yêu cầu hay tiêu chí nghiệm thu.
- **Kiểm thử sản phẩm:** NOT_RUN, vì chưa có ứng dụng.
- **Kiểm thử quản trị:** kiểm tra cấu trúc ID/trạng thái bằng validator khi ghi file; CI GitHub Actions chỉ được tính PASS khi có run thành công.
- **Bằng chứng:** xem Git history của các file governance (commit cụ thể ghi trong GitHub; không giả định CI đã xanh).
- **Blocker:** cần người dùng cho phép bắt đầu G0 trước khi viết code ứng dụng.
- **Next:** G0 / CC-001, xác minh toolchain và lock versions theo Master Plan.
