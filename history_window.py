import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import tkinter
import pyperclip
import tempfile
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import database
from edit_window import EditWindow
from multi_compare_setup_window import MultiCompareSetupWindow
from recurrence_report_window import RecurrenceReportWindow
import pdf_generator

class HistoryWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master

        self.title("History & Reports")
        self.geometry("1200x700")
        self.transient(master)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.batch_label = ctk.CTkLabel(self.top_frame, text="Filter by Batch:")
        self.batch_label.pack(side="left", padx=(10, 5))
        self.batch_combobox = ctk.CTkComboBox(self.top_frame, values=[], command=self.filter_by_batch)
        self.batch_combobox.pack(side="left", padx=5)

        self.reset_button = ctk.CTkButton(self.top_frame, text="Reset Filter", width=100, command=self.reset_filter)
        self.reset_button.pack(side="left", padx=5)
        
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.search_data)
        self.search_entry = ctk.CTkEntry(self.top_frame, placeholder_text="Search...", textvariable=self.search_var)
        self.search_entry.pack(side="left", padx=10, expand=True, fill="x")

        self.action_frame = ctk.CTkFrame(self)
        self.action_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        self.multi_compare_button = ctk.CTkButton(self.action_frame, text="Multi-Batch Compare", command=self.open_multi_compare_setup)
        self.multi_compare_button.pack(side="left", padx=5)
        
        self.recurrence_report_button = ctk.CTkButton(self.action_frame, text="Recurrence Report", command=self.open_recurrence_report)
        self.recurrence_report_button.pack(side="left", padx=5)

        self.pdf_report_button = ctk.CTkButton(self.action_frame, text="Generate PDF Report", command=self.generate_pdf_report)
        self.pdf_report_button.pack(side="left", padx=5)

        self.export_button = ctk.CTkButton(self.action_frame, text="Export to CSV", command=self.export_to_csv)
        self.export_button.pack(side="left", padx=5)

        self.delete_selected_button = ctk.CTkButton(self.action_frame, text="Delete Selected Batch", fg_color="#E74C3C", hover_color="#C0392B", command=self.delete_selected_batch)
        self.delete_selected_button.pack(side="right", padx=5)

        self.columns = ("id", "ip_address", "country", "is_malicious", "fraud_score", "isp", "organization", "otx_pulses", "tags", "notes")
        self.tree = ttk.Treeview(self, columns=self.columns, show="headings")
        
        for col in self.columns:
            self.tree.heading(col, text=col.replace("_", " ").title(), command=lambda c=col: self.sort_by_column(c, False))
            self.tree.column(col, width=100, anchor="w")
        
        self.tree.column("ip_address", width=120)
        self.tree.column("isp", width=150)
        self.tree.column("organization", width=150)
        
        self.tree.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="nsew")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=2, column=1, sticky="ns")
        
        self.context_menu = tkinter.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Copy IP Address", command=self.copy_ip)
        self.context_menu.add_command(label="Edit Details (Tags/Notes)", command=self.edit_details)

        self.tree.bind("<Button-3>", self.show_context_menu)
        
        self.load_batches()
        self.load_data()

    def load_batches(self):
        current_selection = self.batch_combobox.get()
        self.batches = database.get_all_batches()
        batch_display_list = ["All Batches"] + [f"{b['id']}: {b['description'] or b['file_name']}" for b in self.batches]
        self.batch_combobox.configure(values=batch_display_list)
        if current_selection in batch_display_list:
            self.batch_combobox.set(current_selection)
        else:
            self.batch_combobox.set("All Batches")

    def load_data(self, batch_id=None):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.all_data = database.get_ips_by_batch_ids([batch_id] if batch_id else [])
        self.display_data(self.all_data)
        self.load_batches()
        if batch_id is None:
            self.batch_combobox.set("All Batches")

    def display_data(self, data):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree.tag_configure('high_risk', background='#E74C3C', foreground='white')
        self.tree.tag_configure('medium_risk', background='#F39C12', foreground='black')
        for row in data:
            if not row: continue
            tags_to_apply = ()
            score = row['fraud_score'] or 0
            if score > 85:
                tags_to_apply = ('high_risk',)
            elif score >= 75:
                tags_to_apply = ('medium_risk',)
            try:
                values_tuple = tuple(row[col] for col in self.columns)
                self.tree.insert("", "end", values=values_tuple, tags=tags_to_apply)
            except (KeyError, IndexError) as e:
                print(f"Skipping row with mismatched data: {dict(row)}. Error: {e}")

    def filter_by_batch(self, choice):
        if choice == "All Batches":
            self.load_data()
        else:
            selected_batch_id = int(choice.split(":")[0])
            self.all_data = database.get_ips_by_batch_ids([selected_batch_id])
            self.display_data(self.all_data)
            self.batch_combobox.set(choice)
        self.search_var.set("")

    def reset_filter(self):
        self.batch_combobox.set("All Batches")
        self.load_data()
        self.search_var.set("")

    def search_data(self, *args):
        query = self.search_var.get().lower()
        if not query:
            self.display_data(self.all_data)
            return

        filtered_data = [
            row for row in self.all_data
            if any(query in str(row[key]).lower() for key in row.keys() if row[key] is not None)
        ]
        self.display_data(filtered_data)

    def sort_by_column(self, col, reverse):
        data_list = []
        for k in self.tree.get_children(''):
            try:
                val = self.tree.set(k, col)
                data_list.append((val, k))
            except tkinter.TclError:
                print(f"Warning: Could not find column '{col}' for sorting.")
                return
        try:
            data_list.sort(key=lambda t: float(t[0] if t[0] and t[0] != 'None' else 0), reverse=reverse)
        except (ValueError, TypeError):
            data_list.sort(key=lambda t: str(t[0]), reverse=reverse)
        for index, (val, k) in enumerate(data_list):
            self.tree.move(k, '', index)
        self.tree.heading(col, command=lambda c=col: self.sort_by_column(c, not reverse))

    def show_context_menu(self, event):
        selection = self.tree.identify_row(event.y)
        if selection:
            self.tree.selection_set(selection)
            self.context_menu.post(event.x_root, event.y_root)

    def copy_ip(self):
        selected_item = self.tree.selection()
        if selected_item:
            item_values = self.tree.item(selected_item[0])['values']
            try:
                ip_address = item_values[self.columns.index('ip_address')]
                pyperclip.copy(ip_address)
                messagebox.showinfo("Copied", f"IP Address '{ip_address}' copied to clipboard.")
            except (IndexError, ValueError):
                messagebox.showerror("Error", "Could not determine the IP address from the selected row.")

    def edit_details(self):
        selected_item = self.tree.selection()
        if selected_item:
            item_id = self.tree.item(selected_item[0])['values'][0]
            item_values_dict = None
            for row in self.all_data:
                if row['id'] == item_id:
                    item_values_dict = dict(row)
                    break
            if item_values_dict is None:
                messagebox.showerror("Error", "Could not find details for the selected item.")
                return
            current_batch_choice = self.batch_combobox.get()
            batch_id = None
            if current_batch_choice != "All Batches":
                batch_id = int(current_batch_choice.split(":")[0])
            EditWindow(self, item_values_dict, lambda: self.load_data(batch_id))

    def open_multi_compare_setup(self):
        MultiCompareSetupWindow(self)
        
    def open_recurrence_report(self):
        all_batches = database.get_all_batches()
        if len(all_batches) < 2:
            messagebox.showinfo("Not Enough Data", "You need at least two import batches to generate a recurrence report.")
            return
        latest_batch_id = all_batches[0]['id']
        previous_batch_ids = [b['id'] for b in all_batches[1:]]
        latest_ips_raw = database.get_ips_by_batch_ids([latest_batch_id])
        previous_ips_raw = database.get_ips_by_batch_ids(previous_batch_ids)
        latest_ip_set = {ip['ip_address'] for ip in latest_ips_raw if ip}
        previous_ip_set = {ip['ip_address'] for ip in previous_ips_raw if ip}
        recurring_ip_addresses = latest_ip_set.intersection(previous_ip_set)
        recurring_ip_details = [ip for ip in latest_ips_raw if ip and ip['ip_address'] in recurring_ip_addresses]
        if not recurring_ip_details:
            messagebox.showinfo("No Recurrence", "No recurring IPs found between the latest batch and all previous batches.")
            return
        RecurrenceReportWindow(self, data=recurring_ip_details)

    def delete_selected_batch(self):
        selected_batch_str = self.batch_combobox.get()
        if not selected_batch_str or selected_batch_str == "All Batches":
            messagebox.showwarning("No Batch Selected", "Please select a specific batch from the filter to delete.")
            return
        batch_id_to_delete = int(selected_batch_str.split(":")[0])
        if messagebox.askyesno("Confirm Deletion", f"ARE YOU SURE?\n\nThis will permanently delete all data associated with batch:\n'{selected_batch_str}'.\n\nThis action cannot be undone."):
            try:
                database.delete_batch(batch_id_to_delete)
                messagebox.showinfo("Success", "The selected batch has been deleted.")
                self.reset_filter()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete batch: {e}")

    def export_to_csv(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save data as CSV"
        )
        if not file_path:
            return
        try:
            import csv
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(self.columns)
                for row in self.all_data:
                    writer.writerow(tuple(row[col] for col in self.columns))
            messagebox.showinfo("Success", f"Data successfully exported to\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {e}")

    def generate_pdf_report(self):
        current_data = self.all_data
        if not current_data:
            messagebox.showwarning("No Data", "There is no data to generate a report from.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Save report as PDF"
        )
        if not file_path:
            return
        try:
            report_title = self.batch_combobox.get()
            stats = {
                "total_ips": len(current_data),
                "malicious_count": sum(1 for row in current_data if row['is_malicious'] == 1),
            }
            country_counts = {}
            for row in current_data:
                if row['is_malicious'] == 1 and row['country'] and row['country'] != 'N/A':
                    country_counts[row['country']] = country_counts.get(row['country'], 0) + 1
            stats["top_country"] = max(country_counts, key=country_counts.get) if country_counts else "N/A"
            top_malicious_ips = sorted(current_data, key=lambda row: row['fraud_score'] or 0, reverse=True)[:10]
            temp_dir = tempfile.gettempdir()
            graph_paths = {}
            fig1 = Figure(figsize=(5, 4), dpi=100)
            ax1 = fig1.add_subplot(111)
            if country_counts:
                ax1.pie(country_counts.values(), labels=country_counts.keys(), autopct='%1.1f%%', startangle=90)
                ax1.set_title('Malicious IP Distribution')
            else:
                ax1.text(0.5, 0.5, 'No Malicious IPs', ha='center', va='center')
            fig1.tight_layout()
            pie_chart_path = os.path.join(temp_dir, "pie_chart.png")
            fig1.savefig(pie_chart_path)
            graph_paths['pie_chart'] = pie_chart_path
            fig2 = Figure(figsize=(4, 3), dpi=100)
            ax2 = fig2.add_subplot(111)
            benign_count = stats['total_ips'] - stats['malicious_count']
            ax2.bar(['Malicious', 'Benign'], [stats['malicious_count'], benign_count], color=['#e74c3c', '#2ecc71'])
            ax2.set_title('Security Assessment')
            ax2.set_ylabel('Count')
            fig2.tight_layout()
            bar_chart_path = os.path.join(temp_dir, "bar_chart.png")
            fig2.savefig(bar_chart_path)
            graph_paths['bar_chart'] = bar_chart_path
            pdf_generator.create_report(file_path, report_title, stats, top_malicious_ips, graph_paths)
            messagebox.showinfo("Success", f"PDF report successfully generated at\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF report: {e}")