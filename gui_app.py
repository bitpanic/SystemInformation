"""GUI Application for System Information Collection."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import json
import time
from datetime import datetime
from log_config import setup_application_logging, SystemInfoLogger, log_config
from system_info_manager import SystemInfoManager


class SystemInfoGUI:
    """Main GUI application for system information collection."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("System Information Collector - Windows")
        self.root.geometry("1200x800")
        
        # Setup logging first
        setup_application_logging(console_level="INFO", file_level="DEBUG")
        self.logger = SystemInfoLogger(__name__)
        self.logger.log_info("GUI Application started")
        
        # Initialize system info manager (with logging already setup)
        self.manager = SystemInfoManager(enable_logging=False)  # Don't reinitialize logging
        self.system_info = {}
        
        # Create GUI components
        self.create_widgets()
        
        # Status
        self.is_collecting = False
        
        # Log update timer
        self.log_update_timer = None
        self.start_log_updates()
    
    def create_widgets(self):
        """Create the main GUI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="System Information Collector - Windows", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.N), padx=(0, 10))
        
        # Collect button
        self.collect_btn = ttk.Button(control_frame, text="Collect System Info", 
                                     command=self.start_collection, width=20)
        self.collect_btn.grid(row=0, column=0, pady=(0, 10))
        
        # Export buttons
        export_frame = ttk.LabelFrame(control_frame, text="Export Options", padding="10")
        export_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.export_json_btn = ttk.Button(export_frame, text="Export as JSON", 
                                         command=self.export_json, width=18, state='disabled')
        self.export_json_btn.grid(row=0, column=0, pady=(0, 5))
        
        self.export_csv_btn = ttk.Button(export_frame, text="Export as CSV", 
                                        command=self.export_csv, width=18, state='disabled')
        self.export_csv_btn.grid(row=1, column=0)

        self.export_pdf_btn = ttk.Button(export_frame, text="Export as PDF", 
                                        command=self.export_pdf, width=18, state='disabled')
        self.export_pdf_btn.grid(row=2, column=0, pady=(5,0))
        
        # Logging controls
        log_frame = ttk.LabelFrame(control_frame, text="Logging Controls", padding="10")
        log_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(log_frame, text="Open Log Directory", 
                  command=self.open_log_directory, width=18).grid(row=0, column=0, pady=(0, 5))
        
        ttk.Button(log_frame, text="Clear Logs", 
                  command=self.clear_logs, width=18).grid(row=1, column=0, pady=(0, 5))
        
        ttk.Button(log_frame, text="Refresh Log View", 
                  command=self.refresh_log_view, width=18).grid(row=2, column=0)
        
        # Progress bar
        self.progress_var = tk.StringVar(value="Ready to collect system information")
        progress_label = ttk.Label(control_frame, textvariable=self.progress_var)
        progress_label.grid(row=3, column=0, pady=(20, 5))
        
        self.progress_bar = ttk.Progressbar(control_frame, mode='indeterminate')
        self.progress_bar.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Summary frame
        summary_frame = ttk.LabelFrame(control_frame, text="Summary", padding="10")
        summary_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.summary_text = scrolledtext.ScrolledText(summary_frame, width=30, height=12, 
                                                     wrap=tk.WORD, state='disabled')
        self.summary_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Main content area with tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create tabs
        self.create_tabs()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready - Logging initialized")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def create_tabs(self):
        """Create tabs for different information categories."""
        self.tabs = {}
        
        tab_names = [
            ("Overview", "overview"),
            ("PCI Devices", "pci"),
            ("USB Devices", "usb"),
            ("Memory", "memory"),
            ("Storage", "storage"),
            ("Operating System", "operating_system"),
            ("Software", "software"),
            ("CodeMeter Dongles", "dongles"),
            ("System Info", "system"),
            ("Logs", "logs")  # New logs tab
        ]
        
        for tab_name, tab_key in tab_names:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=tab_name)
            
            if tab_key == "logs":
                # Special handling for logs tab
                self.create_logs_tab(frame)
            else:
                # Create scrolled text widget for other tabs
                text_widget = scrolledtext.ScrolledText(frame, wrap=tk.WORD, state='disabled')
                text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                self.tabs[tab_key] = text_widget
    
    def create_logs_tab(self, frame):
        """Create the logs tab with log viewer and controls."""
        # Create notebook for different log types
        log_notebook = ttk.Notebook(frame)
        log_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Main application log
        main_log_frame = ttk.Frame(log_notebook)
        log_notebook.add(main_log_frame, text="Application Log")
        
        self.main_log_text = scrolledtext.ScrolledText(main_log_frame, wrap=tk.WORD, 
                                                      font=("Consolas", 9))
        self.main_log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Error log
        error_log_frame = ttk.Frame(log_notebook)
        log_notebook.add(error_log_frame, text="Error Log")
        
        self.error_log_text = scrolledtext.ScrolledText(error_log_frame, wrap=tk.WORD, 
                                                       font=("Consolas", 9))
        self.error_log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Collection log
        collection_log_frame = ttk.Frame(log_notebook)
        log_notebook.add(collection_log_frame, text="Collection Log")
        
        self.collection_log_text = scrolledtext.ScrolledText(collection_log_frame, wrap=tk.WORD, 
                                                           font=("Consolas", 9))
        self.collection_log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Log control frame
        log_control_frame = ttk.Frame(frame)
        log_control_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(log_control_frame, text="Auto-refresh:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.auto_refresh_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_control_frame, text="Enabled", 
                       variable=self.auto_refresh_var).pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Button(log_control_frame, text="Refresh Now", 
                  command=self.refresh_log_view).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(log_control_frame, text="Save Log", 
                  command=self.save_log).pack(side=tk.LEFT, padx=(0, 10))
        
        # Store log widgets for updates
        self.log_widgets = {
            'main': self.main_log_text,
            'error': self.error_log_text,
            'collection': self.collection_log_text
        }
    
    def start_log_updates(self):
        """Start automatic log updates."""
        self.update_logs()
        
    def update_logs(self):
        """Update log displays."""
        if self.auto_refresh_var.get():
            try:
                # Update main application log
                main_log_content = self.read_log_file("system_info_app.log")
                self.update_log_widget(self.main_log_text, main_log_content)
                
                # Update error log
                error_log_content = self.read_log_file("system_info_errors.log")
                self.update_log_widget(self.error_log_text, error_log_content)
                
                # Update collection log
                collection_log_content = self.read_log_file("collections.log")
                self.update_log_widget(self.collection_log_text, collection_log_content)
                
            except Exception as e:
                pass  # Silently handle log reading errors
        
        # Schedule next update
        self.log_update_timer = self.root.after(2000, self.update_logs)  # Update every 2 seconds
    
    def read_log_file(self, log_filename: str, max_lines: int = 500) -> str:
        """Read content from a specific log file."""
        try:
            log_file_path = log_config.log_dir / log_filename
            if log_file_path.exists():
                with open(log_file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Return last max_lines
                    return ''.join(lines[-max_lines:])
            return f"Log file {log_filename} not found."
        except Exception as e:
            return f"Error reading {log_filename}: {e}"
    
    def update_log_widget(self, widget, content: str):
        """Update a log text widget with new content."""
        try:
            # Store current scroll position
            current_pos = widget.yview()
            at_bottom = current_pos[1] >= 0.98  # Check if scrolled to bottom
            
            # Update content
            widget.config(state='normal')
            widget.delete(1.0, tk.END)
            widget.insert(1.0, content)
            widget.config(state='disabled')
            
            # Auto-scroll to bottom if user was already at bottom
            if at_bottom:
                widget.see(tk.END)
                
        except Exception:
            pass  # Silently handle widget update errors
    
    def refresh_log_view(self):
        """Manually refresh log views."""
        self.update_logs()
        self.logger.log_info("Log views refreshed manually")
    
    def open_log_directory(self):
        """Open the log directory in file explorer."""
        try:
            import subprocess
            import os
            log_dir = str(log_config.log_dir.absolute())
            if os.name == 'nt':  # Windows
                subprocess.Popen(['explorer', log_dir])
            self.logger.log_info(f"Opened log directory: {log_dir}")
        except Exception as e:
            self.logger.logger.error(f"Failed to open log directory: {e}")
            messagebox.showerror("Error", f"Failed to open log directory: {e}")
    
    def clear_logs(self):
        """Clear log files after confirmation."""
        if messagebox.askyesno("Clear Logs", "Are you sure you want to clear all log files?"):
            try:
                log_files = log_config.get_log_files()
                cleared_count = 0
                
                for log_file in log_files:
                    try:
                        log_file.unlink()
                        cleared_count += 1
                    except Exception:
                        pass
                
                self.logger.log_info(f"Cleared {cleared_count} log files")
                messagebox.showinfo("Success", f"Cleared {cleared_count} log files")
                
                # Refresh log views
                self.refresh_log_view()
                
            except Exception as e:
                self.logger.logger.error(f"Failed to clear logs: {e}")
                messagebox.showerror("Error", f"Failed to clear logs: {e}")
    
    def save_log(self):
        """Save current log content to a file."""
        try:
            # Get current tab
            current_tab = self.log_widgets.get('main')  # Default to main log
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".log",
                filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")],
                title="Save Log File"
            )
            
            if filename and current_tab:
                content = current_tab.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.logger.log_info(f"Log saved to: {filename}")
                messagebox.showinfo("Success", f"Log saved to: {filename}")
                
        except Exception as e:
            self.logger.logger.error(f"Failed to save log: {e}")
            messagebox.showerror("Error", f"Failed to save log: {e}")
    
    def start_collection(self):
        """Start system information collection in a separate thread."""
        if self.is_collecting:
            self.logger.log_info("Collection already in progress, ignoring request")
            return
        
        self.logger.log_info("Starting system information collection from GUI")
        
        self.is_collecting = True
        self.collect_btn.config(state='disabled')
        self.export_json_btn.config(state='disabled')
        self.export_csv_btn.config(state='disabled')
        
        self.progress_var.set("Collecting system information...")
        self.progress_bar.start()
        
        # Clear previous data
        self.clear_all_tabs()
        
        # Start collection in separate thread
        thread = threading.Thread(target=self.collect_info_thread)
        thread.daemon = True
        thread.start()
    
    def collect_info_thread(self):
        """Thread function for collecting system information."""
        try:
            collection_start_time = time.time()
            self.logger.log_info("Collection thread started")
            
            self.system_info = self.manager.collect_all_info()
            
            collection_duration = time.time() - collection_start_time
            self.logger.log_performance("GUI collection thread", collection_duration)
            
            # Update GUI in main thread
            self.root.after(0, self.collection_completed)
            
        except Exception as e:
            self.logger.logger.error(f"Error during collection thread: {str(e)}", exc_info=True)
            self.root.after(0, lambda: self.collection_error(str(e)))
    
    def collection_completed(self):
        """Handle completion of system information collection."""
        self.is_collecting = False
        self.progress_bar.stop()
        self.progress_var.set("Collection completed successfully")
        self.status_var.set("Collection completed")
        
        # Enable export buttons
        self.export_json_btn.config(state='normal')
        self.export_csv_btn.config(state='normal')
        self.export_pdf_btn.config(state='normal')
        self.collect_btn.config(state='normal')
        
        # Update all tabs with collected information
        self.update_all_tabs()
        
        # Update summary
        self.update_summary()
        
        # Log completion stats
        if self.system_info:
            successful = self.system_info.get('successful_collections', 0)
            failed = self.system_info.get('failed_collections', 0)
            duration = self.system_info.get('total_collection_duration_seconds', 0)
            
            self.logger.log_info(f"Collection completed - Success: {successful}, Failed: {failed}, Duration: {duration}s")
        
        messagebox.showinfo("Success", "System information collection completed successfully!")
    
    def collection_error(self, error_msg):
        """Handle error during collection."""
        self.is_collecting = False
        self.progress_bar.stop()
        self.progress_var.set("Collection failed")
        self.status_var.set("Error occurred")
        self.collect_btn.config(state='normal')
        
        self.logger.logger.error(f"Collection failed: {error_msg}")
        messagebox.showerror("Error", f"Failed to collect system information:\n{error_msg}")
    
    def clear_all_tabs(self):
        """Clear content from all tabs."""
        for text_widget in self.tabs.values():
            text_widget.config(state='normal')
            text_widget.delete(1.0, tk.END)
            text_widget.config(state='disabled')
    
    def update_all_tabs(self):
        """Update all tabs with collected information."""
        if not self.system_info:
            return
        
        # Overview tab
        self.update_overview_tab()
        
        # Individual category tabs
        categories = ['pci', 'usb', 'memory', 'storage', 'operating_system', 'software', 'system']
        
        for category in categories:
            if category in self.system_info and category in self.tabs:
                self.update_tab_content(category, self.system_info[category])
        
        # Update dongles tab separately
        if 'dongles' in self.tabs:
            dongle_data = self.manager.get_dongle_info()
            self.update_tab_content('dongles', dongle_data)
    
    def update_overview_tab(self):
        """Update the overview tab with summary information."""
        if 'overview' not in self.tabs:
            return
        
        text_widget = self.tabs['overview']
        text_widget.config(state='normal')
        text_widget.delete(1.0, tk.END)
        
        # Get summary
        summary = self.manager.get_summary()
        
        overview_text = f"""System Information Overview
