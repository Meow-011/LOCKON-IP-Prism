import customtkinter as ctk
from tkinter import filedialog, messagebox
import csv

class ComparisonReportWindow(ctk.CTkToplevel):
    def __init__(self, master, recurring_ips, batch_a_name, batch_b_name):
        super().__init__(master)
        self.title("Batch Comparison Report")
        self.geometry("600x450")
        self.transient(master)
        self.grab_set()

        self.recurring_ips = recurring_ips
        self.batch_a_name = batch_a_name.split(' (')[0] # เอาเฉพาะชื่อไฟล์
        self.batch_b_name = batch_b_name.split(' (')[0]

        # --- Widgets ---
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        title_text = f"Found {len(self.recurring_ips)} recurring IPs between:\n- {self.batch_a_name}\n- {self.batch_b_name}"
        self.title_label = ctk.CTkLabel(self.main_frame, text=title_text, justify="left")
        self.title_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.results_textbox = ctk.CTkTextbox(self.main_frame, state="disabled", wrap="none")
        self.results_textbox.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

        self.export_button = ctk.CTkButton(self.main_frame, text="Export to CSV", command=self.export_to_csv)
        self.export_button.grid(row=2, column=0, padx=10, pady=10)
        
        self.populate_results()

    def populate_results(self):
        """แสดงรายการ IP ที่ซ้ำซ้อนใน Textbox"""
        self.results_textbox.configure(state="normal")
        self.results_textbox.delete("1.0", "end")
        if self.recurring_ips:
            self.results_textbox.insert("1.0", "\n".join(self.recurring_ips))
        else:
            self.results_textbox.insert("1.0", "No recurring IPs found between the selected batches.")
        self.results_textbox.configure(state="disabled")

    def export_to_csv(self):
        """บันทึกรายการ IP ที่ซ้ำซ้อนเป็นไฟล์ CSV"""
        if not self.recurring_ips:
            messagebox.showinfo("Info", "There are no IPs to export.", parent=self)
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Recurrence Report",
            initialfile=f"comparison_{self.batch_a_name}_vs_{self.batch_b_name}.csv"
        )

        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["Recurring IP Address"])  # Header
                    for ip in self.recurring_ips:
                        writer.writerow([ip])
                messagebox.showinfo("Success", f"Report successfully saved to:\n{file_path}", parent=self)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}", parent=self)
