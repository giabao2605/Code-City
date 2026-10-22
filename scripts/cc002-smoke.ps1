# CC-002: from repository root in Windows PowerShell, with pinned Python/Node installed.
$ErrorActionPreference = "Stop"
if (-not (Test-Path ".\frontend\package.json")) { throw "Run from repository root" }
py -3.12 -c "import sys,struct; assert sys.version_info[:3] == (3,12,10) and struct.calcsize('P')*8 == 64"
if ((node --version) -ne "v24.22.0") { throw "Requires Node 24.22.0" }
if ((npm --version) -ne "11.19.1") { throw "Requires npm 11.19.1" }
if (-not (Test-Path ".\.venv\Scripts\python.exe")) { py -3.12 -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt -c python-constraints.txt
if ($LASTEXITCODE -ne 0) { throw "pip install failed" }
& .\.venv\Scripts\python.exe -m pip check
if ($LASTEXITCODE -ne 0) { throw "pip check failed" }
Push-Location frontend
try {
    npm ci --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { throw "npm ci failed" }
    npm run typecheck
    if ($LASTEXITCODE -ne 0) { throw "Typecheck failed" }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Build failed" }
}
finally { Pop-Location }
& .\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_protocol.py" -v
if ($LASTEXITCODE -ne 0) { throw "IPC unit tests failed" }
& .\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_security.py" -v
if ($LASTEXITCODE -ne 0) { throw "Policy tests failed" }
Write-Host "Real Qt WebEngine integration test (offscreen, not a physical GUI smoke)"
$oldPlatform = $env:QT_QPA_PLATFORM
try {
    $env:QT_QPA_PLATFORM = "offscreen"
    & .\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_webengine.py" -v
    if ($LASTEXITCODE -ne 0) { throw "Qt WebEngine integration failed" }
}
finally { $env:QT_QPA_PLATFORM = $oldPlatform }
node scripts/verify_governance.mjs
if ($LASTEXITCODE -ne 0) { throw "Governance failed" }
Write-Host "To inspect a REAL GUI, run: .\.venv\Scripts\python.exe -m spike.app"
