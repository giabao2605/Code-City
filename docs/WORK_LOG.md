# WORK LOG — Nhật ký bàn giao theo phiên

> **Append-only.** Thêm entry mới ở đầu danh sách, không sửa/xóa lịch sử để che lỗi. Mỗi entry cần ngày UTC, CC task/gate, hành động thực tế, bằng chứng commit/PR, kiểm thử đã chạy/chưa chạy, blockers, next task. Khi thay đổi một entry cũ để sửa lỗi thông tin, thêm ghi chú correction có ngày.

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
