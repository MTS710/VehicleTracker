import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "vehicles.db")
ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")


def assign_warranty(make, year, mileage):
    current_year = datetime.now().year
    age = current_year - year
    make_lower = make.lower()

    if make_lower == "kia" and age <= 5 and mileage < 80000:
        return "CPO"
    if make_lower == "kia" and age <= 5 and 80000 <= mileage < 100000:
        return "Limited"
    if make_lower != "kia" and age < 7 and mileage < 80000:
        return "Limited"
    return "As-Is"


class VehicleTracker(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Used Vehicle Tracker")
        self.geometry("900x600")

        # Dashboard label
        self.label = ctk.CTkLabel(self, text="Tracker Dashboard", font=ctk.CTkFont(size=20, weight="bold"))
        self.label.grid(row=0, column=0, padx=20, pady=20)

        # Button Frame
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=1, column=0, padx=20, pady=10, sticky="w")

        self.add_vehicle_button = ctk.CTkButton(button_frame, text="Add Vehicle", command=self.open_add_vehicle_popup)
        self.add_vehicle_button.grid(row=0, column=0, padx=10, pady=10)

        self.sell_vehicle_button = ctk.CTkButton(button_frame, text="Sell Vehicle", command=self.open_sell_vehicle_popup)
        self.sell_vehicle_button.grid(row=0, column=1, padx=10)

        self.photos_button = ctk.CTkButton(button_frame, text="Photo Tracker", command=self.open_photo_tracker)
        self.photos_button.grid(row=0, column=2, padx=10, pady=10)

        # Header
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.grid(row=2, column=0, padx=20, pady=(10, 0), sticky="ew")
        self.header_frame.grid_columnconfigure((0,1,2,3,4,5,6), weight=1)
        headers = ["Stock#", "Make", "Model", "Year", "Status", "Location", "Notes"]
        for col, text in enumerate(headers):
            label = ctk.CTkLabel(self.header_frame, text=text, font=ctk.CTkFont(weight="bold"))
            label.grid(row=0, column=col, padx=5, pady=5, sticky="nsew")

        # Scrollable list
        self.list_frame = ctk.CTkFrame(self)
        self.list_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.scrollable_frame = ctk.CTkScrollableFrame(self.list_frame)
        self.scrollable_frame.pack(fill="both", expand=True)

        self.vehicles = []
        self.init_db()
        self.load_vehicles()

    # ---------------- Database Setup ---------------- #
    def init_db(self):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT,
                stock_number TEXT,
                vin TEXT,
                make TEXT,
                model TEXT,
                year TEXT,
                mileage TEXT,
                damage_notes TEXT,
                notes TEXT,
                status TEXT,
                location TEXT,
                warranty TEXT,
                photos_taken TEXT DEFAULT 'No'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sold_vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_number TEXT,
                vin TEXT,
                make TEXT,
                model TEXT,
                year TEXT,
                mileage TEXT,
                damage_notes TEXT,
                notes TEXT,
                status TEXT,
                location TEXT,
                seller_name TEXT,
                date_sold TEXT
            )
        """)
        conn.commit()
        conn.close()

    # ---------------- Load Vehicles ---------------- #
    def load_vehicles(self):
        self.vehicles.clear()
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, stock_number, vin, make, model, year, mileage, damage_notes, notes, status, location, photos_taken
            FROM vehicles
        """)
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            vid, stock_number, vin, make, model, year, mileage, damage_notes, notes, status, location, photos_taken = row
            try: year_int = int(year)
            except: year_int = datetime.now().year
            try: mileage_int = int(mileage)
            except: mileage_int = 0

            vehicle_data = {
                "id": vid,
                "Stock Number": stock_number,
                "VIN": vin,
                "Make": make,
                "Model": model,
                "Year": year,
                "Mileage": mileage,
                "Damage Notes": damage_notes or "",
                "notes": notes or "",
                "Status": status or "Undecided",
                "Location": location or "Service",
                "warranty": assign_warranty(make, year_int, mileage_int),
                "photos_taken": photos_taken or "No"
            }
            self.vehicles.append(vehicle_data)
        self.refresh_vehicle_list()

    # ---------------- Add Vehicle Popup ---------------- #
    def open_add_vehicle_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Add Vehicle")
        popup.geometry("400x500")
        self.center_popup(popup)

        fields = ["Stock Number", "VIN", "Make", "Model", "Year", "Mileage", "Damage Notes", "Notes"]
        entries = {}

        for i, field in enumerate(fields):
            ctk.CTkLabel(popup, text=field).pack(pady=(10 if i == 0 else 5,0), padx=10, anchor="w")
            entry = ctk.CTkEntry(popup, width=350)
            entry.pack(padx=10, pady=5)
            entries[field] = entry

        # Status
        status_var = ctk.StringVar(value="Undecided")
        ctk.CTkLabel(popup, text="Status").pack(padx=10, anchor="w")
        status_dropdown = ctk.CTkOptionMenu(popup, values=["Undecided","Retail","Wholesale"], variable=status_var)
        status_dropdown.pack(padx=10, pady=5)

        # Location
        location_var = ctk.StringVar(value="Service")
        ctk.CTkLabel(popup, text="Location").pack(padx=10, anchor="w")
        location_dropdown = ctk.CTkOptionMenu(popup, values=["Service","Detail","Retail lot","Wholesale lot"], variable=location_var)
        location_dropdown.pack(padx=10, pady=5)

        def save_vehicle():
            try:
                data = {field: entries[field].get() for field in fields}
                year_int = int(data["Year"])
                mileage_int = int(data["Mileage"])
                warranty = assign_warranty(data["Make"], year_int, mileage_int)

                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO vehicles (stock_number, vin, make, model, year, mileage, damage_notes, notes, status, location, warranty)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data["Stock Number"], data["VIN"], data["Make"], data["Model"],
                    data["Year"], data["Mileage"], data["Damage Notes"], data["Notes"],
                    status_var.get(), location_var.get(), warranty
                ))
                conn.commit()
                conn.close()
                self.load_vehicles()
                popup.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add vehicle: {e}")

        ctk.CTkButton(popup, text="Save", command=save_vehicle).pack(pady=10)
        ctk.CTkButton(popup, text="Cancel", command=popup.destroy).pack()

    # ---------------- Sell Vehicle Popup ---------------- #
    def open_sell_vehicle_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Sell Vehicle")
        popup.geometry("400x250")
        self.center_popup(popup)

        ctk.CTkLabel(popup, text="Stock Number").pack(pady=(20,5), padx=10, anchor="w")
        stock_entry = ctk.CTkEntry(popup, width=350)
        stock_entry.pack(padx=10, pady=5)

        ctk.CTkLabel(popup, text="Seller Name").pack(pady=5, padx=10, anchor="w")
        seller_entry = ctk.CTkEntry(popup, width=350)
        seller_entry.pack(padx=10, pady=5)

        ctk.CTkLabel(popup, text="Date Sold (YYYY-MM-DD)").pack(pady=5, padx=10, anchor="w")
        date_entry = ctk.CTkEntry(popup, width=350)
        date_entry.pack(padx=10, pady=5)
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        def sell_vehicle():
            stock_number = stock_entry.get()
            seller = seller_entry.get()
            date_sold = date_entry.get()
            if not stock_number or not seller:
                messagebox.showerror("Error", "Stock number and seller are required.")
                return
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM vehicles WHERE stock_number = ?", (stock_number,))
                vehicle = cursor.fetchone()
                if not vehicle:
                    messagebox.showerror("Error", f"No vehicle with Stock# {stock_number}")
                    conn.close()
                    return
                cursor.execute("""
                    INSERT INTO sold_vehicles (stock_number, vin, make, model, year, mileage, damage_notes, notes, status, location, seller_name, date_sold)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (vehicle[2], vehicle[3], vehicle[4], vehicle[5], vehicle[6], vehicle[7], vehicle[8], vehicle[9],
                      vehicle[10], vehicle[11], seller, date_sold))
                cursor.execute("DELETE FROM vehicles WHERE stock_number = ?", (stock_number,))
                conn.commit()
                conn.close()
                self.load_vehicles()
                popup.destroy()
                messagebox.showinfo("Success", f"Vehicle {stock_number} sold to {seller}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to sell vehicle: {e}")

        ctk.CTkButton(popup, text="Sell Vehicle", command=sell_vehicle).pack(pady=10)
        ctk.CTkButton(popup, text="Cancel", command=popup.destroy).pack()

    # ---------------- Notes Popup ---------------- #
    def open_notes_popup(self, vehicle):
        popup = ctk.CTkToplevel(self)
        popup.title(f"Notes for {vehicle.get('Stock Number')}")
        popup.geometry("400x300")
        self.center_popup(popup)
        popup.transient(self)
        popup.grab_set()
        popup.focus_force()

        ctk.CTkLabel(popup, text="Notes:", anchor="w").pack(pady=(10,0), padx=10, fill="x")
        notes_text = ctk.CTkTextbox(popup, width=350, height=150)
        notes_text.pack(padx=10, pady=5)
        notes_text.insert("0.0", vehicle.get("notes",""))

        def save_notes():
            new_notes = notes_text.get("0.0","end-1c")
            vehicle["notes"] = new_notes
            self.update_vehicle_field(vehicle["id"], "notes", new_notes)
            popup.destroy()

        btn_frame = ctk.CTkFrame(popup)
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="Save", command=save_notes).grid(row=0, column=0, padx=5)
        ctk.CTkButton(btn_frame, text="Profile", command=lambda v=vehicle:self.open_profile_popup(v)).grid(row=0, column=1, padx=5)
        ctk.CTkButton(btn_frame, text="Close", command=popup.destroy).grid(row=0, column=2, padx=5)

    # ---------------- Profile Popup ---------------- #
    def open_profile_popup(self, vehicle=None):
        popup = ctk.CTkToplevel(self)
        popup.title("Profile")
        popup.geometry("400x300")
        self.center_popup(popup)
        popup.transient(self)
        popup.grab_set()
        popup.focus_force()

        ctk.CTkLabel(popup, text="Vehicle Profile", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        if vehicle:
            info = f"Stock#: {vehicle.get('Stock Number','')}\nMake: {vehicle.get('Make','')}\nModel: {vehicle.get('Model','')}\nYear: {vehicle.get('Year','')}"
        else:
            info = "No vehicle selected."
        ctk.CTkLabel(popup, text=info, justify="left").pack(pady=10)
        ctk.CTkButton(popup, text="Close", command=popup.destroy).pack(pady=10)

    # ---------------- Refresh Vehicle List ---------------- #
    def refresh_vehicle_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.status_vars = {}
        self.location_vars = {}

        for row, vehicle in enumerate(self.vehicles):
            # Status Dropdown
            status_var = ctk.StringVar(value=vehicle.get("Status","Undecided"))
            self.status_vars[vehicle["id"]] = status_var
            status_dropdown = ctk.CTkOptionMenu(self.scrollable_frame, values=["Undecided","Retail","Wholesale"],
                                                variable=status_var, width=80, height=25, font=ctk.CTkFont(size=10))
            status_dropdown.grid(row=row, column=4, padx=(20,5), pady=2, sticky="ew")
            status_var.trace_add("write", lambda *args, var=status_var, veh=vehicle: (veh.update({"Status": var.get()}), self.update_vehicle_field(veh["id"], "status", var.get())))

            # Location Dropdown
            location_var = ctk.StringVar(value=vehicle.get("Location","Service"))
            self.location_vars[vehicle["id"]] = location_var
            location_dropdown = ctk.CTkOptionMenu(self.scrollable_frame, values=["Service","Detail","Retail lot","Wholesale lot"],
                                                  variable=location_var, width=100, height=25, font=ctk.CTkFont(size=10))
            location_dropdown.grid(row=row, column=5, padx=(30,5), pady=2, sticky="ew")
            location_var.trace_add("write", lambda *args, var=location_var, veh=vehicle: (veh.update({"Location": var.get()}), self.update_vehicle_field(veh["id"], "Location", var.get())))

            # Columns
            ctk.CTkLabel(self.scrollable_frame, text=vehicle.get("Stock Number","")).grid(row=row, column=0, padx=5, pady=8, sticky="ew")
            ctk.CTkLabel(self.scrollable_frame, text=vehicle.get("Make","")).grid(row=row, column=1, padx=5, pady=5, sticky="ew")
            ctk.CTkLabel(self.scrollable_frame, text=vehicle.get("Model","")).grid(row=row, column=2, padx=5, pady=5, sticky="ew")
            ctk.CTkLabel(self.scrollable_frame, text=vehicle.get("Year","")).grid(row=row, column=3, padx=10, pady=5, sticky="ew")

            # Notes Button
            notes_btn = ctk.CTkButton(self.scrollable_frame, text="Notes", width=60, height=25, font=ctk.CTkFont(size=10),
                                      command=lambda v=vehicle:self.open_notes_popup(v))
            notes_btn.grid(row=row, column=6, padx=(50,5), pady=2, sticky="ew")

    # ---------------- Update Field ---------------- #
    def update_vehicle_field(self, vehicle_id, field, new_value):
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(f"UPDATE vehicles SET {field} = ? WHERE id = ?", (new_value, vehicle_id))
            conn.commit()
            conn.close()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to update {field}: {e}")

    # ---------------- Photo Tracker ---------------- #
    def open_photo_tracker(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Photo Tracker")
        popup.geometry("800x500")
        self.photos_vars = {}
        popup.transient(self)
        popup.grab_set()
        popup.focus_force()
        self.center_popup(popup)

        scroll_frame = ctk.CTkScrollableFrame(popup, width=760, height=400)
        scroll_frame.pack(padx=10, pady=10, fill="both", expand=True)

        headers = ["Stock #","Make","Model","Year","Warranty","Location","Photos Taken"]
        for col, text in enumerate(headers):
            ctk.CTkLabel(scroll_frame, text=text, font=("Arial",14,"bold")).grid(row=0, column=col, padx=5, pady=5)

        row_index = 1
        for vehicle in self.vehicles:
            if vehicle.get("Location") == "Wholesale lot":
                continue
            ctk.CTkLabel(scroll_frame, text=vehicle.get("Stock Number","")).grid(row=row_index, column=0, padx=5, pady=5)
            ctk.CTkLabel(scroll_frame, text=vehicle.get("Make","")).grid(row=row_index, column=1, padx=5, pady=5)
            ctk.CTkLabel(scroll_frame, text=vehicle.get("Model","")).grid(row=row_index, column=2, padx=5, pady=5)
            ctk.CTkLabel(scroll_frame, text=vehicle.get("Year","")).grid(row=row_index, column=3, padx=5, pady=5)
            ctk.CTkLabel(scroll_frame, text=vehicle.get("warranty","N/A")).grid(row=row_index, column=4, padx=5, pady=5)
            ctk.CTkLabel(scroll_frame, text=vehicle.get("Location","")).grid(row=row_index, column=5, padx=5, pady=5)

            photos_var = ctk.StringVar(value=vehicle.get("photos_taken","No"))
            self.photos_vars[vehicle["id"]] = photos_var
            dropdown = ctk.CTkOptionMenu(scroll_frame, values=["Yes","No"], variable=photos_var,
                                         command=lambda choice, v=vehicle, var=photos_var:self.update_photos_status(v,var.get()))
            dropdown.grid(row=row_index, column=6, padx=5, pady=5)
            row_index += 1

        ctk.CTkButton(popup, text="Close", command=popup.destroy).pack(pady=10)

    def update_photos_status(self, vehicle, status):
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("UPDATE vehicles SET photos_taken = ? WHERE id = ?", (status, vehicle["id"]))
            conn.commit()
            conn.close()
            vehicle["photos_taken"] = status
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to update photos: {e}")

    # ---------------- Center Popup ---------------- #
    def center_popup(self, popup):
        popup.update_idletasks()
        screen_width = popup.winfo_screenwidth()
        screen_height = popup.winfo_screenheight()
        size = tuple(int(_) for _ in popup.geometry().split('+')[0].split('x'))
        x = (screen_width - size[0]) // 2
        y = (screen_height - size[1]) // 2
        popup.geometry(f"{size[0]}x{size[1]}+{x}+{y}")


if __name__ == "__main__":
    app = VehicleTracker()
    app.mainloop()
