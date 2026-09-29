@echo off
title Key Dynamics Solutions - Live Cloud Tunnel
color 0A
echo ======================================================================
echo    KEY DYNAMICS SOLUTIONS - LIVE SERVER & TUNNEL LAUNCHER
echo ======================================================================
echo.
set "PATH=%LOCALAPPDATA%\Programs\Git\cmd;%PATH%"
cd /d "C:\Users\ITkey\.gemini\antigravity\scratch\job-requirement-tracker"

echo [1/2] Checking Flask server...
curl -s http://127.0.0.1:5000/api/dashboard/stats >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Starting Python Flask App...
    start /b python app.py
    timeout /t 3 /nobreak >nul
)

echo.
echo [2/2] Connecting Live Public Cloudflare Tunnel...
echo The link ending in .trycloudflare.com will be shown below:
echo (Share that link with your friend to test live updates!)
echo.
cloudflared.exe tunnel --url http://127.0.0.1:5000
pause
