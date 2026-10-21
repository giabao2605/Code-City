# CODE CITY V1 — MASTER IMPLEMENTATION PLAN

> **Tài liệu điều hành duy nhất (source of truth) cho việc xây dựng Code City V1.**
>
> **Phiên bản:** 1.0.1 · **Ngày lập và rà soát:** 2026-10-21 · **Trạng thái:** Planning baseline, CHƯA triển khai code · **Nền tảng:** Windows 10 (1809+) / Windows 11 x64.
>
> **Quy tắc:** Không bắt đầu một hạng mục nếu chưa thỏa điều kiện đầu vào (DoR); không đánh dấu hoàn thành nếu chưa có bằng chứng nghiệm thu (DoD). Mọi thay đổi ảnh hưởng scope/kiến trúc/tiêu chí phải cập nhật tài liệu này trước khi triển khai.

## 0. Cách đọc, nguồn và mức độ chắc chắn

- **[R] Nguồn nghiên cứu:** Báo cáo “Code City V1: Deep Technical Research and Implementation Blueprint for Windows”, được cung cấp trong cuộc hội thoại ngày 2026-10-21. Đây là nguồn nền về kiến trúc, scanner, snapshot, layout, Three.js, bảo mật, đóng gói và CI.
- **[V] Đã đối chiếu:** Tài liệu chính thức liên kết tại mục 21, kiểm tra ngày 2026-10-21; kiểm tra trực tiếp repository GitHub giabao2605/Code-City (public, mặc định main, đang trống khi lập kế hoạch).
- **[D] Quyết định thiết kế:** Các chính sách và ngưỡng do Master Plan chốt để có thể thực thi; không được hiểu là tính năng đã có hoặc benchmark đã đạt.
- **[P] Cần chứng minh:** Các giả định phụ thuộc môi trường Windows, GPU, phiên bản thư viện hoặc kết quả thực nghiệm. Không ghi “đã đạt” trước khi chạy test.

**Ưu tiên khi có xung đột:** bảo vệ dữ liệu và tính đúng đắn > ổn định snapshot/layout > khả năng chạy trên Windows > hiệu năng > hiệu ứng hình ảnh. Không tự ý mở rộng scope để đổi lấy UI đẹp.

## 1. Tuyên bố sản phẩm và định nghĩa thành công

**Code City V1** là ứng dụng desktop Windows, chạy local-first/offline, biến một thư mục source code bất kỳ thành thành phố 3D có thể khám phá: mỗi file là một tòa nhà, mỗi folder là một khu vực, kích thước biểu đạt metrics, màu biểu đạt ngôn ngữ; có tìm kiếm, chọn file, xem chi tiết, mở file trong VS Code, rescan và so sánh snapshot.

**Luồng người dùng chuẩn:** mở CodeCity.exe → chọn thư mục bất kỳ, kể cả không có Git → quét và hiển thị tiến độ → thành phố 3D → orbit/pan/zoom → click xem thông tin → search/focus → double-click mở VS Code → sửa file ngoài ứng dụng → Rescan → xem added/modified/deleted, các file còn tồn tại giữ nguyên địa chỉ.

**V1 thành công khi:**
1. Chạy offline trên Windows mục tiêu, không yêu cầu Git, Node, Python hoặc Internet trên máy người dùng cuối sau khi đóng gói.
2. Không thực thi, không upload, không nhúng hoặc lưu nội dung source code; chỉ đọc bytes để lấy metadata, LOC và hash.
3. Mỗi file được hỗ trợ có đúng một building; không có building chồng lấn; snapshot nhất quán và có thể so sánh.
4. Rescan giữ nguyên grid X/Z của file còn tồn tại; thay đổi metrics chỉ đổi hình dáng/màu/trạng thái.
5. Tương tác 3D và thao tác mở file hoạt động ổn định; lỗi scan/VS Code/WebGL được hiển thị rõ.
6. Có kiểm thử tự động, Windows smoke test, build tái lập được và artifact chứa CodeCity.exe.

**Không được xem là thành công:** demo Three.js tĩnh, UI dùng mock data nhưng không scan thực, một bản .exe chỉ chạy trên máy build, hoặc snapshot sai khi scan bị lỗi.

## 2. Phạm vi đóng băng V1

### Bắt buộc (MUST)
- Chọn folder qua hộp thoại native; danh sách project gần đây; project ID UUID và root canonical.
- Scanner Python không dùng Git: traversal có ignore, bỏ symlink/junction, metadata, physical lines, bytes, mtime, content hash, tiến độ và cancel.
- 17 đuôi file ở mục 5; 9 thư mục ignore mặc định ở mục 5; hỗ trợ Unicode path và filename.
- SQLite trong per-user AppData; migration; snapshot nguyên tử; diff added/modified/deleted; tọa độ persist/tombstone.
- 3D city theo folder/district, building mapping, màu ngôn ngữ, legend, highlight file mới/sửa/gần đây, statistics.
- Instanced rendering có chunk; click/picking, chi tiết file, orbit/zoom/pan/reset, search theo tên/path, camera focus, double-click mở VS Code an toàn.
- Giao diện dark developer tool; empty/loading/error/cancel/partial/WebGL-fail/VSCode-missing states.
- Production không CDN, không localhost API, không telemetry, không network dependency; Windows standalone distribution và GitHub Actions artifact.
- Unit/integration/security/performance/smoke tests; README hướng dẫn build và giới hạn hỗ trợ.

### Không làm trong V1 (WON'T)
Git history, GitHub integration cho folder được scan, dependency/import graph, complexity/AST, rename detection, watcher/live sync, timeline animation, cloud sync, login, analytics/telemetry, auto-update, installer bắt buộc, code signing bắt buộc, multi-platform, shader cao cấp, nội dung source preview, extension tùy ý, tự động compact layout.

**Quy tắc scope:** một tính năng mới chỉ vào V1 nếu khắc phục blocker của MUST hoặc lỗi bảo mật/dữ liệu. Các ý tưởng còn lại vào V2/V3.

