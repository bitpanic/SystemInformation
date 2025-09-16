"""Command Line Interface for System Information Collection."""

import argparse
import sys
import time
from pathlib import Path
from log_config import setup_application_logging, SystemInfoLogger
from system_info_manager import SystemInfoManager


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="System Information Collector for Windows",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --json                     # Collect and export to JSON
  %(prog)s --csv                      # Collect and export to CSV
  %(prog)s --json --csv               # Export to both formats
  %(prog)s --json data.json           # Export to specific JSON file
  %(prog)s --log-level DEBUG          # Enable debug logging
  %(prog)s --no-console-log           # Disable console logging
        """
    )
    
    # Export options
    parser.add_argument('--json', nargs='?', const=True, 
                      help='Export to JSON format (optionally specify filename)')
    parser.add_argument('--csv', nargs='?', const=True,
                      help='Export to CSV format (optionally specify filename)')
    parser.add_argument('--pdf', nargs='?', const=True,
                      help='Export to PDF format (optionally specify filename)')
    
    # Logging options
    parser.add_argument('--log-level', default='INFO',
                      choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                      help='Set console logging level (default: INFO)')
    parser.add_argument('--no-console-log', action='store_true',
                      help='Disable console logging')
    parser.add_argument('--no-file-log', action='store_true',
                      help='Disable file logging')
    
    # Collection options
    parser.add_argument('--quick', action='store_true',
                      help='Quick collection mode (reduced data collection)')
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Verbose output (same as --log-level DEBUG)')
    
    args = parser.parse_args()
    
    # Setup logging based on arguments
    console_level = 'DEBUG' if args.verbose else args.log_level
    enable_console = not args.no_console_log
    enable_file = not args.no_file_log
    
    if enable_file or enable_console:
        setup_application_logging(
            console_level=console_level if enable_console else "CRITICAL", 
            file_level="DEBUG" if enable_file else "CRITICAL"
        )
    
    logger = SystemInfoLogger("CLI")
    logger.log_info(f"CLI Application started with args: {vars(args)}")
    
    if not args.json and not args.csv and not args.pdf:
        print("No export format specified. Use --json, --csv and/or --pdf to export data.")
        print("Use --help for more information.")
        logger.logger.warning("No export format specified")
        sys.exit(1)
    
    try:
        # Initialize the system info manager
        manager = SystemInfoManager(enable_logging=False)  # Logging already setup
        
        # Collect system information
        print("Collecting system information...")
        logger.log_info("Starting system information collection")
        
        collection_start_time = time.time()
        system_info = manager.collect_all_info()
        collection_duration = time.time() - collection_start_time
        
        # Log collection results
        successful = system_info.get('successful_collections', 0)
        failed = system_info.get('failed_collections', 0)
        total = system_info.get('total_collectors', 0)
        
        print(f"Collection completed: {successful}/{total} successful, {failed} failed")
        print(f"Collection time: {collection_duration:.2f} seconds")
        
        logger.log_info(f"Collection completed - Success: {successful}/{total}, Duration: {collection_duration:.2f}s")
        
        if failed > 0:
            logger.logger.warning(f"Some collections failed: {failed}/{total}")
            print("Warning: Some data collection operations failed. Check logs for details.")
        
        # Export data
        export_files = []
        
        if args.json:
            try:
                print("Exporting to JSON...")
                export_start_time = time.time()
                
                json_filename = args.json if isinstance(args.json, str) else None
                exported_json = manager.export_to_json(json_filename)
                
                export_duration = time.time() - export_start_time
                file_size = Path(exported_json).stat().st_size if Path(exported_json).exists() else 0
                
                print(f"JSON exported: {exported_json} ({file_size:,} bytes)")
                export_files.append(exported_json)
                
                logger.log_performance(f"CLI JSON export ({file_size:,} bytes)", export_duration)
                
            except Exception as e:
                logger.logger.error(f"JSON export failed: {e}", exc_info=True)
                print(f"Error exporting JSON: {e}")
        
        if args.csv:
            try:
                print("Exporting to CSV...")
                export_start_time = time.time()
                
                csv_filename = args.csv if isinstance(args.csv, str) else None
                exported_csv = manager.export_to_csv(csv_filename)
                
                export_duration = time.time() - export_start_time
                file_size = Path(exported_csv).stat().st_size if Path(exported_csv).exists() else 0
                
                print(f"CSV exported: {exported_csv} ({file_size:,} bytes)")
                export_files.append(exported_csv)
                
                logger.log_performance(f"CLI CSV export ({file_size:,} bytes)", export_duration)
                
            except Exception as e:
                logger.logger.error(f"CSV export failed: {e}", exc_info=True)
                print(f"Error exporting CSV: {e}")
        
        if args.pdf:
            try:
                print("Exporting to PDF...")
                export_start_time = time.time()
                
                pdf_filename = args.pdf if isinstance(args.pdf, str) else None
                exported_pdf = manager.export_to_pdf(pdf_filename)
                
                export_duration = time.time() - export_start_time
                file_size = Path(exported_pdf).stat().st_size if Path(exported_pdf).exists() else 0
                
                print(f"PDF exported: {exported_pdf} ({file_size:,} bytes)")
                export_files.append(exported_pdf)
                
                logger.log_performance(f"CLI PDF export ({file_size:,} bytes)", export_duration)
                
            except Exception as e:
                logger.logger.error(f"PDF export failed: {e}", exc_info=True)
                print(f"Error exporting PDF: {e}")

        # Summary
        total_duration = time.time() - collection_start_time
        print(f"\nTotal operation time: {total_duration:.2f} seconds")
        
        if export_files:
            print(f"Files created: {len(export_files)}")
            for file in export_files:
                print(f"  - {file}")
        
        logger.log_performance("Complete CLI operation", total_duration)
        logger.log_info(f"CLI operation completed successfully. Files: {export_files}")
        
        # Show log location
        if enable_file:
            from log_config import log_config
            print(f"\nLogs saved to: {log_config.log_dir.absolute()}")
        
        print("System information collection completed successfully!")
        
    except KeyboardInterrupt:
        logger.log_info("CLI operation interrupted by user")
        print("\nOperation interrupted by user.")
        sys.exit(1)
        
    except Exception as e:
        logger.logger.error(f"Critical error in CLI application: {e}", exc_info=True)
        print(f"Critical error: {e}")
        print("Check logs for detailed error information.")
        sys.exit(1)


if __name__ == "__main__":
    main() 