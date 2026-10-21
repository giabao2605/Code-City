## Task / Gate

- **CC-xxx:** 
- **Gate:** Gx
- **Master Plan version:** 1.0.1
- **Mục tiêu/DoR:** 
- **Không làm (out of scope):** 

## Thay đổi và bằng chứng

- **Đã thay đổi:** 
- **Các test đã chạy (lệnh + kết quả thực tế):** 
- **Test chưa chạy và lý do:** 
- **Windows/WebGL/packaging smoke (nếu liên quan):** 
- **Ảnh hưởng A01–A18:** 
- **Bằng chứng (commit, CI run, log, screenshot, benchmark):** 
- **Rủi ro / rollback:** 
- **ADR nếu lệch Master Plan:** 

## Checklist trước merge

- [ ] Đúng CC-xxx và gate đang mở trong `PROGRESS.md`; không lấn scope V2/V3.
- [ ] Đã đối chiếu DoR/DoD và exit gate trong `MASTER_PLAN.md`.
- [ ] `PROGRESS.md` cập nhật task/acceptance/gate cùng evidence thật.
- [ ] `docs/WORK_LOG.md` ghi rõ kết quả, blocker và next task.
- [ ] Đã chạy `node scripts/verify_governance.mjs` và GitHub Actions governance xanh.
- [ ] Unit/integration/security tests liên quan đã chạy, hoặc ghi rõ chưa chạy.
- [ ] Không khẳng định đã smoke trên Windows/GPU nếu chưa có kết quả thực.
- [ ] Không vi phạm offline/no-execution/atomic snapshot/stable layout.
- [ ] Không force push, không xóa lịch sử, không auto-publish release.
