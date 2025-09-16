@echo off
setlocal enableextensions
echo Cleaning build artifacts, caches, logs, and generated reports...

rem Remove top-level artifact directories if they exist
for %%D in (
  build
  dist
  installer_output
  SystemInformationCollector_Distribution
  .pytest_cache
  htmlcov
) do (
  if exist "%%D" (
    echo Removing directory: %%D
    rd /s /q "%%D"
  )
)

rem Remove nested __pycache__ folders
for /d /r %%i in (__pycache__) do (
  if exist "%%i" rd /s /q "%%i"
)

rem Remove compiled python files
for /r %%i in (*.pyc) do del /q "%%i" 2>nul
for /r %%i in (*.pyo) do del /q "%%i" 2>nul

rem Clean logs but keep the folder (and .gitkeep if present)
if exist "logs" (
  del /q "logs\*.log" 2>nul
  del /q "logs\*.log.*" 2>nul
)

rem Remove generated reports (keep committed fixtures like test_*.json)
del /q "system_info_*.json" 2>nul
  del /q "system_info_*.csv" 2>nul
  del /q "final_enhanced_report.json" 2>nul
  del /q "test_output.json" 2>nul

  echo Done.
  endlocal
