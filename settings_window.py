import customtkinter as ctk
from tkinter import messagebox
from dotenv import find_dotenv, set_key
import os
import database

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master

        self.title("Settings")
        self.geometry("500x400") # Increased height for cache setting
        self.transient(master)
        self.grab_set()

        self.grid_columnconfigure(1, weight=1)

        # --- IPQualityScore API Key ---
        self.ipqs_label = ctk.CTkLabel(self, text="IPQualityScore API Key:")
        self.ipqs_label.grid(row=0, column=0, padx=10, pady=(20, 5), sticky="w")
        self.ipqs_entry = ctk.CTkEntry(self, width=300)
        self.ipqs_entry.grid(row=0, column=1, padx=10, pady=(20, 5), sticky="ew")

        # --- AlienVault OTX API Key ---
        self.otx_label = ctk.CTkLabel(self, text="AlienVault OTX API Key:")
        self.otx_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.otx_entry = ctk.CTkEntry(self, width=300)
        self.otx_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # --- NEW: Cache Duration Setting ---
        self.cache_label = ctk.CTkLabel(self, text="Cache Duration (hours):")
        self.cache_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.cache_entry = ctk.CTkEntry(self, width=100)
        self.cache_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        # --- Save Button ---
        self.save_button = ctk.CTkButton(self, text="Save and Apply", command=self.save_settings)
        self.save_button.grid(row=3, column=0, columnspan=2, padx=10, pady=20)

        # --- Danger Zone ---
        self.danger_frame = ctk.CTkFrame(self, fg_color="transparent", border_color="#E74C3C", border_width=1)
        self.danger_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.danger_frame.grid_columnconfigure(0, weight=1)
        
        self.danger_label = ctk.CTkLabel(self.danger_frame, text="Danger Zone", text_color="#E74C3C", font=ctk.CTkFont(weight="bold"))
        self.danger_label.grid(row=0, column=0, padx=10, pady=(5,0))

        self.clear_button = ctk.CTkButton(self.danger_frame, text="Clear All Data", fg_color="#E74C3C", hover_color="#C0392B", command=self.clear_all_data)
        self.clear_button.grid(row=1, column=0, padx=10, pady=10)


        self.load_existing_settings()

    def load_existing_settings(self):
        """ Loads current settings into the entry fields. """
        self.ipqs_entry.insert(0, self.master.api_key_ipqs or "")
        self.otx_entry.insert(0, self.master.api_key_otx or "")
        self.cache_entry.insert(0, str(self.master.cache_duration_hours))


    def save_settings(self):
        """ Saves all settings to the .env file. """
        ipqs_key_to_save = self.ipqs_entry.get()
        otx_key_to_save = self.otx_entry.get()
        cache_duration_to_save = self.cache_entry.get()

        # Validate cache duration
        if not cache_duration_to_save.isdigit() or int(cache_duration_to_save) < 0:
            messagebox.showerror("Invalid Input", "Cache duration must be a positive number.")
            return

        try:
            dotenv_path = find_dotenv()
            if not dotenv_path:
                dotenv_path = os.path.join(os.getcwd(), '.env')
                with open(dotenv_path, 'w') as f:
                    pass

            set_key(dotenv_path, "IPQS_API_KEY", ipqs_key_to_save)
            set_key(dotenv_path, "OTX_API_KEY", otx_key_to_save)
            set_key(dotenv_path, "CACHE_DURATION_HOURS", cache_duration_to_save)
            
            messagebox.showinfo("Success", "Settings saved successfully!")
            
            self.master.check_api_key(from_settings=True)
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings:\n{e}")

    def clear_all_data(self):
        """ Deletes the database file and restarts the application. """
        if messagebox.askyesno("Confirm", "ARE YOU SURE?\n\nThis will permanently delete all analysis history. The application will close after this action."):
            try:
                database.delete_database()
                messagebox.showinfo("Success", "All data has been cleared. Please restart the application.")
                self.master.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear data: {e}")

