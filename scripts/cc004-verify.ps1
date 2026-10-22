[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Root,
    [string]$Manifest='',
    [switch]$Cleanup,
    [string]$PythonCommand='python'
)
$ErrorActionPreference='Stop'
$repo=Split-Path $PSScriptRoot -Parent
$cliArgs=@((Join-Path $repo 'benchmarks\verify_fixture.py'),'--root',$Root)
if($Manifest){$cliArgs+=@('--manifest',$Manifest)}
if($Cleanup){$cliArgs+='--cleanup'}
& $PythonCommand @cliArgs
if($LASTEXITCODE -ne 0){throw "CC004 verification/cleanup failed with exit $LASTEXITCODE"}
