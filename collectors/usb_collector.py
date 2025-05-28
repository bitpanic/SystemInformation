"""USB Devices information collector."""

import wmi
import re
from typing import Dict, Any, List
from .base_collector import BaseCollector


class USBCollector(BaseCollector):
    """Collects information about USB devices."""
    
    def collect(self) -> Dict[str, Any]:
        """Collect USB device information."""
        try:
            c = wmi.WMI()
            usb_devices = []
            
            # Get USB devices
            for device in c.Win32_PnPEntity():
                if device.DeviceID and device.DeviceID.startswith('USB\\'):
                    device_info = {
                        "device_name": device.Name or "Unknown",
                        "device_id": device.DeviceID or "Unknown",
                        "pnp_device_id": device.PNPDeviceID or "Unknown",
                        "status": device.Status or "Unknown",
                        "manufacturer": device.Manufacturer or "Unknown"
                    }
                    
                    # Parse USB device ID to extract vendor and product IDs
                    if device.DeviceID:
                        # USB device ID format: USB\VID_xxxx&PID_xxxx\serial or USB\VID_xxxx&PID_xxxx&MI_xx\serial
                        vid_match = re.search(r'VID_([0-9A-Fa-f]{4})', device.DeviceID)
                        pid_match = re.search(r'PID_([0-9A-Fa-f]{4})', device.DeviceID)
                        
                        if vid_match:
                            device_info["vendor_id"] = vid_match.group(1)
                        else:
                            device_info["vendor_id"] = "Unknown"
                            
                        if pid_match:
                            device_info["product_id"] = pid_match.group(1)
                        else:
                            device_info["product_id"] = "Unknown"
                        
                        # Try to extract serial number from the device ID
                        parts = device.DeviceID.split('\\')
                        if len(parts) > 2:
                            serial_part = parts[2]
                            # Remove interface info if present
                            if '&' in serial_part:
                                serial_part = serial_part.split('&')[0]
                            device_info["serial_number"] = serial_part
                        else:
                            device_info["serial_number"] = "Not available"
                    
                    # Determine USB class/type based on device info
                    device_name = device.Name.lower() if device.Name else ""
                    if "hub" in device_name:
                        device_info["usb_class"] = "Hub"
                    elif "storage" in device_name or "disk" in device_name:
                        device_info["usb_class"] = "Mass Storage"
                    elif "keyboard" in device_name:
                        device_info["usb_class"] = "HID (Keyboard)"
                    elif "mouse" in device_name:
                        device_info["usb_class"] = "HID (Mouse)"
                    elif "audio" in device_name or "speaker" in device_name:
                        device_info["usb_class"] = "Audio"
                    elif "camera" in device_name or "webcam" in device_name:
                        device_info["usb_class"] = "Video"
                    elif "network" in device_name or "ethernet" in device_name:
                        device_info["usb_class"] = "Communications"
                    else:
                        device_info["usb_class"] = "Unknown"
                    
                    usb_devices.append(device_info)
            
            # Also check for USB controllers
            usb_controllers = []
            for controller in c.Win32_USBController():
                controller_info = {
                    "name": controller.Name or "Unknown",
                    "device_id": controller.DeviceID or "Unknown",
                    "manufacturer": controller.Manufacturer or "Unknown",
                    "status": controller.Status or "Unknown"
                }
                usb_controllers.append(controller_info)
            
            return {
                "usb_devices": usb_devices,
                "usb_controllers": usb_controllers,
                "total_devices": len(usb_devices),
                "total_controllers": len(usb_controllers),
                "status": "success"
            }
            
        except Exception as e:
            self.log_error(f"Error collecting USB information: {str(e)}", exc_info=True)
            return {
                "usb_devices": [],
                "usb_controllers": [],
                "total_devices": 0,
                "total_controllers": 0,
                "error": str(e),
                "status": "failed"
            } 