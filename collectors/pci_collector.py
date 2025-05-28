"""PCI Cards information collector."""

import wmi
from typing import Dict, Any, List
from .base_collector import BaseCollector


class PCICollector(BaseCollector):
    """Collects information about PCI cards and devices."""
    
    VERSION = "1.1"
    
    def collect(self) -> Dict[str, Any]:
        """Collect PCI device information."""
        self.log_info("Starting PCI device collection")
        
        try:
            self.log_debug_info("Initializing WMI connection")
            c = wmi.WMI()
            pci_devices = []
            device_count = 0
            
            self.log_debug_info("Querying Win32_PnPEntity for PCI devices")
            
            # Get PCI devices
            for device in c.Win32_PnPEntity():
                if device.DeviceID and device.DeviceID.startswith('PCI\\'):
                    device_count += 1
                    
                    self.log_debug_info(f"Processing PCI device: {device.Name}", 
                                       {"device_id": device.DeviceID})
                    
                    device_info = {
                        "device_name": device.Name or "Unknown",
                        "manufacturer": device.Manufacturer or "Unknown",
                        "device_id": device.DeviceID or "Unknown",
                        "pnp_device_id": device.PNPDeviceID or "Unknown",
                        "status": device.Status or "Unknown",
                        "service": device.Service or "Unknown"
                    }
                    
                    # Try to extract vendor and device IDs from PCI string
                    if device.DeviceID:
                        try:
                            parts = device.DeviceID.split('\\')
                            if len(parts) > 1:
                                ids = parts[1].split('&')
                                for id_part in ids:
                                    if id_part.startswith('VEN_'):
                                        device_info["vendor_id"] = id_part[4:]
                                    elif id_part.startswith('DEV_'):
                                        device_info["device_id_short"] = id_part[4:]
                        except Exception as e:
                            self.log_warning(f"Failed to parse device ID {device.DeviceID}: {e}")
                    
                    # Try to get additional properties
                    try:
                        # Serial number
                        if hasattr(device, 'SerialNumber') and device.SerialNumber:
                            device_info["serial_number"] = device.SerialNumber
                        else:
                            device_info["serial_number"] = "Not available"
                        
                        # Hardware IDs
                        if hasattr(device, 'HardwareID') and device.HardwareID:
                            device_info["hardware_ids"] = device.HardwareID
                        
                        # Friendly name
                        if hasattr(device, 'FriendlyName') and device.FriendlyName:
                            device_info["friendly_name"] = device.FriendlyName
                        
                        # Driver version and date
                        if hasattr(device, 'DriverVersion') and device.DriverVersion:
                            device_info["driver_version"] = device.DriverVersion
                        
                        if hasattr(device, 'DriverDate') and device.DriverDate:
                            device_info["driver_date"] = str(device.DriverDate)
                            
                    except Exception as e:
                        self.log_debug_info(f"Could not get additional properties for device {device.Name}: {e}")
                    
                    pci_devices.append(device_info)
            
            self.log_info(f"Successfully collected {len(pci_devices)} PCI devices")
            
            if len(pci_devices) == 0:
                self.log_warning("No PCI devices found - this might indicate a collection issue")
            
            return {
                "pci_devices": pci_devices,
                "total_count": len(pci_devices),
                "devices_processed": device_count,
                "status": "success"
            }
            
        except Exception as e:
            error_msg = f"Error collecting PCI information: {str(e)}"
            self.logger.logger.error(error_msg, exc_info=True)
            
            return {
                "pci_devices": [],
                "total_count": 0,
                "devices_processed": 0,
                "error": str(e),
                "error_type": type(e).__name__,
                "status": "failed"
            }
    
    def _get_item_count(self, result: Dict[str, Any]) -> int:
        """Override to return PCI device count."""
        return result.get('total_count', 0) 