import customtkinter as ctk
from tkinter import ttk, messagebox

class RecurrenceReportWindow(ctk.CTkToplevel):
    def __init__(self, master, data):
        super().__init__(master)
        self.title("Recurrence Report (Latest vs. All Previous)")
        self.geometry("1200x600")
        self.transient(master)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Header ---
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        self.title_label = ctk.CTkLabel(self.header_frame, text=f"Found {len(data)} Recurring IPs", font=ctk.CTkFont(weight="bold"))
        self.title_label.pack(padx=10, pady=5)

        # --- Treeview for Data ---
        self.columns = ("ip_address", "country", "fraud_score", "isp", "organization", "otx_pulses", "tags")
        self.tree = ttk.Treeview(self, columns=self.columns, show="headings")
        
        for col in self.columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
        
        self.tree.column("ip_address", width=120)
        self.tree.column("isp", width=150)
        self.tree.column("organization", width=150)
        self.tree.column("tags", width=150)

        self.tree.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=1, column=1, sticky="ns")

        self.populate_data(data)

    def populate_data(self, data):
        """ Populates the treeview with recurring IP details, now fully armored. """
        self.tree.tag_configure('high_risk', background='#E74C3C', foreground='white')
        self.tree.tag_configure('medium_risk', background='#F39C12', foreground='black')

        for row in data:
            if not row: continue

            # --- Fully Armored Data Preparation for Display ---
            display_values = (
                row['ip_address'] or "",
                row['country'] or "N/A",
                row['fraud_score'] or 0,
                row['isp'] or "",
                row['organization'] or "",
                row['otx_pulses'] or 0,
                row['tags'] or ""
            )

            tags_to_apply = ()
            score = display_values[2] 
            if score > 85:
                tags_to_apply = ('high_risk',)
            elif score >= 75:
                tags_to_apply = ('medium_risk',)

            self.tree.insert("", "end", values=display_values, tags=tags_to_apply)

