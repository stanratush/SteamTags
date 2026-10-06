@echo off
rem Start the Tag Network app from this App Bundle (Windows). Tries "py -3", then "python".
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 start_tag_network.py %*
) else (
  python start_tag_network.py %*
)
if errorlevel 1 (
  echo.
  pause
)
