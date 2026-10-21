# Code City

**Code City** là dự án ứng dụng desktop Windows để biến thư mục source code local thành thành phố 3D tương tác. V1 được thiết kế offline-first, không yêu cầu Git/GitHub cho thư mục được scan, không upload hoặc thực thi source code của người dùng.

## Tài liệu chính thức

**[ĐỌC MASTER PLAN V1](MASTER_PLAN.md)**

MASTER_PLAN.md là **source of truth** cho phạm vi, kiến trúc, hợp đồng dữ liệu, lộ trình G0–G8, 43 đầu việc CC-xxx, tiêu chí nghiệm thu A01–A18, kiểm thử, rủi ro và quy trình thay đổi. Khi có mâu thuẫn giữa đề xuất triển khai và Master Plan, phải cập nhật Master Plan/ADR trước khi thực hiện.

## Trạng thái

- **Planning baseline:** Master Plan v1.0.1, ngày 2026-10-21.
- **Chưa có mã nguồn ứng dụng, binary, installer hay CI.**
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
