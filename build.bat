@echo off
echo System Information Collector - Build Script
echo ==========================================

echo Installing dependencies...
pip install -r requirements.txt

echo Building executable...
python build_installer.py

echo.
echo Build process completed!
echo Check the dist\ folder for the executable.
echo Check installer_output\ folder for the installer (after Inno Setup compilation).

pause 