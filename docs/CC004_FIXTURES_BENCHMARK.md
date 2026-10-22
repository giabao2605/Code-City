# CC-004 — Deterministic fixtures and Windows benchmark baseline

**Gate:** G0 · **Task:** CC-004 · **Master Plan:** v1.0.1 · [Issue #9](https://github.com/giabao2605/Code-City/issues/9).
**Scope:** reusable offline synthetic source projects and environmental inventory. **Out of scope:** G1 scanner, G2 snapshots, G3 layout, G4 product renderer, CC-005 TOCTOU security architecture, G6 A16/A17 performance acceptance, G7/G8 packaging/release.

## Exact dependencies

CC-004 uses **Python standard library only**, target CPython 3.12.10 x64, without pip install or network. The existing locked dependencies remain unchanged: PySide6/Qt 6.12.0, PySide6-WebEngine/Pdf 6.12.0.140; Node 24.22.0/npm 11.19.1; React/DOM 19.3.1; Three.js 0.186.1; Vite 8.3.4; TypeScript 5.9.3; Nuitka 4.1.1 (CC-003 build tool).

## Reproduction: fresh clone, PowerShell

~~~powershell
git clone https://github.com/giabao2605/Code-City.git
cd Code-City
git switch feature/CC-004-fixture-benchmark-baseline
python --version
python -m unittest discover -s tests -p test_fixture_generator.py -v
foreach ($n in @(500,1000,5000,10000)) {
    $root = Join-Path $env:TEMP "CC004 fixture $n"
    .\scripts\cc004-generate.ps1 -Output $root -Count $n -Profile mixed -Seed 42
    .\scripts\cc004-verify.ps1 -Root $root
}
.\benchmarks\capture_environment.ps1 -FixtureRoot $env:TEMP
node scripts/verify_governance.mjs
~~~

Use NEW output paths; the generator never overwrites existing directories or manifests. Direct CLI examples:

~~~powershell
python benchmarks/generate_fixture.py --output "$env:TEMP\fixture-5000" --count 5000 --profile mixed --seed 42 --max-bytes 268435456
python benchmarks/verify_fixture.py --root "$env:TEMP\fixture-5000" --manifest "$env:TEMP\fixture-5000.manifest.json"
~~~

Exit code 0 means verified success; 2 means file, security or integrity error; argparse rejects invalid options nonzero. JSON stdout captures generation/verification timings. Large-file progress prints to stderr. Explicit, verified cleanup: `.\scripts\cc004-verify.ps1 -Root $root -Cleanup`. Cleanup fails closed on unknown/unowned directories or tampering.

## Profiles and exact count policy

Supported-file quotas are 500 / 1000 / 5000 / 10000, excluding ignored decoys, unsupported decoys and metadata. The generator inserts **9 ignored-source decoy files + 4 unsupported-extension files + 1 ownership marker** for physical-file counts of **514 / 1014 / 5014 / 10014**. The JSON manifest is a **sibling to the fixture directory**, never source.

Supported extensions (17): `.py .js .jsx .ts .tsx .html .css .java .cs .cpp .c .go .rs .php .json .yaml .yml`. Ignored directories (9, case-insensitive): `.git .venv venv node_modules __pycache__ dist build .next .idea`. Unsupported decoys: `.txt .md .svg .lock`.

- `mixed`: multiple nested modules, all extensions, tiny/medium and some larger synthetic texts, Unicode Vietnamese folders, whitespace, mixed-case names.
- `tiny`: zero-byte and sub-KiB files with varied newline endings; stresses traversal overhead.
- `deep`: branched 10+ component paths, Windows-portable length guardrails and Unicode.
- `large`: occasional 128 KiB and 1 MiB text files, streamed without retaining whole file payloads in memory.

Generated source is *synthetic data*, never compiled, imported or executed. It need not be syntactically valid software. Directory `.git` is only an ignore decoy, not a Git repository.

## Reproducibility and SHA-256 verifier

Same generator version (1), count, profile, seed and options produce identical normalized relative paths, source bytes, sizes and checksums regardless of output parent, locale, clock or filesystem traversal order. Different seeds change logical dataset. The external UTF-8 JSON manifest includes: `schemaVersion`, `generatorVersion`, `count`, `seed`, `profile`, `supportedFileCount`, `ignoredFileCount`, `unsupportedFileCount`, `metadataFileCount`, `physicalFileCount`, `totalBytes`, `datasetDigest` and all files' path, category, byte size and SHA-256. No absolute output root or creation timestamps enter file bytes.

The independent verifier walks **actual disk files** instead of trusting generated counters, rehashes source/decoy/ownership marker, catches missing/extra/modified files, manifest corruption, count or digest tampering, category errors, duplicate casefold paths, incomplete extension/ignore coverage and illegal symlinks/junctions. This verifier only validates fixture structure; it does not implement G1 production scanner traversal.

Safety: fail on existing output/manifest, symlink/junction output ancestors, impossible count/profile, budget overflow, low disk space or Windows-too-long paths. Default total byte budget 256 MiB; configurable upper bound 2 GiB; disk reserve 16 MiB. Generator streams <=8 KiB chunks and verifier hashes <=1 MiB chunks. Partial output stays on disk for inspection, never automatically deleted. Cleanup requires full ownership-marker and manifest validation, deletes only enumerated files with no recursive `rmtree`, and refuses paths with links/junctions. A malicious concurrent Windows reparse-point race still requires CC-005 handle-level security assessment. Never claim adversarial TOCTOU immunity here.

## Windows machine environment and metrics

The read-only PowerShell capture records observed CPU model/core/logical processors/architecture/clock; GPU model/vendor/driver with physical acceleration UNVERIFIED; RAM total/free; drive filesystem/capacity/free, bus/media if observable, otherwise UNKNOWN; Windows edition/version/build/architecture; screen width/height and scale where accessible; headless/hosted display limitation, power scheme and AC/battery UNVERIFIED if needed; Python/Node/npm, Git commit SHA, generator version and UTC timestamp. It never collects serials, Windows username or hardware IDs. A GitHub-hosted Windows Server 2022 runner is **not** a physical Windows 10/11 GPU workstation, a verified SSD, or proof of 1080p graphics capability.

The generator and verifier emit real wall-clock elapsed seconds and dataset byte count. These figures are **fixture I/O metrics**, not scan/persist/layout/render performance. A single cold run does not provide meaningful p50/p95; future G6 measurements must capture repeat count, warmup and cache conditions.

## CI, negative tests and constraints

[Windows CI workflow](../.github/workflows/cc004-fixtures.yml) on hosted Windows Server 2022 installs pinned CPython 3.12.10 x64; runs 24 unittest cases for 17 extensions, 9 ignored folders, counts, determinism, all 4 profiles, Unicode/space, malformed count/budget, overwrite protection, checksum/file additions/deletions/changes, corrupt manifests, owned/unowned cleanup, no execution/network and CLI exit; then actually generates and verifies all four supported sizes. Upload evidence is **manifests, JSON logs and hardware report only**; not 10k source files. Actions checkout/setup-python/upload-artifact SHA pinned like CC-003.

| Metric | CC-004 evidence rule |
|---|---|
| 500/1k/5k/10k supported files and SHA-256 | VERIFIED only when CI actually passes |
| Generation/verification seconds and total physical bytes | MEASURED only from real logs |
| CPU/GPU/RAM/storage/display/power | OBSERVED or UNKNOWN/UNVERIFIED in report |
| Scanner, SQLite snapshot, layout, renderer p50/p95/draw calls, app peak RSS | NOT_RUN |
| A16: 5k scan+persist+layout <=60s; 1080p render p95 <=33.3ms; RSS <=1.5 GiB | NOT_RUN |
| A17: 10k no OOM/crash, search/select, timings | NOT_RUN |
| G0 WebGL 100 genuine boxes | NOT_RUN pending real Qt/Three.js canvas probe, never count 100 HTML divs |

CC-004 VERIFIED, if achieved, is **not** G0 exit. CC-005 and G0 exit evidence remain required; G1–G8 remain LOCKED. Record actual final CI run/artifact links before marking VERIFIED. Physical hardware benchmarks and real WebGL 100-box tests cannot be fabricated from the hosted runner.