## 3. Kiến trúc và quyết định công nghệ

| Lớp | Quyết định V1 | Lý do / giới hạn |
|---|---|---|
| Desktop | PySide6 + QWebEngineView | Native picker, Windows integration, Python backend; Chromium/WebEngine đóng gói nặng [R,V] |
| IPC | QWebChannel nội bộ Qt | Không mở cổng TCP/HTTP trong production [R,V] |
| Frontend | React + TypeScript + Vite | Build static assets, typed UI, không cần Node ở runtime [R] |
| 3D | Three.js + OrbitControls + Raycaster | InstancedMesh giảm draw calls; picking trả instanceId [R,V] |
| Backend | Python 3.12 x64 | scandir, Path.is_junction (có từ 3.12), sqlite3, subprocess [R,V] |
| Storage | SQLite, WAL trên local AppData | Giao dịch và đọc/ghi cục bộ; không đặt WAL trên network drive [R,V] |
| Build | pyside6-deploy/Nuitka standalone | Official Qt for Python path; PyInstaller onedir là fallback [R,V] |
| Release | GitHub Actions Windows artifact | Installer NSIS và ký mã để sau khi standalone đã qua smoke [R] |

**Chính sách phiên bản:** cố định Python 3.12.x, dòng PySide6/Qt 6.12.x để giữ baseline Windows 10; cố định Node major LTS dùng khi build (đề xuất Node 24), cùng exact versions của React/Three/Vite/TypeScript sau spike G0. Lock frontend bằng package-lock.json + npm ci; lock Python bằng constraints/lock có hash hoặc phiên bản chính xác. Không để dấu sao, dấu lớn hơn hoặc tự nâng Qt major trong CI. **Chưa xác nhận tổ hợp phiên bản chính xác cho đến G0** [P]. Qt nói 6.12 là dòng cuối hỗ trợ Win10, nhưng patch release có thể thay đổi cấu hình được hỗ trợ: kiểm thử lại từng lần nâng cấp [V].

**Ranh giới tin cậy:**

~~~text
QFileDialog -> Python scanner worker -> typed metadata -> SQLite snapshot+layout
                                      -> QWebChannel -> React state -> Three.js
React -> fileKey (opaque) -> Python revalidate -> VS Code process
~~~

React không có quyền chọn arbitrary path để mở. Không load file HTML/JS của project vào WebEngine. Chỉ bundle asset do chính Code City build; dự án người dùng không được phục vụ như web assets.

## 4. Hợp đồng dữ liệu và nhận dạng

- **Project:** UUID được tạo khi lần đầu mở canonical root; project không phụ thuộc .git. Lưu cả canonicalRoot để hiển thị và canonicalRootKey (casefold/normalized) để UNIQUE lookup trên Windows; nếu hai đường dẫn có key trùng nhưng thực thể khác thì báo collision. Root được lưu ở AppData. Nếu di chuyển/đổi tên root, V1 coi là project mới (không tự ghép lịch sử).
- **File identity:** khóa logic dựa trên project UUID + normalized relative path (dấu /, casefold cho Windows), tạo opaque fileKey ổn định; giữ relPath gốc để hiển thị. Casefold/Unicode collision phải phát hiện và báo lỗi, không âm thầm ghi đè. Rename = deleted + added.
- **Metadata:** fileKey, name, relPath, relPathNorm, parentRelPath, extension, language, lineCount, sizeBytes, mtimeNs, modifiedAtUtc, contentHash.
- **Hash:** streaming BLAKE2b-256 (32 bytes) [D, tăng độ dài so với ví dụ BLAKE2b-128 trong [R]]; so sánh hash là chuẩn phân loại modified, không chỉ mtime/size.
- **LOC:** số dòng vật lý, KHÔNG phải semantic/code-only LOC. Đếm dòng rỗng; file rỗng = 0; có hoặc không newline cuối; xử lý LF, CRLF và bare CR qua chunk boundaries; không decode toàn file. Ghi rõ cách tính trong UI/docs.
- **Thời gian:** lưu UTC ISO-8601 và mtime_ns; UI chuyển múi giờ local; mtime tương lai không gây overflow recency.
- **Snapshot:** một scan COMPLETE = một snapshot mới; file state đầy đủ, diff với snapshot COMPLETE liền trước; snapshot đầu tiên có tất cả file là added; không ghi nội dung source.

## 5. Scanner: quy tắc cố định

**17 extension:** .py; .js; .jsx; .ts; .tsx; .html; .css; .java; .cs; .cpp; .c; .go; .rs; .php; .json; .yaml; .yml. Phân loại theo bảng tĩnh, không đoán qua shebang hay nội dung. JS/JSX cùng JavaScript; TS/TSX cùng TypeScript.

**9 ignored directory names:** .git; .venv; venv; node_modules; __pycache__; dist; build; .next; .idea. So sánh case-insensitive, prune trước khi descend. V1 không parse .gitignore vì sản phẩm không phụ thuộc Git; file ngoài extension được hỗ trợ không thành building.

**Pipeline và giới hạn:**
1. QFileDialog lấy root, kiểm tra tồn tại/là folder trên ổ local; resolve(strict=True). V1 từ chối root là symlink/junction; UNC/network share nằm ngoài cam kết offline V1 (phát hiện và báo unsupported, kiểm tra cả mapped network drives tại G0); ghi lý do để người dùng chọn đường dẫn thực.
2. Iterative os.scandir; sắp xếp deterministic theo normalized relative path; skip symlink và junction (kể cả trỏ vào trong root); chỉ regular files.
3. Trước khi đọc, resolve và kiểm tra containment; đọc binary streaming từng chunk (đề xuất 1 MiB), đếm LOC + hash một lượt; stat trước/sau, retry tối đa một lần nếu biến động.
4. Discovery/reading trong worker ngoài GUI thread; giới hạn concurrency ban đầu 2–4, có bounded queue; sort kết quả trước diff/layout.
5. Progress theo stage (discover/read/persist/render), số file hoàn thành/tổng, lỗi và current path; hỗ trợ cancel.
6. Chặn tài nguyên bất thường bằng guardrail **đề xuất**: tối đa 20.000 file được hỗ trợ và 64 MiB/file. Vượt ngưỡng => cảnh báo rõ, scan PARTIAL, không commit. Xác nhận/tinh chỉnh các ngưỡng bằng benchmark G0/G5 [P].
7. Không mở/parse project config để chạy script; không import/exec/eval/compile source, không gọi npm/git/build tools của project.

