"""Memory information collector."""

import wmi
import psutil
from typing import Dict, Any, List
from .base_collector import BaseCollector


class MemoryCollector(BaseCollector):
    """Collects information about system memory (RAM)."""
    
    def collect(self) -> Dict[str, Any]:
        """Collect memory information."""
        try:
            c = wmi.WMI()
            
            # Get total RAM using psutil
            total_ram_bytes = psutil.virtual_memory().total
            total_ram_gb = round(total_ram_bytes / (1024**3), 2)
            
            # Get detailed memory module information
            memory_modules = []
            total_modules = 0
            
            for memory in c.Win32_PhysicalMemory():
                total_modules += 1
                
                # Get capacity in bytes and convert to GB
                capacity_bytes = int(memory.Capacity) if memory.Capacity else 0
                capacity_gb = round(capacity_bytes / (1024**3), 2)
                
                # Get speed in MHz
                speed_mhz = int(memory.Speed) if memory.Speed else "Unknown"
                
                module_info = {
                    "device_locator": memory.DeviceLocator or "Unknown",
                    "bank_label": memory.BankLabel or "Unknown",
                    "capacity_bytes": capacity_bytes,
                    "capacity_gb": capacity_gb,
                    "speed_mhz": speed_mhz,
                    "manufacturer": memory.Manufacturer or "Unknown",
                    "part_number": memory.PartNumber or "Unknown",
                    "serial_number": memory.SerialNumber or "Unknown",
                    "memory_type": self._get_memory_type(memory.MemoryType) if memory.MemoryType else "Unknown",
                    "form_factor": self._get_form_factor(memory.FormFactor) if memory.FormFactor else "Unknown",
                    "data_width": int(memory.DataWidth) if memory.DataWidth else "Unknown",
                    "total_width": int(memory.TotalWidth) if memory.TotalWidth else "Unknown"
                }
                
                memory_modules.append(module_info)
            
            # Get memory slots information
            memory_slots = []
            for slot in c.Win32_PhysicalMemoryArray():
                slot_info = {
                    "max_capacity_kb": int(slot.MaxCapacity) if slot.MaxCapacity else "Unknown",
                    "max_capacity_gb": round(int(slot.MaxCapacity) / (1024**2), 2) if slot.MaxCapacity else "Unknown",
                    "memory_devices": int(slot.MemoryDevices) if slot.MemoryDevices else "Unknown",
                    "memory_error_correction": self._get_error_correction(slot.MemoryErrorCorrection) if slot.MemoryErrorCorrection else "Unknown"
                }
                memory_slots.append(slot_info)
            
            return {
                "total_ram_bytes": total_ram_bytes,
                "total_ram_gb": total_ram_gb,
                "total_modules": total_modules,
                "memory_modules": memory_modules,
                "memory_slots": memory_slots,
                "status": "success"
            }
            
        except Exception as e:
            self.log_error(f"Error collecting memory information: {str(e)}", exc_info=True)
            return {
                "total_ram_bytes": 0,
                "total_ram_gb": 0,
                "total_modules": 0,
                "memory_modules": [],
                "memory_slots": [],
                "error": str(e),
                "status": "failed"
            }
    
    def _get_memory_type(self, memory_type: int) -> str:
        """Convert memory type code to readable string."""
        memory_types = {
            0: "Unknown",
            1: "Other",
            2: "DRAM",
            3: "Synchronous DRAM",
            4: "Cache DRAM",
            5: "EDO",
            6: "EDRAM",
            7: "VRAM",
            8: "SRAM",
            9: "RAM",
            10: "ROM",
            11: "Flash",
            12: "EEPROM",
            13: "FEPROM",
            14: "EPROM",
            15: "CDRAM",
            16: "3DRAM",
            17: "SDRAM",
            18: "SGRAM",
            19: "RDRAM",
            20: "DDR",
            21: "DDR2",
            22: "DDR2 FB-DIMM",
            24: "DDR3",
            25: "FBD2",
            26: "DDR4",
            27: "LPDDR",
            28: "LPDDR2",
            29: "LPDDR3",
            30: "LPDDR4"
        }
        return memory_types.get(memory_type, f"Unknown ({memory_type})")
    
    def _get_form_factor(self, form_factor: int) -> str:
        """Convert form factor code to readable string."""
        form_factors = {
            0: "Unknown",
            1: "Other",
            2: "SIP",
            3: "DIP",
            4: "ZIP",
            5: "SOJ",
            6: "Proprietary",
            7: "SIMM",
            8: "DIMM",
            9: "TSOP",
            10: "PGA",
            11: "RIMM",
            12: "SODIMM",
            13: "SRIMM",
            14: "SMD",
            15: "SSMP",
            16: "QFP",
            17: "TQFP",
            18: "SOIC",
            19: "LCC",
            20: "PLCC",
            21: "BGA",
            22: "FPBGA",
            23: "LGA"
        }
        return form_factors.get(form_factor, f"Unknown ({form_factor})")
    
    def _get_error_correction(self, error_correction: int) -> str:
        """Convert error correction code to readable string."""
        error_corrections = {
            0: "Reserved",
            1: "Other",
            2: "Unknown",
            3: "None",
            4: "Parity",
            5: "Single-bit ECC",
            6: "Multi-bit ECC",
            7: "CRC"
        }
        return error_corrections.get(error_correction, f"Unknown ({error_correction})") 