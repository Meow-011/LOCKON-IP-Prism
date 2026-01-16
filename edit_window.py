import customtkinter as ctk
from tkinter import messagebox
import database

class EditWindow(ctk.CTkToplevel):
    def __init__(self, master, item_values_dict, callback):
        super().__init__(master)
        self.title("Edit IP Details")
        self.geometry("400x300")
        self.transient(master)
        self.grab_set()

        self.item_data = item_values_dict
        self.callback = callback
        
        self.grid_columnconfigure(1, weight=1)

        self.ip_label = ctk.CTkLabel(self, text="IP Address:")
        self.ip_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.ip_value = ctk.CTkLabel(self, text=self.item_data.get('ip_address', 'N/A'))
        self.ip_value.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        self.tags_label = ctk.CTkLabel(self, text="Tags (comma-separated):")
        self.tags_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.tags_entry = ctk.CTkEntry(self, width=250)
        self.tags_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        self.tags_entry.insert(0, self.item_data.get('tags') or "")

        self.notes_label = ctk.CTkLabel(self, text="Notes:")
        self.notes_label.grid(row=2, column=0, padx=10, pady=10, sticky="nw")
        self.notes_text = ctk.CTkTextbox(self, height=100)
        self.notes_text.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        self.notes_text.insert("1.0", self.item_data.get('notes') or "")
        
        self.save_button = ctk.CTkButton(self, text="Save Changes", command=self.save_changes)
        self.save_button.grid(row=3, column=0, columnspan=2, padx=10, pady=20)

    def save_changes(self):
        """ Saves the updated tags and notes to the database. """
        new_tags = self.tags_entry.get()
        new_notes = self.notes_text.get("1.0", "end-1c")
        ip_id = self.item_data.get('id')

        if ip_id is None:
            messagebox.showerror("Error", "Cannot save changes: Item ID is missing.")
            return

        try:
            database.update_ip_details(ip_id, new_tags, new_notes)
            messagebox.showinfo("Success", "Details updated successfully.")
            self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to save changes: {e}")

