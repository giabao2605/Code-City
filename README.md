# Code City

**Code City** là dự án ứng dụng desktop Windows để biến thư mục source code local thành thành phố 3D tương tác. V1 được thiết kế offline-first, không yêu cầu Git/GitHub cho thư mục được scan, không upload hoặc thực thi source code của người dùng.

## Tài liệu chính thức và cách tiếp tục dự án

**[MASTER PLAN V1](MASTER_PLAN.md)** là nguồn sự thật về yêu cầu, kiến trúc, lộ trình G0–G8, 43 đầu việc CC-xxx và tiêu chí nghiệm thu A01–A18. Không thay đổi scope/kiến trúc mà không có ADR và cập nhật Master Plan.

**[PROGRESS.md](PROGRESS.md)** là bảng tiến độ duy nhất: gate hiện tại, task tiếp theo, 43 task, 18 acceptance, blockers và bằng chứng. **[AGENTS.md](AGENTS.md)** là quy tắc bắt buộc cho AI/coding agent trong mọi phiên, kể cả chat mới. **[docs/WORK_LOG.md](docs/WORK_LOG.md)** là nhật ký bàn giao append-only. **[docs/ADR_TEMPLATE.md](docs/ADR_TEMPLATE.md)** là mẫu ghi quyết định thay đổi.

**Trước khi làm bất cứ task nào:** đọc AGENTS → MASTER_PLAN → PROGRESS → WORK_LOG; kiểm tra đúng CC-xxx và quyền bắt đầu. Sau mỗi task phải cập nhật tiến độ, nhật ký, bằng chứng và chạy `node scripts/verify_governance.mjs`. GitHub Actions governance kiểm tra tự động consistency của tài liệu, không thay thế kiểm thử sản phẩm.

## Trạng thái

> Đây là checkpoint CC-004 ngày 2026-10-22. **[PROGRESS.md](PROGRESS.md) là nguồn sự thật** về trạng thái mới nhất. Các trường Phase/Current gate/Next task dưới đây được kiểm tra đồng bộ với PROGRESS bằng governance CI.

- **Phase:** `IN_DEVELOPMENT`
- **Current gate:** `G0`
- **Next task:** `CC-005`
- **CC-001:** `VERIFIED`, đã [squash merge PR #2](https://github.com/giabao2605/Code-City/pull/2) vào `main` ở commit [`38d091e`](https://github.com/giabao2605/Code-City/commit/38d091e6539f524337414807a72612fcebec5748); Python/Qt/frontend dependencies và npm lock đã có, Windows hosted dependency CI PASS.
- **CC-002:** `VERIFIED` trong phạm vi spike, [Issue #5](https://github.com/giabao2605/Code-City/issues/5), [PR #6](https://github.com/giabao2605/Code-City/pull/6). Qt WebEngine/QWebChannel thực trên Windows Server 2022 và 6/6 integration tests PASS; [CI #39578515051](https://github.com/giabao2605/Code-City/actions/runs/39578515051), [hướng dẫn CC-002](docs/CC002_SPIKE.md). **CC-003 đã VERIFIED trong phạm vi packaging spike, CC-004 chưa được cấp quyền bắt đầu.**
- **CC-003:** `VERIFIED` trong phạm vi G0 standalone feasibility, [Issue #7](https://github.com/giabao2605/Code-City/issues/7), [PR #8](https://github.com/giabao2605/Code-City/pull/8) (đã merge 2026-10-22), [CC-003 docs](docs/CC003_PACKAGING.md). Nuitka packaged .exe/Qt WebEngine/Vite/QWebChannel thực, ZIP SHA256 và smoke trên runner Windows Server 2022 khác máy build: [push #39710663609](https://github.com/giabao2605/Code-City/actions/runs/39710663609), [PR #39710667523](https://github.com/giabao2605/Code-City/actions/runs/39710667523), cả hai SUCCESS. Không tự merge PR.
- **CC-004:** `VERIFIED` trong phạm vi fixture generator, [Issue #9](https://github.com/giabao2605/Code-City/issues/9), [PR #10](https://github.com/giabao2605/Code-City/pull/10), [Windows CI #39715441291 SUCCESS](https://github.com/giabao2605/Code-City/actions/runs/39715441291), 24 tests PASS, 500/1k/5k/10k verified, [baseline and reproduction](docs/CC004_FIXTURES_BENCHMARK.md). Hosted virtual GPU và SSD vật lý chưa verified; WebGL 100 boxes/A16/A17 NOT_RUN; G0 IN_PROGRESS.
- **Ứng dụng:** có integration spike Qt + React/Vite + QWebChannel được kiểm thử trên hosted Windows Server 2022; chưa có desktop shell đầy đủ, 3D renderer hoặc installer; CC-003 standalone spike đã build và chạy cross-runner trên Windows Server 2022; physical Windows 10/11 GUI/GPU smoke và máy vật lý không có Python/Node vẫn chưa thực hiện. [Dependency matrix](docs/DEPENDENCY_MATRIX.md) và [Windows setup](docs/CC001_SETUP.md). Theo dõi [CC-003 packaging / PowerShell / test matrix](docs/CC003_PACKAGING.md), [Issue #7](https://github.com/giabao2605/Code-City/issues/7).
- **Hệ điều hành mục tiêu:** Windows 10 1809+ x64 và Windows 11 x64; cần kiểm chứng qua các gate tiếp theo, không coi dependency CI là smoke test ứng dụng.

## Nguyên tắc không thương lượng

1. Scanner chỉ đọc bytes và metadata; không execute source code.
2. Source code không rời khỏi máy người dùng.
3. Snapshot chỉ được commit khi scan COMPLETE; partial/cancel không phá snapshot trước.
4. File còn tồn tại giữ nguyên tọa độ X/Z sau rescan.
5. 3D dùng instancing/chunking thay vì một Mesh cho mỗi file.
6. Đóng gói standalone Windows phải chạy trên máy sạch trước khi phát hành.

> Repository đang ở **G0 / IN_DEVELOPMENT**, chưa có ứng dụng hoàn chỉnh. Đọc [PROGRESS.md](PROGRESS.md) trước khi nhận task; không dùng ghi chú lịch sử như trạng thái hiện tại.
