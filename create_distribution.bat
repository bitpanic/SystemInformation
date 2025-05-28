@echo off
echo Creating distribution package...
echo ================================

REM Create distribution folder
if exist "SystemInformationCollector_Distribution" rmdir /s /q "SystemInformationCollector_Distribution"
mkdir "SystemInformationCollector_Distribution"

REM Copy the standalone executable
echo Copying standalone executable...
copy "dist\SystemInformationCollector.exe" "SystemInformationCollector_Distribution\"

REM Copy documentation
echo Copying documentation...
copy "README.md" "SystemInformationCollector_Distribution\"
copy "INSTALLATION_GUIDE.md" "SystemInformationCollector_Distribution\"

REM Copy installer script (for advanced users)
echo Copying installer files...
copy "system_info_installer.iss" "SystemInformationCollector_Distribution\"

REM Create a simple instruction file
echo Creating quick start instructions...
echo # Quick Start Instructions > "SystemInformationCollector_Distribution\QUICK_START.txt"
echo. >> "SystemInformationCollector_Distribution\QUICK_START.txt"
echo 1. Double-click SystemInformationCollector.exe >> "SystemInformationCollector_Distribution\QUICK_START.txt"
echo 2. If Windows warns about security, click "More info" then "Run anyway" >> "SystemInformationCollector_Distribution\QUICK_START.txt"
echo 3. For best results, right-click and "Run as administrator" >> "SystemInformationCollector_Distribution\QUICK_START.txt"
echo 4. Click "Collect System Info" to scan your system >> "SystemInformationCollector_Distribution\QUICK_START.txt"
echo 5. Use Export buttons to save data as JSON or CSV >> "SystemInformationCollector_Distribution\QUICK_START.txt"
echo. >> "SystemInformationCollector_Distribution\QUICK_START.txt"
echo For full documentation, see README.md and INSTALLATION_GUIDE.md >> "SystemInformationCollector_Distribution\QUICK_START.txt"

echo.
echo Distribution package created in: SystemInformationCollector_Distribution\
echo.
echo Contents:
echo - SystemInformationCollector.exe (12MB) - Standalone application
echo - README.md - Full documentation
echo - INSTALLATION_GUIDE.md - Deployment guide  
echo - system_info_installer.iss - Inno Setup script for creating installer
echo - QUICK_START.txt - Simple instructions
echo.
echo Ready for distribution!
pause 