**Quy tắc lỗi để không tạo diff sai (bổ sung quan trọng sau double-check):**
- COMPLETE: đã duyệt hết cây, tất cả file hợp lệ đọc ổn định, không collision và không lỗi discovery; **mới được commit** snapshot+layout trong một transaction.
- PARTIAL: có unreadable directory/file, unstable file, quota exceeded hoặc collision; UI hiển thị lỗi. Nếu có snapshot trước: giữ nguyên city/snapshot cũ. Nếu scan đầu: cho phép preview chỉ trong RAM (có nhãn “Incomplete preview”), **không ghi snapshot, không tính deleted/modified chính thức**.
- CANCELLED/FAILED: dừng lập lịch công việc mới; giữ snapshot và layout cuối cùng, không commit.
- File bị xóa giữa scan được coi là unstable/PARTIAL, không biến thành “deleted” trừ khi scan COMPLETE tiếp theo xác nhận vắng mặt.
- Nếu project thực sự xóa file trước khi scan bắt đầu và discovery hoàn tất không lỗi, đó là deleted hợp lệ.

**Giới hạn bảo mật được thừa nhận:** kiểm tra resolve/containment và skip links giảm rủi ro; TOCTOU do tiến trình đối kháng liên tục thay thế reparse points khi đang mở file vẫn là rủi ro. G0/G1 phải khảo sát kiểm tra path theo Windows file handle nếu cần cam kết chống attacker chủ động; không tuyên bố “chống mọi race” khi chưa có bằng chứng [P].

## 6. SQLite và snapshot transaction

**Vị trí:** QStandardPaths.AppDataLocation của Code City (local per-user), tuyệt đối không tạo .codecity/DB trong project được scan. Bật foreign_keys, WAL (chỉ local disk), busy_timeout; migration theo PRAGMA user_version, backup khi nâng schema.

**Các bảng tối thiểu:**
- projects(id UUID PK, canonical_root, canonical_root_key UNIQUE, display_name, created_at, last_opened_at)
- snapshots(id PK, project_id FK, scanned_at_utc, total_files, total_folders, total_languages, total_lines, duration_ms, scanner_version, layout_version)
- snapshot_files(snapshot_id + file_key PK, rel_path, rel_path_norm UNIQUE trong snapshot, parent, name, extension, language, lines, bytes, mtime_ns, content_hash)
- snapshot_changes(snapshot_id + file_key + change_type PK, previous_snapshot_id, rel_path, change_type IN added/modified/deleted)
- layout_entities(project_id + entity_key PK, kind file/folder, rel_path_norm, parent_key, grid_x, grid_z, layout_version, first_seen_snapshot_id, last_seen_snapshot_id, tombstoned_snapshot_id)
- project_settings(project_id + key PK, value_json)
- schema_migrations hoặc user_version (chọn một cơ chế, có test nâng cấp).

**Commit contract:** đọc snapshot trước → tính current state/diff → cấp phát layout mới trong bộ nhớ → BEGIN IMMEDIATE → insert snapshot/files/changes, upsert layout/tombstone, update project → COMMIT; mọi exception => ROLLBACK. Một scan đồng thời trên cùng project phải bị từ chối hoặc xếp hàng. Đọc snapshot hiện hành không thấy trạng thái nửa chừng. Kiểm thử đóng app giữa giao dịch và khởi động lại.

**Diff:** added=current−previous; deleted=previous−current; modified=common có hash khác; unchanged=common có hash giống. Mtime đổi mà hash giữ nguyên không tính modified. Trạng thái deleted có trong change log nhưng không vẽ building active ở snapshot mới.

## 7. Layout thành phố: bất biến trước thẩm mỹ

**Đơn vị:** lưới integer grid (gridX, gridZ), pitch 9 world units, road/gutter 1, building tối đa 7×7; chỉ một active building mỗi ô. Mỗi folder có district/anchor và các ô liên quan. Tất cả tọa độ active + tombstone lưu trong DB.

**Lần đầu:** dựng folder tree → sort siblings theo normalized path → tính nhu cầu ô → deterministic shelf/guillotine packing các district với ít nhất một road-cell giữa các block → cấp phát file cell → kiểm tra collision → persist.

**Rescan:** cùng fileKey giữ nguyên ô; file mất được tombstone (không repack); file trở lại cùng path nhận lại ô; file mới dùng ô trống trong district hoặc annex gần parent. Global occupancy map gồm active + tombstone chưa thu hồi để không vô tình ghi đè. Folder mới có district/annex mới. Nếu hết vùng, mở rộng không gian ra ngoài; tuyệt đối không dịch chuyển các tòa nhà cũ. “Compact City” chỉ là hành động explicit ở V2.

**Bất biến test được:**
- Với mọi file xuất hiện trong hai snapshot COMPLETE liên tiếp: (gridX, gridZ) bằng nhau tuyệt đối.
- Với mọi cặp active file: ô khác nhau; world AABB không giao nhau.
- Cùng input/sort/layoutVersion/DB trống → cùng initial coordinates.
- Deleted/re-added path khôi phục vị trí nếu tombstone còn.
- Layout migration không được âm thầm thay địa chỉ; tăng layoutVersion cần kế hoạch migration/opt-in.

