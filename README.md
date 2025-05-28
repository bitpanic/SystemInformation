# System Information Collector

A comprehensive Python application that collects detailed hardware and software information about Windows PCs with both GUI and command-line interfaces. Features comprehensive logging, performance tracking, and error monitoring.

## Features

### Hardware Information Collection
- **PCI Cards**: Device name, manufacturer, serial number, device ID, vendor ID
- **USB Devices**: Device name, serial number, vendor/product ID, USB class/type
- **Memory**: Total RAM, number of modules, per-module details (capacity, speed, manufacturer)
- **Storage**: Disk model, serial number, size, interface type (SATA/NVMe), partition layout
- **CPU**: Model, manufacturer, cores, speed, architecture details
- **GPU**: Model(s), memory, driver information
- **Motherboard**: Manufacturer, model, serial number, BIOS information

### Operating System Information
- Windows version and build number
- System architecture (x86/x64)
- Hostname and username
- System environment details

### Software Detection
- **SPIN Software Check**: Specifically searches for SPIN software installation
- **Version and License Extraction**: Attempts to extract SPIN version and license information from:
  - Windows Registry entries
  - Configuration files (INI, JSON, XML, TXT)
  - Installation directories
- **General Software**: Lists installed programs from Windows registry

### Comprehensive Logging System
- **Multi-Level Logging**: DEBUG, INFO, WARNING, ERROR, CRITICAL levels
- **Multiple Log Files**:
  - `system_info_app.log` - Main application log with all activities
  - `system_info_errors.log` - Error-only log for quick issue identification
  - `collections.log` - Collection-specific activities with daily rotation
- **Performance Tracking**: Automatic timing of all operations
- **Log Rotation**: Automatic file rotation to prevent disk space issues
- **Real-Time Log Viewer**: Built-in GUI log viewer with auto-refresh
- **Export Capabilities**: Save logs for analysis or support

### Export Options
- **JSON Format**: Complete structured data export
- **CSV Format**: Flattened data suitable for spreadsheet analysis
- **Automatic Timestamping**: Files are automatically timestamped unless specified otherwise

### User Interfaces
- **GUI Application**: Modern tkinter-based interface with tabbed view and real-time log monitoring
- **Command-Line Interface**: Full-featured CLI for automation and headless operation
- **Permission Handling**: Graceful handling of permission errors with informative messages

## Installation

### Prerequisites
- Python 3.7 or higher
- Windows operating system
- Administrator rights recommended (for complete hardware access)

### Install Dependencies

```bash
pip install -r requirements.txt
```

The application requires:
- `psutil==5.9.6` - System and process utilities
- `pywin32==306` - Windows API access
- `WMI==1.5.1` - Windows Management Instrumentation

## Usage

### GUI Application

Run the graphical interface:

```bash
python gui_app.py
```

**GUI Features:**
- Click "Collect System Info" to gather all information
- View data in organized tabs (Overview, PCI, USB, Memory, Storage, OS, Software, System, **Logs**)
- **Real-time log monitoring** with separate tabs for Application, Error, and Collection logs
- Export data using "Export as JSON" or "Export as CSV" buttons
- **Logging controls**: Open log directory, clear logs, refresh log view
- Real-time progress indication during collection
- Summary panel showing key statistics
- Error handling with user-friendly messages

### Command-Line Interface

The CLI provides powerful options for automation and scripting with comprehensive logging control:

#### Basic Usage

```bash
# Collect all information and export to JSON
python cli_app.py --json system_info.json

# Collect and export to both JSON and CSV
python cli_app.py --json report.json --csv report.csv

# Auto-generate filenames with timestamp
python cli_app.py --json --csv
```

#### Logging Options

```bash
# Enable verbose logging (DEBUG level)
python cli_app.py --json --verbose

# Set specific log level
python cli_app.py --json --log-level WARNING

# Disable console logging (file logging only)
python cli_app.py --json --no-console-log

# Disable file logging (console only)
python cli_app.py --json --no-file-log

# Minimal logging
python cli_app.py --json --no-console-log --no-file-log
```

#### CLI Arguments

**Export Options:**
- `--json [FILENAME]`: Export to JSON format (optionally specify filename)
- `--csv [FILENAME]`: Export to CSV format (optionally specify filename)

**Logging Options:**
- `--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}`: Set console logging level (default: INFO)
- `--no-console-log`: Disable console logging
- `--no-file-log`: Disable file logging
- `--verbose, -v`: Verbose output (same as --log-level DEBUG)

**Collection Options:**
- `--quick`: Quick collection mode (reduced data collection)