Collection Time: {summary.get('collection_timestamp', 'Unknown')}
Collection Status: {summary.get('collection_status', 'Unknown')}

=== SUMMARY ===
"""
        
        if 'summary' in summary:
            for key, value in summary['summary'].items():
                overview_text += f"{key.replace('_', ' ').title()}: {value}\n"
        
        # Add SPIN software status prominently
        if 'software' in self.system_info and 'spin_info' in self.system_info['software']:
            spin_info = self.system_info['software']['spin_info']
            overview_text += f"\n=== SPIN SOFTWARE STATUS ===\n"
            overview_text += f"Installed: {spin_info.get('installed', 'Unknown')}\n"
            overview_text += f"Version: {spin_info.get('version', 'Not found')}\n"
            overview_text += f"License: {spin_info.get('license_number', 'Not found')}\n"
            overview_text += f"Install Path: {spin_info.get('install_path', 'Not found')}\n"
        
        # Add CodeMeter dongle status
        dongle_data = self.manager.get_dongle_info()
        overview_text += f"\n=== CODEMETER DONGLES ===\n"
        if 'error' in dongle_data:
            overview_text += f"Status: {dongle_data['error']}\n"
        else:
            total_dongles = dongle_data.get('total_dongles', 0)
            overview_text += f"Total Dongles Found: {total_dongles}\n"
            overview_text += f"CodeMeter Service: {'Running' if dongle_data.get('codemeter_service_running') else 'Not Running'}\n"
            overview_text += f"CodeMeter Installed: {'Yes' if dongle_data.get('codemeter_installed') else 'No'}\n"
            
            if total_dongles > 0:
                overview_text += f"\nDongle Details:\n"
                for i, dongle in enumerate(dongle_data.get('dongles', []), 1):
                    overview_text += f"  {i}. {dongle.get('device_name', 'Unknown')} - Serial: {dongle.get('serial_number', 'Unknown')}\n"
                    if dongle.get('version'):
                        overview_text += f"     Version: {dongle.get('version')}\n"
                    if dongle.get('status'):
                        overview_text += f"     Status: {dongle.get('status')}\n"
        
        text_widget.insert(tk.END, overview_text)
        text_widget.config(state='disabled')
    
    def update_tab_content(self, category, data):
        """Update a specific tab with data."""
        if category not in self.tabs:
            return
        
        text_widget = self.tabs[category]
        text_widget.config(state='normal')
        text_widget.delete(1.0, tk.END)
        
        # For software tab, exclude dongle data to avoid duplication and show filtered list
        if category == 'software' and isinstance(data, dict):
            filtered_data = data.copy()
            filtered_data.pop('codemeter_dongles', None)
            filtered_data.pop('_separate_dongles', None)
            # Prefer showing installed_programs_filtered for clarity
            if 'installed_programs_filtered' in filtered_data:
                filtered_data['installed_programs'] = filtered_data['installed_programs_filtered']
                filtered_data.pop('installed_programs_filtered', None)
            formatted_data = json.dumps(filtered_data, indent=2, ensure_ascii=False)
        else:
            # Format and display the data
            formatted_data = json.dumps(data, indent=2, ensure_ascii=False)
        
        text_widget.insert(tk.END, formatted_data)
        text_widget.config(state='disabled')
    
    def update_summary(self):
        """Update the summary text widget."""
        self.summary_text.config(state='normal')
        self.summary_text.delete(1.0, tk.END)
        
        summary = self.manager.get_summary()
        
        summary_text = "=== SYSTEM SUMMARY ===\n\n"
        
        if 'summary' in summary:
            for key, value in summary['summary'].items():
                summary_text += f"{key.replace('_', ' ').title()}:\n  {value}\n\n"
        
        self.summary_text.insert(tk.END, summary_text)
        self.summary_text.config(state='disabled')
    
    def export_json(self):
        """Export system information to JSON file."""
        if not self.system_info:
            self.logger.logger.warning("No system information to export")
            messagebox.showwarning("Warning", "No system information collected yet!")
            return
        
        self.logger.log_info("Starting JSON export from GUI")
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save System Information as JSON"
        )
        
        if filename:
            try:
                export_start_time = time.time()
                actual_filename = self.manager.export_to_json(filename)
                export_duration = time.time() - export_start_time
                
                self.logger.log_performance(f"GUI JSON export", export_duration)
                messagebox.showinfo("Success", f"System information exported to:\n{actual_filename}")
                
            except Exception as e:
                self.logger.logger.error(f"JSON export failed: {str(e)}", exc_info=True)
                messagebox.showerror("Error", f"Failed to export JSON file:\n{str(e)}")
    
    def export_csv(self):
        """Export system information to CSV file."""
        if not self.system_info:
            self.logger.logger.warning("No system information to export")
            messagebox.showwarning("Warning", "No system information collected yet!")
            return
        
        self.logger.log_info("Starting CSV export from GUI")
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save System Information as CSV"
        )
        
        if filename:
            try:
                export_start_time = time.time()
                actual_filename = self.manager.export_to_csv(filename)
                export_duration = time.time() - export_start_time
                
                self.logger.log_performance(f"GUI CSV export", export_duration)
                messagebox.showinfo("Success", f"System information exported to:\n{actual_filename}")
                
            except Exception as e:
                self.logger.logger.error(f"CSV export failed: {str(e)}", exc_info=True)
                messagebox.showerror("Error", f"Failed to export CSV file:\n{str(e)}")

    def export_pdf(self):
        """Export system information to PDF file."""
        if not self.system_info:
            self.logger.logger.warning("No system information to export")
            messagebox.showwarning("Warning", "No system information collected yet!")
            return
        
        self.logger.log_info("Starting PDF export from GUI")
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Save System Information as PDF"
        )
        
        if filename:
            try:
                export_start_time = time.time()
                actual_filename = self.manager.export_to_pdf(filename)
                export_duration = time.time() - export_start_time
                
                self.logger.log_performance(f"GUI PDF export", export_duration)
                messagebox.showinfo("Success", f"System information exported to:\n{actual_filename}")
                
            except Exception as e:
                self.logger.logger.error(f"PDF export failed: {str(e)}", exc_info=True)
                messagebox.showerror("Error", f"Failed to export PDF file:\n{str(e)}")


def main():
    """Main function to run the GUI application."""
    try:
        root = tk.Tk()
        app = SystemInfoGUI(root)
        
        # Handle application shutdown
        def on_closing():
            if app.log_update_timer:
                root.after_cancel(app.log_update_timer)
            app.logger.log_info("GUI Application shutting down")
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
        
    except Exception as e:
        print(f"Critical error starting GUI application: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 