"""Base collector class for system information gathering."""

import logging
import time
import pythoncom
from abc import ABC, abstractmethod
from typing import Dict, Any
from log_config import SystemInfoLogger


class BaseCollector(ABC):
    """Abstract base class for all system information collectors."""
    
    def __init__(self):
        self.logger = SystemInfoLogger(self.__class__.__name__)
        self.collection_start_time = None
        
    @abstractmethod
    def collect(self) -> Dict[str, Any]:
        """Collect system information and return as dictionary."""
        pass
    
    def safe_collect(self) -> Dict[str, Any]:
        """Safely collect information with error handling and performance tracking."""
        collector_name = self.__class__.__name__.replace('Collector', '')
        
        # Initialize COM for WMI (needed when running in threads)
        try:
            pythoncom.CoInitialize()
        except:
            pass  # Already initialized
        
        # Start performance tracking
        self.collection_start_time = time.time()
        self.logger.log_collection_start(collector_name)
        
        try:
            # Perform the actual collection
            result = self.collect()
            
            # Calculate performance metrics
            duration = time.time() - self.collection_start_time
            self.logger.log_performance(f"{collector_name} collection", duration)
            
            # Log success with item count if available
            item_count = self._get_item_count(result)
            self.logger.log_collection_success(collector_name, item_count)
            
            # Add metadata to result
            result['collection_metadata'] = {
                'collection_duration_seconds': round(duration, 3),
                'collection_timestamp': time.time(),
                'collector_version': getattr(self, 'VERSION', '1.0'),
                'status': 'success'
            }
            
            return result
            
        except Exception as e:
            # Calculate duration even for failed collections
            duration = time.time() - self.collection_start_time if self.collection_start_time else 0
            
            # Log the error with full traceback
            self.logger.log_collection_error(collector_name, e)
            
            # Return error information
            error_result = {
                "error": str(e), 
                "status": "failed",
                "error_type": type(e).__name__,
                "collection_metadata": {
                    'collection_duration_seconds': round(duration, 3),
                    'collection_timestamp': time.time(),
                    'collector_version': getattr(self, 'VERSION', '1.0'),
                    'status': 'failed'
                }
            }
            
            return error_result
        finally:
            # Cleanup COM
            try:
                pythoncom.CoUninitialize()
            except:
                pass
    
    def _get_item_count(self, result: Dict[str, Any]) -> int:
        """
        Extract item count from collection result.
        Override in subclasses for specific counting logic.
        """
        if isinstance(result, dict):
            # Common patterns for counting items
            for key in result:
                if isinstance(result[key], list):
                    return len(result[key])
                elif key.endswith('_count') and isinstance(result[key], int):
                    return result[key]
        return None
    
    def log_debug_info(self, message: str, data: Any = None):
        """Log debug information during collection."""
        if data:
            self.logger.log_debug(f"{message}: {data}")
        else:
            self.logger.log_debug(message)
    
    def log_debug(self, message: str):
        """Log debug message during collection."""
        self.logger.log_debug(message)
    
    def log_warning(self, message: str):
        """Log warning during collection."""
        self.logger.log_warning(message)
    
    def log_info(self, message: str):
        """Log info message during collection."""
        self.logger.log_info(message)
    
    def log_error(self, message: str, exc_info: bool = False):
        """Log error message during collection."""
        self.logger.log_error(message, exc_info=exc_info) 