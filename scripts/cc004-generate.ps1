[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Output,
    [ValidateSet(500,1000,5000,10000)][int]$Count=500,
    [ValidateSet('mixed','tiny','deep','large')][string]$Profile='mixed',
    [int]$Seed=42,
    [string]$PythonCommand='python',
    [long]$MaxBytes=268435456
)
$ErrorActionPreference='Stop'
$repo=Split-Path $PSScriptRoot -Parent
& $PythonCommand (Join-Path $repo 'benchmarks\generate_fixture.py') --output $Output --count $Count --profile $Profile --seed $Seed --max-bytes $MaxBytes
if($LASTEXITCODE -ne 0){throw "CC004 generation failed with exit $LASTEXITCODE"}
