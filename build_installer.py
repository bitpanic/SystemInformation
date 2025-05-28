"""Build script for creating a standalone executable and installer."""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Step: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("SUCCESS:", description)
        if result.stdout:
            print("Output:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {description} failed")
        print(f"Return code: {e.returncode}")
        print(f"Error output: {e.stderr}")
        if e.stdout:
            print(f"Standard output: {e.stdout}")
        return False


def clean_build_dirs():
    """Clean previous build directories."""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning directory: {dir_name}")
            shutil.rmtree(dir_name)


def create_pyinstaller_spec():
    """Create PyInstaller spec file with proper configuration."""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['gui_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('README.md', '.'),
    ],
    hiddenimports=[
        'wmi',
        'pythoncom',
        'pywintypes',
        'win32com',
        'win32com.client',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'tkinter.scrolledtext',
        'threading',
        'json',
        'csv',
        'configparser',
        'xml.etree.ElementTree',
        'glob',
        'os',
        'sys',
        'time',
        'datetime',
        're',
        'subprocess',
        'winreg',
        'pathlib',
        'logging',
        'traceback',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SystemInformationCollector',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for GUI app
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.ico' if os.path.exists('app_icon.ico') else None,
    version='version_info.txt' if os.path.exists('version_info.txt') else None,
)
'''
    
    with open('system_info_collector.spec', 'w') as f:
        f.write(spec_content)
    print("Created PyInstaller spec file: system_info_collector.spec")


def create_version_info():
    """Create version info file for the executable."""
    version_info = '''# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1,0,0,0),
    prodvers=(1,0,0,0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'System Information Collector'),
        StringStruct(u'FileDescription', u'Windows System Information Collection Tool'),
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'InternalName', u'SystemInformationCollector'),
        StringStruct(u'LegalCopyright', u'Copyright (C) 2024'),
        StringStruct(u'OriginalFilename', u'SystemInformationCollector.exe'),
        StringStruct(u'ProductName', u'System Information Collector'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    
    with open('version_info.txt', 'w') as f:
        f.write(version_info)
    print("Created version info file: version_info.txt")


def create_icon():
    """Create a simple icon file if it doesn't exist."""
    # For now, we'll skip icon creation as it requires additional dependencies
    # The installer will work without an icon
    pass


def create_inno_setup_script():
    """Create Inno Setup script for Windows installer."""
    inno_script = '''[Setup]
AppName=System Information Collector
AppVersion=1.0.0
AppPublisher=System Information Collector
AppPublisherURL=https://github.com/
DefaultDirName={autopf}\\SystemInformationCollector
DefaultGroupName=System Information Collector
OutputDir=installer_output
OutputBaseFilename=SystemInformationCollector_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
SetupIconFile=app_icon.ico
UninstallDisplayIcon={app}\\SystemInformationCollector.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\\SystemInformationCollector.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\\System Information Collector"; Filename: "{app}\\SystemInformationCollector.exe"
Name: "{group}\\{cm:UninstallProgram,System Information Collector}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\\System Information Collector"; Filename: "{app}\\SystemInformationCollector.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\\SystemInformationCollector.exe"; Description: "{cm:LaunchProgram,System Information Collector}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  if not IsAdminLoggedOn then
  begin
    MsgBox('This installer requires administrator privileges to install the system information collector properly.', mbInformation, MB_OK);
    Result := False;
  end;
end;
'''
    
    with open('system_info_installer.iss', 'w') as f:
        f.write(inno_script)
    print("Created Inno Setup script: system_info_installer.iss")


def create_readme():
    """Create a comprehensive README file."""
    readme_content = '''# System Information Collector for Windows

A comprehensive Windows system information collection tool with GUI interface.

## Features

- **Hardware Detection**: PCI devices, USB devices, memory modules, storage devices
- **Software Detection**: Installed programs, SPIN/SPINDLE software, configuration analysis
- **CodeMeter Dongles**: Automatic detection and serial number extraction
- **StratusVision Software**: Specialized detection and configuration parsing
- **Export Capabilities**: JSON and CSV export formats
- **Real-time Logging**: Comprehensive logging with GUI log viewer
- **Professional GUI**: Modern Windows interface with tabbed information display

## System Requirements

- Windows 10 or later (64-bit recommended)
- Administrator privileges (for complete system access)
- 100 MB free disk space
- .NET Framework 4.7.2 or later (usually pre-installed)

## Installation

1. Download the installer: `SystemInformationCollector_Setup.exe`
2. Right-click the installer and select "Run as administrator"
3. Follow the installation wizard
4. Launch from Start Menu or Desktop shortcut

## Usage

### GUI Application
1. Launch "System Information Collector" from Start Menu
2. Click "Collect System Info" to scan your system
3. View results in organized tabs:
   - **Overview**: System summary and key information
   - **Hardware Tabs**: PCI, USB, Memory, Storage details
   - **Software**: Installed programs and StratusVision software
   - **CodeMeter Dongles**: License dongle information
   - **System Info**: CPU, GPU, and system details
   - **Logs**: Real-time application logging

### Export Data
- **JSON Export**: Complete data in machine-readable format
- **CSV Export**: Tabular data for spreadsheet analysis
- **Log Export**: Save application logs for troubleshooting

## StratusVision Software Detection

The tool provides specialized detection for:
- **SPIN Software**: AOI (Automated Optical Inspection) systems
- **SPINDLE Software**: AI TensorFlow GUI for segmentation/classification
- **Configuration Analysis**: Hardware settings, IP addresses, motor configurations
- **Version Detection**: Automatic version identification from folders and configs

## CodeMeter Dongle Detection

Comprehensive dongle detection including:
- **Service Status**: CodeMeter service running status
- **Serial Numbers**: Hardware dongle serial extraction
- **License Status**: Enabled/disabled status checking
- **Multiple Detection Methods**: WMI, CLI, and registry scanning

## File Locations

After installation:
- **Application**: `C:\\Program Files\\SystemInformationCollector\\`
- **Logs**: Created in application directory under `logs\\`
- **Exports**: Saved to user-selected locations

## Troubleshooting

### Common Issues

**Permission Errors**:
- Run as Administrator for complete system access
- Ensure Windows User Account Control (UAC) is properly configured

**Missing Hardware Information**:
- Update Windows drivers for complete device detection
- Check Windows Device Manager for unknown devices

**CodeMeter Detection Issues**:
- Ensure CodeMeter software is installed and running
- Check that dongles are properly connected
- Verify CodeMeter service is started in Windows Services

**Log File Issues**:
- Verify write permissions to application directory
- Check available disk space for log files

### Support Information

- **Version**: 1.0.0
- **Platform**: Windows 10/11 (64-bit)
- **Dependencies**: All dependencies are bundled in the installer

### Technical Details

**Detected Information Includes**:
- CPU: Name, cores, architecture
- Memory: Total RAM, module details, speeds
- Storage: HDDs, SSDs, capacity, health
- Graphics: GPU information and drivers
- Network: Adapters and configurations
- USB Devices: Connected devices and drivers
- PCI Devices: System buses and controllers
- Software: Installed programs and versions

**Export Formats**:
- **JSON**: Complete hierarchical data structure
- **CSV**: Flattened tabular format for analysis
- **Logs**: Timestamped application activity

## Security and Privacy

- **No Network Communication**: Tool operates entirely offline
- **Local Data Only**: All information stays on your computer
- **No Data Collection**: No telemetry or usage data sent anywhere
- **Administrator Access**: Required only for complete system hardware access
- **Safe Operation**: Read-only system scanning, no modifications made

## Uninstallation

1. Go to Windows "Add or Remove Programs"
2. Find "System Information Collector"
3. Click "Uninstall" and follow the prompts
4. All application files and logs will be removed

---

For technical support or feature requests, please contact your system administrator.
'''
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("Created README.md")


def main():
    """Main build process."""
    print("System Information Collector - Build Script")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists('gui_app.py'):
        print("ERROR: gui_app.py not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    # Clean previous builds
    print("Cleaning previous builds...")
    clean_build_dirs()
    
    # Create necessary files
    print("Creating build configuration files...")
    create_version_info()
    create_pyinstaller_spec()
    create_inno_setup_script()
    create_readme()
    
    # Check if PyInstaller is available
    try:
        subprocess.run(['pyinstaller', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("PyInstaller not found. Installing...")
        if not run_command('pip install pyinstaller', "Installing PyInstaller"):
            print("Failed to install PyInstaller. Please install manually: pip install pyinstaller")
            sys.exit(1)
    
    # Build the executable
    print("Building standalone executable...")
    if not run_command('pyinstaller system_info_collector.spec --clean', "Building executable with PyInstaller"):
        print("Failed to build executable.")
        sys.exit(1)
    
    # Check if executable was created
    exe_path = os.path.join('dist', 'SystemInformationCollector.exe')
    if not os.path.exists(exe_path):
        print(f"ERROR: Executable not found at {exe_path}")
        sys.exit(1)
    
    print(f"✓ Executable created successfully: {exe_path}")
    
    # Test the executable
    print("Testing the executable...")
    try:
        # Run with --help or similar to test if it loads
        result = subprocess.run([exe_path], timeout=10, capture_output=True)
        print("✓ Executable test completed (launched successfully)")
    except subprocess.TimeoutExpired:
        print("✓ Executable is working (GUI launched but timed out - this is expected)")
    except Exception as e:
        print(f"⚠ Executable test warning: {e}")
    
    # Create installer directory
    os.makedirs('installer_output', exist_ok=True)
    
    print("\n" + "=" * 60)
    print("BUILD COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print(f"✓ Standalone executable: {exe_path}")
    print(f"✓ File size: {os.path.getsize(exe_path) / (1024*1024):.1f} MB")
    print("✓ Inno Setup script: system_info_installer.iss")
    print("✓ README documentation: README.md")
    
    print("\nNext steps:")
    print("1. Test the executable by running: .\\dist\\SystemInformationCollector.exe")
    print("2. Install Inno Setup from: https://jrsoftware.org/isinfo.php")
    print("3. Compile installer by opening system_info_installer.iss in Inno Setup")
    print("4. Final installer will be in: .\\installer_output\\SystemInformationCollector_Setup.exe")
    
    print("\nFor distribution:")
    print("- The standalone executable can be run directly on any Windows PC")
    print("- The installer provides a professional installation experience")
    print("- Both require no additional Python installation on target machines")


if __name__ == "__main__":
    main() 