import customtkinter as ctk
from tkinter import messagebox

import database
from multi_compare_report_window import MultiCompareReportWindow

class MultiCompareSetupWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.title("Multi-Batch Comparison Setup")
        self.geometry("400x500")
        self.transient(master)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.label = ctk.CTkLabel(self.main_frame, text="Select Batches to Compare:", font=ctk.CTkFont(weight="bold"))
        self.label.pack(padx=10, pady=(10, 5), anchor="w")
        
        self.checkbox_frame = ctk.CTkScrollableFrame(self.main_frame, label_text="Available Batches")
        self.checkbox_frame.pack(padx=10, pady=5, expand=True, fill="both")

        self.checkboxes = {}
        self.load_batches()

        self.generate_button = ctk.CTkButton(self, text="Generate Comparison Report", command=self.generate_report)
        self.generate_button.grid(row=1, column=0, padx=10, pady=10)

    def load_batches(self):
        """ Loads all batches and creates checkboxes for them. """
        all_batches = database.get_all_batches()
        for batch_data in all_batches:
            var = ctk.StringVar(value="off")
            batch_id = batch_data['id']
            text = f"ID {batch_id}: {batch_data['description'] or batch_data['file_name']}"
            cb = ctk.CTkCheckBox(self.checkbox_frame, text=text, variable=var, onvalue=str(batch_id), offvalue="off")
            cb.pack(padx=10, pady=5, anchor="w")
            self.checkboxes[cb] = var

    def generate_report(self):
        """ Gathers data for selected batches and opens the report window, now fully armored. """
        selected_ids = [int(var.get()) for var in self.checkboxes.values() if var.get() != "off"]
        
        if len(selected_ids) < 2:
            messagebox.showerror("Selection Error", "Please select at least two batches to compare.")
            return

        selected_batch_names = [cb.cget("text") for cb, var in self.checkboxes.items() if var.get() != "off"]
        
        all_ips_by_batch = {}
        for batch_id in selected_ids:
            all_ips_by_batch[batch_id] = database.get_ips_by_batch_ids([batch_id])

        comparison_data = {}
        for batch_id, ips in all_ips_by_batch.items():
            for ip_details in ips:
                try:
                    if not ip_details: continue
                    
                    ip_address = ip_details['ip_address']
                    if not ip_address: continue

                    if ip_address not in comparison_data:
                        comparison_data[ip_address] = {
                            'count': 0, 'batches': set(), 'countries': set(), 'isps': set(),
                            'max_score': 0, 'max_otx': 0
                        }
                    
                    data = comparison_data[ip_address]
                    data['count'] += 1
                    data['batches'].add(batch_id)
                    
                    if ip_details['country']: data['countries'].add(ip_details['country'])
                    if ip_details['isp']: data['isps'].add(ip_details['isp'])
                    
                    current_score = int(ip_details['fraud_score'] or 0)
                    if current_score > data.get('max_score', 0):
                        data['max_score'] = current_score

                    current_otx = int(ip_details['otx_pulses'] or 0)
                    if current_otx > data.get('max_otx', 0):
                        data['max_otx'] = current_otx
                except (IndexError, TypeError, ValueError, KeyError) as e:
                    # Now that we use dicts, this error is less likely, but we keep it for safety
                    print(f"Skipping malformed row during comparison: {dict(ip_details) if ip_details else 'Empty'}. Error: {e}")
                    continue
        
        if not comparison_data:
            messagebox.showinfo("No Data", "No common or unique IPs found in the selected batches to compare.")
            return
            
        MultiCompareReportWindow(self, comparison_data, selected_batch_names)