**Building mapping (giá trị khởi điểm cần visual tuning, không phải dữ liệu nghiên cứu):**
- height = clamp(2.5 + 3.0 × log2(lines + 1), 2.5, 60).
- area = clamp(6 + 2.5 × log2(sizeKB + 1), 6, 42); aspect = 0.80 + 0.45 × hash01(relPath); width = sqrt(area × aspect); depth = sqrt(area ÷ aspect); clamp từng chiều ≤7 để luôn nằm trong ô 7×7.
- Language dùng palette cố định versioned; recency = exp(−max(ageHours,0)/72) tại thời điểm render; added/modified/selected có accent riêng; legend và renderer đọc cùng palette.
- Metrics thay đổi chỉ ảnh hưởng height/footprint/glow, không ảnh hưởng tọa độ.

## 8. 3D engine và hiệu năng

- Scene: ground + district tiles/labels + light + spatial chunks of InstancedMesh + selection overlay. Dùng BoxGeometry/material dùng chung, per-instance matrix/color; KHÔNG tạo Mesh hoặc React component riêng cho mỗi file.
- Chunk 128–512 buildings (khởi điểm 256), bounding box/sphere riêng để culling; raycaster hit (chunkId, instanceId) → fileKey. Không phụ thuộc thứ tự instance qua snapshot; rebuild lookup mỗi lần đổi payload.
- Camera OrbitControls: orbit/pan/zoom, home/reset, focus target animation, giới hạn góc và khoảng cách, click vs drag threshold, double-click open không nhầm với drag.
- LOD ngữ nghĩa: gần có labels/effects, xa chỉ buildings/district; hạn chế folder labels; shadows tĩnh/cập nhật khi scene đổi.
- Chỉ một selection highlight mesh/outline; không rebuild toàn bộ instance buffers khi chọn.
- Phân phối city data theo batch có thứ tự và giới hạn dung lượng; không JSON stringify cả dự án quá lớn vào một event; tránh nghẽn UI thread.
- Theo dõi renderer.info (draw calls), frame p50/p95, memory, WebGL context loss/recovery. Khi WebGL không hỗ trợ, hiện error state có hướng dẫn chứ không blank.

## 9. UX và tương tác bắt buộc

**Layout:** header (project/snapshot/search/rescan/reset) + sidebar project gần đây + canvas 3D + detail panel (ẩn khi chưa chọn) + status bar stats/changes. Dark developer-tool, dễ đọc, không dùng hiệu ứng che thông tin.

**Các trạng thái:** no-project; selecting; scanning/progress; cancelling; ready; incomplete-preview; scan-error; empty-supported-files; project-root-missing; WebGL-failure; VSCode-missing; rescan-in-progress (giữ city cũ). UI phân biệt “scan complete” với “preview không đầy đủ”.

**Thông tin file:** tên, relative path, folder, language, physical LOC, bytes, mtime local, trạng thái diff; không hiển thị source content. Search rank exact name > prefix > name substring > path substring; kết quả chọn sẽ focus camera và highlight.

**VS Code:** double-click file → bridge gửi fileKey → backend tra trusted record, kiểm tra project/root/path còn tồn tại, containment và link policy → tìm executable/launcher VS Code → subprocess argument list, shell=False. Không nhận absolute path từ frontend; nếu không có VS Code, thông báo không fatal. Không tự chạy code.

**Accessibility cơ bản:** thao tác search bằng bàn phím, Esc bỏ chọn, trạng thái có text ngoài màu sắc, contrast đủ đọc, loading có thông tin tiến độ.

## 10. Hợp đồng IPC Qt ↔ React

**Transport:** QWebChannel gắn vào QWebEnginePage; qwebchannel.js được load local qua Qt resource. Production bundle Vite assets tương đối, không CDN và không web server.

**Envelope version 1:** {schemaVersion, requestId?, event|command, payload}. Validate runtime tại boundary cả Python và TypeScript; reject schemaVersion không tương thích, unknown command, invalid fileKey và payload quá lớn.

**Commands tối thiểu:** project.openDialog, project.openRecent(projectId), project.rescan(projectId), scan.cancel(requestId), file.openInVSCode(fileKey), projects.list, snapshot.getLatest(projectId).

**Events tối thiểu:** app.ready, scan.started, scan.progress, scan.error, scan.filesBatch, scan.completed, scan.cancelled, project.listUpdated. Batch gồm projectId, snapshotId (chỉ COMPLETE), batchIndex, isLast, files. Giới hạn khởi điểm 250 records/batch, có sequencing/ack hoặc bounded producer để chống queue phình to [P: spike G0].

**Lifecycle:** React chỉ nhận city model COMPLETE sau DB commit; incomplete preview có event/type riêng và không được giả dạng snapshot. Khi user mở project khác, hủy/đợi scan trước, tránh event trộn project. Mọi signal từ worker về UI theo Qt thread-safe signal/slot; không truy cập GUI từ worker.

## 11. Bảo mật và riêng tư: tiêu chí chặn release

- Không execute/import/eval/compile source, không chạy package scripts, không parse nội dung HTML để hiển thị, không ghi nội dung file vào SQLite/logs.
- Skip symlink/junction (file và directory), root canonical, kiểm tra containment và TOCTOU trước mở file; không tin fileKey/path/JSON từ frontend.
- Không gửi request HTTP/HTTPS/WS/WSS trong production; QWebEngineProfile off-the-record; chặn navigation ngoài app assets, URL scheme lạ, popups và downloads; cấu hình hạn chế local-file access; CSP chặt và chỉ asset tin cậy. Ghi nhận các hạn chế WebEngine sau smoke.
- SQLite dùng parameterized queries; không string-concat SQL từ filename; logging không chứa source content, có thể chứa local relative path (cần ghi rõ trong privacy note).
- VS Code chạy bằng argument list, shell=False; không chấp nhận URL/fileKey giả hoặc traversal.
- Không lưu token, không telemetry, không cloud sync; mọi dữ liệu scan ở máy người dùng.
- Dependency audit/license audit (Qt/PySide, Chromium third-party notices) là gate trước public release. Tính tương thích license phải được xác minh theo mô hình phân phối thực tế [P].

## 12. Cấu trúc repository đích

