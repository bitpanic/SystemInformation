"""Operating System information collector."""

import wmi
import platform
import os as os_module
import getpass
from typing import Dict, Any
from .base_collector import BaseCollector


class OSCollector(BaseCollector):
    """Collects information about the operating system."""
    
    def collect(self) -> Dict[str, Any]:
        """Collect operating system information."""
        try:
            c = wmi.WMI()
            
            # Get OS information from WMI
            os_info = {}
            for os in c.Win32_OperatingSystem():
                os_info = {
                    "name": os.Name.split('|')[0] if os.Name else "Unknown",
                    "version": os.Version or "Unknown",
                    "build_number": os.BuildNumber or "Unknown",
                    "service_pack": os.ServicePackMajorVersion or "0",
                    "architecture": os.OSArchitecture or "Unknown",
                    "manufacturer": os.Manufacturer or "Unknown",
                    "serial_number": os.SerialNumber or "Unknown",
                    "install_date": str(os.InstallDate) if os.InstallDate else "Unknown",
                    "last_boot_up_time": str(os.LastBootUpTime) if os.LastBootUpTime else "Unknown",
                    "system_directory": os.SystemDirectory or "Unknown",
                    "windows_directory": os.WindowsDirectory or "Unknown",
                    "total_virtual_memory_size": int(os.TotalVirtualMemorySize) if os.TotalVirtualMemorySize else 0,
                    "total_visible_memory_size": int(os.TotalVisibleMemorySize) if os.TotalVisibleMemorySize else 0,
                    "free_virtual_memory": int(os.FreeVirtualMemory) if os.FreeVirtualMemory else 0,
                    "free_physical_memory": int(os.FreePhysicalMemory) if os.FreePhysicalMemory else 0
                }
                break  # Usually only one OS entry
            
            # Get computer system information
            computer_info = {}
            for computer in c.Win32_ComputerSystem():
                computer_info = {
                    "computer_name": computer.Name or "Unknown",
                    "domain": computer.Domain or "Unknown",
                    "workgroup": computer.Workgroup or "Unknown",
                    "manufacturer": computer.Manufacturer or "Unknown",
                    "model": computer.Model or "Unknown",
                    "total_physical_memory": int(computer.TotalPhysicalMemory) if computer.TotalPhysicalMemory else 0,
                    "number_of_processors": int(computer.NumberOfProcessors) if computer.NumberOfProcessors else 0,
                    "number_of_logical_processors": int(computer.NumberOfLogicalProcessors) if computer.NumberOfLogicalProcessors else 0,
                    "system_type": computer.SystemType or "Unknown",
                    "primary_owner_name": computer.PrimaryOwnerName or "Unknown"
                }
                break
            
            # Get additional information using platform module
            platform_info = {
                "platform": platform.platform(),
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version()
            }
            
            # Get environment information
            env_info = {
                "hostname": os_module.environ.get('COMPUTERNAME', 'Unknown'),
                "username": getpass.getuser(),
                "user_domain": os_module.environ.get('USERDOMAIN', 'Unknown'),
                "user_profile": os_module.environ.get('USERPROFILE', 'Unknown'),
                "program_files": os_module.environ.get('PROGRAMFILES', 'Unknown'),
                "program_files_x86": os_module.environ.get('PROGRAMFILES(X86)', 'Unknown'),
                "system_root": os_module.environ.get('SYSTEMROOT', 'Unknown'),
                "temp_dir": os_module.environ.get('TEMP', 'Unknown')
            }
            
            # Get Windows edition information
            windows_edition = {}
            try:
                for product in c.Win32_OperatingSystemSKU():
                    windows_edition = {
                        "sku": int(product.SKU) if product.SKU else "Unknown",
                        "edition": self._get_windows_edition(product.SKU) if product.SKU else "Unknown"
                    }
                    break
            except:
                windows_edition = {"sku": "Unknown", "edition": "Unknown"}
            
            return {
                "os_info": os_info,
                "computer_info": computer_info,
                "platform_info": platform_info,
                "environment_info": env_info,
                "windows_edition": windows_edition,
                "status": "success"
            }
            
        except Exception as e:
            self.log_error(f"Error collecting OS information: {str(e)}", exc_info=True)
            return {
                "os_info": {},
                "computer_info": {},
                "platform_info": {},
                "environment_info": {},
                "windows_edition": {},
                "error": str(e),
                "status": "failed"
            }
    
    def _get_windows_edition(self, sku: int) -> str:
        """Convert Windows SKU to edition name."""
        sku_mapping = {
            0: "Undefined",
            1: "Ultimate",
            2: "Home Basic",
            3: "Home Premium",
            4: "Enterprise",
            5: "Home Basic N",
            6: "Business",
            7: "Standard Server",
            8: "Datacenter Server",
            9: "Small Business Server",
            10: "Enterprise Server",
            11: "Starter",
            12: "Datacenter Server Core",
            13: "Standard Server Core",
            14: "Enterprise Server Core",
            15: "Enterprise Server IA64",
            16: "Business N",
            17: "Web Server",
            18: "Cluster Server",
            19: "Home Server",
            20: "Storage Express Server",
            21: "Storage Standard Server",
            22: "Storage Workgroup Server",
            23: "Storage Enterprise Server",
            24: "Server For Small Business",
            25: "Small Business Server Premium",
            26: "Home Premium N",
            27: "Enterprise N",
            28: "Ultimate N",
            29: "Web Server Core",
            30: "Windows Essential Business Server Management Server",
            31: "Windows Essential Business Server Security Server",
            32: "Windows Essential Business Server Messaging Server",
            33: "Server Foundation",
            34: "Windows Home Server 2011",
            35: "Windows Server 2008 without Hyper-V for Windows Essential Server Solutions",
            36: "Server Standard without Hyper-V",
            37: "Server Datacenter without Hyper-V",
            38: "Server Enterprise without Hyper-V",
            39: "Server Datacenter without Hyper-V (core)",
            40: "Server Standard without Hyper-V (core)",
            41: "Server Enterprise without Hyper-V (core)",
            42: "Microsoft Hyper-V Server",
            43: "Storage Server Express (core)",
            44: "Storage Server Standard (core)",
            45: "Storage Server Workgroup (core)",
            46: "Storage Server Enterprise (core)",
            47: "Starter N",
            48: "Professional",
            49: "Professional N",
            50: "Windows Small Business Server 2011 Essentials",
            101: "Home",
            102: "Home N",
            103: "Home Single Language",
            104: "Home Country Specific",
            121: "Education",
            122: "Education N",
            161: "Pro for Workstations",
            162: "Pro for Workstations N"
        }
        return sku_mapping.get(sku, f"Unknown Edition (SKU: {sku})") 