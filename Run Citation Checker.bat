@echo off
title Citation Checker
echo.
echo ================================================
echo            CITATION CHECKER
echo ================================================
echo.
echo Drag and drop your document onto this window,
echo OR type/paste the full path to your document below.
echo.
echo Supported file types: .pdf  .docx  .md
echo.
set /p DOCPATH="Drop file here or type path: "

REM Remove quotes if user dragged and dropped (Windows adds them)
set DOCPATH=%DOCPATH:"=%

echo.
echo Checking citations in: %DOCPATH%
echo This may take 1-2 minutes depending on how many citations...
echo.

py "C:\Users\Paul\Desktop\Claude Projects\Citation-Checker\main.py" "%DOCPATH%"

echo.
echo ================================================
echo Done! Check the folder where your document lives
echo for two new files:
echo   - [filename]_citations.html   (open in Firefox)
echo   - [filename]_with_urls.docx   (open in Word)
echo ================================================
echo.
pause
