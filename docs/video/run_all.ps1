# Run Say Less End-to-End Demo Video Generator
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " Say Less - Automated Video Generator" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

# Step 1: Synthesize caller audio turns
Write-Host "`n[1/3] Preparing caller speech turns..." -ForegroundColor Yellow
python prepare_audio.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to prepare caller audio." -ForegroundColor Red
    exit 1
}

# Step 2: Record Playwright screencast on live web app
Write-Host "`n[2/3] Recording live web demo with Playwright..." -ForegroundColor Yellow
python record.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Recording failed." -ForegroundColor Red
    exit 1
}

# Step 3: Compose video with AI voiceover and subtitles
Write-Host "`n[3/3] Composing final video with voiceover & subtitles..." -ForegroundColor Yellow
python compose.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Composition failed." -ForegroundColor Red
    exit 1
}

Write-Host "`nDemo video created successfully at: $scriptDir\say-less-demo.mp4" -ForegroundColor Green