~~~text
Code-City/
  README.md
  MASTER_PLAN.md
  pyproject.toml
  python-constraints.txt / lock
  .gitignore
  src/code_city/
    __main__.py
    app.py
    desktop/{bridge.py,web_page.py,resources.qrc}
    scanner/{scanner.py,languages.py,models.py,metrics.py}
    storage/{database.py,migrations.py,snapshots.py}
    layout/{allocator.py,mapping.py}
    integrations/vscode.py
  frontend/
    package.json
    package-lock.json
    vite.config.ts
    src/{app,bridge,city,components,types}
    tests/
  tests/{scanner,snapshots,layout,security,integration,fixtures}
  scripts/{build_frontend.ps1,build_windows.ps1,smoke_windows.ps1}
  benchmarks/{generate_fixture.py,run_benchmarks.py,results/}
  docs/{ARCHITECTURE.md,SECURITY.md,TEST_MATRIX.md,RELEASE.md,ADR/}
  .github/workflows/{ci.yml,windows-build.yml}
~~~

**Chỉ MASTER_PLAN.md là baseline bắt buộc lúc khởi tạo.** Các file khác sẽ được tạo ở milestone tương ứng, không tạo skeleton rỗng chỉ để đẹp cây thư mục.

## 13. Lộ trình thực thi có dependency và exit gate

**Ước lượng theo tỷ trọng từ [R]:** foundation 10%, scanner 20%, SQLite/diff 15%, layout/renderer 25%, UX/integration 15%, QA/performance/security 10%, packaging/CI 5%. Đây là tỷ trọng effort, KHÔNG phải cam kết ngày giao. G0 là spike bắt buộc để giảm rủi ro trước khi khóa lockfiles.

### G0 — Feasibility, version lock và benchmark baseline (phải làm đầu tiên)
- [ ] **CC-001** Chốt Python 3.12, PySide6/Qt 6.12.x, Node LTS, React, Three.js, Vite, TypeScript exact versions; tạo lockfiles và dependency matrix.
- [ ] **CC-002** Spike Qt WebEngine tải static Vite assets + QWebChannel ping/pong trên Windows; chặn navigation/network trong production mode.
- [ ] **CC-003** Spike standalone build tối thiểu có QtWebEngineProcess/resources; chạy trên máy Windows khác máy build.
- [ ] **CC-004** Tạo fixture generator 500/1k/5k/10k files; ghi rõ CPU/GPU/RAM/SSD/resolution/Windows của máy benchmark.
- [ ] **CC-005** Chốt chiến lược path containment/TOCTOU trên Windows, file limits và scan error semantics qua test nhỏ; viết ADR nếu đổi quyết định.
**Exit G0:** phiên bản khóa, ping/pong, WebGL hiển thị 100 boxes, thử build standalone chạy được trên máy sạch, benchmark baseline và risk/ADR được ghi. Nếu WebEngine packaging thất bại, thử PyInstaller onedir trước khi cân nhắc đổi stack.

### G1 — Desktop shell + scanner (10% + 20%)
- [ ] **CC-010** Python project CLI entrypoint, PySide main window, Qt resources, native picker, thread-safe bridge, basic React shell.
- [ ] **CC-011** Language map 17 extensions + ignored dirs 9 + deterministic traversal.
- [ ] **CC-012** Symlink/junction/root/containment policy; Unicode/casefold collision handling.
- [ ] **CC-013** Streaming binary LOC/hash/metadata, stat consistency, quotas.
- [ ] **CC-014** Bounded worker, progress, cancellation, COMPLETE/PARTIAL/FAILED result.
- [ ] **CC-015** Unit/security fixtures: CRLF/LF/CR, UTF path, long path, 64MiB edge, permissions, no-execution marker, links.
**Exit G1:** scan folder không Git ra records đúng, GUI không freeze, cancel không tạo snapshot, scanner test suite xanh. Đo memory/time trên 5k fixture và lưu kết quả.

### G2 — Persistence + snapshots (15%)
- [ ] **CC-020** SQLite location, migrations v1, indexes/foreign keys/WAL.
- [ ] **CC-021** Projects/recent projects; UUID/canonical root và missing-root handling.
- [ ] **CC-022** Atomic COMPLETE snapshot commit, rollback khi lỗi/cancel; PARTIAL preview không commit.
- [ ] **CC-023** Diff added/modified/deleted, hash same-size test, rename delete+add.
- [ ] **CC-024** Tests concurrency, crash/restart, migration, snapshot isolation.
**Exit G2:** 3 lần scan fixture có diff chính xác; fail giữa transaction giữ snapshot cũ; DB không được ghi vào project.

### G3 — Layout ổn định + city data contract (12% trong nhóm layout/renderer)
- [ ] **CC-030** Folder tree, district packing deterministic, global occupancy, no-overlap.
- [ ] **CC-031** Persist file/folder slots, tombstones, re-add reclaim, annex expansion.
- [ ] **CC-032** Metric mapping + palette + mappingVersion/layoutVersion.
- [ ] **CC-033** City payload schema + batching/order, Python↔TS fixtures.
- [ ] **CC-034** Property tests 1k/5k paths: no collision, deterministic initial, stable X/Z qua add/delete/edit/re-add.
**Exit G3:** 100% file chung giữa hai COMPLETE snapshots giữ X/Z, tất cả AABB không overlap; dữ liệu city không chứa source contents.

### G4 — Three.js renderer + interaction cơ bản (13% còn lại của nhóm layout/renderer)
- [ ] **CC-040** Scene/camera/lights/ground/district layer, WebGL error state.
- [ ] **CC-041** Chunked InstancedMesh, per-instance colors, selection overlay, renderer.info.
- [ ] **CC-042** Raycast chunk+instanceId→fileKey; orbit/pan/zoom/reset; focus animation.
- [ ] **CC-043** Label LOD, recency/changes accent, resize/context-loss handling.
- [ ] **CC-044** Vitest for mapping/picking/camera + browser/mock bridge smoke.
**Exit G4:** 5k buildings hiển thị và click đúng file; không có Mesh riêng cho từng file; performance số đo được lưu.

