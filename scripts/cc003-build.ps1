# CC-003 build reproducibility: invoke from any CWD on Windows x64 with pinned
# CPython 3.12.10 and Node 24.22.0/npm 11.19.1 installed. Requires MSVC C compiler.
[CmdletBinding()]
param([string]$PythonCommand = 'python')
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $repo
try {
    if (-not (Test-Path '.\cc003_entry.py') -or -not (Test-Path '.\frontend\package-lock.json')) {
        throw 'CC-003 files not found at detected repository root'
    }
    if (-not (Test-Path '.\.venv\Scripts\python.exe')) {
        & $PythonCommand -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Failed to create venv' }
    }
    $py = (Resolve-Path '.\.venv\Scripts\python.exe').Path
    & $py -c "import sys,struct; assert sys.version_info[:3]==(3,12,10) and struct.calcsize('P')*8==64, (sys.version,struct.calcsize('P')*8)"
    if ($LASTEXITCODE -ne 0) { throw 'Requires exact CPython 3.12.10 x64' }
    if ((node --version) -ne 'v24.22.0') { throw 'Requires Node 24.22.0' }
    if ((npm --version) -ne '11.19.1') { throw 'Requires npm 11.19.1' }
    & $py -m pip install --only-binary=:all: -r requirements.txt -c python-constraints.txt
    if ($LASTEXITCODE -ne 0) { throw 'Pinned PySide6 install failed' }
    & $py -m pip install -r packaging/cc003-build-requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Pinned Nuitka build tools install failed' }
    & $py -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'pip check failed' }
    & $py -m nuitka --version
    if ($LASTEXITCODE -ne 0) { throw 'Nuitka unavailable' }
    Push-Location frontend
    try {
        npm ci --no-audit --no-fund
        if ($LASTEXITCODE -ne 0) { throw 'npm ci failed' }
        npm run typecheck
        if ($LASTEXITCODE -ne 0) { throw 'frontend typecheck failed' }
        npm run build
        if ($LASTEXITCODE -ne 0) { throw 'frontend Vite build failed' }
    } finally { Pop-Location }
    & $py -m unittest discover -s tests -p 'test_protocol.py' -v
    if ($LASTEXITCODE -ne 0) { throw 'protocol unit tests failed' }
    & $py -m unittest discover -s tests -p 'test_security.py' -v
    if ($LASTEXITCODE -ne 0) { throw 'security unit tests failed' }
    & $py -m unittest discover -s tests -p 'test_resources.py' -v
    if ($LASTEXITCODE -ne 0) { throw 'resource unit tests failed' }
    & node scripts/verify_governance.mjs
    if ($LASTEXITCODE -ne 0) { throw 'governance failed' }

    $work = Join-Path $repo 'build\cc003'
    $staging = Join-Path $repo 'dist\cc003'
    if (Test-Path $work) { Remove-Item -LiteralPath $work -Recurse -Force }
    if (Test-Path $staging) { Remove-Item -LiteralPath $staging -Recurse -Force }
    New-Item -ItemType Directory -Path $work,$staging -Force | Out-Null
    Write-Host "CC003_NUITKA_BUILD_START $(Get-Date -Format o)"
    # Official Nuitka PySide6 plugin handles WebEngine DLLs, process and Qt resources.
    # Data directory is application-authored, NOT a user-selected project folder.
    & $py -m nuitka --mode=standalone --enable-plugin=pyside6 `
        --include-data-dir="frontend/dist=frontend/dist" `
        --output-dir="$work" --output-filename="CodeCitySpike.exe" `
        --msvc=latest --report="$work\nuitka-report.xml" `
        cc003_entry.py
    if ($LASTEXITCODE -ne 0) { throw "Nuitka packaging failed, see $work" }
    $dists = @(Get-ChildItem -LiteralPath $work -Directory -Filter '*.dist')
    if ($dists.Count -ne 1) { throw "Expected one Nuitka .dist folder, found $($dists.Count)" }
    $destination = Join-Path $staging 'CodeCitySpike'
    Copy-Item -LiteralPath $dists[0].FullName -Destination $destination -Recurse -Force
    & (Join-Path $PSScriptRoot 'cc003-verify-package.ps1') -PackageDir $destination -WriteManifest
    if ($LASTEXITCODE -ne 0) { throw 'Structural verification failed' }
    $tools = Join-Path $staging 'tools'
    New-Item -ItemType Directory -Path $tools -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'cc003-verify-package.ps1') -Destination $tools
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'cc003-smoke.ps1') -Destination $tools
    $zip = Join-Path $staging 'CodeCitySpike.zip'
    Compress-Archive -Path "$destination","$tools" -DestinationPath $zip -CompressionLevel Optimal -Force
    $sum = (Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant()
    "$sum  CodeCitySpike.zip" | Set-Content -LiteralPath (Join-Path $staging 'CodeCitySpike.sha256') -Encoding ASCII
    Write-Host "CC003_BUILD=PASS"
    Write-Host "CC003_ZIP=$zip"
    Write-Host "CC003_SHA256=$sum"
}
finally { Pop-Location }
