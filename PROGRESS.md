# Code City V1 — PROGRESS (sổ tiến độ chính thức)

> **Trạng thái triển khai, không thay thế [MASTER_PLAN.md](MASTER_PLAN.md).** Mọi ID CC-xxx và Axx được lấy trực tiếp từ Master Plan v1.0.1. Không sửa nội dung/scope task tại đây; chỉ cập nhật trạng thái và bằng chứng.
>
> **Cách đọc:** TODO = chưa làm; IN_PROGRESS = đang làm; BLOCKED = bị chặn; VERIFIED = đã kiểm chứng và có link bằng chứng. Không có bằng chứng = không được VERIFIED.

## 1. Trạng thái hiện tại

- **Plan version:** `1.0.1`
- **Phase:** `IN_DEVELOPMENT`
- **Current gate:** `G0`
- **Next task:** `CC-004`
- **Updated (UTC):** `2026-10-22`
- **Authorization:** `G0_CC-004_APPROVED` (CC-004 đã được chủ dự án cấp quyền riêng ngày 2026-10-22; CC-005 chưa được cấp quyền).
- **Ghi chú:** CC-001 VERIFIED/merged. CC-002 VERIFIED trong phạm vi spike nhờ Qt WebEngine + QWebChannel thực chạy trên hosted Windows Server 2022, 6 integration tests, protocol/security unit, static Vite build và governance CI PASS ([run #39578515051](https://github.com/giabao2605/Code-City/actions/runs/39578515051)). PR #6 là bằng chứng code/test; xác minh trạng thái merge trực tiếp trên GitHub. CC-003 VERIFIED trong giới hạn packaging feasibility nhờ Nuitka standalone exe thực, Qt WebEngine assets và hai lượt build + real packaged smoke trên các Windows Server 2022 hosted runners độc lập ([PR #8](https://github.com/giabao2605/Code-City/pull/8), [push run #39710663609](https://github.com/giabao2605/Code-City/actions/runs/39710663609), [PR run #39710667523](https://github.com/giabao2605/Code-City/actions/runs/39710667523)). CC-004 là next task và đang IN_PROGRESS theo ủy quyền ngày 2026-10-22. Chưa có benchmark hoặc physical Windows 10/11 GUI smoke; các nghiệm thu A01–A18 vẫn NOT_RUN.
- **Bằng chứng trạng thái:** [Master Plan](MASTER_PLAN.md); [Nhật ký làm việc](docs/WORK_LOG.md); [Governance CI đã chạy thành công](https://github.com/giabao2605/Code-City/actions/runs/39551417792) (run đầu, không phải test ứng dụng).

## 2. Gate tracker

| Gate | Trạng thái | Exit evidence | Ghi chú |
|---|---|---|---|
| G0 | IN_PROGRESS | - | CC-001, CC-002, CC-003 VERIFIED theo đúng DoD từng task; CC-004 IN_PROGRESS; CC-005 TODO/chưa cấp phép; G0 chưa đạt exit gate |
| G1 | LOCKED | - | Desktop shell + scanner (10% + 20%); chưa mở gate |
| G2 | LOCKED | - | Persistence + snapshots (15%); chưa mở gate |
| G3 | LOCKED | - | Layout ổn định + city data contract (12% trong nhóm layout/renderer); chưa mở gate |
| G4 | LOCKED | - | Three.js renderer + interaction cơ bản (13% còn lại của nhóm layout/renderer); chưa mở gate |
| G5 | LOCKED | - | Product UX và native integration (15%); chưa mở gate |
| G6 | LOCKED | - | Hardening, đo hiệu năng và kiểm thử hệ thống (10%); chưa mở gate |
| G7 | LOCKED | - | Windows release engineering (5%); chưa mở gate |
| G8 | LOCKED | - | V1 release decision (không tự động publish); chưa mở gate |

**Quy tắc gate:** chỉ gate hiện tại được READY / IN_PROGRESS / BLOCKED; gate trước phải VERIFIED và có exit evidence; gate sau LOCKED. Không nhảy G0→G2. Gate chỉ VERIFIED khi tất cả task thuộc gate VERIFIED và có bằng chứng exit gate trong Master Plan.

## 3. Task tracker

| Task | Gate | Nội dung từ Master Plan | Trạng thái | Evidence | Ghi chú |
|---|---|---|---|---|---|
| CC-001 | G0 | Chốt Python 3.12, PySide6/Qt 6.12.x, Node LTS, React, Three.js, Vite, TypeScript exact versions; tạo lockfiles và dependency matrix. | VERIFIED | https://github.com/giabao2605/Code-City/pull/2 | DoD dependency: Windows Server 2022 Python/Qt imports, pip check, npm ci from committed lock, npm ls, toolchain PASS; governance CI PASS; chủ dự án cho phép merge; physical Windows smoke là task G0/G7 sau |
| CC-002 | G0 | Spike Qt WebEngine tải static Vite assets + QWebChannel ping/pong trên Windows; chặn navigation/network trong production mode. | VERIFIED | https://github.com/giabao2605/Code-City/pull/6 | Windows Server 2022 WebEngine thật, React Vite static, QWebChannel ping/pong + Python signal, 6 integration + 8 protocol + 4 URL-policy tests PASS; download/loopback negative PASS, CI #39578515051; physical Win10/11 NOT_RUN (không phải CC-002 standalone acceptance) |
| CC-003 | G0 | Spike standalone build tối thiểu có QtWebEngineProcess/resources; chạy trên máy Windows khác máy build. | VERIFIED | https://github.com/giabao2605/Code-City/pull/8 | Nuitka 4.1.1 Windows standalone EXE, QtWebEngineProcess/resources and Vite assets; two independent Windows Server 2022 workflows [#39710663609](https://github.com/giabao2605/Code-City/actions/runs/39710663609) and [#39710667523](https://github.com/giabao2605/Code-City/actions/runs/39710667523): build + separate consumer real packaged Qt/React/QWebChannel 3 Ping/Pong, app.ready, CSP/network/IPC negative, reload/restart, Unicode relocation/missing resources PASS; physical Win10/11, unplugged network, true no-Python/Node machine NOT_RUN/UNVERIFIED |
| CC-004 | G0 | Tạo fixture generator 500/1k/5k/10k files; ghi rõ CPU/GPU/RAM/SSD/resolution/Windows của máy benchmark. | IN_PROGRESS | https://github.com/giabao2605/Code-City/issues/9 | Source, tests, Windows CI và capture script trên feature branch; chờ final Windows evidence để VERIFIED |
| CC-005 | G0 | Chốt chiến lược path containment/TOCTOU trên Windows, file limits và scan error semantics qua test nhỏ; viết ADR nếu đổi quyết định. | TODO | - | Chưa bắt đầu |
| CC-010 | G1 | Python project CLI entrypoint, PySide main window, Qt resources, native picker, thread-safe bridge, basic React shell. | TODO | - | Chưa bắt đầu |
| CC-011 | G1 | Language map 17 extensions + ignored dirs 9 + deterministic traversal. | TODO | - | Chưa bắt đầu |
| CC-012 | G1 | Symlink/junction/root/containment policy; Unicode/casefold collision handling. | TODO | - | Chưa bắt đầu |
| CC-013 | G1 | Streaming binary LOC/hash/metadata, stat consistency, quotas. | TODO | - | Chưa bắt đầu |
| CC-014 | G1 | Bounded worker, progress, cancellation, COMPLETE/PARTIAL/FAILED result. | TODO | - | Chưa bắt đầu |
| CC-015 | G1 | Unit/security fixtures: CRLF/LF/CR, UTF path, long path, 64MiB edge, permissions, no-execution marker, links. | TODO | - | Chưa bắt đầu |
| CC-020 | G2 | SQLite location, migrations v1, indexes/foreign keys/WAL. | TODO | - | Chưa bắt đầu |
| CC-021 | G2 | Projects/recent projects; UUID/canonical root và missing-root handling. | TODO | - | Chưa bắt đầu |
| CC-022 | G2 | Atomic COMPLETE snapshot commit, rollback khi lỗi/cancel; PARTIAL preview không commit. | TODO | - | Chưa bắt đầu |
| CC-023 | G2 | Diff added/modified/deleted, hash same-size test, rename delete+add. | TODO | - | Chưa bắt đầu |
| CC-024 | G2 | Tests concurrency, crash/restart, migration, snapshot isolation. | TODO | - | Chưa bắt đầu |
| CC-030 | G3 | Folder tree, district packing deterministic, global occupancy, no-overlap. | TODO | - | Chưa bắt đầu |
| CC-031 | G3 | Persist file/folder slots, tombstones, re-add reclaim, annex expansion. | TODO | - | Chưa bắt đầu |
| CC-032 | G3 | Metric mapping + palette + mappingVersion/layoutVersion. | TODO | - | Chưa bắt đầu |
| CC-033 | G3 | City payload schema + batching/order, Python↔TS fixtures. | TODO | - | Chưa bắt đầu |
| CC-034 | G3 | Property tests 1k/5k paths: no collision, deterministic initial, stable X/Z qua add/delete/edit/re-add. | TODO | - | Chưa bắt đầu |
| CC-040 | G4 | Scene/camera/lights/ground/district layer, WebGL error state. | TODO | - | Chưa bắt đầu |
| CC-041 | G4 | Chunked InstancedMesh, per-instance colors, selection overlay, renderer.info. | TODO | - | Chưa bắt đầu |
| CC-042 | G4 | Raycast chunk+instanceId→fileKey; orbit/pan/zoom/reset; focus animation. | TODO | - | Chưa bắt đầu |
| CC-043 | G4 | Label LOD, recency/changes accent, resize/context-loss handling. | TODO | - | Chưa bắt đầu |
| CC-044 | G4 | Vitest for mapping/picking/camera + browser/mock bridge smoke. | TODO | - | Chưa bắt đầu |
| CC-050 | G5 | Sidebar recent projects, open/rescan/cancel, status/progress/errors. | TODO | - | Chưa bắt đầu |
| CC-051 | G5 | Details, stats, language legend, added/modified/deleted indicators. | TODO | - | Chưa bắt đầu |
| CC-052 | G5 | Search ranking, keyboard flow, focus/highlight/reset. | TODO | - | Chưa bắt đầu |
| CC-053 | G5 | Double-click VS Code with fileKey validation, safe subprocess, missing-VSCode UI. | TODO | - | Chưa bắt đầu |
| CC-054 | G5 | All states: empty/partial/missing-root/WebGL/offline/large-project. | TODO | - | Chưa bắt đầu |
| CC-060 | G6 | Automated test matrix cho scanner/snapshot/layout/IPC/UI; coverage report. | TODO | - | Chưa bắt đầu |
| CC-061 | G6 | Security tests path traversal, symlink/junction, race, SQL injection, no execution, blocked network/navigation. | TODO | - | Chưa bắt đầu |
| CC-062 | G6 | Benchmark 500/1k/5k/10k + large/deep projects; capture p50/p95 frame, scan time, peak RSS, draw calls. | TODO | - | Chưa bắt đầu |
| CC-063 | G6 | Fix regressions, test crash recovery, cancel/rescan/project switch, DB migrations. | TODO | - | Chưa bắt đầu |
| CC-064 | G6 | Privacy/license/dependency review; known limitations và docs. | TODO | - | Chưa bắt đầu |
| CC-070 | G7 | Reproducible build_frontend.ps1/build_windows.ps1, pinned toolchain. | TODO | - | Chưa bắt đầu |
| CC-071 | G7 | pyside6-deploy standalone, kiểm tra exe, QtWebEngineProcess, DLL, resources, locales, bundled assets; fallback PyInstaller onedir nếu cần. | TODO | - | Chưa bắt đầu |
| CC-072 | G7 | GitHub Actions Windows test/lint/build/upload artifact; cùng scripts local. | TODO | - | Chưa bắt đầu |
| CC-073 | G7 | Smoke trên Windows 10 1809+ x64 và Windows 11 x64, máy sạch không Python/Node/Internet. | TODO | - | Chưa bắt đầu |
| CC-074 | G7 | README user/developer, SECURITY, LICENSE/third-party notices, checksum/release notes. | TODO | - | Chưa bắt đầu |
| CC-080 | G8 | Đối chiếu checklist nghiệm thu, kết quả CI, security, benchmark, license, smoke; lập biên bản Go/No-Go. | TODO | - | Chưa bắt đầu |
| CC-081 | G8 | Gắn tag v1.0.0 và GitHub Release sau khi Go; optional NSIS installer/signing có thể là release phụ, không cản RC. | TODO | - | Chưa bắt đầu |

**Quy tắc task:** trạng thái VERIFIED chỉ hợp lệ khi có URL GitHub PR/commit và ghi chú kết quả test/đối chiếu DoD. Một task chưa VERIFIED không được tính là xong chỉ vì code đã commit. Không có test hoặc môi trường chạy thật thì ghi BLOCKED/IN_PROGRESS và nói rõ giới hạn.

## 4. Acceptance tracker

| Acceptance | Trạng thái | Evidence | Ghi chú |
|---|---|---|---|
| A01 | NOT_RUN | - | No Git: chưa kiểm thử |
| A02 | NOT_RUN | - | Offline: chưa kiểm thử |
| A03 | NOT_RUN | - | Extensions/ignore: chưa kiểm thử |
| A04 | NOT_RUN | - | Metadata/LOC: chưa kiểm thử |
| A05 | NOT_RUN | - | Security links: chưa kiểm thử |
| A06 | NOT_RUN | - | Scanner resilience: chưa kiểm thử |
| A07 | NOT_RUN | - | Snapshot diff: chưa kiểm thử |
| A08 | NOT_RUN | - | DB integrity: chưa kiểm thử |
| A09 | NOT_RUN | - | Stable layout: chưa kiểm thử |
| A10 | NOT_RUN | - | City completeness: chưa kiểm thử |
| A11 | NOT_RUN | - | 3D interaction: chưa kiểm thử |
| A12 | NOT_RUN | - | VS Code: chưa kiểm thử |
| A13 | NOT_RUN | - | UI states: chưa kiểm thử |
| A14 | NOT_RUN | - | Windows startup: chưa kiểm thử |
| A15 | NOT_RUN | - | Reproducible build: chưa kiểm thử |
| A16 | NOT_RUN | - | 5k performance: chưa kiểm thử |
| A17 | NOT_RUN | - | Headroom 10k: chưa kiểm thử |
| A18 | NOT_RUN | - | Quality gate: chưa kiểm thử |

**Quy tắc acceptance:** NOT_RUN / PASS / FAIL / WAIVED. PASS cần link bằng chứng thực tế; WAIVED phải có ADR và chấp thuận rõ của chủ dự án, không được dùng để bỏ qua nguyên tắc an toàn/bảo mật. FAIL phải ghi lỗi và kế hoạch khắc phục. Mọi A01–A18 ban đầu đều NOT_RUN.

## 5. Blockers và rủi ro mở

- **CC-002 và CC-003 spikes đã VERIFIED trên hosted Windows Server 2022:** không đồng nghĩa kiểm thử physical Windows 10/11 GUI/GPU hay ứng dụng V1 offline hoàn chỉnh. Giới hạn: network isolation không chứng minh mọi loại Chromium traffic/OS-level bypass; rủi ro packaging, GPU, license và TOCTOU còn cho các gate/task sau.
- **Điều kiện bắt đầu task tiếp:** CC-002 có PR #6, trạng thái merge phải xác minh trên GitHub. CC-003 VERIFIED qua artifact/runtime/cross-runner CI thực ngày 2026-10-22; CC-004 đang triển khai với ủy quyền mới 2026-10-22, chưa VERIFIED khi chưa đủ CI proof. Không nhầm Next task với authorization.
- **Thay đổi kiến trúc hoặc scope:** phải có ADR, cập nhật Master Plan (version mới), cập nhật PROGRESS và ghi WORK_LOG trước khi code theo quyết định mới.

## 6. Checklist mỗi lần bắt đầu / kết thúc phiên làm việc

**Trước khi làm:** đọc `AGENTS.md` → `MASTER_PLAN.md` → `PROGRESS.md` → các mục gần nhất của `docs/WORK_LOG.md` → ADR liên quan; xác minh branch/PR và task kế tiếp; chỉ làm đúng task được phép.

**Khi làm:** đổi task TODO→IN_PROGRESS; ghi blockers nếu có; code/test theo DoR/DoD; không lấn scope, không tuyên bố test đã chạy nếu chưa chạy.

**Trước khi kết thúc:** cập nhật task/acceptance/gate cùng link bằng chứng; ghi entry mới vào `docs/WORK_LOG.md` (đã làm, test, commit/PR, chưa làm, blocker, next); chạy `node scripts/verify_governance.mjs`; commit thay đổi cùng PR/task. Nếu kiểm tra thất bại thì không merge.

**Để tiếp tục ở chat khác:** dùng GitHub repo như nguồn sự thật. Đọc PROGRESS để lấy `Current gate` + `Next task`, rồi kiểm tra WORK_LOG và PR trước khi đụng code. Trạng thái ở cuộc chat không thay thế trạng thái đã commit.

## 7. Chính sách cập nhật và tránh tự đánh lừa

1. **MASTER_PLAN.md:** nguồn sự thật về yêu cầu và acceptance, không dùng để đánh dấu tiến độ.
2. **PROGRESS.md:** nguồn sự thật về trạng thái gate/task/acceptance và next task.
3. **docs/WORK_LOG.md:** nhật ký append-only, ghi lại điều thực sự đã làm và kiểm thử.
4. **docs/ADR_TEMPLATE.md / docs/ADR/**: quyết định thay đổi có lý do và phê duyệt.
5. **AGENTS.md:** quy tắc cho AI/coding agent, áp dụng kể cả chat mới.
6. **scripts/verify_governance.mjs + GitHub Actions:** chặn lệch ID, thiếu bằng chứng và trạng thái không nhất quán ở mức có thể kiểm tra bằng máy. CI không thể thay thế kiểm thử chức năng/Windows thực tế.

**Cấm:** tự ghi VERIFIED, PASS, “đã build Windows”, “đã test offline” hoặc “đã release” nếu không có bằng chứng cụ thể. Không được đổi gate bằng cảm tính hoặc vì muốn demo nhanh.
