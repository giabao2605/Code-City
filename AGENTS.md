# AGENTS.md — Quy tắc bắt buộc cho mọi AI/coding agent làm việc với Code City

> Tài liệu này áp dụng cho bất kỳ phiên làm việc hoặc agent nào. Không dựa vào trí nhớ hội thoại làm nguồn sự thật.

## Thứ tự đọc bắt buộc trước khi thao tác repository

1. `MASTER_PLAN.md`: phạm vi V1, kiến trúc, CC-xxx, A01–A18, gate G0–G8.
2. `PROGRESS.md`: current gate, next task, task/acceptance state và blockers.
3. `docs/WORK_LOG.md`: các phiên gần nhất, PR/commit và việc dang dở.
4. `docs/ADR/` (nếu có): các quyết định thay đổi đã được chấp thuận.
5. `README.md`: trạng thái và hướng dẫn chung.

**Nếu tài liệu mâu thuẫn:** dừng, đối chiếu Master Plan và Git history, báo rõ mâu thuẫn, cập nhật theo change control; không âm thầm chọn một cách hiểu.

## Luật vận hành

- **Quyền bắt đầu:** chỉ được làm những gì chủ dự án đã cho phép rõ ràng, đúng CC-xxx và gate. Ghi chú `DOCS_ONLY`/chưa cho phép code tại bootstrap 2026-10-21 **là trạng thái lịch sử, không phải lệnh cấm vĩnh viễn**. CC-001 đã được triển khai và merge; CC-002 được cấp phép riêng trong prompt phiên mới. Khi bắt đầu, đọc `PROGRESS.md` và lệnh mới nhất của chủ dự án, đối chiếu GitHub thực tế. `Next task` chỉ là thứ tự, không tự cấp quyền sang task kế tiếp.
- **Một task có kiểm soát:** xác định CC-xxx và DoR trước khi sửa code. Không làm feature ngoài V1 MUST hoặc thuộc V2/V3 khi chưa có quyết định mới.
- **Bất biến không thương lượng:** offline, không upload/execute source code, COMPLETE-only snapshot commit, stable file X/Z, không lộ nội dung source, không dùng shell=True với đường dẫn từ project.
- **Bằng chứng trước trạng thái:** chỉ VERIFIED nếu code/test/docs/DoD có link PR hoặc commit. Acceptance PASS chỉ khi đã chạy test thực tế và lưu bằng chứng. Chưa chạy test thì phải ghi NOT_RUN/IN_PROGRESS/BLOCKED.
- **Gate:** G0→G8 theo thứ tự. Không mở gate sau trước khi exit gate trước VERIFIED. Không tự động publish release.
- **Git:** ưu tiên branch `feature/CC-xxx-...` và PR vào main khi triển khai; không force push, không overwrite thay đổi khác, không xóa lịch sử. Bootstrap governance docs có thể commit trực tiếp main theo yêu cầu chủ dự án.
- **Trước khi merge:** cập nhật PROGRESS và WORK_LOG cùng PR, kiểm tra validator, test tương ứng, đọc diff, ghi rõ giới hạn. Không coi CI xanh là bằng chứng của Windows/GPU smoke khi CI không chạy bài đó.
- **Change control:** mọi thay đổi stack, scope, schema, thuật toán layout, acceptance phải tạo ADR, nêu before/after/risk/test/migration, xin chấp thuận khi ảnh hưởng mục tiêu và cập nhật version Master Plan.
- **Bàn giao:** cuối mỗi phiên phải có entry WORK_LOG ghi task, commit/PR, test pass/fail/not run, blocker, next step; PROGRESS phải chỉ đúng task kế tiếp.
- **Trung thực:** không bịa commit, file, test, benchmark, Windows smoke, screenshot hay kết quả. Nếu công cụ không thể xác minh, ghi rõ là chưa xác minh.

## Checklist mở phiên

- [ ] Đã đọc đủ tài liệu và kiểm tra HEAD/PR thực tế.
- [ ] Task đang làm đúng Current gate, có DoR và không bị BLOCKED.
- [ ] Biết acceptance và test phải chạy, biết cách rollback.
- [ ] Được phép thực hiện bước này, không tự mở rộng phạm vi.

## Checklist đóng phiên

- [ ] Code/docs và tests tương ứng đã commit, hoặc ghi rõ chưa commit.
- [ ] PROGRESS cập nhật trạng thái + bằng chứng, không có VERIFIED/PASS vô căn cứ.
- [ ] WORK_LOG có mục bàn giao mới, next task khớp PROGRESS.
- [ ] `node scripts/verify_governance.mjs` đã chạy và kết quả được ghi; nếu chưa chạy, nói rõ.
- [ ] Không tự nhận đã hoàn thành milestone/release khi chưa đạt exit gate.

**Mục tiêu:** người hoặc AI bất kỳ có thể tiếp tục dự án từ GitHub mà không cần đoán phiên trước đã làm gì.
