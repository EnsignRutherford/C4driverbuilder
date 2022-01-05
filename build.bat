@echo off
rem Check for required packages and install if necessary
python3 -m pip list > build.tmp
findstr Pillow build.tmp 1>nul
if errorlevel 1 (
  echo. Installing Pillow Image Library
  python3 -m pip install Pillow
)
findstr wget build.tmp 1>nul
if errorlevel 1 (
  echo. Installing wget Library
  python3 -m pip install wget
)
findstr lxml build.tmp 1>nul
if errorlevel 1 (
  echo. Installing lxml Library
  python3 -m pip install lxml
)
del build.tmp
if "%1"=="" goto have_0
if "%2"=="" goto have_1
goto end
:have_0
for /f "delims=" %%i in ('dir /b *.png ^| findstr /v selected') do (
  python c4driver.py %%~ni
)
goto end
:have_1
python c4driver.py %1
:end
