# CC-005: Windows filesystem security and scan outcome decision (G0)

**Master Plan:** v1.0.1. **Scope:** independent Python 3.12 proof-of-concept, quotas and outcome-contract tests. Not a production scanner, not complete snapshot persistence. **Issue:** [#11](https://github.com/giabao2605/Code-City/issues/11).

## Threat and trust model
The chosen local project is untrusted. Other processes with access may swap files/ancestors to symlinks, NTFS junctions or other reparse points while scan is running; files may grow, truncate, disappear, be unreadable, or contain adversarial names (path traversal, device names, ADS, Unicode/casefold collisions). A higher-privileged malicious process or filesystem filter can invalidate weaker checks. No source is executed, compiled, imported or sent over the network by the probe.

## Root and path rules
- Accept only an absolute, existing directory on an observed fixed local volume; fail closed for UNC roots and mapped remote drives using `GetDriveTypeW` plus UNC lexical checks. Reject a root itself marked symlink/junction/reparse via `lstat` and the Windows reparse attribute. Canonicalize via `resolve(strict=True)`; root location/drive can change during scan, so revalidate.
- Accept source *relative paths* from trusted discovery only, never arbitrary frontend absolute strings. Refuse empty, `.`, `..`, backslashes, drive/colon/ADS, NUL/control, trailing dots/spaces, reserved device components. Join beneath canonical root, `resolve(strict=True)`, use `relative_to` not `startswith`.
- Before accessing a candidate check each path component using `lstat` and `FILE_ATTRIBUTE_REPARSE_POINT`; refuse all symlinks/junctions, even inward links. File must be regular. `NFC` plus `casefold` forms the relative identity key; collisions make scan PARTIAL. Do not descend into any linked directory.
- Probe handles UNC/network policy; Windows mount points, removable volumes and remote filesystem virtualization beyond observed fixed/remote API classification need G1/G6 hardening.

## TOCTOU alternatives and chosen V1 direction

| Option | Strength | Weakness | Decision |
|---|---|---|---|
| A: path checks + stat/retry | Simple, platform-friendly | Resolve→open is raceable; malicious reparse substitution may escape | Reject as sole containment defense |
| B: Win32 opened-handle verification | Validates what was *actually opened*: path, volume, attrs, identity | Handle final-path check alone is not an atomic ancestor walk; aliasing/rename/mount races persist | Useful building block |
| C: hybrid, fail closed | Root/path preflight + reject reparse + pinned handles + actual-target verification before ReadFile + read stability + bounded retry | Additional OS calls and residual races, Windows-specific code | **Selected for V1 G1 implementation**, subject to successful Windows probes |

### Security prototype order
1. Check selected absolute root, link flag, canonicalized root and `GetDriveTypeW` (fixed only). Parse strictly relative candidate; walk each component via `lstat`, detect reparse; reject escaping canonical target; capture root/file stat.
2. Open root with `CreateFileW(FILE_FLAG_OPEN_REPARSE_POINT|FILE_FLAG_BACKUP_SEMANTICS)`; open file with `CreateFileW(FILE_FLAG_OPEN_REPARSE_POINT|FILE_FLAG_SEQUENTIAL_SCAN)`. Share read/write/delete for adversarial race testing.
3. `GetFileInformationByHandle` on both handles: fail closed on reparse; require same volume serial. `GetFinalPathNameByHandleW` on both handles: require file final path be *component-wise beneath root final path*, not an arbitrary prefix. **No content read before these checks.**
4. Enforce actual handle file size, streaming `ReadFile` chunks up to 1 MiB, check bytes read, final file identity/time/size, root identity, final paths, path-level stat and reparse again. On any mismatch/unknown, reject or mark unstable/PARTIAL. Always `CloseHandle` via `finally`.
5. G1 production may retry **once** on transient change; second failure → PARTIAL without commit. The POC does not implement scan worker/retry/persistence.

**Precise guarantee:** the POC is designed not to return a hash of outside-root file data under the deterministic substitutions tested, because it refuses untrusted handle targets before reading. It does **not** establish robust security against an adversarial process with unbounded ability to relocate ancestors, directory mount points, change file content while preserving size/mtime, use hardlinks, or exploit path aliases. `GetFinalPathNameByHandleW` may expose DOS paths requiring better file-ID-based ancestor chaining for strong containment. Do not claim universally TOCTOU-proof. Consider stronger handle-relative traversal/FileIdInfo in G1/G6 if the threat model requires it, or refuse uncertain volumes and abort scan.

## Resource limits (confirmed as guardrail semantics; **not** scanner throughput)
- Supported: 17 configured extensions; prune nine ignored directory names case-insensitively; ignored and unsupported do not count towards quota.
- `MAX_FILES=20_000`, inclusive; 20,001st supported file causes `FILE_COUNT_LIMIT`, PARTIAL. 0 supported files may COMPLETE if discovery finishes cleanly.
- `MAX_BYTES=64*1024*1024=67,108,864` bytes, inclusive; one more byte causes `FILE_SIZE_LIMIT`, PARTIAL. Preflight **and handle size** are checked. Actual bytes read must match handle metadata; truncation/growth/mismatch → UNSTABLE/PARTIAL, excess bytes → PARTIAL immediately.
- Up to 1 MiB per read chunk; initially 2 workers, 4 hard maximum; bounded work queue remains G1. Max one retry for instability. Reject invalid/negative/Boolean limits. Do not aggregate source contents in memory.
- Deterministic `after_first_chunk` hooks exercise growth and truncation while the file handle remains open; both must fail closed. CC-004 500/1k/5k/10k **generation and verification measurements** are synthetic dataset baselines and NOT scanner throughput/A16/A17. This probe's 20k count is an isolated counter boundary test, not a real 20k-file scanner run.

## Outcome and snapshot eligibility

| Situation | Outcome | Error examples | Snapshot |
|---|---|---|---|
| All discovery/read success, no link/collision/quota/unstable/cancel | COMPLETE | none | Eligible for atomic commit |
| Traversal error, unreadable file, collision, deleted during scan, growth/truncate, quota | PARTIAL | UNREADABLE_DIRECTORY, UNREADABLE_FILE, UNSTABLE_FILE, PATH_COLLISION, FILE_COUNT_LIMIT, FILE_SIZE_LIMIT, CONTAINMENT | **No commit** |
| User cancels; no new work scheduled | CANCELLED | CANCELLED | **No commit** |
| Invalid root, unsupported storage, unrecoverable systemic problem preventing meaningful scan | FAILED | INVALID_ROOT, UNSUPPORTED_DRIVE, SYSTEM_FATAL | **No commit** |

All non-COMPLETE outcomes must preserve last COMPLETE snapshot and layout; incomplete first scan may only preview RAM with an explicit `Incomplete preview` label. Deletions may only be calculated after a *new* fully completed discovery/read. Deleted mid-scan is PARTIAL; file absent before clean discovery is a valid deletion. Error records include stage, code, relative path (never source body), user-facing message and bounded retry count. Stage and counts are explicit. SQLite atomic transaction remains G2 CC-022.

## Test evidence and reproduction
Fresh Windows x64 repository clone, Python **3.12.10**:
```powershell
python -m unittest discover -s tests -p test_cc005_security.py -v
python -m unittest discover -s tests -p test_fixture_generator.py -v
node scripts/verify_governance.mjs
```
Windows Actions workflow: `.github/workflows/cc005-security.yml` on `windows-2022`, pins checkout/setup-python/upload-artifact to known SHAs and saves host report, tests and governance output. Tests using symlink privilege or mapped drives must say SKIP with reason rather than PASS. Physical Windows 10/11, full 20k-file scan, deterministic content mutation during `ReadFile`, 100 genuine WebGL boxes and A01–A18 end-to-end acceptance are **NOT_RUN** unless backed by separate evidence.

## Downstream requirements and change control
CC-011 performs iterative sorted discovery and ignore; CC-012 implements V1 root/link/path rules and logs unsupported volume; CC-013 actual streaming LOC+BLAKE2b-256 and consistency on opened handle, quota; CC-014 bounded workers, retry/cancel and fail-closed statuses; CC-015 expands links/UNC/race/permissions/long-path tests. G2 CC-022 commits only COMPLETE. G6 validates limitations and physical Windows. The chosen hybrid is a **conservative implementation detail of the current Master Plan** (sections 5 and 18 already call for handle-level investigation), not an architecture/contract change, so no ADR required at this point. Any stronger containment guarantee or V1 scope change requires ADR and owner approval.

## G0 exit gap
100 **real WebGL** rendered boxes are required by Master Plan G0. Neither CC-004 nor this filesystem-only CC-005 probe establishes that evidence. Keep **G0 IN_PROGRESS** until independently verified; do not silently implement G4 renderer.

## Observed first Windows run (branch push; not final PR-head evidence)
- [Windows CI #39718295537](https://github.com/giabao2605/Code-City/actions/runs/39718295537): SUCCESS, Python 3.12.10 x64, security **27 tests (26 pass, 1 mapped-drive SKIP)**; real symlink, junction, file substitution, streaming 64MiB boundary tested; CC-004 regression and governance passed. This result precedes the in-read mutation tests and must not be attributed to later PR heads.
- No mapped network drive on the hosted runner, thus the integration case is NOT_RUN/SKIP; `GetDriveTypeW` policy code exists but lacks real mapped-drive exercise. Physical Win10/Win11 and G0 100-WebGL-box proof are NOT_RUN.
