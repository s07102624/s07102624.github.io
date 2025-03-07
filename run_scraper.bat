@echo off
chcp 65001>nul
cd /d "%~dp0"

:menu
cls
echo 스크래퍼 실행 모드를 선택하세요:
echo 1. 자동 실행 (스케줄러)
echo 2. 수동 실행 (1회)
echo 3. 종료
choice /c 123 /n /m "선택하세요 (1-3): "

if errorlevel 3 goto :eof
if errorlevel 2 goto manual
if errorlevel 1 goto auto

:manual
echo [%date% %time%] 수동 스크래퍼 시작 >> scraper.log
"C:\Python312\python.exe" scraping_example.py manual >> scraper.log 2>&1
echo [%date% %time%] 수동 스크래퍼 종료 >> scraper.log
pause
goto menu

:auto
echo [%date% %time%] 자동 스크래퍼 시작 >> scraper.log
"C:\Python312\python.exe" scraping_example.py >> scraper.log 2>&1
echo [%date% %time%] 자동 스크래퍼 종료 >> scraper.log
