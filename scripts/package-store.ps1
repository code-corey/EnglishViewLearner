# Package extension for Chrome Web Store upload.
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$extDir = Join-Path $root 'extension'
$distDir = Join-Path $root 'dist'
$version = python -c "import json; print(json.load(open(r'$extDir\manifest.json',encoding='utf-8'))['version'])"
$zipName = "immersive-english-v$version.zip"
$zipPath = Join-Path $distDir $zipName

if (-not (Test-Path (Join-Path $extDir 'icons\icon128.png'))) {
    Write-Host 'Generating icons...'
    python (Join-Path $extDir 'scripts\generate_icons.py')
}

New-Item -ItemType Directory -Force -Path $distDir | Out-Null
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }

$exclude = @(
    'scripts\cedict_ts.u8',
    'scripts\oxford_5000.csv',
    'scripts\oxford_5000_levels.csv',
    'scripts\merge_dict.py',
    'scripts\download_cedict.py',
    'scripts\download_oxford.py',
    'scripts\generate_icons.py',
    'store',
    'test.html'
)

$temp = Join-Path $env:TEMP "evl-store-$(Get-Random)"
New-Item -ItemType Directory -Force -Path $temp | Out-Null

Get-ChildItem $extDir -Force | ForEach-Object {
    $rel = $_.Name
    $skip = $false
    foreach ($pattern in $exclude) {
        if ($rel -eq ($pattern -replace '\\', '/').Split('/')[-1] -and $_.PSIsContainer -eq $false) { $skip = $true; break }
    }
    if ($rel -eq 'scripts' -or $rel -eq 'store') { return }
    if ($skip) { return }
    Copy-Item $_.FullName -Destination (Join-Path $temp $rel) -Recurse -Force
}

Compress-Archive -Path (Join-Path $temp '*') -DestinationPath $zipPath -Force
Remove-Item $temp -Recurse -Force

Write-Host "Created $zipPath"
Get-Item $zipPath | Select-Object FullName, @{N='SizeMB';E={[math]::Round($_.Length/1MB,2)}}
