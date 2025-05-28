"""Software information collector."""

import wmi
import winreg
import os
import glob
import json
import configparser
import xml.etree.ElementTree as ET
from typing import Dict, Any, List
from .base_collector import BaseCollector


class SoftwareCollector(BaseCollector):
    """Collects information about installed software, specifically SPIN and SPINDLE."""
    
    VERSION = "1.2"
    
    def collect(self) -> Dict[str, Any]:
        """Collect software information with focus on SPIN/SPINDLE software and CodeMeter dongles."""
        try:
            result = {
                "stratusvision_software": self._check_stratus_software(),
                "codemeter_dongles": self._check_codemeter_dongles(),
                "spin_info": self._check_spin_software(),  # Keep legacy check
                "installed_programs": self._get_installed_programs(),
                "status": "success"
            }
            return result
            
        except Exception as e:
            self.log_error(f"Error collecting software information: {str(e)}", exc_info=True)
            return {
                "stratusvision_software": {"error": str(e)},
                "codemeter_dongles": {"error": str(e)},
                "spin_info": {"installed": False, "error": str(e)},
                "installed_programs": [],
                "error": str(e),
                "status": "failed"
            }
    
    def _check_stratus_software(self) -> Dict[str, Any]:
        """Check for SPIN and SPINDLE software in C:\ProgramData\StratusVision."""
        self.log_info("Checking for Stratus software in C:\\ProgramData\\StratusVision")
        
        stratus_info = {
            "base_path": r"C:\ProgramData\StratusVision",
            "installations": [],
            "total_installations": 0,
            "spin_versions": [],
            "spindle_versions": [],
            "hardware_configs": []
        }
        
        stratus_path = r"C:\ProgramData\StratusVision"
        
        if not os.path.exists(stratus_path):
            self.log_warning(f"StratusVision directory not found: {stratus_path}")
            stratus_info["error"] = "StratusVision directory not found"
            return stratus_info
        
        self.log_info(f"Found StratusVision directory: {stratus_path}")
        
        try:
            # List all directories in StratusVision folder
            for item in os.listdir(stratus_path):
                item_path = os.path.join(stratus_path, item)
                
                if os.path.isdir(item_path):
                    self.log_debug(f"Processing StratusVision directory: {item}")
                    installation_info = self._analyze_stratus_installation(item_path, item)
                    
                    if installation_info:
                        stratus_info["installations"].append(installation_info)
                        stratus_info["total_installations"] += 1
                        
                        # Categorize by software type
                        if installation_info.get("software_type") == "SPIN":
                            stratus_info["spin_versions"].append({
                                "version": installation_info.get("version", "Unknown"),
                                "path": installation_info.get("path"),
                                "config_file": installation_info.get("config_file")
                            })
                        elif installation_info.get("software_type") == "SPINDLE":
                            stratus_info["spindle_versions"].append({
                                "version": installation_info.get("version", "Unknown"),
                                "path": installation_info.get("path"),
                                "config_file": installation_info.get("config_file")
                            })
                        
                        # Collect hardware configurations
                        if installation_info.get("hardware_config"):
                            stratus_info["hardware_configs"].append({
                                "software": installation_info.get("software_type"),
                                "version": installation_info.get("version"),
                                "config": installation_info.get("hardware_config")
                            })
            
            self.log_info(f"Found {stratus_info['total_installations']} StratusVision installations")
            
        except Exception as e:
            self.log_error(f"Error scanning StratusVision directory: {str(e)}", exc_info=True)
            stratus_info["error"] = str(e)
        
        return stratus_info
    
    def _analyze_stratus_installation(self, install_path: str, folder_name: str) -> Dict[str, Any]:
        """Analyze a single Stratus software installation directory."""
        installation_info = {
            "path": install_path,
            "folder_name": folder_name,
            "software_type": "Unknown",
            "version": "Unknown",
            "config_files": [],
            "executables": [],
            "hardware_config": None
        }
        
        try:
            # Determine software type from folder name or contents
            folder_lower = folder_name.lower()
            if "spin" in folder_lower and "spindle" not in folder_lower:
                installation_info["software_type"] = "SPIN"
            elif "spindle" in folder_lower:
                installation_info["software_type"] = "SPINDLE"
            
            # Look for executables to confirm software type
            for file in os.listdir(install_path):
                if file.lower().endswith('.exe'):
                    installation_info["executables"].append(file)
                    file_lower = file.lower()
                    if "spin.exe" in file_lower and "spindle" not in file_lower:
                        installation_info["software_type"] = "SPIN"
                    elif "spindle" in file_lower:
                        installation_info["software_type"] = "SPINDLE"
            
            # Extract version from folder name if possible
            import re
            version_match = re.search(r'(\d+\.\d+(?:\.\d+)?(?:\.\d+)?)', folder_name)
            if version_match:
                installation_info["version"] = version_match.group(1)
            
            # Search for configuration files
            config_patterns = [
                "*.xml", "*.config", "*.cfg", "*.ini", "*.json", 
                "hardware.xml", "config.xml", "system.xml", "settings.xml"
            ]
            
            for pattern in config_patterns:
                for config_file in glob.glob(os.path.join(install_path, pattern)):
                    config_info = self._parse_stratus_config_file(config_file)
                    if config_info:
                        installation_info["config_files"].append(config_info)
                        
                        # Extract version from config if not found yet
                        if installation_info["version"] == "Unknown" and config_info.get("version"):
                            installation_info["version"] = config_info["version"]
                        
                        # Store hardware configuration
                        if config_info.get("hardware_config"):
                            installation_info["hardware_config"] = config_info["hardware_config"]
            
            # Search recursively for config files in subdirectories
            for root, dirs, files in os.walk(install_path):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in ['.xml', '.config', '.cfg', '.ini']):
                        if "hardware" in file.lower() or "config" in file.lower():
                            config_file_path = os.path.join(root, file)
                            config_info = self._parse_stratus_config_file(config_file_path)
                            if config_info and config_info not in installation_info["config_files"]:
                                installation_info["config_files"].append(config_info)
                                
                                if config_info.get("hardware_config"):
                                    installation_info["hardware_config"] = config_info["hardware_config"]
            
            # Generate readable hardware summary
            installation_info["hardware_summary"] = self._format_hardware_summary(installation_info)
            
            return installation_info
            
        except Exception as e:
            self.log_error(f"Error analyzing installation {install_path}: {str(e)}", exc_info=True)
            installation_info["error"] = str(e)
            return installation_info
    
    def _parse_stratus_config_file(self, file_path: str) -> Dict[str, Any]:
        """Parse Stratus configuration files for hardware and version information."""
        config_info = {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "file_type": os.path.splitext(file_path)[1].lower(),
            "hardware_config": {},
            "version": None,
            "content_summary": {},
            "important_settings": {}
        }
        
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.xml':
                config_info.update(self._parse_xml_config(file_path))
            elif file_ext in ['.ini', '.cfg']:
                config_info.update(self._parse_ini_config(file_path))
            elif file_ext == '.json':
                config_info.update(self._parse_json_config(file_path))
            elif file_ext == '.config':
                # Try XML first, then INI format
                try:
                    config_info.update(self._parse_xml_config(file_path))
                except:
                    config_info.update(self._parse_ini_config(file_path))
            
            return config_info
            
        except Exception as e:
            self.log_debug(f"Error parsing config file {file_path}: {str(e)}")
            config_info["error"] = str(e)
            return config_info
    
    def _parse_xml_config(self, file_path: str) -> Dict[str, Any]:
        """Parse XML configuration files."""
        result = {"hardware_config": {}, "content_summary": {}, "important_settings": {}}
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Look for hardware-related elements
            hardware_elements = [
                "Camera", "Cameras", "Hardware", "System", "Configuration",
                "Lighting", "Optics", "Stage", "Motion", "Sensors", "Motor", "Motors",
                "IO", "Input", "Output", "BarcodeScanner", "Scanner", "Network",
                "Communication", "Ethernet", "Serial", "USB"
            ]
            
            for element_name in hardware_elements:
                elements = root.findall(f".//{element_name}")
                if elements:
                    element_data = []
                    for elem in elements:
                        elem_dict = self._xml_element_to_dict(elem)
                        if elem_dict:
                            element_data.append(elem_dict)
                    if element_data:
                        result["hardware_config"][element_name] = element_data
            
            # Extract important settings
            result["important_settings"] = self._extract_important_settings(root)
            
            # Look for version information
            version_elements = root.findall(".//Version") + root.findall(".//version")
            for elem in version_elements:
                if elem.text:
                    result["version"] = elem.text.strip()
                    break
            
            # Create content summary
            result["content_summary"] = {
                "root_tag": root.tag,
                "total_elements": len(list(root.iter())),
                "main_sections": [child.tag for child in root],
                "has_network_config": len(root.findall(".//IP") + root.findall(".//ip") + root.findall(".//Network")) > 0,
                "has_motor_config": len(root.findall(".//Motor") + root.findall(".//motion") + root.findall(".//Stage")) > 0,
                "has_io_config": len(root.findall(".//IO") + root.findall(".//Input") + root.findall(".//Output")) > 0,
                "has_scanner_config": len(root.findall(".//Scanner") + root.findall(".//Barcode")) > 0
            }
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def _extract_important_settings(self, root) -> Dict[str, Any]:
        """Extract important SPIN configuration settings from XML."""
        important = {
            "network_settings": {},
            "motor_settings": {},
            "io_configuration": {},
            "scanner_settings": {},
            "camera_settings": {},
            "lighting_settings": {}
        }
        
        try:
            # Network/IP Configuration
            ip_elements = root.findall(".//IP") + root.findall(".//ip") + root.findall(".//IPAddress")
            for elem in ip_elements:
                if elem.text:
                    parent_name = elem.getparent().tag if elem.getparent() is not None else "unknown"
                    important["network_settings"][f"{parent_name}_ip"] = elem.text.strip()
                for attr, value in elem.attrib.items():
                    if "ip" in attr.lower() or "address" in attr.lower():
                        important["network_settings"][f"{parent_name}_{attr}"] = value
            
            # Port Configuration
            port_elements = root.findall(".//Port") + root.findall(".//port")
            for elem in port_elements:
                if elem.text:
                    parent_name = elem.getparent().tag if elem.getparent() is not None else "unknown"
                    important["network_settings"][f"{parent_name}_port"] = elem.text.strip()
            
            # Motor/Motion Configuration
            motor_elements = root.findall(".//Motor") + root.findall(".//motion") + root.findall(".//Stage")
            for elem in motor_elements:
                motor_info = {}
                if elem.text:
                    motor_info["value"] = elem.text.strip()
                motor_info.update(elem.attrib)
                
                # Look for common motor parameters
                for child in elem:
                    if child.tag.lower() in ["speed", "acceleration", "position", "home", "limit", "enable"]:
                        motor_info[child.tag.lower()] = child.text.strip() if child.text else child.attrib
                
                if motor_info:
                    motor_name = elem.attrib.get("name", elem.attrib.get("id", f"motor_{len(important['motor_settings'])}"))
                    important["motor_settings"][motor_name] = motor_info
            
            # I/O Configuration
            io_elements = root.findall(".//IO") + root.findall(".//Input") + root.findall(".//Output")
            for elem in io_elements:
                io_info = {}
                if elem.text:
                    io_info["value"] = elem.text.strip()
                io_info.update(elem.attrib)
                
                # Look for I/O specific parameters
                for child in elem:
                    if child.tag.lower() in ["pin", "channel", "type", "state", "function", "trigger"]:
                        io_info[child.tag.lower()] = child.text.strip() if child.text else child.attrib
                
                if io_info:
                    io_name = elem.attrib.get("name", elem.attrib.get("id", f"io_{len(important['io_configuration'])}"))
                    important["io_configuration"][io_name] = io_info
            
            # Scanner Configuration
            scanner_elements = root.findall(".//Scanner") + root.findall(".//Barcode") + root.findall(".//BarcodeScanner")
            for elem in scanner_elements:
                scanner_info = {}
                if elem.text:
                    scanner_info["value"] = elem.text.strip()
                scanner_info.update(elem.attrib)
                
                # Look for scanner specific parameters
                for child in elem:
                    if child.tag.lower() in ["type", "model", "interface", "baudrate", "timeout", "enable"]:
                        scanner_info[child.tag.lower()] = child.text.strip() if child.text else child.attrib
                
                if scanner_info:
                    scanner_name = elem.attrib.get("name", elem.attrib.get("id", f"scanner_{len(important['scanner_settings'])}"))
                    important["scanner_settings"][scanner_name] = scanner_info
            
            # Camera Configuration
            camera_elements = root.findall(".//Camera")
            for elem in camera_elements:
                camera_info = {}
                camera_info.update(elem.attrib)
                
                # Look for camera specific parameters
                for child in elem:
                    if child.tag.lower() in ["model", "serialnumber", "resolution", "interface", "exposure", "gain"]:
                        camera_info[child.tag.lower()] = child.text.strip() if child.text else child.attrib
                
                if camera_info:
                    camera_name = elem.attrib.get("name", elem.attrib.get("id", f"camera_{len(important['camera_settings'])}"))
                    important["camera_settings"][camera_name] = camera_info
            
            # Lighting Configuration
            lighting_elements = root.findall(".//Lighting") + root.findall(".//LED") + root.findall(".//Light")
            for elem in lighting_elements:
                lighting_info = {}
                if elem.text:
                    lighting_info["value"] = elem.text.strip()
                lighting_info.update(elem.attrib)
                
                # Look for lighting specific parameters
                for child in elem:
                    if child.tag.lower() in ["intensity", "channel", "color", "type", "control"]:
                        lighting_info[child.tag.lower()] = child.text.strip() if child.text else child.attrib
                
                if lighting_info:
                    lighting_name = elem.attrib.get("name", elem.attrib.get("id", f"lighting_{len(important['lighting_settings'])}"))
                    important["lighting_settings"][lighting_name] = lighting_info
            
        except Exception as e:
            important["parsing_error"] = str(e)
        
        return important
    
    def _xml_element_to_dict(self, element) -> Dict[str, Any]:
        """Convert XML element to dictionary."""
        result = {}
        
        # Add attributes
        if element.attrib:
            result.update(element.attrib)
        
        # Add text content
        if element.text and element.text.strip():
            result["text"] = element.text.strip()
        
        # Add child elements
        for child in element:
            child_data = self._xml_element_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result
    
    def _parse_ini_config(self, file_path: str) -> Dict[str, Any]:
        """Parse INI/CFG configuration files."""
        result = {"hardware_config": {}, "content_summary": {}, "important_settings": {}}
        
        try:
            config = configparser.ConfigParser()
            config.read(file_path, encoding='utf-8')
            
            hardware_sections = []
            important = {
                "network_settings": {},
                "motor_settings": {},
                "io_configuration": {},
                "scanner_settings": {},
                "camera_settings": {},
                "lighting_settings": {}
            }
            
            for section_name in config.sections():
                section_lower = section_name.lower()
                section_data = dict(config[section_name])
                
                # Categorize sections
                if any(keyword in section_lower for keyword in 
                       ["camera", "hardware", "system", "lighting", "motion", "stage", "motor", "io", "scanner", "network"]):
                    hardware_sections.append(section_name)
                    result["hardware_config"][section_name] = section_data
                
                # Extract important settings by section type
                if "network" in section_lower or "ethernet" in section_lower or "communication" in section_lower:
                    important["network_settings"].update(section_data)
                elif "motor" in section_lower or "motion" in section_lower or "stage" in section_lower:
                    important["motor_settings"].update(section_data)
                elif "io" in section_lower or "input" in section_lower or "output" in section_lower:
                    important["io_configuration"].update(section_data)
                elif "scanner" in section_lower or "barcode" in section_lower:
                    important["scanner_settings"].update(section_data)
                elif "camera" in section_lower:
                    important["camera_settings"].update(section_data)
                elif "lighting" in section_lower or "led" in section_lower:
                    important["lighting_settings"].update(section_data)
                
                # Look for version in any section
                for key, value in section_data.items():
                    if "version" in key.lower():
                        result["version"] = value
            
            result["important_settings"] = important
            result["content_summary"] = {
                "total_sections": len(config.sections()),
                "sections": list(config.sections()),
                "hardware_sections": hardware_sections,
                "has_network_config": bool(important["network_settings"]),
                "has_motor_config": bool(important["motor_settings"]),
                "has_io_config": bool(important["io_configuration"]),
                "has_scanner_config": bool(important["scanner_settings"])
            }
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def _parse_json_config(self, file_path: str) -> Dict[str, Any]:
        """Parse JSON configuration files."""
        result = {"hardware_config": {}, "content_summary": {}}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Look for hardware-related keys
            hardware_keys = []
            for key, value in data.items():
                key_lower = key.lower()
                if any(keyword in key_lower for keyword in 
                       ["camera", "hardware", "system", "lighting", "motion", "stage"]):
                    hardware_keys.append(key)
                    result["hardware_config"][key] = value
                
                # Look for version
                if "version" in key_lower:
                    result["version"] = str(value)
            
            result["content_summary"] = {
                "total_keys": len(data),
                "main_keys": list(data.keys()),
                "hardware_keys": hardware_keys
            }
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def _check_codemeter_dongles(self) -> Dict[str, Any]:
        """Check for CodeMeter dongles and extract serial numbers."""
        self.log_info("Checking for CodeMeter dongles")
        
        codemeter_info = {
            "dongles": [],
            "total_dongles": 0,
            "codemeter_service_running": False,
            "codemeter_installed": False
        }
        
        try:
            # Check if CodeMeter is installed and service is running
            c = wmi.WMI()
            
            # Check for CodeMeter service
            for service in c.Win32_Service():
                if "codemeter" in service.Name.lower():
                    codemeter_info["codemeter_service_running"] = (service.State == "Running")
                    codemeter_info["codemeter_installed"] = True
                    self.log_info(f"Found CodeMeter service: {service.Name}, State: {service.State}")
                    break
            
            # Check for CodeMeter USB devices
            for device in c.Win32_PnPEntity():
                if device.DeviceID and ("codemeter" in device.DeviceID.lower() or 
                                      "wibu" in device.DeviceID.lower()):
                    dongle_info = {
                        "device_name": device.Name or "Unknown",
                        "device_id": device.DeviceID or "Unknown",
                        "manufacturer": device.Manufacturer or "Unknown",
                        "status": device.Status or "Unknown",
                        "serial_number": "Unknown"
                    }
                    
                    # Try to extract serial number from device ID
                    if device.DeviceID:
                        import re
                        # Look for serial number patterns in device ID
                        serial_match = re.search(r'\\([A-Z0-9]+)$', device.DeviceID)
                        if serial_match:
                            dongle_info["serial_number"] = serial_match.group(1)
                    
                    codemeter_info["dongles"].append(dongle_info)
                    self.log_info(f"Found CodeMeter dongle: {dongle_info['device_name']}")
            
            # Try to get more detailed info from CodeMeter registry
            self._check_codemeter_registry(codemeter_info)
            
            # Try to run CodeMeter command line tool if available
            self._check_codemeter_cli(codemeter_info)
            
            codemeter_info["total_dongles"] = len(codemeter_info["dongles"])
            
        except Exception as e:
            self.log_error(f"Error checking CodeMeter dongles: {str(e)}", exc_info=True)
            codemeter_info["error"] = str(e)
        
        return codemeter_info
    
    def _check_codemeter_registry(self, codemeter_info: Dict[str, Any]):
        """Check CodeMeter registry entries for additional information."""
        try:
            registry_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WIBU-SYSTEMS"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\WIBU-SYSTEMS"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\CodeMeter"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\CodeMeter")
            ]
            
            for hkey, path in registry_paths:
                try:
                    with winreg.OpenKey(hkey, path) as key:
                        codemeter_info["codemeter_installed"] = True
                        self.log_debug(f"Found CodeMeter registry entry: {path}")
                        
                        # Try to enumerate subkeys for more info
                        i = 0
                        while True:
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                self.log_debug(f"CodeMeter registry subkey: {subkey_name}")
                                i += 1
                            except WindowsError:
                                break
                                
                except FileNotFoundError:
                    continue
                except Exception as e:
                    self.log_debug(f"Error reading CodeMeter registry {path}: {str(e)}")
                    
        except Exception as e:
            self.log_debug(f"Error checking CodeMeter registry: {str(e)}")
    
    def _check_codemeter_cli(self, codemeter_info: Dict[str, Any]):
        """Try to get dongle information using CodeMeter command line tools."""
        try:
            import subprocess
            
            # Common CodeMeter CLI paths
            cli_paths = [
                r"C:\Program Files\CodeMeter\Runtime\bin\cmu.exe",
                r"C:\Program Files (x86)\CodeMeter\Runtime\bin\cmu.exe",
                r"C:\Program Files\WIBU-SYSTEMS\CodeMeter\Runtime\bin\cmu.exe",
                r"C:\Program Files (x86)\WIBU-SYSTEMS\CodeMeter\Runtime\bin\cmu.exe"
            ]
            
            for cli_path in cli_paths:
                if os.path.exists(cli_path):
                    self.log_info(f"Found CodeMeter CLI: {cli_path}")
                    try:
                        # Try to list dongles
                        result = subprocess.run([cli_path, "--list-dongles"], 
                                              capture_output=True, text=True, timeout=10)
                        if result.returncode == 0 and result.stdout:
                            self._parse_codemeter_cli_output(result.stdout, codemeter_info)
                    except Exception as e:
                        self.log_debug(f"Error running CodeMeter CLI: {str(e)}")
                    break
                    
        except Exception as e:
            self.log_debug(f"Error checking CodeMeter CLI: {str(e)}")
    
    def _parse_codemeter_cli_output(self, output: str, codemeter_info: Dict[str, Any]):
        """Parse CodeMeter CLI output for dongle information."""
        try:
            lines = output.split('\n')
            for line in lines:
                if "dongle" in line.lower() or "serial" in line.lower():
                    # Extract serial number from CLI output
                    import re
                    serial_match = re.search(r'(\d+)', line)
                    if serial_match:
                        # Check if we already have this dongle
                        serial = serial_match.group(1)
                        found = False
                        for dongle in codemeter_info["dongles"]:
                            if serial in dongle.get("serial_number", ""):
                                found = True
                                break
                        
                        if not found:
                            codemeter_info["dongles"].append({
                                "device_name": "CodeMeter Dongle (CLI)",
                                "serial_number": serial,
                                "source": "CLI"
                            })
                            
        except Exception as e:
            self.log_debug(f"Error parsing CodeMeter CLI output: {str(e)}")
    
    def _check_spin_software(self) -> Dict[str, Any]:
        """Legacy check for SPIN software (keep for backward compatibility)."""
        spin_info = {
            "installed": False,
            "version": "Not found",
            "license_number": "Not found",
            "install_path": "Not found",
            "registry_entries": [],
            "config_files": []
        }
        
        # Check common registry locations for SPIN
        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\SPIN"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\SPIN"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\SPIN"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
        ]
        
        for hkey, path in registry_paths:
            try:
                self._search_registry_for_spin(hkey, path, spin_info)
            except Exception as e:
                self.log_debug(f"Error accessing registry {path}: {str(e)}")
        
        # Check common installation directories
        common_paths = [
            r"C:\Program Files\SPIN",
            r"C:\Program Files (x86)\SPIN",
            r"C:\SPIN",
            os.path.expanduser(r"~\AppData\Local\SPIN"),
            os.path.expanduser(r"~\AppData\Roaming\SPIN")
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                spin_info["installed"] = True
                spin_info["install_path"] = path
                self._search_config_files(path, spin_info)
        
        # Search for SPIN executables
        self._search_spin_executables(spin_info)
        
        return spin_info
    
    def _search_registry_for_spin(self, hkey: int, path: str, spin_info: Dict[str, Any]):
        """Search registry for SPIN-related entries."""
        try:
            with winreg.OpenKey(hkey, path) as key:
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        if "spin" in subkey_name.lower():
                            subkey_path = f"{path}\\{subkey_name}"
                            self._extract_spin_registry_info(hkey, subkey_path, spin_info)
                        i += 1
                    except WindowsError:
                        break
        except Exception as e:
            self.log_debug(f"Registry search error in {path}: {str(e)}")
    
    def _extract_spin_registry_info(self, hkey: int, path: str, spin_info: Dict[str, Any]):
        """Extract SPIN information from registry key."""
        try:
            with winreg.OpenKey(hkey, path) as key:
                registry_entry = {"path": path, "values": {}}
                
                i = 0
                while True:
                    try:
                        name, value, reg_type = winreg.EnumValue(key, i)
                        registry_entry["values"][name] = str(value)
                        
                        # Look for version information
                        if name.lower() in ["version", "displayversion", "versioninfo"]:
                            spin_info["version"] = str(value)
                            spin_info["installed"] = True
                        
                        # Look for license information
                        if "license" in name.lower() or "serial" in name.lower() or "key" in name.lower():
                            spin_info["license_number"] = str(value)
                        
                        # Look for install path
                        if name.lower() in ["installpath", "installlocation", "uninstallstring"]:
                            install_path = str(value)
                            if os.path.exists(install_path):
                                spin_info["install_path"] = install_path
                                spin_info["installed"] = True
                        
                        i += 1
                    except WindowsError:
                        break
                
                if registry_entry["values"]:
                    spin_info["registry_entries"].append(registry_entry)
                    
        except Exception as e:
            self.log_debug(f"Error extracting registry info from {path}: {str(e)}")
    
    def _search_config_files(self, install_path: str, spin_info: Dict[str, Any]):
        """Search for SPIN configuration files."""
        config_patterns = [
            "*.ini", "*.cfg", "*.conf", "*.config", 
            "*.json", "*.xml", "*.txt", "license.txt", 
            "version.txt", "spin.conf", "config.ini"
        ]
        
        for pattern in config_patterns:
            search_pattern = os.path.join(install_path, "**", pattern)
            for config_file in glob.glob(search_pattern, recursive=True):
                try:
                    config_info = self._parse_config_file(config_file)
                    if config_info:
                        spin_info["config_files"].append(config_info)
                        
                        # Extract version and license from config
                        if config_info.get("version"):
                            spin_info["version"] = config_info["version"]
                        if config_info.get("license"):
                            spin_info["license_number"] = config_info["license"]
                            
                except Exception as e:
                    self.log_debug(f"Error parsing config file {config_file}: {str(e)}")
    
    def _parse_config_file(self, file_path: str) -> Dict[str, Any]:
        """Parse configuration file for version and license information."""
        config_info = {"file_path": file_path, "content": {}}
        
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    config_info["content"] = data
                    
                    # Look for version and license in JSON
                    for key, value in data.items():
                        if "version" in key.lower():
                            config_info["version"] = str(value)
                        if "license" in key.lower() or "serial" in key.lower():
                            config_info["license"] = str(value)
            
            elif file_ext in ['.ini', '.cfg', '.conf']:
                config = configparser.ConfigParser()
                config.read(file_path, encoding='utf-8')
                
                for section in config.sections():
                    section_data = dict(config[section])
                    config_info["content"][section] = section_data
                    
                    # Look for version and license in INI sections
                    for key, value in section_data.items():
                        if "version" in key.lower():
                            config_info["version"] = value
                        if "license" in key.lower() or "serial" in key.lower():
                            config_info["license"] = value
            
            else:
                # For text files, search for version and license patterns
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    config_info["content"]["raw"] = content[:1000]  # First 1000 chars
                    
                    # Simple pattern matching
                    import re
                    version_match = re.search(r'version[:\s=]+([^\s\n\r]+)', content, re.IGNORECASE)
                    if version_match:
                        config_info["version"] = version_match.group(1)
                    
                    license_match = re.search(r'license[:\s=]+([^\s\n\r]+)', content, re.IGNORECASE)
                    if license_match:
                        config_info["license"] = license_match.group(1)
            
            return config_info
            
        except Exception as e:
            self.log_debug(f"Error parsing {file_path}: {str(e)}")
            return None
    
    def _search_spin_executables(self, spin_info: Dict[str, Any]):
        """Search for SPIN executable files."""
        search_paths = [
            r"C:\Program Files",
            r"C:\Program Files (x86)",
            os.path.expanduser(r"~\AppData\Local"),
            os.path.expanduser(r"~\AppData\Roaming")
        ]
        
        for search_path in search_paths:
            if os.path.exists(search_path):
                try:
                    for root, dirs, files in os.walk(search_path):
                        for file in files:
                            if "spin" in file.lower() and file.lower().endswith(('.exe', '.msi')):
                                full_path = os.path.join(root, file)
                                spin_info["installed"] = True
                                if "install_path" not in spin_info or spin_info["install_path"] == "Not found":
                                    spin_info["install_path"] = root
                                break
                except Exception as e:
                    self.log_debug(f"Error searching {search_path}: {str(e)}")
    
    def _get_installed_programs(self) -> List[Dict[str, Any]]:
        """Get list of installed programs from registry."""
        programs = []
        
        # Registry paths for installed programs
        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
        ]
        
        for hkey, path in registry_paths:
            try:
                with winreg.OpenKey(hkey, path) as key:
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            program_info = self._get_program_info(hkey, f"{path}\\{subkey_name}")
                            if program_info and program_info.get("display_name"):
                                programs.append(program_info)
                            i += 1
                        except WindowsError:
                            break
            except Exception as e:
                self.log_debug(f"Error accessing programs registry {path}: {str(e)}")
        
        return programs[:50]  # Limit to first 50 programs to avoid overwhelming output
    
    def _get_program_info(self, hkey: int, path: str) -> Dict[str, Any]:
        """Get program information from registry key."""
        try:
            with winreg.OpenKey(hkey, path) as key:
                program_info = {}
                
                value_names = ["DisplayName", "DisplayVersion", "Publisher", "InstallDate", "InstallLocation"]
                for value_name in value_names:
                    try:
                        value, _ = winreg.QueryValueEx(key, value_name)
                        program_info[value_name.lower().replace("display", "")] = str(value)
                    except WindowsError:
                        continue
                
                return program_info
        except Exception:
            return {}
    
    def _format_hardware_summary(self, installation_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create a readable summary of hardware configuration."""
        summary = {
            "installation_summary": {
                "software_type": installation_info.get("software_type", "Unknown"),
                "version": installation_info.get("version", "Unknown"),
                "path": installation_info.get("path", "Unknown"),
                "total_config_files": len(installation_info.get("config_files", []))
            },
            "hardware_overview": {
                "network_devices": 0,
                "motors_configured": 0,
                "io_points": 0,
                "scanners": 0,
                "cameras": 0,
                "lighting_zones": 0
            },
            "key_configurations": {
                "ip_addresses": [],
                "motor_types": [],
                "scanner_types": [],
                "camera_models": [],
                "io_points_summary": []
            }
        }
        
        try:
            # Analyze each config file
            for config_file in installation_info.get("config_files", []):
                important_settings = config_file.get("important_settings", {})
                
                if important_settings:
                    # Count and extract network info
                    network_settings = important_settings.get("network_settings", {})
                    for key, value in network_settings.items():
                        if "ip" in key.lower() and value not in summary["key_configurations"]["ip_addresses"]:
                            summary["key_configurations"]["ip_addresses"].append(value)
                            summary["hardware_overview"]["network_devices"] += 1
                    
                    # Count and extract motor info
                    motor_settings = important_settings.get("motor_settings", {})
                    for motor_name, motor_config in motor_settings.items():
                        motor_type = motor_config.get("type", motor_config.get("model", "Unknown Motor"))
                        if motor_type not in summary["key_configurations"]["motor_types"]:
                            summary["key_configurations"]["motor_types"].append(motor_type)
                        summary["hardware_overview"]["motors_configured"] += 1
                    
                    # Count and extract I/O info
                    io_config = important_settings.get("io_configuration", {})
                    for io_name, io_settings in io_config.items():
                        io_type = io_settings.get("type", io_settings.get("function", "Unknown I/O"))
                        summary["key_configurations"]["io_points_summary"].append(f"{io_name}: {io_type}")
                        summary["hardware_overview"]["io_points"] += 1
                    
                    # Count and extract scanner info
                    scanner_settings = important_settings.get("scanner_settings", {})
                    for scanner_name, scanner_config in scanner_settings.items():
                        scanner_type = scanner_config.get("type", scanner_config.get("model", "Unknown Scanner"))
                        if scanner_type not in summary["key_configurations"]["scanner_types"]:
                            summary["key_configurations"]["scanner_types"].append(scanner_type)
                        summary["hardware_overview"]["scanners"] += 1
                    
                    # Count and extract camera info
                    camera_settings = important_settings.get("camera_settings", {})
                    for camera_name, camera_config in camera_settings.items():
                        camera_model = camera_config.get("model", camera_config.get("name", "Unknown Camera"))
                        if camera_model not in summary["key_configurations"]["camera_models"]:
                            summary["key_configurations"]["camera_models"].append(camera_model)
                        summary["hardware_overview"]["cameras"] += 1
                    
                    # Count lighting zones
                    lighting_settings = important_settings.get("lighting_settings", {})
                    summary["hardware_overview"]["lighting_zones"] = len(lighting_settings)
            
        except Exception as e:
            summary["summary_error"] = str(e)
        
        return summary 