## Logging System

The application features a comprehensive logging system designed for Windows environments:

### Log Files

All logs are stored in the `logs/` directory (created automatically):

1. **system_info_app.log**
   - Main application log with all activities
   - Rotating log files (10MB max, 5 backups)
   - DEBUG level and above

2. **system_info_errors.log**
   - Error-only log for quick issue identification
   - ERROR and CRITICAL levels only
   - Rotating log files (10MB max, 5 backups)

3. **collections.log**
   - Collection-specific activities
   - Daily rotation (kept for 30 days)
   - Filtered for collection-related messages

### Log Levels

- **DEBUG**: Detailed technical information for troubleshooting
- **INFO**: General information about operations
- **WARNING**: Something might be wrong but operation continues
- **ERROR**: Something went wrong but application continues
- **CRITICAL**: Serious error that might stop the application

### Log Format

```
2024-01-15 10:30:45 - ModuleName - INFO - filename.py:123 - function_name() - Message here
```

### Performance Tracking

The logging system automatically tracks:
- Individual collector performance
- Export operation timing
- Overall collection duration
- File sizes and counts

### Log Management

**GUI Application:**
- Real-time log viewer with auto-refresh
- Open log directory in Windows Explorer
- Clear all log files
- Save current log view to file

**CLI Application:**
- Log file location displayed after operations
- Configurable logging levels
- Option to disable specific log types

### Example Log Output

```
2024-01-15 10:30:45 - SystemInfoManager - INFO - Starting comprehensive system information collection
2024-01-15 10:30:45 - PCI - INFO - Starting collection: PCI
2024-01-15 10:30:45 - PCI - DEBUG - Initializing WMI connection
2024-01-15 10:30:46 - PCI - INFO - Performance - PCI collection: 0.85 seconds
2024-01-15 10:30:46 - PCI - INFO - Collection completed successfully: PCI - 24 items collected
2024-01-15 10:30:47 - SystemInfoManager - INFO - Performance - Complete system information collection: 2.34 seconds
```

## Testing the Logging System

### Quick Test

```bash
# Run logging demonstration
python test_logging_demo.py

# Test CLI with full logging
python cli_app.py --json test_output.json --verbose

# Test GUI (includes log viewer)
python gui_app.py
```

### Log File Locations

After running the application, check these locations:
- `logs/system_info_app.log` - Main log
- `logs/system_info_errors.log` - Errors only
- `logs/collections.log` - Collection activities

## Architecture

The application is designed with a modular architecture:

### Core Components

```
├── collectors/              # Information collection modules
│   ├── base_collector.py   # Abstract base class with logging
│   ├── pci_collector.py    # PCI device information
│   ├── usb_collector.py    # USB device information
│   ├── memory_collector.py # Memory/RAM information
│   ├── storage_collector.py# Storage device information
│   ├── os_collector.py     # Operating system information
│   ├── software_collector.py# Software installation check
│   └── system_collector.py # CPU/GPU/Motherboard information
├── log_config.py           # Comprehensive logging configuration
├── system_info_manager.py  # Main coordinator and data manager
├── gui_app.py              # Tkinter GUI application with log viewer
├── cli_app.py              # Command-line interface with logging options
├── test_logging_demo.py    # Logging system demonstration
├── test_logging.bat        # Windows batch file for testing
└── requirements.txt        # Python dependencies
```

### Design Principles

- **Modular Design**: Each collector is independent and focused on specific hardware/software
- **Error Resilience**: Individual collector failures don't prevent other data collection
- **Comprehensive Logging**: All operations are logged with appropriate detail levels
- **Performance Monitoring**: Automatic timing and performance tracking
- **Extensible**: Easy to add new collectors or modify existing ones
- **Cross-Interface**: Same core logic powers both GUI and CLI
- **Permission Aware**: Graceful handling of permission restrictions

## SPIN Software Detection

The application includes comprehensive SPIN software detection:

### Detection Methods

1. **Registry Search**: Searches common Windows registry locations
   - `HKEY_LOCAL_MACHINE\SOFTWARE\SPIN`
   - `HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\SPIN`
   - Uninstall registry entries

2. **File System Search**: Looks in standard installation directories
   - `C:\Program Files\SPIN`
   - `C:\Program Files (x86)\SPIN`
   - User AppData directories

3. **Configuration Files**: Parses various config file formats
   - INI/CFG files
   - JSON configuration files
   - XML files
   - Text files with version/license patterns

4. **Executable Search**: Locates SPIN-related executables

### SPIN Information Extracted