### G5 — Product UX và native integration (15%)
- [ ] **CC-050** Sidebar recent projects, open/rescan/cancel, status/progress/errors.
- [ ] **CC-051** Details, stats, language legend, added/modified/deleted indicators.
- [ ] **CC-052** Search ranking, keyboard flow, focus/highlight/reset.
- [ ] **CC-053** Double-click VS Code with fileKey validation, safe subprocess, missing-VSCode UI.
- [ ] **CC-054** All states: empty/partial/missing-root/WebGL/offline/large-project.
**Exit G5:** E2E happy path bằng folder thật, không Git, offline; mỗi state có test/screenshot; VS Code error không làm app crash.

### G6 — Hardening, đo hiệu năng và kiểm thử hệ thống (10%)
- [ ] **CC-060** Automated test matrix cho scanner/snapshot/layout/IPC/UI; coverage report.
- [ ] **CC-061** Security tests path traversal, symlink/junction, race, SQL injection, no execution, blocked network/navigation.
- [ ] **CC-062** Benchmark 500/1k/5k/10k + large/deep projects; capture p50/p95 frame, scan time, peak RSS, draw calls.
- [ ] **CC-063** Fix regressions, test crash recovery, cancel/rescan/project switch, DB migrations.
- [ ] **CC-064** Privacy/license/dependency review; known limitations và docs.
**Exit G6:** toàn bộ acceptance ở mục 15 xanh hoặc có waiver được ghi rõ, không còn P0/P1 bug; báo cáo benchmark có cấu hình máy.

### G7 — Windows release engineering (5%)
- [ ] **CC-070** Reproducible build_frontend.ps1/build_windows.ps1, pinned toolchain.
- [ ] **CC-071** pyside6-deploy standalone, kiểm tra exe, QtWebEngineProcess, DLL, resources, locales, bundled assets; fallback PyInstaller onedir nếu cần.
- [ ] **CC-072** GitHub Actions Windows test/lint/build/upload artifact; cùng scripts local.
- [ ] **CC-073** Smoke trên Windows 10 1809+ x64 và Windows 11 x64, máy sạch không Python/Node/Internet.
- [ ] **CC-074** README user/developer, SECURITY, LICENSE/third-party notices, checksum/release notes.
**Exit G7 = V1 RC:** tải artifact → giải nén → chạy CodeCity.exe trên môi trường được chứng thực → open/scan/render/search/rescan/VS Code chạy được offline. Nếu không có môi trường Win10 để kiểm thử, **không tuyên bố đã hỗ trợ Win10 đầy đủ**.

### G8 — V1 release decision (không tự động publish)
- [ ] **CC-080** Đối chiếu checklist nghiệm thu, kết quả CI, security, benchmark, license, smoke; lập biên bản Go/No-Go.
- [ ] **CC-081** Gắn tag v1.0.0 và GitHub Release sau khi Go; optional NSIS installer/signing có thể là release phụ, không cản RC.
**Exit G8:** release public có artifact + checksum + known limitations; hoặc No-Go có issue blocker cụ thể.

**Thứ tự phụ thuộc:** G0 → G1 → G2 → G3 → G4 → G5 → G6 → G7 → G8. UI mock/fixture và build smoke được spike sớm ở G0, nhưng không được coi là hoàn thành milestone sau. Nếu một gate fail, sửa gate đó trước khi đi tiếp.

## 14. Quy tắc thực thi từng task và quản trị GitHub

- **Definition of Ready (DoR):** có ID CC-xxx, mục tiêu, dependencies, file/module dự kiến, test cases, tiêu chí pass, mức rủi ro và phạm vi không làm.
- **Definition of Done (DoD):** code + unit/integration tests + lint/typecheck + docs nếu đổi contract + Windows smoke khi liên quan; PR có bằng chứng (log/screenshot/benchmark); reviewer đối chiếu acceptance; CI xanh.
- **Workflow đề xuất:** mỗi CC task là một GitHub Issue; branch feature/CC-xxx-short-name; PR vào main; squash merge khi CI xanh. Không commit source trực tiếp main trong giai đoạn triển khai trừ bootstrap đã được chấp thuận.
- **Labels:** area:scanner, area:storage, area:layout, area:renderer, area:desktop, area:ux, area:release; type:feature/bug/spike/docs; priority:P0/P1/P2; gate:G0..G8.
- **Progress:** chỉ đánh dấu milestone DONE khi toàn bộ task + exit gate có bằng chứng; cập nhật bảng trạng thái theo tuần/đợt. Trạng thái hợp lệ: TODO / IN_PROGRESS / BLOCKED / VERIFIED.
- **Change control:** sửa quyết định lớn phải ghi “trước/sau/lý do/ảnh hưởng test, lịch, dữ liệu/migration” và tạo ADR trong docs/ADR; tăng phiên bản Master Plan (1.0.1 chỉnh văn bản, 1.1 thay scope/contract, 2.0 thay kiến trúc).
- **Không xóa các bất biến** (offline, không execute/upload, stable positions, atomic snapshots) chỉ để đạt tốc độ hoặc demo.

## 15. Acceptance matrix đo được

