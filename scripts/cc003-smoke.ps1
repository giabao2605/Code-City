# Run from inside extracted artifact on a separate Windows machine.
# Uses packaged CodeCitySpike.exe ONLY; no checkout/venv/Node/npm needed.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$PackageDir,
    [int]$TimeoutSeconds = 110,
    [switch]$NegativeTests
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath $PackageDir).Path
$exe = Join-Path $root 'CodeCitySpike.exe'
if (-not (Test-Path -LiteralPath $exe)) { throw "Missing exe: $exe" }
$logs = Join-Path (Split-Path $root -Parent) 'smoke-logs'
New-Item -Path $logs -ItemType Directory -Force | Out-Null

function Invoke-Check {
    param([string]$Directory,[string]$Label,[bool]$ExpectSuccess)
    $binary = Join-Path $Directory 'CodeCitySpike.exe'
    $output = Join-Path $logs "$Label.stdout.log"
    $err = Join-Path $logs "$Label.stderr.log"
    $working = [IO.Path]::GetTempPath()
    $before = @(Get-Process -Name 'QtWebEngineProcess' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
    Write-Host "CC003_START=$Label dir=$Directory cwd=$working runner=$env:RUNNER_NAME"
    $proc = Start-Process -FilePath $binary -ArgumentList '--smoke-test' -WorkingDirectory $working -PassThru -RedirectStandardOutput $output -RedirectStandardError $err
    $done = $proc.WaitForExit($TimeoutSeconds * 1000)
    if (-not $done) {
        & taskkill.exe /F /T /PID $proc.Id 2>$null | Out-Null
        throw "CC003_SMOKE=FAIL $Label timeout $TimeoutSeconds s"
    }
    $exit = $proc.ExitCode
    if (Test-Path $output) { Get-Content -LiteralPath $output | Select-Object -Last 10 | Write-Host }
    if (Test-Path $err) { Get-Content -LiteralPath $err | Select-Object -Last 30 | Write-Host }
    Start-Sleep -Seconds 2
    $after = @(Get-Process -Name 'QtWebEngineProcess' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
    $orphans = @($after | Where-Object { $_ -notin $before })
    if ($orphans.Count -gt 0) { throw "CC003_SMOKE=FAIL orphan QtWebEngineProcess PIDs: $orphans" }
    if ($ExpectSuccess -and $exit -ne 0) { throw "CC003_SMOKE=FAIL $Label process exit=$exit" }
    if (-not $ExpectSuccess -and $exit -eq 0) { throw "CC003_NEGATIVE=FAIL $Label unexpectedly succeeded" }
    if ($ExpectSuccess) {
        $all = (Get-Content -LiteralPath $err -Raw) + (Get-Content -LiteralPath $output -Raw)
        if (-not $all.Contains('CC003_PACKAGED_SMOKE=PASS')) {
            throw "CC003_SMOKE=FAIL $Label missing real UI/IPC pass marker"
        }
    }
    Write-Host "CC003_SMOKE=PASS $Label exit=$exit expected_success=$ExpectSuccess"
}

Invoke-Check -Directory $root -Label 'normal-01' -ExpectSuccess $true
Invoke-Check -Directory $root -Label 'normal-restart' -ExpectSuccess $true
if ($NegativeTests) {
    # Each destructive probe runs on a throwaway clone; never mutate the original.
    $probe = Join-Path ([IO.Path]::GetTempPath()) ('CC003 thử đường dẫn Unicode có dấu ' + [guid]::NewGuid().ToString('N'))
    try {
        Copy-Item -LiteralPath $root -Destination $probe -Recurse -Force
        Invoke-Check -Directory $probe -Label 'unicode-relocated' -ExpectSuccess $true
        Remove-Item -LiteralPath (Join-Path $probe 'frontend\dist\index.html') -Force
        Invoke-Check -Directory $probe -Label 'missing-frontend' -ExpectSuccess $false
    } finally { if (Test-Path $probe) { Remove-Item -LiteralPath $probe -Recurse -Force } }
    $probe2 = Join-Path ([IO.Path]::GetTempPath()) ('CC003 missing helper ' + [guid]::NewGuid().ToString('N'))
    try {
        Copy-Item -LiteralPath $root -Destination $probe2 -Recurse -Force
        $helpers = @(Get-ChildItem -LiteralPath $probe2 -Recurse -File -Filter 'QtWebEngineProcess.exe')
        if ($helpers.Count -eq 0) { throw 'Expected helper for destructive negative test' }
        $helpers | Remove-Item -Force
        Invoke-Check -Directory $probe2 -Label 'missing-helper' -ExpectSuccess $false
    } finally { if (Test-Path $probe2) { Remove-Item -LiteralPath $probe2 -Recurse -Force } }
}
Write-Host "CC003_ALL_PACKAGED_SMOKE=PASS"
