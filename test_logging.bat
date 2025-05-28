@echo off
echo Testing System Information Collector with Enhanced Logging
echo =======================================================

echo.
echo Testing CLI with verbose logging...
python cli_app.py --json --csv --verbose

echo.
echo.
echo Testing GUI application (will open in new window)...
python gui_app.py

echo.
echo Logging test completed. Check the 'logs' directory for log files.
pause 