# Code City

**Code City** là dự án ứng dụng desktop Windows để biến thư mục source code local thành thành phố 3D tương tác. V1 được thiết kế offline-first, không yêu cầu Git/GitHub cho thư mục được scan, không upload hoặc thực thi source code của người dùng.

## Tài liệu chính thức và cách tiếp tục dự án

**[MASTER PLAN V1](MASTER_PLAN.md)** là nguồn sự thật về yêu cầu, kiến trúc, lộ trình G0–G8, 43 đầu việc CC-xxx và tiêu chí nghiệm thu A01–A18. Không thay đổi scope/kiến trúc mà không có ADR và cập nhật Master Plan.

**[PROGRESS.md](PROGRESS.md)** là bảng tiến độ duy nhất: gate hiện tại, task tiếp theo, 43 task, 18 acceptance, blockers và bằng chứng. **[AGENTS.md](AGENTS.md)** là quy tắc bắt buộc cho AI/coding agent trong mọi phiên, kể cả chat mới. **[docs/WORK_LOG.md](docs/WORK_LOG.md)** là nhật ký bàn giao append-only. **[docs/ADR_TEMPLATE.md](docs/ADR_TEMPLATE.md)** là mẫu ghi quyết định thay đổi.

**Trước khi làm bất cứ task nào:** đọc AGENTS → MASTER_PLAN → PROGRESS → WORK_LOG; kiểm tra đúng CC-xxx và quyền bắt đầu. Sau mỗi task phải cập nhật tiến độ, nhật ký, bằng chứng và chạy `node scripts/verify_governance.mjs`. GitHub Actions governance kiểm tra tự động consistency của tài liệu, không thay thế kiểm thử sản phẩm.

## Trạng thái

- **Planning baseline:** Master Plan v1.0.1, ngày 2026-10-21.
- **Chưa có mã nguồn ứng dụng, binary hoặc installer.** Đã thiết lập tài liệu quản trị và CI kiểm tra consistency, không phải CI sản phẩm.
- **Bước triển khai đầu tiên:** G0 / CC-001: khóa phiên bản công nghệ và xác minh Qt WebEngine + QWebChannel + Windows standalone build.
- **Hệ điều hành mục tiêu:** Windows 10 1809+ x64 và Windows 11 x64; khả năng chạy thực tế phải được xác nhận bằng smoke test.

## Nguyên tắc không thương lượng

1. Scanner chỉ đọc bytes và metadata; không execute source code.
2. Source code không rời khỏi máy người dùng.
3. Snapshot chỉ được commit khi scan COMPLETE; partial/cancel không phá snapshot trước.
4. File còn tồn tại giữ nguyên tọa độ X/Z sau rescan.
5. 3D dùng instancing/chunking thay vì một Mesh cho mỗi file.
6. Đóng gói standalone Windows phải chạy trên máy sạch trước khi phát hành.

> Repository này hiện là giai đoạn **lập kế hoạch**. Bắt đầu bằng [Master Plan](MASTER_PLAN.md), không tự suy đoán rằng tool đã hoàn thiện.
