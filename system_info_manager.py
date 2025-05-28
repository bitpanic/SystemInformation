"""Main system information manager."""

import json
import csv
import os
import time
from datetime import datetime
from typing import Dict, Any
from log_config import setup_application_logging, SystemInfoLogger
from collectors.pci_collector import PCICollector
from collectors.usb_collector import USBCollector
from collectors.memory_collector import MemoryCollector
from collectors.storage_collector import StorageCollector
from collectors.os_collector import OSCollector
from collectors.software_collector import SoftwareCollector
from collectors.system_collector import SystemCollector


class SystemInfoManager:
    """Manages system information collection and export."""
    
    def __init__(self, enable_logging: bool = True, log_level: str = "INFO"):
        # Setup logging first
        if enable_logging:
            setup_application_logging(console_level=log_level, file_level="DEBUG")
        
        self.logger = SystemInfoLogger(__name__)
        self.logger.log_info("SystemInfoManager initialized")
        
        self.collectors = {
            "pci": PCICollector(),
            "usb": USBCollector(),
            "memory": MemoryCollector(),
            "storage": StorageCollector(),
            "operating_system": OSCollector(),
            "software": SoftwareCollector(),
            "system": SystemCollector()
        }
        self.system_info = {}
    
    def collect_all_info(self) -> Dict[str, Any]:
        """Collect information from all collectors."""
        overall_start_time = time.time()
        self.logger.log_info("Starting comprehensive system information collection")
        
        self.system_info = {
            "collection_timestamp": datetime.now().isoformat(),
            "collection_status": "in_progress",
            "collection_start_time": overall_start_time
        }
        
        successful_collections = 0
        failed_collections = 0
        
        for name, collector in self.collectors.items():
            self.logger.log_info(f"Starting {name} information collection")
            try:
                collection_result = collector.safe_collect()
                self.system_info[name] = collection_result
                
                # Check if collection was successful
                if collection_result.get("status") != "failed":
                    successful_collections += 1
                    self.logger.log_info(f"Successfully collected {name} information")
                else:
                    failed_collections += 1
                    self.logger.logger.warning(f"Collection failed for {name}: {collection_result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                failed_collections += 1
                error_msg = f"Unexpected error collecting {name} information: {str(e)}"
                self.logger.logger.error(error_msg, exc_info=True)
                self.system_info[name] = {
                    "error": str(e), 
                    "status": "failed",
                    "error_type": type(e).__name__
                }
        
        # Calculate overall collection time
        overall_duration = time.time() - overall_start_time
        
        # Update final status
        self.system_info.update({
            "collection_status": "completed",
            "collection_end_time": time.time(),
            "total_collection_duration_seconds": round(overall_duration, 3),
            "successful_collections": successful_collections,
            "failed_collections": failed_collections,
            "total_collectors": len(self.collectors)
        })
        
        self.logger.log_performance("Complete system information collection", overall_duration)
        self.logger.log_info(f"System information collection completed - Success: {successful_collections}, Failed: {failed_collections}")
        
        return self.system_info
    
    def export_to_json(self, filename: str = None) -> str:
        """Export system information to JSON file."""
        start_time = time.time()
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"system_info_{timestamp}.json"
        
        self.logger.log_info(f"Starting JSON export to {filename}")
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.system_info, f, indent=2, ensure_ascii=False, default=str)
            
            duration = time.time() - start_time
            file_size = os.path.getsize(filename) if os.path.exists(filename) else 0
            
            self.logger.log_export_operation("JSON", filename, True)
            self.logger.log_performance(f"JSON export ({file_size} bytes)", duration)
            
            return filename
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.log_export_operation("JSON", filename, False)
            self.logger.logger.error(f"Failed to export to JSON file {filename}: {str(e)}", exc_info=True)
            raise
    
    def export_to_csv(self, filename: str = None) -> str:
        """Export system information to CSV file (flattened format)."""
        start_time = time.time()
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"system_info_{timestamp}.csv"
        
        self.logger.log_info(f"Starting CSV export to {filename}")
        
        try:
            flattened_data = self._flatten_data(self.system_info)
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                if flattened_data:
                    # Collect all possible fieldnames from all rows
                    all_fieldnames = set()
                    for row in flattened_data:
                        all_fieldnames.update(row.keys())
                    
                    # Sort fieldnames for consistent output, with 'category' first
                    fieldnames = sorted(all_fieldnames)
                    if 'category' in fieldnames:
                        fieldnames.remove('category')
                        fieldnames.insert(0, 'category')
                    
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(flattened_data)
            
            duration = time.time() - start_time
            file_size = os.path.getsize(filename) if os.path.exists(filename) else 0
            row_count = len(flattened_data) if flattened_data else 0
            
            self.logger.log_export_operation("CSV", filename, True)
            self.logger.log_performance(f"CSV export ({file_size} bytes, {row_count} rows)", duration)
            
            return filename
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.log_export_operation("CSV", filename, False)
            self.logger.logger.error(f"Failed to export to CSV file {filename}: {str(e)}", exc_info=True)
            raise
    
    def _flatten_data(self, data: Dict[str, Any], parent_key: str = '') -> list:
        """Flatten nested dictionary data for CSV export."""
        flattened_rows = []
        
        def flatten_dict(d: dict, parent: str = '') -> dict:
            items = []
            for k, v in d.items():
                new_key = f"{parent}_{k}" if parent else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key).items())
                elif isinstance(v, list):
                    for i, item in enumerate(v):
                        if isinstance(item, dict):
                            items.extend(flatten_dict(item, f"{new_key}_{i}").items())
                        else:
                            items.append((f"{new_key}_{i}", str(item)))
                else:
                    items.append((new_key, str(v)))
            return dict(items)
        
        # Create separate rows for different categories
        categories = ['pci', 'usb', 'memory', 'storage', 'operating_system', 'software', 'system']
        
        for category in categories:
            if category in data and isinstance(data[category], dict):
                category_data = data[category]
                
                # Handle different structures
                if category == 'pci' and 'pci_devices' in category_data:
                    for device in category_data['pci_devices']:
                        row = {'category': 'PCI Device'}
                        row.update(flatten_dict(device))
                        flattened_rows.append(row)
                
                elif category == 'usb' and 'usb_devices' in category_data:
                    for device in category_data['usb_devices']:
                        row = {'category': 'USB Device'}
                        row.update(flatten_dict(device))
                        flattened_rows.append(row)
                
                elif category == 'memory' and 'memory_modules' in category_data:
                    for module in category_data['memory_modules']:
                        row = {'category': 'Memory Module'}
                        row.update(flatten_dict(module))
                        flattened_rows.append(row)
                
                elif category == 'storage' and 'storage_devices' in category_data:
                    for device in category_data['storage_devices']:
                        row = {'category': 'Storage Device'}
                        row.update(flatten_dict(device))
                        flattened_rows.append(row)
                
                elif category == 'system' and 'gpu_info' in category_data:
                    for gpu in category_data['gpu_info']:
                        row = {'category': 'GPU'}
                        row.update(flatten_dict(gpu))
                        flattened_rows.append(row)
                
                else:
                    # For other categories, create a single row
                    row = {'category': category.replace('_', ' ').title()}
                    row.update(flatten_dict(category_data))
                    flattened_rows.append(row)
        
        return flattened_rows
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of collected information."""
        if not self.system_info:
            return {"error": "No data collected yet"}
        
        summary = {
            "collection_timestamp": self.system_info.get("collection_timestamp", "Unknown"),
            "collection_status": self.system_info.get("collection_status", "Unknown"),
            "summary": {}
        }
        
        # PCI summary
        if "pci" in self.system_info and "pci_devices" in self.system_info["pci"]:
            summary["summary"]["pci_devices_count"] = len(self.system_info["pci"]["pci_devices"])
        
        # USB summary
        if "usb" in self.system_info and "usb_devices" in self.system_info["usb"]:
            summary["summary"]["usb_devices_count"] = len(self.system_info["usb"]["usb_devices"])
        
        # Memory summary
        if "memory" in self.system_info and "total_ram_gb" in self.system_info["memory"]:
            summary["summary"]["total_ram_gb"] = self.system_info["memory"]["total_ram_gb"]
            summary["summary"]["memory_modules_count"] = self.system_info["memory"].get("total_modules", 0)
        
        # Storage summary
        if "storage" in self.system_info and "storage_devices" in self.system_info["storage"]:
            summary["summary"]["storage_devices_count"] = len(self.system_info["storage"]["storage_devices"])
        
        # OS summary
        if "operating_system" in self.system_info and "os_info" in self.system_info["operating_system"]:
            os_info = self.system_info["operating_system"]["os_info"]
            summary["summary"]["os_name"] = os_info.get("name", "Unknown")
            summary["summary"]["os_version"] = os_info.get("version", "Unknown")
        
        # SPIN software summary
        if "software" in self.system_info and "spin_info" in self.system_info["software"]:
            spin_info = self.system_info["software"]["spin_info"]
            summary["summary"]["spin_installed"] = spin_info.get("installed", False)
            summary["summary"]["spin_version"] = spin_info.get("version", "Not found")
        
        # CPU summary
        if "system" in self.system_info and "cpu_info" in self.system_info["system"]:
            cpu_info = self.system_info["system"]["cpu_info"]
            summary["summary"]["cpu_name"] = cpu_info.get("name", "Unknown")
            summary["summary"]["cpu_cores"] = cpu_info.get("number_of_cores", 0)
        
        # GPU summary
        if "system" in self.system_info and "gpu_info" in self.system_info["system"]:
            gpu_count = len(self.system_info["system"]["gpu_info"])
            summary["summary"]["gpu_count"] = gpu_count
            if gpu_count > 0:
                summary["summary"]["primary_gpu"] = self.system_info["system"]["gpu_info"][0].get("name", "Unknown")
        
        return summary 