| ID | Bài kiểm tra | PASS khi |
|---|---|---|
| A01 | No Git | Folder không có .git vẫn scan/render được |
| A02 | Offline | Trên máy đã cài/bundle, ngắt mạng vẫn open/scan/render/search/rescan được; không request Internet |
| A03 | Extensions/ignore | Đúng 17 extension, 9 ignore dir theo fixture; case-insensitive |
| A04 | Metadata/LOC | name/path/folder/language/bytes/mtime/hash và LOC LF/CRLF/CR/trailing newline đúng fixture |
| A05 | Security links | Symlink/junction không được scan; traversal/fileKey giả bị từ chối; no-execution marker không xuất hiện |
| A06 | Scanner resilience | Unreadable/unstable/limit => PARTIAL, không commit, lỗi hiển thị; cancel giữ snapshot trước |
| A07 | Snapshot diff | added/modified/deleted đúng; cùng bytes-length nhưng nội dung khác là modified; mtime-only không phải modified |
| A08 | DB integrity | Crash/rollback không để snapshot/layout nửa chừng; AppData nằm ngoài project |
| A09 | Stable layout | 100% common file giữ X/Z; không AABB overlap; delete/re-add reclaim |
| A10 | City completeness | 1 building/active supported file ở COMPLETE snapshot; language palette/legend nhất quán |
| A11 | 3D interaction | orbit/pan/zoom/reset, click đúng instance, search/focus đúng file, details đúng metadata |
| A12 | VS Code | Double-click mở đúng path được revalidate; không VS Code thì nonfatal error |
| A13 | UI states | Có no-project/progress/cancel/partial/error/empty/WebGL/missing-root states; không blank canvas vô thông báo |
| A14 | Windows startup | Standalone chạy trên máy sạch Win11 x64 và Win10 1809+ x64 đã kiểm chứng |
| A15 | Reproducible build | Fresh clone + pinned dependencies + documented scripts => build artifact có CodeCity.exe và WebEngine resources |
| A16 | 5k performance | Trên máy benchmark chuẩn G0, scan+persist+layout ≤60 giây, renderer p95 frame ≤33.3 ms ở 1080p trong cảnh 5k buildings, peak app RSS ≤1.5 GiB |
| A17 | Headroom 10k | Không crash/OOM, vẫn có thể chọn/search; ghi lại số đo, chưa bắt buộc đạt A16 |
| A18 | Quality gate | Test/lint/typecheck/CI xanh; không còn P0/P1; dependency/license review hoàn tất |

**A16 là budget kỹ thuật ĐỀ XUẤT, chưa có số đo thực tế [P].** Máy benchmark G0 phải ghi CPU/GPU/RAM/SSD/Windows, power profile và cách đo. Nếu budget không thực tế, cập nhật bằng ADR với kết quả đo và mục tiêu thay thế trước khi đánh dấu G6, tuyệt đối không âm thầm coi là pass. Phải đo cả scan trên SSD và GPU thực; CI Windows hosted không thay thế test đồ họa máy thật.

## 16. Chiến lược test và fixture

- **Python pytest:** parametrized 17 extensions, 9 ignore, casefold, Unicode/Vietnamese/emoji/long paths, empty/no-newline/LF/CRLF/CR, large files, permissions, race, symlink/junction, no-execution, quotas, cancel, transaction rollback, migrations.
- **Layout property-based:** random trees với 1k–5k paths, duplicate normalized paths, add/delete/re-add/modify; assert unique cells, no overlap, stable coords, deterministic initial.
- **TypeScript Vitest:** mapping clamp/log, palette, search ranking, payload schema, chunk instance lookup, camera focus, selection, error states.
- **Integration:** Qt QWebChannel request/response, multi-batch order, project switch while scan, resource loading, network block, VS Code launcher path.
- **Windows smoke:** build packaged app, first launch, select fixture, scan, screenshot city, search, rescan, restart DB, offline, WebEngine subprocess/resource check.
- **Benchmark:** fixtures 500/1k/5k/10k, many tiny files, deep tree, few large files; record scan/persist/layout/render times, p50/p95 frames, draw calls, RSS, environment, regression from baseline.
- **Test dữ liệu nguy hiểm:** fixture .py chứa side effect ghi marker; scanner chỉ đọc bytes, marker phải không tồn tại. Fixture path traversal, crafted JSON, symlink/junction và SQL metacharacters.

## 17. Build, CI, release và rollback

**Dev:** Python venv 3.12; npm ci trong frontend; Vite build base relative; Python desktop shell load local resources. Dev server nếu có chỉ phục vụ tài sản Code City trong môi trường dev, không serve source người dùng.

**CI:** trên pull_request và push main: Python tests/lint → npm ci/typecheck/lint/Vitest/build → Windows packaging → structural smoke → upload artifact. Workflow pin action revisions theo chính sách bảo mật; versions của actions và toolchain phải được kiểm tra tại thời điểm G7, không copy mù ví dụ [R].

**Windows package:** standalone/one-folder là V1; kiểm tra QtWebEngineProcess.exe, plugins, translations/locales, DLL, app assets; test startup trên máy sạch. Onefile không phải mục tiêu. NSIS installer, signing, auto-update là hậu V1/optional.

**Rollback:** mỗi release giữ artifact + checksum + tag; schema migration có backup/rollback plan; không nâng schema DB không tương thích khi chưa có migration test; lỗi startup bản mới phải có hướng dẫn quay lại bản cũ (không ghi đè database không thể đọc lại).

## 18. Risk register và phương án dự phòng

| Rủi ro | Mức | Dấu hiệu / trigger | Giảm thiểu / fallback | Gate |
|---|---|---|---|---|
| Qt WebEngine thiếu runtime khi đóng gói | Cao | Exe chỉ chạy trên máy build, trắng màn hình | Spike standalone sớm, verify helpers/resources; PyInstaller onedir fallback | G0/G7 |
| Qt patch/Chromium không tương thích Win10 | Cao | Fail smoke Win10 | Pin tested Qt6.12 patch; release chỉ claim OS đã test | G0/G7 |
| Symlink/junction/TOCTOU thoát root | Cao | Fixture truy cập ngoài root | Skip links, containment, handle-level hardening nếu cần, document residual | G1/G6 |
| Scan partial gây false deleted | Cao | Lỗi I/O rồi diff báo deleted | Chỉ COMPLETE commit, preview riêng | G1/G2 |
| Layout bị dịch sau thêm file | Cao | X/Z common file thay đổi | Persist slots, tombstone, property tests | G3 |
| 5k city lag/WebGL context loss | Cao | p95 frame vượt budget, blank | Instancing/chunks/labels LOD; WebGL error UI; benchmark | G4/G6 |
| Memory/scan time quá cao | Trung/Cao | RSS/time vượt budget | Binary streaming, bounded workers, quotas, batch IPC | G1/G6 |
| IPC race, event lẫn project | Trung | UI hiện data project cũ | requestId/projectId, state machine, ordering, cancel | G0/G5 |
| SQLite corruption/migration | Cao | Restart không đọc snapshot | Transaction, migration tests, backup, crash recovery | G2/G6 |
| VS Code command/path injection | Cao | Forged fileKey mở file khác | Trusted mapping, revalidate, shell=False | G5/G6 |
| License/third-party notices | Cao | Không đủ điều kiện public | Audit trước release, bổ sung notices hoặc đổi distribution model | G6/G8 |
| Scope creep V2 chen V1 | Trung | Gate trễ, feature chưa nghiệm thu | MUST/WON'T + ADR + task gating | Mọi gate |

