"""Storage information collector."""

import wmi
import psutil
from typing import Dict, Any, List
from .base_collector import BaseCollector


class StorageCollector(BaseCollector):
    """Collects information about storage devices (HDD/SSD)."""
    
    def collect(self) -> Dict[str, Any]:
        """Collect storage device information."""
        try:
            c = wmi.WMI()
            storage_devices = []
            
            # Get physical disk information
            for disk in c.Win32_DiskDrive():
                device_info = {
                    "model": disk.Model or "Unknown",
                    "manufacturer": disk.Manufacturer or "Unknown",
                    "serial_number": disk.SerialNumber.strip() if disk.SerialNumber else "Unknown",
                    "size_bytes": int(disk.Size) if disk.Size else 0,
                    "size_gb": round(int(disk.Size) / (1024**3), 2) if disk.Size else 0,
                    "interface_type": disk.InterfaceType or "Unknown",
                    "media_type": disk.MediaType or "Unknown",
                    "device_id": disk.DeviceID or "Unknown",
                    "pnp_device_id": disk.PNPDeviceID or "Unknown",
                    "status": disk.Status or "Unknown",
                    "partitions": int(disk.Partitions) if disk.Partitions else 0
                }
                
                # Try to determine if it's SSD or HDD
                if disk.Model:
                    model_lower = disk.Model.lower()
                    if "ssd" in model_lower or "solid state" in model_lower:
                        device_info["drive_type"] = "SSD"
                    elif "nvme" in model_lower:
                        device_info["drive_type"] = "NVMe SSD"
                    else:
                        device_info["drive_type"] = "HDD"
                else:
                    device_info["drive_type"] = "Unknown"
                
                # Get partition information for this disk
                partitions = []
                for partition in c.Win32_DiskPartition():
                    if partition.DiskIndex == disk.Index:
                        partition_info = {
                            "partition_number": int(partition.Index) if partition.Index else "Unknown",
                            "size_bytes": int(partition.Size) if partition.Size else 0,
                            "size_gb": round(int(partition.Size) / (1024**3), 2) if partition.Size else 0,
                            "starting_offset": int(partition.StartingOffset) if partition.StartingOffset else 0,
                            "type": partition.Type or "Unknown",
                            "bootable": bool(partition.Bootable) if partition.Bootable is not None else False,
                            "primary_partition": bool(partition.PrimaryPartition) if partition.PrimaryPartition is not None else False
                        }
                        
                        # Get logical disk information
                        for logical_disk in c.Win32_LogicalDiskToPartition():
                            if logical_disk.Antecedent.Index == partition.Index:
                                for volume in c.Win32_LogicalDisk():
                                    if volume.DeviceID in logical_disk.Dependent.DeviceID:
                                        partition_info.update({
                                            "drive_letter": volume.DeviceID or "Unknown",
                                            "file_system": volume.FileSystem or "Unknown",
                                            "volume_label": volume.VolumeName or "Unknown",
                                            "free_space_bytes": int(volume.FreeSpace) if volume.FreeSpace else 0,
                                            "free_space_gb": round(int(volume.FreeSpace) / (1024**3), 2) if volume.FreeSpace else 0
                                        })
                                        break
                        
                        partitions.append(partition_info)
                
                device_info["partition_details"] = partitions
                storage_devices.append(device_info)
            
            # Get additional disk usage information using psutil
            disk_usage = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    usage_info = {
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "file_system": partition.fstype,
                        "total_bytes": usage.total,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_bytes": usage.used,
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_bytes": usage.free,
                        "free_gb": round(usage.free / (1024**3), 2),
                        "usage_percent": round((usage.used / usage.total) * 100, 2) if usage.total > 0 else 0
                    }
                    disk_usage.append(usage_info)
                except PermissionError:
                    # Skip inaccessible drives
                    continue
            
            return {
                "storage_devices": storage_devices,
                "disk_usage": disk_usage,
                "total_devices": len(storage_devices),
                "status": "success"
            }
            
        except Exception as e:
            self.log_error(f"Error collecting storage information: {str(e)}", exc_info=True)
            return {
                "storage_devices": [],
                "disk_usage": [],
                "total_devices": 0,
                "error": str(e),
                "status": "failed"
            } 