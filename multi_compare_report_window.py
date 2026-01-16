import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import tempfile
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import pdf_generator

class MultiCompareReportWindow(ctk.CTkToplevel):
    def __init__(self, master, comparison_data, batch_names):
        super().__init__(master)
        self.title("Multi-Batch Comparison Report")
        self.geometry("1000x700")
        self.transient(master)
        self.grab_set()

        self.data = comparison_data
        self.batch_names = batch_names
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Header ---
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        title_text = "Comparison Report for: " + ", ".join(self.batch_names)
        self.title_label = ctk.CTkLabel(self.header_frame, text=title_text, font=ctk.CTkFont(weight="bold"))
        self.title_label.pack(side="left", padx=10, pady=5)
        
        self.pdf_button = ctk.CTkButton(self.header_frame, text="Generate PDF Report", command=self.generate_pdf_report)
        self.pdf_button.pack(side="right", padx=10, pady=5)

        # --- Treeview for Data ---
        self.columns = ("ip_address", "count", "countries", "isps", "score", "otx")
        self.tree = ttk.Treeview(self, columns=self.columns, show="headings")
        
        self.tree.heading("ip_address", text="IP Address")
        self.tree.heading("count", text="Appeared In # Batches")
        self.tree.heading("countries", text="Countries")
        self.tree.heading("isps", text="ISPs")
        self.tree.heading("score", text="Max Fraud Score")
        self.tree.heading("otx", text="Max OTX Pulses")

        self.tree.column("count", anchor="center", width=150)
        self.tree.column("score", anchor="center", width=120)
        self.tree.column("otx", anchor="center", width=120)

        self.tree.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=1, column=1, sticky="ns")

        self.populate_data()
    
    def populate_data(self):
        """ Populates the treeview with comparison data. """
        self.tree.tag_configure('high_recurrence', background='#E74C3C', foreground='white')
        self.tree.tag_configure('medium_recurrence', background='#F39C12', foreground='black')

        for ip, details in self.data.items():
            if not details: continue

            display_values = (
                ip,
                f"{details.get('count', 0)} / {len(self.batch_names)}",
                ', '.join(c for c in details.get('countries', []) if c),
                ', '.join(i for i in details.get('isps', []) if i),
                details.get('max_score', 0),
                details.get('max_otx', 0)
            )

            tags_to_apply = ()
            count = details.get('count', 0)
            if count == len(self.batch_names):
                tags_to_apply = ('high_recurrence',)
            elif count > 1:
                tags_to_apply = ('medium_recurrence',)

            self.tree.insert("", "end", values=display_values, tags=tags_to_apply)

    def generate_pdf_report(self):
        """ Generates a PDF report of the comparison data """
        if not self.data:
            messagebox.showwarning("No Data", "There is no data to generate a report from.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Save Comparison Report as PDF"
        )
        if not file_path:
            return
            
        try:
            report_title = f"Comparison for: {', '.join(self.batch_names)}"
            
            recurring_ips = {ip: details for ip, details in self.data.items() if details.get('count', 0) > 1}
            
            stats = {
                "total_ips": len(self.data),
                "malicious_count": len(recurring_ips),
            }

            country_counts = {}
            for ip, details in recurring_ips.items():
                for country in details.get('countries', []):
                    if country and country != 'N/A':
                        country_counts[country] = country_counts.get(country, 0) + 1
            
            stats["top_country"] = max(country_counts, key=country_counts.get) if country_counts else "N/A"

            top_malicious_ips_data = sorted(recurring_ips.items(), key=lambda item: (item[1].get('count', 0), item[1].get('max_score', 0)), reverse=True)[:10]
            
            # --- FIXED: Create a list of DICTIONARIES, not lists ---
            top_malicious_ips_for_pdf = []
            for ip, details in top_malicious_ips_data:
                countries_str = ', '.join(c for c in details.get('countries', []) if c)
                isps_str = ', '.join(i for i in details.get('isps', []) if i)
                # Create a dictionary that matches the keys used in pdf_generator.py
                row_dict = {
                    'ip_address': ip,
                    'country': countries_str,
                    'isp': isps_str,
                    'fraud_score': details.get('max_score', 0),
                    'otx_pulses': details.get('max_otx', 0)
                }
                top_malicious_ips_for_pdf.append(row_dict)

            temp_dir = tempfile.gettempdir()
            graph_paths = {}

            fig1 = Figure(figsize=(5, 4), dpi=100)
            ax1 = fig1.add_subplot(111)
            if country_counts:
                ax1.pie(country_counts.values(), labels=country_counts.keys(), autopct='%1.1f%%', startangle=90)
                ax1.set_title('Recurring IP Geolocation')
            else:
                ax1.text(0.5, 0.5, 'No Recurring IPs', ha='center', va='center')
            fig1.tight_layout()
            pie_chart_path = os.path.join(temp_dir, "comp_pie_chart.png")
            fig1.savefig(pie_chart_path)
            graph_paths['pie_chart'] = pie_chart_path
            
            pdf_generator.create_report(file_path, report_title, stats, top_malicious_ips_for_pdf, graph_paths)
            
            messagebox.showinfo("Success", f"PDF report successfully generated at\n{file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF report: {e}")

