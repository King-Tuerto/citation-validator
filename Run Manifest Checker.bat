@echo off
title Graphics Manifest Checker
cls

echo.
echo ================================================
echo        GRAPHICS MANIFEST CHECKER
echo ================================================
echo.

:loop

echo Drag and drop your MANIFEST.md file onto this window,
echo OR type/paste the full path to your MANIFEST.md below.
echo.
echo Type EXIT to quit.
echo.
set DOCPATH=
set /p DOCPATH="Drop MANIFEST.md here or type path: "

REM Remove quotes if user dragged and dropped (Windows adds them)
set DOCPATH=%DOCPATH:"=%

REM Allow user to exit
if /i "%DOCPATH%"=="EXIT" goto done

REM Skip if nothing was entered
if "%DOCPATH%"=="" (
    echo Nothing entered. Please try again.
    echo.
    goto loop
)

echo.
echo Checking figures in: %DOCPATH%
echo.

py "C:\Users\Paul\Desktop\Claude Projects\Citation-Checker\manifest_checker.py" "%DOCPATH%"

echo.
echo ================================================
echo Done! Two files have been saved next to
echo your MANIFEST.md file:
echo   - [manifest_name]_figure_citations.html  (open in browser)
echo   - Use "Save as Word" button inside the HTML for a .doc copy
echo ================================================
echo.
echo ------------------------------------------------
echo Check another manifest? Drop it below,
echo or type EXIT to close.
echo ------------------------------------------------
echo.
goto loop

:done
echo.
echo Goodbye!
timeout /t 2 >nul
