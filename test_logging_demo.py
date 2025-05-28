"""Demonstration script for the enhanced logging system."""

import time
from log_config import setup_application_logging, SystemInfoLogger, log_config


def demonstrate_logging():
    """Demonstrate the logging functionality."""
    
    print("System Information Collector - Logging Demonstration")
    print("=" * 60)
    
    # Setup logging
    print("1. Setting up comprehensive logging...")
    setup_application_logging(console_level="DEBUG", file_level="DEBUG")
    
    # Create a logger
    logger = SystemInfoLogger("Demo")
    
    print(f"2. Log files will be created in: {log_config.log_dir.absolute()}")
    
    # Demonstrate different log levels
    print("\n3. Demonstrating different log levels...")
    
    logger.logger.debug("This is a DEBUG message - detailed technical information")
    logger.logger.info("This is an INFO message - general information")
    logger.logger.warning("This is a WARNING message - something might be wrong")
    logger.logger.error("This is an ERROR message - something went wrong")
    
    # Demonstrate collection logging
    print("\n4. Demonstrating collection-specific logging...")
    
    logger.log_collection_start("Demo Collector")
    time.sleep(0.1)  # Simulate collection work
    logger.log_collection_success("Demo Collector", 42)
    
    # Demonstrate performance logging
    print("\n5. Demonstrating performance logging...")
    
    start_time = time.time()
    time.sleep(0.2)  # Simulate some work
    duration = time.time() - start_time
    logger.log_performance("Demo operation", duration)
    
    # Demonstrate export logging
    print("\n6. Demonstrating export logging...")
    
    logger.log_export_operation("JSON", "demo_file.json", True)
    logger.log_export_operation("CSV", "demo_file.csv", True)
    
    # Demonstrate error logging with exception
    print("\n7. Demonstrating error logging with exception...")
    
    try:
        # Simulate an error
        raise ValueError("This is a simulated error for demonstration")
    except Exception as e:
        logger.log_collection_error("Demo Collector", e)
    
    # Show log file information
    print("\n8. Log file information:")
    log_files = log_config.get_log_files()
    for log_file in log_files:
        try:
            size = log_file.stat().st_size
            print(f"   - {log_file.name}: {size} bytes")
        except:
            print(f"   - {log_file.name}: Error reading file")
    
    # Demonstrate log content reading
    print("\n9. Sample log content (last 10 lines):")
    try:
        content = log_config.get_latest_log_content(max_lines=10)
        print("   " + "\n   ".join(content.split('\n')[-10:]))
    except Exception as e:
        print(f"   Error reading log content: {e}")
    
    print("\n" + "=" * 60)
    print("Logging demonstration completed!")
    print(f"Check the logs directory: {log_config.log_dir.absolute()}")
    print("Files created:")
    print("  - system_info_app.log (main application log)")
    print("  - system_info_errors.log (error-only log)")
    print("  - collections.log (collection-specific log)")


if __name__ == "__main__":
    demonstrate_logging() 