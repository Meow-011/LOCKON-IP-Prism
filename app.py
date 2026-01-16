import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
from datetime import datetime, timedelta
import traceback
import sys
import asyncio
import aiohttp

# --- Import from our custom modules ---
try:
    from dotenv import load_dotenv, set_key
    import database
    import api
    from settings_window import SettingsWindow
    from history_window import HistoryWindow
    from help_window import HelpWindow
except ImportError as e:
    messagebox.showerror("Startup Error", f"A required module is missing: {e}\nPlease run 'pip install -r requirements.txt' and try again.")
    sys.exit(1)

def handle_exception(*args):
    """ Global error handler to catch fatal errors and log them. """
    try:
        # --- Start Enhanced Debugging ---
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        debug_info = []
        debug_info.append("--- INTERNAL DEBUG ---")
        debug_info.append(f"sys.exc_info(): {repr(sys.exc_info())}")
        debug_info.append(f"args received by handler: {repr(args)}")
        
        try:
            error_from_args = "".join(traceback.format_exception(*args))
            debug_info.append("Formatted from args:\n" + error_from_args)
        except Exception as e:
            debug_info.append(f"Could not format from args: {e}")

        try:
            error_from_sys_exc_info = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            debug_info.append("Formatted from sys.exc_info():\n" + error_from_sys_exc_info)
        except Exception as e:
            debug_info.append(f"Could not format from sys.exc_info(): {e}")
        
        debug_info.append("--- END INTERNAL DEBUG ---\n")
        
        final_log_message = "\n".join(debug_info)
        # --- End Enhanced Debugging ---

        messagebox.showerror("A fatal error occurred", 
                             "The application has encountered a critical error and will close.\n\n" 
                             "Please check the crash_log.txt file for details.")
        
        with open("crash_log.txt", "a") as f:
            f.write(f"--- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            f.write(final_log_message) # Write the detailed debug log
            f.write("\n")

    except Exception as e:
        # Fallback for if the handler itself fails
        with open("crash_log.txt", "a") as f:
            f.write(f"--- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            f.write(f"FATAL: The exception handler itself failed: {e}\n")
            f.write(f"Original args: {repr(args)}\n")

sys.excepthook = handle_exception
ctk.CTk.report_callback_exception = lambda exc, val, tb: handle_exception(exc, val, tb)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        load_dotenv()

        self.title("LOCKON IP Prism")
        self.geometry("800x750") # Increased height for new panel
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1) # Adjusted for new panel

        self.selected_file_path = ""
        self.history_win = None
        self.settings_win = None
        self.help_win = None
        self.is_closing = False
        
        self.analysis_thread = None
        self.cancel_requested = threading.Event()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- Header Frame ---
        self.header_frame = ctk.CTkFrame(self, corner_radius=0)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.grid_columnconfigure(1, weight=1)

        self.history_button = ctk.CTkButton(self.header_frame, text="View History & Reports", command=self.open_history_window)
        self.history_button.pack(side="left", padx=10, pady=10)
        
        self.app_title = ctk.CTkLabel(self.header_frame, text="LOCKON IP Prism", font=ctk.CTkFont(size=16, weight="bold"))
        self.app_title.pack(side="left", padx=10, pady=10, expand=True)

        self.help_button = ctk.CTkButton(self.header_frame, text="?", width=40, command=self.open_help_window)
        self.help_button.pack(side="right", padx=5, pady=10)
        
        self.settings_button = ctk.CTkButton(self.header_frame, text="Settings", width=100, command=self.open_settings_window)
        self.settings_button.pack(side="right", padx=5, pady=10)
        
        # --- Dashboard Frame ---
        self.dashboard_frame = ctk.CTkFrame(self)
        self.dashboard_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.dashboard_frame.grid_columnconfigure((0,1,2,3), weight=1)

        self.stat_total_ips = self._create_stat_box(self.dashboard_frame, "Total Unique IPs", "0")
        self.stat_total_ips.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.stat_total_batches = self._create_stat_box(self.dashboard_frame, "Total Batches", "0")
        self.stat_total_batches.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.stat_top_country = self._create_stat_box(self.dashboard_frame, "Top Malicious Country", "N/A")
        self.stat_top_country.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        self.stat_last_analysis = self._create_stat_box(self.dashboard_frame, "Last Analysis", "N/A")
        self.stat_last_analysis.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        # --- API Status Frame ---
        self.api_status_frame = ctk.CTkFrame(self)
        self.api_status_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.api_status_frame.grid_columnconfigure(1, weight=1)

        self.ipqs_status_label = ctk.CTkLabel(self.api_status_frame, text="IPQS:", anchor="w", font=ctk.CTkFont(weight="bold"))
        self.ipqs_status_label.grid(row=0, column=0, padx=(10, 5), pady=2, sticky="w")
        self.ipqs_status_value = ctk.CTkLabel(self.api_status_frame, text="Checking...", anchor="w")
        self.ipqs_status_value.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        self.otx_status_label = ctk.CTkLabel(self.api_status_frame, text="OTX:", anchor="w", font=ctk.CTkFont(weight="bold"))
        self.otx_status_label.grid(row=1, column=0, padx=(10, 5), pady=2, sticky="w")
        self.otx_status_value = ctk.CTkLabel(self.api_status_frame, text="Checking...", anchor="w")
        self.otx_status_value.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        
        self.refresh_api_button = ctk.CTkButton(self.api_status_frame, text="↻", width=35, height=35, command=self.update_api_stats_thread)
        self.refresh_api_button.grid(row=0, column=2, rowspan=2, padx=10, pady=5)

        # --- Input Frame ---
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(1, weight=1)

        self.select_file_button = ctk.CTkButton(self.input_frame, text="Select IP File (.txt, .log)", command=self.select_file)
        self.select_file_button.grid(row=0, column=0, padx=10, pady=10)

        self.file_path_label = ctk.CTkLabel(self.input_frame, text="No file selected", anchor="w")
        self.file_path_label.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.description_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Enter a description for this batch...")
        self.description_entry.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        # --- Control Frame ---
        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
        self.control_frame.grid_columnconfigure(0, weight=1)

        self.start_analysis_button = ctk.CTkButton(self.control_frame, text="Start Analysis", command=self.start_analysis_thread, height=40)
        self.start_analysis_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # --- Log Console Frame ---
        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.grid(row=5, column=0, padx=10, pady=(0, 0), sticky="nsew")
        self.log_frame.grid_rowconfigure(0, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)
        
        self.log_console = ctk.CTkTextbox(self.log_frame, state="disabled", wrap="word")
        self.log_console.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="nsew")
        
        # --- Progress Bar ---
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=6, column=0, padx=10, pady=(5, 10), sticky="ew")
        
        self.check_api_key()
        self.update_dashboard()
        self.update_api_stats_thread()

    def _create_stat_box(self, parent, title, value):
        frame = ctk.CTkFrame(parent, border_width=1)
        frame.grid_columnconfigure(0, weight=1)
        lbl_title = ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=12))
        lbl_title.grid(row=0, column=0, padx=5, pady=(5,0), sticky="ew")
        lbl_value = ctk.CTkLabel(frame, text=value, font=ctk.CTkFont(size=20, weight="bold"))
        lbl_value.grid(row=1, column=0, padx=5, pady=(0,5), sticky="ew")
        frame.value_label = lbl_value
        return frame

    def update_dashboard(self):
        stats = database.get_dashboard_stats()
        self.stat_total_ips.value_label.configure(text=str(stats.get("total_ips", 0)))
        self.stat_total_batches.value_label.configure(text=str(stats.get("total_batches", 0)))
        self.stat_top_country.value_label.configure(text=stats.get("top_country", "N/A"))
        self.stat_last_analysis.value_label.configure(text=stats.get("last_analysis", "N/A"))

    def on_closing(self):
        self.is_closing = True
        self.cancel_requested.set()
        if self.analysis_thread and self.analysis_thread.is_alive():
            self.analysis_thread.join(timeout=1)
        self.destroy()

    def check_api_key(self, from_settings=False):
        load_dotenv(override=True)
        self.api_key_ipqs = api.get_ipqs_api_key()
        self.api_key_otx = api.get_otx_api_key()
        self.cache_duration_hours = int(os.getenv("CACHE_DURATION_HOURS", 24))

        # --- Update API Status Panel ---
        if not self.api_key_ipqs:
            self.ipqs_status_value.configure(text="Key Not Set", text_color="orange")
            self.start_analysis_button.configure(state="disabled")
        else:
            self.ipqs_status_value.configure(text="OK", text_color="green")
            self.start_analysis_button.configure(state="normal")

        if not self.api_key_otx:
            self.otx_status_value.configure(text="Key Not Set", text_color="gray")
        else:
            self.otx_status_value.configure(text="OK", text_color="green")
        
        if from_settings:
            self.update_log(f"[INFO] Cache duration is set to {self.cache_duration_hours} hours.")
            if self.api_key_ipqs:
                 self.update_log("[SUCCESS] Settings applied successfully.")
            self.update_api_stats_thread()

    def update_api_stats_thread(self):
        """ Starts a thread to fetch API stats without freezing the GUI. """
        self.refresh_api_button.configure(state="disabled")
        self.ipqs_status_value.configure(text="Checking...", text_color="gray")
        
        stats_thread = threading.Thread(target=self._run_get_api_stats, daemon=True)
        stats_thread.start()

    def _run_get_api_stats(self):
        """ Worker function to run the async API call. """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def fetch():
                async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
                    return await api.get_ipqs_account_stats_async(session)
            
            result = loop.run_until_complete(fetch())
            loop.close()
            
            if not self.is_closing:
                self.after(0, self._on_api_stats_received, result)
        except Exception as e:
            if not self.is_closing:
                self.after(0, self._on_api_stats_received, {'error': str(e)})

    def _on_api_stats_received(self, result):
        """ Callback to update GUI with API stats. Runs in the main thread. """
        self.refresh_api_button.configure(state="normal")
        if 'error' in result:
            self.ipqs_status_value.configure(text=f"Error: {result['error']}", text_color="red")
        elif 'data' in result:
            credits = result['data'].get('credits_remaining', 'N/A')
            self.ipqs_status_value.configure(text=f"OK (Credits: {credits})", text_color="green")

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Select an IP address file",
            filetypes=(("Text files", "*.txt"), ("Log files", "*.log"), ("All files", "*.*"))
        )
        if file_path:
            self.selected_file_path = file_path
            self.file_path_label.configure(text=os.path.basename(file_path))

    def update_log(self, message, clear=False):
        if self.is_closing: return
        self.log_console.configure(state="normal")
        if clear:
            self.log_console.delete("1.0", "end")
        self.log_console.insert("end", f"{message}\n")
        self.log_console.configure(state="disabled")
        self.log_console.see("end")

    def start_analysis_thread(self):
        if not self.selected_file_path:
            messagebox.showerror("Error", "Please select a file first.")
            return
        
        self.check_api_key()
        if not self.api_key_ipqs:
            messagebox.showerror("API Key Missing", "IPQualityScore API Key is required. Please set it in Settings.")
            return

        self.update_api_stats_thread() # Refresh credits on new analysis
        self.cancel_requested.clear()
        self.start_analysis_button.configure(text="Cancel Analysis", command=self.cancel_analysis, fg_color="#E74C3C", hover_color="#C0392B")
        self.progress_bar.set(0)
        self.update_log("", clear=True)

        self.analysis_thread = threading.Thread(target=self.run_analysis, daemon=True)
        self.analysis_thread.start()

    def cancel_analysis(self):
        """ Signals the analysis thread to stop. """
        self.update_log("[CANCEL] Cancellation requested by user...")
        self.cancel_requested.set()
        self.start_analysis_button.configure(state="disabled", text="Cancelling...")

    def run_analysis(self):
        def safe_update_log(message):
            """ Schedules the update_log method to be called in the main GUI thread. """
            if not self.is_closing:
                self.after(0, self.update_log, message)

        try:
            safe_update_log(f"--- Analysis Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
            
            description = self.description_entry.get()
            file_name = os.path.basename(self.selected_file_path)
            batch_id = database.add_import_batch(datetime.now().isoformat(), file_name, description)

            all_ips_in_file = api.extract_ips_from_file(self.selected_file_path)
            total_ips = len(all_ips_in_file)
            safe_update_log(f"Found {total_ips} unique IPs in '{file_name}'.")

            cache_delta = timedelta(hours=self.cache_duration_hours)
            
            ips_to_query_api = []
            cached_ips = []

            safe_update_log("Checking database for cached data...")

            # --- FIXED: Bulk check for cached IPs to improve performance ---
            cached_records = database.find_ip_details_bulk(all_ips_in_file)
            cached_ips_map = {row['ip_address']: row for row in cached_records}

            for ip in all_ips_in_file:
                if self.cancel_requested.is_set(): break
                details = cached_ips_map.get(ip)
                if details:
                    last_check_str = details['last_api_check']
                    if last_check_str and isinstance(last_check_str, str):
                        last_check_time = datetime.fromisoformat(last_check_str)
                        if datetime.now() - last_check_time < cache_delta:
                            cached_ips.append(details)
                        else:
                            ips_to_query_api.append({'ip': ip, 'details': details})
                    else:
                        ips_to_query_api.append({'ip': ip, 'details': details})
                else:
                    ips_to_query_api.append({'ip': ip, 'details': None})
            
            if self.cancel_requested.is_set(): raise InterruptedError("Cancelled during pre-check")

            processed_count = 0
            if cached_ips:
                safe_update_log(f"Found {len(cached_ips)} fresh IPs in cache.")
                for ip_details in cached_ips:
                    if self.cancel_requested.is_set(): break
                    ip_id = ip_details['id']
                    ip_address = ip_details['ip_address']
                    database.link_ip_to_batch(ip_id, batch_id)
                    processed_count += 1
                    safe_update_log(f"({processed_count}/{total_ips}) Processing IP: {ip_address}... -> [CACHED]")
                    progress = processed_count / total_ips
                    if not self.is_closing: self.after(0, lambda p=progress: self.progress_bar.set(p))
            
            if self.cancel_requested.is_set(): raise InterruptedError("Cancelled after cache processing")

            if ips_to_query_api:
                safe_update_log(f"Querying APIs for {len(ips_to_query_api)} new/stale IPs...")
                
                def progress_callback(ip_info):
                    nonlocal processed_count
                    processed_count += 1
                    safe_update_log(f"({processed_count}/{total_ips}) Processing IP: {ip_info['ip']}...")
                    if 'result' in ip_info:
                        res = ip_info['result']
                        safe_update_log(f" -> IPQS: Score={res['score']}, Country={res['country']}")
                        if self.api_key_otx: safe_update_log(f" -> OTX: Pulses={res['pulses']}")
                    else:
                        error_message = ip_info.get('error', 'Unknown')
                        safe_update_log(f" -> [API ERROR] Could not get IPQS data: {error_message}")
                        if not self.is_closing:
                            self.after(0, self.ipqs_status_value.configure, {'text': f"API Error: {error_message}", 'text_color': "red"})

                    progress = processed_count / total_ips
                    if not self.is_closing: self.after(0, lambda p=progress: self.progress_bar.set(p))

                results = asyncio.run(api.run_concurrent_analysis(ips_to_query_api, self.api_key_otx, progress_callback, self.cancel_requested))
                
                safe_update_log("Saving analysis results to database...")
                for res in results:
                    if self.cancel_requested.is_set(): break
                    if res and 'ip_id' in res:
                        database.link_ip_to_batch(res['ip_id'], batch_id)
            
            if self.cancel_requested.is_set():
                raise InterruptedError("Analysis cancelled by user.")
            else:
                safe_update_log("--- Analysis Complete! ---")
                if not self.is_closing: self.after(0, lambda: self.progress_bar.set(1.0))

        except InterruptedError as e:
            safe_update_log(f"--- {e} ---")
        except Exception:
            if not self.is_closing:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                handle_exception(exc_type, exc_value, exc_traceback)
        finally:
            if not self.is_closing:
                self.after(100, self.analysis_finished)
    
    def analysis_finished(self):
        """Called after analysis is done to reset the button and refresh dashboard."""
        self.start_analysis_button.configure(state="normal", text="Start Analysis", command=self.start_analysis_thread, fg_color=("#3B8ED0", "#1F6AA5"), hover_color=("#36719F", "#144870"))
        self.update_dashboard()
        self.update_api_stats_thread() # Refresh credits after analysis

    def open_settings_window(self):
        if self.settings_win is None or not self.settings_win.winfo_exists():
            self.settings_win = SettingsWindow(self)
            self.settings_win.focus()
        else:
            self.settings_win.focus()

    def open_history_window(self):
        if self.history_win is None or not self.history_win.winfo_exists():
            self.history_win = HistoryWindow(self)
            self.history_win.focus()
        else:
            self.history_win.load_data() 
            self.history_win.focus()

    def open_help_window(self):
        if self.help_win is None or not self.help_win.winfo_exists():
            self.help_win = HelpWindow(self)
            self.help_win.focus()
        else:
            self.help_win.focus()

if __name__ == "__main__":
    database.setup_database()

    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    
    app = App()
    app.mainloop()
