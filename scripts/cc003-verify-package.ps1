# CC-003 standalone structural verification (PowerShell 7 or Windows PowerShell).
# This intentionally cannot prove the Qt WebEngine actually runs.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$PackageDir,
    [switch]$WriteManifest
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath $PackageDir).Path
$exe = Join-Path $root 'CodeCitySpike.exe'
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) { throw "Missing bundled CodeCitySpike.exe in $root" }
$assets = Join-Path $root 'frontend\dist'
$html = Join-Path $assets 'index.html'
if (-not (Test-Path -LiteralPath $html -PathType Leaf)) { throw "Missing bundled frontend/index.html" }
$static = @(Get-ChildItem -LiteralPath (Join-Path $assets 'assets') -File -ErrorAction Stop)
if (@($static | Where-Object { $_.Extension -eq '.js' }).Count -eq 0) { throw 'Missing Vite static JavaScript' }
if (@($static | Where-Object { $_.Extension -eq '.css' }).Count -eq 0) { throw 'Missing Vite static CSS' }
$all = @(Get-ChildItem -LiteralPath $root -File -Recurse -ErrorAction Stop)
$webproc = @($all | Where-Object { $_.Name -eq 'QtWebEngineProcess.exe' })
$platform = @($all | Where-Object { $_.Name -eq 'qwindows.dll' })
$core = @($all | Where-Object { $_.Name -match '^Qt6WebEngineCore\.dll$' })
$pak = @($all | Where-Object { $_.Name -eq 'qtwebengine_resources.pak' })
$icu = @($all | Where-Object { $_.Name -eq 'icudtl.dat' })
$locales = @($all | Where-Object { $_.DirectoryName -match 'qtwebengine_locales' -and $_.Extension -eq '.pak' })
foreach ($check in @(
    @{ Name='QtWebEngineProcess.exe'; Found=$webproc.Count },
    @{ Name='qwindows.dll'; Found=$platform.Count },
    @{ Name='Qt6WebEngineCore.dll'; Found=$core.Count },
    @{ Name='qtwebengine_resources.pak'; Found=$pak.Count },
    @{ Name='icudtl.dat'; Found=$icu.Count },
    @{ Name='Qt WebEngine locales/*.pak'; Found=$locales.Count }
)) {
    if (-not $check.Found) { throw "Missing required Qt resource: $($check.Name)" }
}
if (@($all | Where-Object { $_.FullName -match 'node_modules' }).Count -gt 0) {
    throw 'Consumer artifact unexpectedly contains node_modules'
}
if (@($all | Where-Object { $_.Name -eq 'python.exe' -or $_.Name -eq 'node.exe' }).Count -gt 0) {
    throw 'Consumer artifact unexpectedly contains developer interpreter/node executable'
}
$keys = @($all | Where-Object {
    $_.Name -in @('CodeCitySpike.exe','QtWebEngineProcess.exe','qwindows.dll',
                 'Qt6WebEngineCore.dll','qtwebengine_resources.pak','icudtl.dat','index.html') -or
    ($_.FullName -like "$assets*")
} | Sort-Object FullName -Unique)
$manifest = [ordered]@{
    task = 'CC-003'
    format = 'Nuitka Windows standalone one-folder'
    verifiedAtUtc = [DateTime]::UtcNow.ToString('o')
    exeRelative = 'CodeCitySpike.exe'
    fileCount = $all.Count
    importantFiles = @($keys | ForEach-Object {
        [ordered]@{
            relativePath = $_.FullName.Substring($root.Length).TrimStart('\','/').Replace('\','/')
            bytes = $_.Length
            sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    })
}
if ($WriteManifest) {
    $path = Join-Path $root 'cc003-manifest.json'
    $manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $path -Encoding UTF8
}
else {
    $manifestPath = Join-Path $root 'cc003-manifest.json'
    if (Test-Path -LiteralPath $manifestPath) {
        $saved = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
        foreach ($entry in $saved.importantFiles) {
            $file = Join-Path $root ($entry.relativePath.Replace('/','\'))
            if (-not (Test-Path -LiteralPath $file)) { throw "Manifest entry missing: $($entry.relativePath)" }
            $actual = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($actual -ne $entry.sha256) { throw "Manifest hash mismatch: $($entry.relativePath)" }
        }
    }
}
Write-Host "CC003_STRUCTURE=PASS files=$($all.Count) helpers=$($webproc.Count) core=$($core.Count) locales=$($locales.Count)"
$manifest.importantFiles | ForEach-Object { Write-Host "  $($_.relativePath) $($_.bytes) bytes" }