- Installation status (Yes/No)
- Version number
- License number/key
- Installation path
- Registry entries found
- Configuration files discovered

## Output Formats

### JSON Export

Complete structured data with all collected information:

```json
{
  "collection_timestamp": "2024-01-15T10:30:45.123456",
  "collection_status": "completed",
  "pci": {
    "pci_devices": [...],
    "total_count": 15
  },
  "software": {
    "spin_info": {
      "installed": true,
      "version": "2.1.3",
      "license_number": "SPIN-ABC123-XYZ789",
      "install_path": "C:\\Program Files\\SPIN"
    }
  }
}
```

### CSV Export

Flattened data suitable for analysis in Excel or other tools:

```csv
category,device_name,manufacturer,vendor_id,device_id,...
PCI Device,Intel HD Graphics,Intel Corporation,8086,0416,...
USB Device,USB Mass Storage,SanDisk,0781,5567,...
Memory Module,8GB DDR4,Samsung,,,8192,...
```

## Error Handling

The application implements comprehensive error handling:

- **Permission Errors**: Warns when administrator rights are needed
- **WMI Failures**: Graceful fallback when WMI queries fail
- **Registry Access**: Handles restricted registry access
- **File System**: Manages permission-denied errors for file/directory access
- **Individual Collectors**: Failure of one collector doesn't stop others

## Troubleshooting

### Common Issues

1. **Permission Errors**
   - Run as Administrator for complete hardware access
   - Some information may be limited with standard user privileges

2. **WMI Errors**
   - Restart the Windows Management Instrumentation service
   - Check Windows Event Logs for WMI-related errors

3. **Missing Dependencies**
   - Ensure all packages in requirements.txt are installed
   - Use `pip install --upgrade -r requirements.txt`

4. **SPIN Detection Issues**
   - SPIN software may be installed in non-standard locations
   - Check the detailed output for registry entries and config files found
   - Manual verification may be needed for custom installations

### Verbose Logging

Enable verbose logging for troubleshooting:

```bash
python cli_app.py --collect --json-only --verbose
```

Or check the GUI application logs in the console window.

## Development

### Adding New Collectors

1. Create a new collector class inheriting from `BaseCollector`
2. Implement the `collect()` method
3. Add the collector to `SystemInfoManager`
4. Update the GUI tabs if needed

Example:

```python
from collectors.base_collector import BaseCollector

class NetworkCollector(BaseCollector):
    def collect(self):
        # Implement collection logic
        return {"network_info": "data"}
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Enable verbose logging to diagnose issues
3. Create an issue with detailed error information and system details

## Stratus SPIN/SPINDLE Software Detection

The system information collector has been enhanced with specific detection capabilities for Stratus software:

### StratusVision Software Detection
- **Path**: Automatically scans `C:\ProgramData\StratusVision` for installed software
- **Software Types**: Detects both SPIN (AOI software) and SPINDLE (AI TensorFlow GUI for segmentation/classification training)
- **Version Detection**: Extracts version information from folder names and configuration files
- **Configuration Parsing**: Supports multiple configuration file formats:
  - XML files (`*.xml`)
  - INI/CFG files (`*.ini`, `*.cfg`)
  - JSON files (`*.json`)
  - Generic config files (`*.config`)

### Hardware Configuration Extraction
The collector specifically looks for hardware configuration information in:
- Camera setups and specifications
- Lighting systems and LED controllers
- Motion systems and stages
- Sensors and measurement devices
- AI/GPU configurations for SPINDLE

### CodeMeter Dongle Detection
- **Service Detection**: Checks if CodeMeter service is installed and running
- **USB Device Detection**: Scans for CodeMeter/WIBU USB dongles
- **Serial Number Extraction**: Attempts to extract dongle serial numbers from device IDs
- **Registry Integration**: Checks CodeMeter registry entries for additional information
- **CLI Integration**: Uses CodeMeter command line tools when available for detailed dongle information

### Report Structure
The software collector now includes three main sections:
```json
{
  "software": {
    "stratusvision_software": {
      "base_path": "C:\\ProgramData\\StratusVision",
      "installations": [/* Array of found installations */],
      "total_installations": 1,
      "spin_versions": [/* SPIN installations */],
      "spindle_versions": [/* SPINDLE installations */],
      "hardware_configs": [/* Extracted hardware configurations */]
    },
    "codemeter_dongles": {
      "dongles": [/* Array of detected dongles with serial numbers */],
      "total_dongles": 0,
      "codemeter_service_running": true,
      "codemeter_installed": true
    },
    "spin_info": {/* Legacy SPIN detection for backward compatibility */}
  }
}
``` 