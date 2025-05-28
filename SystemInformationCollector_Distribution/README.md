# System Information Collector for Windows

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
- **Application**: `C:\Program Files\SystemInformationCollector\`
- **Logs**: Created in application directory under `logs\`
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
