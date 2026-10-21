# WORK LOG — Nhật ký bàn giao theo phiên

> **Append-only.** Thêm entry mới ở đầu danh sách, không sửa/xóa lịch sử để che lỗi. Mỗi entry cần ngày UTC, CC task/gate, hành động thực tế, bằng chứng commit/PR, kiểm thử đã chạy/chưa chạy, blockers, next task. Khi thay đổi một entry cũ để sửa lỗi thông tin, thêm ghi chú correction có ngày.

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
