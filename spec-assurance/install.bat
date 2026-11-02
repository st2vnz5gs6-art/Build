@echo off
rem SPT Spec Assurance - offline install. Uses only the files in .\wheelhouse (no internet needed).
setlocal
cd /d "%~dp0"

set "PY="
for %%v in (3.14 3.13 3.12) do (
    if not defined PY (
        py -%%v -c "" >nul 2>nul && set "PY=py -%%v"
    )
)
if not defined PY (
    python -c "import sys; sys.exit(0 if (3,12) <= sys.version_info[:2] <= (3,14) else 1)" >nul 2>nul && set "PY=python"
)
if not defined PY (
    echo.
    echo Python 3.12, 3.13 or 3.14 ^(64-bit^) was not found.
    echo Install it from Company Portal / Software Center or python.org, then run this again.
    pause
    exit /b 1
)
echo Using: %PY%
%PY% --version

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    %PY% -m venv .venv || goto :fail
)

echo Installing packages from wheelhouse (offline)...
".venv\Scripts\python.exe" -m pip install --no-index --find-links wheelhouse -r requirements.txt || goto :fail

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo Created .env - add your ANTHROPIC_API_KEY to it.
)

echo.
echo Installed. Next:
echo   1. Put the specification PDFs in the library folder.
echo   2. Add your API key to .env  ^(optional - without it the tool runs in offline mode^).
echo   3. Double-click run.bat
pause
exit /b 0

:fail
echo.
echo Installation failed - see the messages above.
pause
exit /b 1
