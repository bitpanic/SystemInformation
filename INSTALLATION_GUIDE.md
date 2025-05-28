# Installation Guide - System Information Collector

## 🎯 Quick Start (Standalone Executable)

The fastest way to run the System Information Collector on any Windows PC:

### Option 1: Direct Executable (No Installation Required)
1. **Download/Copy** the file: `dist\SystemInformationCollector.exe` (12MB)
2. **Copy** to target Windows PC
3. **Right-click** → "Run as administrator" (recommended for full hardware access)
4. **Done!** The GUI will launch immediately

✅ **Advantages:**
- No installation required
- Works on any Windows 10/11 PC
- No Python required on target machine
- All dependencies bundled
- Portable - runs from any folder

## 🔧 Option 2: Professional Installer (Recommended for Distribution)

### Step 1: Create Windows Installer

1. **Download Inno Setup** (free): https://jrsoftware.org/isinfo.php
2. **Install Inno Setup** on your development machine
3. **Open** the file: `system_info_installer.iss` in Inno Setup
4. **Click "Build"** → Creates: `installer_output\SystemInformationCollector_Setup.exe`

### Step 2: Deploy Installer

1. **Distribute** the installer: `SystemInformationCollector_Setup.exe`
2. **Users run installer** as Administrator
3. **Installed to**: `C:\Program Files\SystemInformationCollector\`
4. **Available in**: Start Menu + Desktop shortcut (optional)

✅ **Advantages:**
- Professional installation experience
- Start Menu integration
- Proper uninstall support
- Desktop shortcuts
- Administrator privilege handling

## 📋 System Requirements

### Target Systems
- **OS**: Windows 10 or later (64-bit recommended)
- **RAM**: 100MB+ available
- **Disk**: 50MB free space
- **Privileges**: Administrator recommended (for complete hardware access)
- **Dependencies**: None (all bundled)

### What Works Without Admin Rights
- ✅ Basic system info (CPU, memory, OS)
- ✅ Installed software detection
- ✅ StratusVision software analysis
- ✅ CodeMeter detection (if service is running)
- ❌ Some low-level hardware details may be limited

## 🚀 Building from Source

If you need to rebuild or modify the application:

### Prerequisites
```bash
# Python 3.8+ required
pip install -r requirements.txt
```

### Build Commands
```bash
# Option 1: Automated build
build.bat

# Option 2: Manual build
python build_installer.py

# Option 3: Direct PyInstaller
pyinstaller system_info_collector.spec --clean
```

### Build Output
- **Executable**: `dist\SystemInformationCollector.exe`
- **Installer Script**: `system_info_installer.iss`
- **Documentation**: `README.md`

## 📁 File Structure (After Installation)

```
C:\Program Files\SystemInformationCollector\
├── SystemInformationCollector.exe    # Main application
├── README.md                          # Documentation
├── requirements.txt                   # Dependency list
└── logs\                             # Created at runtime
    ├── system_info_app.log           # Application logs
    ├── system_info_errors.log        # Error logs
    └── collections.log               # Collection activity
```

## 🔍 Testing the Installation

### Basic Functionality Test
1. **Launch** application
2. **Click** "Collect System Info"
3. **Verify** tabs populate with data:
   - Overview (system summary)
   - Hardware tabs (PCI, USB, Memory, Storage)
   - Software (installed programs + StratusVision)
   - **CodeMeter Dongles** (separate tab)
   - System Info (CPU/GPU details)
   - Logs (real-time logging)

### Export Test
1. **Export JSON** → Verify file creates successfully
2. **Export CSV** → Open in Excel/spreadsheet program
3. **Check logs** → Verify logging is working

### StratusVision Test (If Applicable)
1. **Check Software tab** → Look for StratusVision installations
2. **Check CodeMeter Dongles tab** → Verify dongle detection
3. **Check Overview** → Summary should show dongle count

## 🛠️ Troubleshooting

### Common Issues

**"Windows protected your PC" message:**
- Right-click executable → Properties → Check "Unblock"
- Or run installer as Administrator

**Missing hardware information:**
- Run as Administrator for complete access
- Update Windows drivers for unknown devices

**CodeMeter dongles not detected:**
- Ensure CodeMeter software is installed
- Check Windows Services → CodeMeter should be running
- Verify dongles are connected

**Application won't start:**
- Check Windows Event Viewer for errors
- Verify Windows 10/11 compatibility
- Try running in compatibility mode for Windows 10

**Log files not created:**
- Check folder permissions
- Run as Administrator
- Verify adequate disk space

### Support Information

**Version**: 1.0.0  
**Architecture**: Windows x64  
**Dependencies**: All bundled (WMI, pywin32, tkinter)  
**Size**: ~12MB standalone executable  

## 🔒 Security Considerations

### For End Users
- **Safe Operation**: Read-only scanning, no system modifications
- **Local Only**: No network communication
- **Privacy**: All data stays on local machine
- **Administrator Access**: Only for complete hardware enumeration

### For IT Administrators
- **Code Signing**: Consider signing the executable for enterprise deployment
- **Group Policy**: Can be deployed via GPO
- **Antivirus**: May need whitelisting (common with PyInstaller apps)
- **Network Deployment**: Executable can be run from network shares

## 📦 Distribution Options

### Option 1: Single Executable
**Best for**: Quick deployment, testing, portable use
```
Just copy: SystemInformationCollector.exe
Size: 12MB
```

### Option 2: Installer Package
**Best for**: Professional deployment, end-user installation
```
Distribute: SystemInformationCollector_Setup.exe
Size: ~8MB (compressed)
```

### Option 3: MSI Package (Advanced)
For enterprise environments, the Inno Setup script can be modified to create MSI packages using tools like WiX Toolset.

## 🔄 Updates

### Updating the Application
1. **Replace** the executable with new version
2. **Or** run new installer (will upgrade existing installation)
3. **Settings preserved**: Logs and user preferences maintained

### Verifying Version
- Check Properties of `SystemInformationCollector.exe`
- Or check About dialog in application (if implemented)

---

## Quick Commands Summary

```bash
# Build executable
python build_installer.py

# Test executable  
.\dist\SystemInformationCollector.exe

# Create installer (after installing Inno Setup)
# Open system_info_installer.iss in Inno Setup and click Build
```

🎉 **You now have a professional Windows installer for your System Information Collector!** 