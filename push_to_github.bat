@echo off
title Upload to GitHub - Key Dynamics Recruitment Tracker
color 0A
echo ======================================================================
echo    KEY DYNAMICS SOLUTIONS - UPLOAD PROJECT TO GITHUB (WITH DATABASE)
echo ======================================================================
echo.
echo Target Repository:
echo https://github.com/nauratan91-collab/recruitment-tracker.git
echo.
echo Database Files Included:
echo  - recruitment_tracker.db (SQLite database with all records)
echo  - recruitment_tracker_dump.sql (Portable SQL Dump)
echo.
echo [1/2] Connecting to GitHub and preparing branch 'main'...
set "PATH=%LOCALAPPDATA%\Programs\Git\cmd;%LOCALAPPDATA%\Programs\Git\mingw64\bin;%PATH%"

cd /d "C:\Users\ITkey\.gemini\antigravity\scratch\job-requirement-tracker"

git remote remove origin >nul 2>&1
git remote add origin https://github.com/nauratan91-collab/recruitment-tracker.git
git branch -M main

echo.
echo [2/2] Pushing code and database to GitHub...
echo (If a GitHub sign-in window opens, click 'Sign in with your browser')
echo.
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo [SUCCESS] Your project and database have been uploaded to GitHub!
    echo View online: https://github.com/nauratan91-collab/recruitment-tracker
    echo ======================================================================
) else (
    echo.
    echo ======================================================================
    echo [AUTHENTICATION HELP]
    echo If GitHub asks for login:
    echo 1. Click 'Sign in with your browser' to authenticate automatically.
    echo 2. Or use a GitHub Personal Access Token (classic) with 'repo' scope from:
    echo    https://github.com/settings/tokens
    echo ======================================================================
)

echo.
pause
