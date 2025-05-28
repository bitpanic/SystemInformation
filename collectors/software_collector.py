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
            # Collect dongle information separately
            codemeter_dongles = self._check_codemeter_dongles()
            
            result = {
                "stratusvision_software": self._check_stratus_software(),
                "codemeter_dongles": codemeter_dongles,
                "spin_info": self._check_spin_software(),  # Keep legacy check
                "installed_programs": self._get_installed_programs(),
                "status": "success"
            }
            
            # Also store dongles separately for easy access by GUI
            # This allows the GUI to get dongles independently
            result["_separate_dongles"] = codemeter_dongles
            
            return result
            
        except Exception as e:
            self.log_error(f"Error collecting software information: {str(e)}", exc_info=True)
            return {
                "stratusvision_software": {"error": str(e)},
                "codemeter_dongles": {"error": str(e)},
                "spin_info": {"installed": False, "error": str(e)},
                "installed_programs": [],
                "error": str(e),
                "status": "failed",
                "_separate_dongles": {"error": str(e)}
            }
    
    def _check_stratus_software(self) -> Dict[str, Any]:
        """Check for SPIN and SPINDLE software in C:\ProgramData\StratusVision."""
        self.log_info("Checking for Stratus software in C:\\ProgramData\\StratusVision")
        
        stratus_info = {
            "base_path": r"C:\ProgramData\StratusVision",
            "overview": {
                "total_installations": 0,
                "spin_count": 0,
                "spindle_count": 0,
                "total_config_files": 0,
                "has_hardware_configs": False
            },
            "installations": [],
            "spin_versions": [],
            "spindle_versions": [],
            "hardware_configs": [],
            "system_summary": {
                "unique_ip_addresses": [],
                "motor_types_found": [],
                "scanner_types_found": [],
                "camera_models_found": [],
                "total_io_points": 0,
                "lighting_zones": 0
            }
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
                        stratus_info["overview"]["total_installations"] += 1
                        stratus_info["overview"]["total_config_files"] += len(installation_info.get("config_files", []))
                        
                        # Count by software type
                        if installation_info.get("software_type") == "SPIN":
                            stratus_info["overview"]["spin_count"] += 1
                            stratus_info["spin_versions"].append({
                                "version": installation_info.get("version", "Unknown"),
                                "path": installation_info.get("path"),
                                "config_files_count": len(installation_info.get("config_files", [])),
                                "hardware_summary": installation_info.get("hardware_summary", {})
                            })
                        elif installation_info.get("software_type") == "SPINDLE":
                            stratus_info["overview"]["spindle_count"] += 1
                            stratus_info["spindle_versions"].append({
                                "version": installation_info.get("version", "Unknown"),
                                "path": installation_info.get("path"),
                                "config_files_count": len(installation_info.get("config_files", [])),
                                "hardware_summary": installation_info.get("hardware_summary", {})
                            })
                        
                        # Collect hardware configurations
                        if installation_info.get("hardware_config"):
                            stratus_info["overview"]["has_hardware_configs"] = True
                            stratus_info["hardware_configs"].append({
                                "software": installation_info.get("software_type"),
                                "version": installation_info.get("version"),
                                "config": installation_info.get("hardware_config")
                            })
                        
                        # Aggregate system-wide information
                        self._aggregate_system_info(installation_info, stratus_info["system_summary"])
            
            self.log_info(f"Found {stratus_info['overview']['total_installations']} StratusVision installations")
            self.log_info(f"SPIN installations: {stratus_info['overview']['spin_count']}")
            self.log_info(f"SPINDLE installations: {stratus_info['overview']['spindle_count']}")
            
        except Exception as e:
            self.log_error(f"Error scanning StratusVision directory: {str(e)}", exc_info=True)
            stratus_info["error"] = str(e)
        
        return stratus_info
    
    def _aggregate_system_info(self, installation_info: Dict[str, Any], system_summary: Dict[str, Any]):
        """Aggregate hardware information across all installations."""
        try:
            hardware_summary = installation_info.get("hardware_summary", {})
            if not hardware_summary:
                return
            
            key_configs = hardware_summary.get("key_configurations", {})
            
            # Aggregate IP addresses
            for ip in key_configs.get("ip_addresses", []):
                if ip not in system_summary["unique_ip_addresses"]:
                    system_summary["unique_ip_addresses"].append(ip)
            
            # Aggregate motor types
            for motor_type in key_configs.get("motor_types", []):
                if motor_type not in system_summary["motor_types_found"]:
                    system_summary["motor_types_found"].append(motor_type)
            
            # Aggregate scanner types
            for scanner_type in key_configs.get("scanner_types", []):
                if scanner_type not in system_summary["scanner_types_found"]:
                    system_summary["scanner_types_found"].append(scanner_type)
            
            # Aggregate camera models
            for camera_model in key_configs.get("camera_models", []):
                if camera_model not in system_summary["camera_models_found"]:
                    system_summary["camera_models_found"].append(camera_model)
            
            # Count I/O points and lighting zones
            hardware_overview = hardware_summary.get("hardware_overview", {})
            system_summary["total_io_points"] += hardware_overview.get("io_points", 0)
            system_summary["lighting_zones"] += hardware_overview.get("lighting_zones", 0)
            
        except Exception as e:
            self.log_debug(f"Error aggregating system info: {str(e)}")
    
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
            "codemeter_installed": False,
            "detection_methods": {
                "wmi_pnp_devices": 0,
                "wmi_usb_devices": 0,
                "cli_detection": 0,
                "registry_detection": 0
            }
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
            
            # Enhanced PnP device detection (this usually works)
            try:
                self.log_debug("Scanning PnP devices for CodeMeter dongles...")
                for device in c.Win32_PnPEntity():
                    if device.DeviceID:
                        device_id_lower = device.DeviceID.lower()
                        device_name_lower = (device.Name or "").lower()
                        
                        # Expanded search patterns
                        codemeter_patterns = [
                            "codemeter", "wibu", "halcon", "mvtec", 
                            "protection", "dongle", "usb\\vid_064b",  # WIBU vendor ID
                            "usb\\vid_1a86"  # Another common dongle vendor
                        ]
                        
                        if any(pattern in device_id_lower or pattern in device_name_lower 
                               for pattern in codemeter_patterns):
                            
                            dongle_info = {
                                "device_name": device.Name or "Unknown",
                                "device_id": device.DeviceID or "Unknown",
                                "manufacturer": device.Manufacturer or "Unknown",
                                "status": device.Status or "Unknown",
                                "serial_number": "Unknown",
                                "source": "WMI PnP"
                            }
                            
                            # Enhanced serial number extraction
                            if device.DeviceID:
                                serial_number = self._extract_serial_from_device_id(device.DeviceID)
                                if serial_number:
                                    dongle_info["serial_number"] = serial_number
                            
                            codemeter_info["dongles"].append(dongle_info)
                            codemeter_info["detection_methods"]["wmi_pnp_devices"] += 1
                            self.log_info(f"Found CodeMeter dongle (PnP): {dongle_info['device_name']}")
            except Exception as e:
                self.log_debug(f"Error in PnP device scanning: {str(e)}")
            
            # Skip USB device detection as it's causing COM errors
            # Enhanced USB device detection
            # self.log_debug("Skipping USB device scanning due to COM errors")
            
            # Try to get more detailed info from CodeMeter registry
            try:
                registry_dongles = self._check_codemeter_registry(codemeter_info)
                codemeter_info["detection_methods"]["registry_detection"] = registry_dongles
            except Exception as e:
                self.log_debug(f"Error in registry detection: {str(e)}")
            
            # Try to run CodeMeter command line tool if available (this is most reliable)
            try:
                cli_dongles_before = len(codemeter_info["dongles"])
                self._check_codemeter_cli(codemeter_info)
                codemeter_info["detection_methods"]["cli_detection"] = len(codemeter_info["dongles"]) - cli_dongles_before
            except Exception as e:
                self.log_error(f"Error in CLI detection: {str(e)}")
            
            codemeter_info["total_dongles"] = len(codemeter_info["dongles"])
            
            # Log summary
            self.log_info(f"CodeMeter detection summary: {codemeter_info['total_dongles']} dongles found")
            for method, count in codemeter_info["detection_methods"].items():
                if count > 0:
                    self.log_info(f"  {method}: {count} dongles")
            
        except Exception as e:
            self.log_error(f"Error checking CodeMeter dongles: {str(e)}", exc_info=True)
            codemeter_info["error"] = str(e)
        
        return codemeter_info
    
    def _extract_serial_from_device_id(self, device_id: str) -> str:
        """Extract serial number from device ID with improved patterns."""
        if not device_id:
            return None
            
        import re
        
        # Multiple patterns for serial number extraction
        serial_patterns = [
            r'\\([A-Z0-9]+-[A-Z0-9]+)$',  # Pattern like "3-6903986"
            r'\\([A-Z0-9]{6,})$',         # Long alphanumeric strings
            r'&([A-Z0-9]+-[A-Z0-9]+)&',   # Pattern with & delimiters
            r'\\([0-9]+-[0-9]+)',         # Numeric pattern like "3-6903986"
            r'SER_([A-Z0-9\-]+)',         # Serial prefix pattern
            r'\\([A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12})',  # GUID pattern
        ]
        
        for pattern in serial_patterns:
            match = re.search(pattern, device_id, re.IGNORECASE)
            if match:
                serial = match.group(1)
                # Validate serial number (should have minimum length and reasonable characters)
                if len(serial) >= 4 and not serial.startswith('0000'):
                    return serial
        
        return None
    
    def _check_codemeter_registry(self, codemeter_info: Dict[str, Any]) -> int:
        """Check CodeMeter registry entries for additional information."""
        dongles_found = 0
        try:
            registry_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WIBU-SYSTEMS"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\WIBU-SYSTEMS"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\CodeMeter"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\CodeMeter"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WIBU-SYSTEMS\CodeMeter\Server"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\WIBU-SYSTEMS\CodeMeter\Server")
            ]
            
            for hkey, path in registry_paths:
                try:
                    with winreg.OpenKey(hkey, path) as key:
                        codemeter_info["codemeter_installed"] = True
                        self.log_debug(f"Found CodeMeter registry entry: {path}")
                        
                        # Try to enumerate subkeys for dongle information
                        i = 0
                        while True:
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                self.log_debug(f"CodeMeter registry subkey: {subkey_name}")
                                
                                # Look for serial number patterns in subkey names
                                if '-' in subkey_name and any(c.isdigit() for c in subkey_name):
                                    # This might be a dongle serial
                                    if not any(subkey_name in dongle.get("serial_number", "") 
                                             for dongle in codemeter_info["dongles"]):
                                        dongle_info = {
                                            "device_name": "CodeMeter Dongle (Registry)",
                                            "serial_number": subkey_name,
                                            "source": "Registry",
                                            "registry_path": f"{path}\\{subkey_name}"
                                        }
                                        codemeter_info["dongles"].append(dongle_info)
                                        dongles_found += 1
                                        self.log_info(f"Found dongle in registry: {subkey_name}")
                                
                                i += 1
                            except WindowsError:
                                break
                                
                except FileNotFoundError:
                    continue
                except Exception as e:
                    self.log_debug(f"Error reading CodeMeter registry {path}: {str(e)}")
                    
        except Exception as e:
            self.log_debug(f"Error checking CodeMeter registry: {str(e)}")
        
        return dongles_found
    
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
                        # Try multiple commands to list dongles
                        commands_to_try = [
                            [cli_path, "--list"],
                            [cli_path, "-l"],
                            [cli_path, "--list-dongles"],
                            [cli_path, "--cmdline", "--list-dongles"],
                            [cli_path, "--enum-dongles"],
                            [cli_path, "--info"]
                        ]
                        
                        for cmd in commands_to_try:
                            try:
                                self.log_debug(f"Trying CodeMeter command: {' '.join(cmd)}")
                                
                                # Use shell=True for Windows to handle the command properly
                                cmd_str = ' '.join(f'"{arg}"' if ' ' in arg else arg for arg in cmd)
                                result = subprocess.run(
                                    cmd_str,
                                    capture_output=True, 
                                    text=True, 
                                    timeout=15,
                                    shell=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                                )
                                
                                self.log_debug(f"Command result - Return code: {result.returncode}")
                                if result.stdout:
                                    self.log_debug(f"CodeMeter CLI output: {result.stdout[:500]}")
                                if result.stderr:
                                    self.log_debug(f"CodeMeter CLI stderr: {result.stderr[:200]}")
                                
                                if result.returncode == 0 and result.stdout:
                                    dongles_before = len(codemeter_info["dongles"])
                                    self._parse_codemeter_cli_output(result.stdout, codemeter_info)
                                    dongles_found = len(codemeter_info["dongles"]) - dongles_before
                                    
                                    if dongles_found > 0:
                                        self.log_info(f"CLI command '{' '.join(cmd)}' found {dongles_found} dongles")
                                        break  # Stop trying other commands if we found dongles
                                    else:
                                        self.log_debug(f"CLI command '{' '.join(cmd)}' found no dongles")
                                else:
                                    self.log_debug(f"CLI command failed: return code {result.returncode}")
                                    
                            except subprocess.TimeoutExpired:
                                self.log_debug(f"CodeMeter CLI command timed out: {' '.join(cmd)}")
                            except FileNotFoundError:
                                self.log_debug(f"CodeMeter CLI not found: {cli_path}")
                            except Exception as e:
                                self.log_debug(f"Error running CodeMeter CLI {' '.join(cmd)}: {str(e)}")
                        
                        # Try to get more detailed info if we found dongles
                        if codemeter_info["dongles"]:
                            try:
                                detail_cmd = f'"{cli_path}" --cmdline --detailed-info'
                                result = subprocess.run(
                                    detail_cmd, 
                                    capture_output=True, 
                                    text=True, 
                                    timeout=15,
                                    shell=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                                )
                                if result.returncode == 0 and result.stdout:
                                    self._parse_detailed_codemeter_info(result.stdout, codemeter_info)
                            except Exception as e:
                                self.log_debug(f"Error getting detailed CodeMeter info: {str(e)}")
                        
                    except Exception as e:
                        self.log_debug(f"Error with CodeMeter CLI {cli_path}: {str(e)}")
                    break  # Stop after trying the first found CLI
                    
        except Exception as e:
            self.log_debug(f"Error checking CodeMeter CLI: {str(e)}")
    
    def _parse_codemeter_cli_output(self, output: str, codemeter_info: Dict[str, Any]):
        """Parse CodeMeter CLI output for dongle information."""
        try:
            lines = output.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                self.log_debug(f"Parsing CLI line: {line}")
                
                # Look for the specific CodeMeter format: "CmContainer with Serial Number X-XXXXXX"
                if "cmcontainer" in line.lower() and "serial number" in line.lower():
                    import re
                    
                    # Extract serial number from format like "CmContainer with Serial Number 3-6903986"
                    serial_match = re.search(r'serial number\s+(\d+-\d+)', line, re.IGNORECASE)
                    if serial_match:
                        serial_number = serial_match.group(1)
                        
                        # Extract version if present
                        version_match = re.search(r'version\s+([0-9.]+)', line, re.IGNORECASE)
                        version = version_match.group(1) if version_match else "Unknown"
                        
                        # Extract status (enabled/disabled)
                        status = "Unknown"
                        if "enabled" in line.lower():
                            status = "Enabled"
                        elif "disabled" in line.lower():
                            status = "Disabled"
                        
                        # Check if we already have this dongle
                        found = False
                        for existing_dongle in codemeter_info["dongles"]:
                            if serial_number in existing_dongle.get("serial_number", ""):
                                found = True
                                # Update existing dongle with more info
                                existing_dongle["version"] = version
                                existing_dongle["status"] = status
                                existing_dongle["source"] = "CLI (Enhanced)"
                                break
                        
                        if not found:
                            dongle_info = {
                                "device_name": "CodeMeter CmContainer",
                                "serial_number": serial_number,
                                "version": version,
                                "status": status,
                                "source": "CLI",
                                "raw_info": line
                            }
                            
                            codemeter_info["dongles"].append(dongle_info)
                            self.log_info(f"Found CodeMeter dongle via CLI: Serial {serial_number}, Version {version}, Status {status}")
                
                # Also look for other dongle-related patterns
                elif any(keyword in line.lower() for keyword in ['dongle', 'stick', 'halcon', 'mvtec']):
                    # Extract serial number patterns
                    import re
                    
                    # Pattern for serial numbers like "3-6903986"
                    serial_patterns = [
                        r'(\d+-\d+)',  # Pattern like "3-6903986"
                        r'Serial[:\s]*(\d+[-\d]*)',  # "Serial: 3-6903986"
                        r'HALCON[:\s]*(\d+[-\d]*)',  # "HALCON 3-6903986"
                        r'MVTec[:\s]*(\d+[-\d]*)'  # "MVTec 3-6903986"
                    ]
                    
                    for pattern in serial_patterns:
                        matches = re.findall(pattern, line, re.IGNORECASE)
                        for match in matches:
                            if match and len(match) >= 4 and match != "2007-2025":  # Exclude copyright years
                                # Check if we already have this dongle
                                found = False
                                for existing_dongle in codemeter_info["dongles"]:
                                    if match in existing_dongle.get("serial_number", ""):
                                        found = True
                                        break
                                
                                if not found:
                                    dongle_info = {
                                        "device_name": self._extract_dongle_name(line),
                                        "serial_number": match,
                                        "source": "CLI",
                                        "raw_info": line
                                    }
                                    
                                    # Look for additional info in the line
                                    if "halcon" in line.lower():
                                        dongle_info["device_name"] = "MVTec HALCON"
                                        dongle_info["manufacturer"] = "MVTec"
                                    elif "mvtec" in line.lower():
                                        dongle_info["manufacturer"] = "MVTec"
                                    
                                    codemeter_info["dongles"].append(dongle_info)
                                    self.log_info(f"Found CodeMeter dongle via CLI: {dongle_info['device_name']} - {match}")
            
            # Also try to parse any table-like output
            self._parse_codemeter_table_output(output, codemeter_info)
                                    
        except Exception as e:
            self.log_debug(f"Error parsing CodeMeter CLI output: {str(e)}")
    
    def _extract_dongle_name(self, line: str) -> str:
        """Extract dongle name from CLI line."""
        line_lower = line.lower()
        if "halcon" in line_lower:
            return "MVTec HALCON"
        elif "mvtec" in line_lower:
            return "MVTec Dongle"
        elif "codemeter" in line_lower:
            return "CodeMeter Dongle"
        elif "wibu" in line_lower:
            return "WIBU Dongle"
        else:
            return "CodeMeter Dongle (CLI)"
    
    def _parse_codemeter_table_output(self, output: str, codemeter_info: Dict[str, Any]):
        """Parse table-formatted CodeMeter output."""
        try:
            lines = output.split('\n')
            header_found = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for table headers
                if any(header in line.lower() for header in ['name', 'serial', 'type', 'status']):
                    header_found = True
                    continue
                
                # If we found headers, subsequent lines might be dongle data
                if header_found and len(line.split()) >= 2:
                    parts = line.split()
                    # Look for serial number patterns in table rows
                    for part in parts:
                        if '-' in part and any(c.isdigit() for c in part):
                            # Potential serial number
                            if not any(part in dongle.get("serial_number", "") for dongle in codemeter_info["dongles"]):
                                dongle_info = {
                                    "device_name": "CodeMeter Dongle (Table)",
                                    "serial_number": part,
                                    "source": "CLI Table",
                                    "raw_info": line
                                }
                                codemeter_info["dongles"].append(dongle_info)
                                self.log_info(f"Found dongle from table: {part}")
                                
        except Exception as e:
            self.log_debug(f"Error parsing CodeMeter table output: {str(e)}")
    
    def _parse_detailed_codemeter_info(self, output: str, codemeter_info: Dict[str, Any]):
        """Parse detailed CodeMeter information."""
        try:
            lines = output.split('\n')
            for line in lines:
                line = line.strip()
                if "capacity" in line.lower() or "version" in line.lower() or "status" in line.lower():
                    # Try to match this info with existing dongles
                    for dongle in codemeter_info["dongles"]:
                        if dongle.get("serial_number") and dongle["serial_number"] in line:
                            if "detailed_info" not in dongle:
                                dongle["detailed_info"] = []
                            dongle["detailed_info"].append(line)
                            
        except Exception as e:
            self.log_debug(f"Error parsing detailed CodeMeter info: {str(e)}")
    
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