## 19. Backlog sau V1, không được làm chậm release

**V2:** optional .gitignore/custom ignore; file watcher; timeline snapshots; compact city explicit; rename heuristics; richer search; more languages; snapshot comparison visual overlay; NSIS installer/code signing.

**V3:** dependency/import graph, AST/complexity, multi-project comparison, architectural insights, plugins, optional cross-platform packaging. Nếu sau này dùng Git, phải là tính năng tự chọn, không thành dependency của scanner V1.

## 20. Biên bản double-check trước khi chốt baseline

**Đã rà soát logic tài liệu [R] và chốt các điểm dễ gây sai khi implement:**
1. **Partial scan vs snapshot:** [R] vừa yêu cầu UI chịu lỗi file vừa yêu cầu snapshot atomic; Master Plan giải quyết bằng COMPLETE-only commit và PARTIAL preview riêng, không tạo false deleted.
2. **Stability:** deterministic sort không đủ giữ tọa độ sau insert; bắt buộc persistent cells + tombstones + annex.
3. **LOC:** byte-stream newline count cần định nghĩa rõ CR/LF/CRLF và chunk boundary; không gọi đây là semantic LOC.
4. **File identity:** casefold có thể collision trên volume case-sensitive; phải detect, không âm thầm hợp nhất.
5. **Security:** skip links và resolve không chứng minh an toàn tuyệt đối trước TOCTOU; thêm spike/giới hạn rõ.
6. **Big files:** [R] không chốt quota; thêm guardrail có trạng thái PARTIAL, cần benchmark để xác nhận.
7. **Hash:** nâng digest BLAKE2b từ ví dụ 128-bit lên 256-bit cho margin; diff vẫn dựa nội dung.
8. **IPC:** phân biệt preview và COMPLETE payload; bổ sung requestId, batching/order/backpressure.
9. **Packaging:** standalone là mục tiêu, không đồng nhất “.exe” với “single physical file”; smoke máy sạch là bắt buộc.
10. **Performance:** không biến dự đoán thành kết quả; đặt budget A16 có nhãn [P] và máy chuẩn G0.
11. **Windows:** Qt 6.12 chính thức hỗ trợ Win10 1809+ và là dòng cuối cho Win10 [V], nhưng hỗ trợ thực tế Code City chỉ được claim sau smoke.
12. **GitHub:** repo đang trống khi bắt đầu; commit planning docs không bao gồm mã nguồn, CI hoặc ứng dụng.
13. **Windows project identity:** SQLite UNIQUE mặc định không tự casefold canonical root; bổ sung canonical_root_key để tránh duplicate project khi chọn lại cùng thư mục với khác kiểu chữ.
14. **Local-first:** giới hạn rõ cam kết V1 cho thư mục trên ổ local; UNC/mapped network share phải được phát hiện, không giả định chúng hoạt động offline.

**Chưa xác minh bằng chạy thực tế:** exact dependency compatibility, Windows Qt WebEngine packaging, TOCTOU hardening, FPS/memory/scan budgets, license distribution, Win10/Win11 smoke. Các mục này là G0/G6/G7 blockers, không phải bằng chứng hoàn thành.

## 21. Nguồn tham khảo chính thức và xuất xứ

Nền nghiên cứu [R]: báo cáo Deep Research “Code City V1: Deep Technical Research and Implementation Blueprint for Windows”, 2026-10-21 (nguồn đầu vào của Master Plan; không phải code hiện có trong repo).

Nguồn chính thức đã đối chiếu [V], truy cập 2026-10-21:
- Qt 6.12 Supported Platforms, Win10 1809+, last Qt Win10: https://doc.qt.io/qt-6.12/supported-platforms.html
- Qt WebChannel JavaScript API, qwebchannel.js local: https://doc.qt.io/QT-6/qtwebchannel-javascript.html
- Qt for Python pyside6-deploy, Nuitka/standalone: https://doc.qt.io/qtforpython-6/deployment/deployment-pyside6-deploy.html
- Python 3.12 pathlib, Path.is_junction: https://docs.python.org/3.12/library/pathlib.html
- Three.js InstancedMesh: https://threejs.org/docs/pages/InstancedMesh.html
- Three.js Raycaster, instanceId: https://threejs.org/docs/pages/Raycaster.html
- SQLite WAL, local host requirement: https://www.sqlite.org/wal.html

Nguồn nghiên cứu [R] đề xuất kiểm tra lại khi implement:
- Python scandir: https://docs.python.org/3.12/library/os.html#os.scandir
- Qt QWebEnginePage: https://doc.qt.io/qt-6/qwebenginepage.html
- Qt QStandardPaths: https://doc.qt.io/qt-6/qstandardpaths.html
- Vite public base path: https://vite.dev/guide/build.html#public-base-path
- GitHub Actions workflow syntax: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- Python subprocess: https://docs.python.org/3.12/library/subprocess.html
- Qt licensing: https://www.qt.io/licensing/

---

**Bản này là master plan để bám vào, không phải tuyên bố đã xây xong tool. Bước tiếp theo được phép thực hiện là G0/CC-001; mọi code phải phục vụ gate đang mở.**