@echo off
if "%1"=="" goto have_0
if "%2"=="" goto have_1
goto end
:have_0
echo ERROR: Missing image file name for driver creation.
goto end
:have_1
python c4driver.py %1
:end
