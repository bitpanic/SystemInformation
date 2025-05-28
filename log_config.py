"""Logging configuration for System Information Collector."""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path


class LogConfig:
    """Centralized logging configuration for the application."""
    
    def __init__(self, log_dir: str = "logs", max_log_size: int = 10485760, backup_count: int = 5):
        """
        Initialize logging configuration.
        
        Args:
            log_dir: Directory to store log files
            max_log_size: Maximum size of each log file in bytes (default: 10MB)
            backup_count: Number of backup log files to keep
        """
        self.log_dir = Path(log_dir)
        self.max_log_size = max_log_size
        self.backup_count = backup_count
        self.setup_log_directory()
        
    def setup_log_directory(self):
        """Create log directory if it doesn't exist."""
        try:
            self.log_dir.mkdir(exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create log directory {self.log_dir}: {e}")
            self.log_dir = Path(".")  # Fallback to current directory
    
    def setup_logging(self, console_level: str = "INFO", file_level: str = "DEBUG", 
                     enable_console: bool = True, enable_file: bool = True):
        """
        Setup comprehensive logging configuration.
        
        Args:
            console_level: Log level for console output (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            file_level: Log level for file output
            enable_console: Whether to enable console logging
            enable_file: Whether to enable file logging
        """
        # Clear any existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Set root logger level to DEBUG to catch everything
        root_logger.setLevel(logging.DEBUG)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        handlers = []
        
        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, console_level.upper()))
            console_handler.setFormatter(simple_formatter)
            handlers.append(console_handler)
        
        # File handlers
        if enable_file:
            # Main application log
            main_log_file = self.log_dir / "system_info_app.log"
            main_handler = logging.handlers.RotatingFileHandler(
                main_log_file, maxBytes=self.max_log_size, backupCount=self.backup_count,
                encoding='utf-8'
            )
            main_handler.setLevel(getattr(logging, file_level.upper()))
            main_handler.setFormatter(detailed_formatter)
            handlers.append(main_handler)
            
            # Error-only log
            error_log_file = self.log_dir / "system_info_errors.log"
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file, maxBytes=self.max_log_size, backupCount=self.backup_count,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(detailed_formatter)
            handlers.append(error_handler)
            
            # Collection-specific log (daily rotation)
            collection_log_file = self.log_dir / "collections.log"
            collection_handler = logging.handlers.TimedRotatingFileHandler(
                collection_log_file, when='midnight', interval=1, backupCount=30,
                encoding='utf-8'
            )
            collection_handler.setLevel(logging.INFO)
            collection_handler.setFormatter(detailed_formatter)
            # Add filter for collection-related logs
            collection_handler.addFilter(CollectionLogFilter())
            handlers.append(collection_handler)
        
        # Add all handlers to root logger
        for handler in handlers:
            root_logger.addHandler(handler)
        
        # Log startup message
        logger = logging.getLogger(__name__)
        logger.info("="*80)
        logger.info("System Information Collector - Logging Started")
        logger.info(f"Log directory: {self.log_dir.absolute()}")
        logger.info(f"Console logging: {'Enabled' if enable_console else 'Disabled'} ({console_level})")
        logger.info(f"File logging: {'Enabled' if enable_file else 'Disabled'} ({file_level})")
        logger.info("="*80)
        
        return handlers
    
    def get_log_files(self) -> list:
        """Get list of all log files in the log directory."""
        try:
            return list(self.log_dir.glob("*.log*"))
        except Exception:
            return []
    
    def get_latest_log_content(self, max_lines: int = 1000) -> str:
        """Get the content of the latest main log file."""
        try:
            main_log_file = self.log_dir / "system_info_app.log"
            if main_log_file.exists():
                with open(main_log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Return last max_lines
                    return ''.join(lines[-max_lines:])
            return "No log file found."
        except Exception as e:
            return f"Error reading log file: {e}"
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up log files older than specified days."""
        try:
            import time
            current_time = time.time()
            cutoff_time = current_time - (days_to_keep * 24 * 60 * 60)
            
            cleaned_count = 0
            for log_file in self.log_dir.glob("*.log*"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    cleaned_count += 1
            
            logger = logging.getLogger(__name__)
            logger.info(f"Cleaned up {cleaned_count} old log files (older than {days_to_keep} days)")
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error during log cleanup: {e}")


class CollectionLogFilter(logging.Filter):
    """Filter to capture collection-related log messages."""
    
    def filter(self, record):
        """Filter collection-related messages."""
        collection_keywords = [
            'collection', 'collecting', 'collect', 'export', 'save',
            'pci', 'usb', 'memory', 'storage', 'system', 'software'
        ]
        
        message = record.getMessage().lower()
        return any(keyword in message for keyword in collection_keywords)


class SystemInfoLogger:
    """Convenience class for logging system information operations."""
    
    def __init__(self, name: str = None):
        self.logger = logging.getLogger(name or __name__)
    
    def log_info(self, message: str):
        """Log info message."""
        self.logger.info(message)
    
    def log_debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)
    
    def log_warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)
    
    def log_error(self, message: str, exc_info: bool = False):
        """Log error message."""
        self.logger.error(message, exc_info=exc_info)
    
    def log_collection_start(self, collector_name: str):
        """Log the start of a collection operation."""
        self.logger.info(f"Starting collection: {collector_name}")
    
    def log_collection_success(self, collector_name: str, item_count: int = None):
        """Log successful completion of collection."""
        if item_count is not None:
            self.logger.info(f"Collection completed successfully: {collector_name} - {item_count} items collected")
        else:
            self.logger.info(f"Collection completed successfully: {collector_name}")
    
    def log_collection_error(self, collector_name: str, error: Exception):
        """Log collection errors with full traceback."""
        self.logger.error(f"Collection failed: {collector_name} - {str(error)}", exc_info=True)
    
    def log_export_operation(self, export_type: str, filename: str, success: bool = True):
        """Log export operations."""
        if success:
            self.logger.info(f"Export successful: {export_type} -> {filename}")
        else:
            self.logger.error(f"Export failed: {export_type} -> {filename}")
    
    def log_system_info(self, info_type: str, details: dict):
        """Log system information details."""
        self.logger.debug(f"System info collected - {info_type}: {details}")
    
    def log_performance(self, operation: str, duration: float):
        """Log performance metrics."""
        self.logger.info(f"Performance - {operation}: {duration:.2f} seconds")


# Global instance for easy access
log_config = LogConfig()


def setup_application_logging(console_level: str = "INFO", file_level: str = "DEBUG"):
    """
    Setup logging for the application.
    
    Args:
        console_level: Log level for console output
        file_level: Log level for file output
    """
    return log_config.setup_logging(console_level=console_level, file_level=file_level)


def get_logger(name: str = None) -> SystemInfoLogger:
    """
    Get a logger instance for system information operations.
    
    Args:
        name: Logger name (uses module name if not provided)
    
    Returns:
        SystemInfoLogger instance
    """
    return SystemInfoLogger(name) 