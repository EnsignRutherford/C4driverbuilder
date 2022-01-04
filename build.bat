@echo off
if "%1"=="" goto have_0
if "%2"=="" goto have_1
goto end
:have_0
for /f "delims=" %%i in ('dir /b *.png ^| findstr /v selected') do (
echo Creating driver uibutton_%%~ni.c4z
python c4driver.py %%~ni
)
goto end
:have_1
echo Creating driver uibutton_%1.c4z
python c4driver.py %1
:end
