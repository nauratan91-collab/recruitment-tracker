@echo off
title Key Dynamics Solutions - Push to GitHub
color 0A
echo ======================================================================
echo    KEY DYNAMICS SOLUTIONS - UPLOAD PROJECT TO GITHUB (WITH DATABASE)
echo ======================================================================
echo.
echo [1/3] Checking Git environment...
set "PATH=%LOCALAPPDATA%\Programs\Git\cmd;%PATH%"

cd /d "C:\Users\ITkey\.gemini\antigravity\scratch\job-requirement-tracker"

echo [2/3] Verifying database and local repository...
git status
echo.

echo ======================================================================
echo Enter your GitHub Repository URL below:
echo (Example: https://github.com/YourUsername/recruitment-tracker.git)
echo ======================================================================
set /p REPO_URL="GitHub Repository URL: "

if "%REPO_URL%"=="" (
    echo [ERROR] No URL entered. Aborted.
    pause
    exit /b
)

echo.
echo [3/3] Linking to %REPO_URL% and pushing branch 'main'...
git remote remove origin >nul 2>&1
git remote add origin %REPO_URL%
git branch -M main
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo [SUCCESS] Your project with full database was uploaded to GitHub!
    echo ======================================================================
) else (
    echo.
    echo ======================================================================
    echo If GitHub asks for password, use a GitHub Personal Access Token (PAT)
    echo or sign in through the browser popup.
    echo ======================================================================
)

echo.
pause
