@echo off
setlocal
cd /d "%~dp0"
echo ==========================================
echo  Say Less - Automated Video Generator
echo ==========================================

echo.
echo [1/3] Preparing caller speech turns...
python prepare_audio.py
if errorlevel 1 exit /b 1

echo.
echo [2/3] Recording live web demo with Playwright...
python record.py
if errorlevel 1 exit /b 1

echo.
echo [3/3] Composing final video with voiceover and subtitles...
python compose.py
if errorlevel 1 exit /b 1

echo.
echo Demo video created successfully at: %~dp0say-less-demo.mp4
pause
