"""General system information collector."""

import wmi
import psutil
from typing import Dict, Any, List
from .base_collector import BaseCollector


class SystemCollector(BaseCollector):
    """Collects general system information including CPU, GPU, and motherboard."""
    
    def collect(self) -> Dict[str, Any]:
        """Collect general system information."""
        try:
            c = wmi.WMI()
            
            result = {
                "cpu_info": self._get_cpu_info(c),
                "gpu_info": self._get_gpu_info(c),
                "motherboard_info": self._get_motherboard_info(c),
                "system_performance": self._get_performance_info(),
                "status": "success"
            }
            return result
            
        except Exception as e:
            self.log_error(f"Error collecting system information: {str(e)}", exc_info=True)
            return {
                "cpu_info": {},
                "gpu_info": [],
                "motherboard_info": {},
                "system_performance": {},
                "error": str(e),
                "status": "failed"
            }
    
    def _get_cpu_info(self, wmi_connection) -> Dict[str, Any]:
        """Get CPU information."""
        try:
            cpu_info = {}
            
            for processor in wmi_connection.Win32_Processor():
                cpu_info = {
                    "name": processor.Name or "Unknown",
                    "manufacturer": processor.Manufacturer or "Unknown",
                    "max_clock_speed_mhz": int(processor.MaxClockSpeed) if processor.MaxClockSpeed else 0,
                    "number_of_cores": int(processor.NumberOfCores) if processor.NumberOfCores else 0,
                    "number_of_logical_processors": int(processor.NumberOfLogicalProcessors) if processor.NumberOfLogicalProcessors else 0,
                    "socket_designation": processor.SocketDesignation or "Unknown",
                    "status": processor.Status or "Unknown"
                }
                break
            
            return cpu_info
            
        except Exception as e:
            self.log_error(f"Error collecting CPU information: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    def _get_gpu_info(self, wmi_connection) -> List[Dict[str, Any]]:
        """Get GPU information."""
        try:
            gpu_list = []
            
            for gpu in wmi_connection.Win32_VideoController():
                gpu_info = {
                    "name": gpu.Name or "Unknown",
                    "adapter_ram_mb": round(int(gpu.AdapterRAM) / (1024**2), 2) if gpu.AdapterRAM else 0,
                    "driver_version": gpu.DriverVersion or "Unknown",
                    "status": gpu.Status or "Unknown"
                }
                gpu_list.append(gpu_info)
            
            return gpu_list
            
        except Exception as e:
            self.log_error(f"Error collecting GPU information: {str(e)}", exc_info=True)
            return [{"error": str(e)}]
    
    def _get_motherboard_info(self, wmi_connection) -> Dict[str, Any]:
        """Get motherboard information."""
        try:
            motherboard_info = {}
            
            for baseboard in wmi_connection.Win32_BaseBoard():
                motherboard_info = {
                    "manufacturer": baseboard.Manufacturer or "Unknown",
                    "product": baseboard.Product or "Unknown",
                    "serial_number": baseboard.SerialNumber or "Unknown",
                    "version": baseboard.Version or "Unknown"
                }
                break
            
            return motherboard_info
            
        except Exception as e:
            self.log_error(f"Error collecting motherboard information: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    def _get_performance_info(self) -> Dict[str, Any]:
        """Get current system performance information."""
        try:
            memory = psutil.virtual_memory()
            
            performance_info = {
                "memory_percent_used": memory.percent,
                "cpu_percent": psutil.cpu_percent(interval=1)
            }
            
            return performance_info
            
        except Exception as e:
            self.log_error(f"Error collecting performance information: {str(e)}", exc_info=True)
            return {"error": str(e)} 