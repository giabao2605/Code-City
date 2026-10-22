# CC-004 read-only Windows environment inventory; no serials, usernames or hostnames.
[CmdletBinding()]
param([string]$FixtureRoot = $env:TEMP,
      [string]$OutputDir = (Join-Path $PSScriptRoot 'results'))
$ErrorActionPreference = 'Stop'
function Probe([scriptblock]$Action, [object]$Fallback='UNVERIFIED') {
    try { $v = & $Action; if ($null -eq $v) { return $Fallback }; return $v }
    catch { return $Fallback }
}
$os = Probe { Get-CimInstance Win32_OperatingSystem }
$sys = Probe { Get-CimInstance Win32_ComputerSystem }
$processors = @(Probe { Get-CimInstance Win32_Processor })
$graphics = @(Probe { Get-CimInstance Win32_VideoController })
$drive = [System.IO.Path]::GetPathRoot([System.IO.Path]::GetFullPath($FixtureRoot)).TrimEnd('\')
$logical = Probe { Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='$drive'" }
$bus = Probe { Get-Partition -DriveLetter $drive.TrimEnd(':') | Get-Disk }
$disks = @(Probe { Get-PhysicalDisk })
$media = 'UNKNOWN'
if ($disks.Count -eq 1 -and $disks[0] -isnot [string]) { $media = [string]$disks[0].MediaType }
$screen = Probe {
    Add-Type -AssemblyName System.Windows.Forms
    $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    @{ width=$bounds.Width; height=$bounds.Height; scale='UNVERIFIED' }
}
$power = Probe { (powercfg /getactivescheme | Out-String).Trim() }
$sha = if ($env:GITHUB_SHA) { $env:GITHUB_SHA } else {
    Probe { (git -C (Split-Path $PSScriptRoot -Parent) rev-parse HEAD).Trim() }
}
$cpu = @($processors | ForEach-Object {
    if ($_ -is [string]) { 'UNVERIFIED' } else {
        @{model=$_.Name; logicalProcessors=$_.NumberOfLogicalProcessors;
          physicalCores=$_.NumberOfCores; architecture=$_.Architecture; maxClockMHz=$_.MaxClockSpeed}
    }
})
$gpu = @($graphics | ForEach-Object {
    if ($_ -is [string]) { 'UNVERIFIED' } else {
        @{model=$_.Name; vendor=$_.AdapterCompatibility; driverVersion=$_.DriverVersion;
          physicalAcceleration='UNVERIFIED'}
    }
})
$storage = if ($logical -is [string]) { 'UNVERIFIED' } else {
    @{drive=$drive; filesystem=$logical.FileSystem;
      totalGiB=[math]::Round($logical.Size / 1GB,3);
      freeGiB=[math]::Round($logical.FreeSpace / 1GB,3);
      mediaType=$media; busType=if($bus -is [string]){'UNKNOWN'}else{[string]$bus.BusType};
      physicalBacking='UNVERIFIED'}
}
$report = [ordered]@{
    schemaVersion=1
    capturedUtc=(Get-Date).ToUniversalTime().ToString('o')
    hostKind=if($env:GITHUB_ACTIONS -eq 'true'){'GITHUB_HOSTED_WINDOWS_RUNNER'}else{'PHYSICALITY_UNVERIFIED'}
    githubRunId=if($env:GITHUB_RUN_ID){$env:GITHUB_RUN_ID}else{'NOT_APPLICABLE'}
    runnerImage=if($env:ImageVersion){$env:ImageVersion}else{'UNVERIFIED'}
    windows=if($os -is [string]){'UNVERIFIED'}else{
        @{edition=$os.Caption;version=$os.Version;build=$os.BuildNumber;architecture=$os.OSArchitecture}}
    cpu=$cpu
    gpu=$gpu
    ram=if($sys -is [string]){'UNVERIFIED'}else{
        @{totalGiB=[math]::Round($sys.TotalPhysicalMemory/1GB,3);
          availableGiB=if($os -is [string]){'UNVERIFIED'}else{[math]::Round($os.FreePhysicalMemory*1KB/1GB,3)}}}
    storage=$storage
    display=$screen
    displayMode=if($env:GITHUB_ACTIONS -eq 'true'){'HOSTED_DISPLAY_UNVERIFIED_GPU'}else{'UNVERIFIED'}
    powerScheme=$power
    acBattery='UNVERIFIED'
    toolchain=@{
        python=Probe { (python --version 2>&1 | Out-String).Trim() }
        node=Probe { (node --version 2>&1 | Out-String).Trim() }
        npm=Probe { (npm --version 2>&1 | Out-String).Trim() }
        generatorVersion='1'; gitCommit=$sha; qt='NOT_PROBED'; threejs='NOT_PROBED'
    }
    acceptance=@{webgl100Boxes='NOT_RUN';a16='NOT_RUN';a17='NOT_RUN';physicalGpu='UNVERIFIED'}
}
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$id=if($env:GITHUB_RUN_ID){$env:GITHUB_RUN_ID}else{(Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')}
$target=Join-Path $OutputDir "environment-$id.json"
$report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $target -Encoding UTF8
Write-Host "CC004_ENVIRONMENT_JSON=$target"
Write-Host "GPU/SSD/physical-workstation claims must be explicitly verified, not inferred from hosted runner."
