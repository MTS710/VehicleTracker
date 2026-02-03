import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from utils import assign_warranty, validate_vin
from .profile_popup import ProfilePopup


class AddVehiclePopup(ctk.CTkToplevel):
    def __init__(self, master, db, refresh_callback=None):
        super().__init__(master)

        self.db = db
        self.refresh_callback = refresh_callback

        self.title("Add Vehicle")
        self.geometry("400x450")
        self.transient(master)
        self.focus_force()
        self.center_window()

        self.make_selected = False
        self.ignore_next_make_focus = False

        # ---------------- Make / Model Mapping ---------------- #
        self.make_model_map = {
            "Acura": ["ILX","Integra","MDX","RDX","RLX","TLX","ZDX"],
            "Audi": ["A3","A4","A5","A6","A7","A8","Q3","Q5","Q7","Q8","TT","e-tron"],
            "BMW": ["2 Series","3 Series","4 Series","5 Series","7 Series","X1","X2","X3","X4","X5","X6","Z4"],
            "Buick": ["Enclave","Encore","Encore GX","Envision","LaCrosse","Regal"],
            "Cadillac": ["CT4","CT5","CT6","Escalade","XT4","XT5","XT6"],
            "Chevrolet": ["Bolt EV","Camaro","Corvette","Equinox","Malibu","Silverado","Tahoe","Traverse","Trax","Suburban","Colorado"],
            "Chrysler": ["300","Pacifica","Voyager"],
            "Dodge": ["Challenger","Charger","Durango","Journey","Grand Caravan"],
            "Ford": ["Bronco","EcoSport","Edge","Escape","Expedition","Explorer","F-150","F-250","F-350","Fusion","Mustang","Ranger","Transit Connect"],
            "GMC": ["Acadia","Canyon","Sierra 1500","Sierra 2500","Sierra 3500","Terrain","Yukon"],
            "Honda": ["Accord","Civic","CR-V","HR-V","Odyssey","Passport","Pilot","Ridgeline"],
            "Hyundai": ["Accent","Elantra","Ioniq","Kona","Palisade","Santa Fe","Sonata","Tucson","Venue","Veloster"],
            "Jeep": ["Cherokee","Compass","Grand Cherokee","Wrangler","Gladiator","Renegade"],
            "Kia": ["Carnival","Forte","K5","K7","Niro","Sorento","Soul","Sportage","Stinger","Telluride"],
            "Mazda": ["3","6","CX-3","CX-30","CX-5","CX-50","CX-9","MX-5 Miata"],
            "Mercedes-Benz": ["A-Class","C-Class","E-Class","GLA","GLC","GLE","GLS","S-Class","EQB","EQC"],
            "Nissan": ["Altima","Armada","Frontier","GT-R","Kicks","Leaf","Maxima","Murano","Pathfinder","Rogue","Sentra","Titan","Versa","Z"],
            "Subaru": ["Ascent","BRZ","Crosstrek","Forester","Impreza","Outback","WRX"],
            "Tesla": ["Model 3","Model S","Model X","Model Y","Cybertruck"],
            "Toyota": ["4Runner","Avalon","Camry","Corolla","Highlander","Land Cruiser","Prius","RAV4","Sequoia","Sienna","Tacoma","Tundra","Venza","Yaris"],
            "Volkswagen": ["Atlas","Golf","Jetta","Passat","Tiguan","ID.4"],
            "Volvo": ["S60","S90","V60","V90","XC40","XC60","XC90"]
        }

        self.fields = [
            "Stock Number", "VIN", "Make", "Model",
            "Year", "Mileage", "Traded In By"
        ]

        self.entries = {}
        self.make_popup = None
        self.make_frame = None

        # ---------------- Form Fields ---------------- #
        for field in self.fields:
            ctk.CTkLabel(self, text=field, anchor="w").pack(
                pady=(10, 0), padx=20, fill="x"
            )

            if field == "Make":
                entry = ctk.CTkEntry(self, width=350)
                entry.bind("<FocusIn>", self.open_make_dropdown)
                entry.bind("<KeyRelease>", self.filter_make_dropdown)
                entry.bind("<Return>", self.confirm_make_from_text)
                self.bind("<Button-1>", self._global_click_handler, add="+")
            elif field == "Model":
                entry = ctk.CTkComboBox(self, width=350, values=[])
                entry.set("")
            else:
                entry = ctk.CTkEntry(self, width=350)

            entry.pack(padx=20)
            self.entries[field] = entry

            if field == "Stock Number":
                entry.bind("<KeyRelease>", self.uppercase_stock)
            if field == "Mileage":
                entry.bind("<KeyRelease>", self.format_mileage)
            if field == "Traded In By":
                entry.bind("<KeyRelease>", self.capitalize_first_letter)

        # ---------------- Buttons ---------------- #
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=15)

        ctk.CTkButton(btn_frame, text="Add Vehicle", command=self.add_vehicle).grid(row=0, column=0, padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", command=self.destroy).grid(row=0, column=1, padx=5)

    # ======================================================
    # Make Dropdown Logic
    # ======================================================
    def open_make_dropdown(self, event=None):
        if self.ignore_next_make_focus:
            self.ignore_next_make_focus = False
            return

        self.make_selected = False

        if self.make_popup and self.make_popup.winfo_exists():
            return

        entry = self.entries["Make"]
        self.update_idletasks()

        x = entry.winfo_rootx()
        y = entry.winfo_rooty() + entry.winfo_height()
        width = entry.winfo_width()

        self.make_popup = ctk.CTkToplevel(self)
        self.make_popup.overrideredirect(True)
        self.make_popup.attributes("-topmost", True)
        self.make_popup.geometry(f"{width}x200+{x}+{y}")

        self.make_frame = ctk.CTkScrollableFrame(
            self.make_popup, width=width, height=200
        )
        self.make_frame.pack(fill="both", expand=True)

        self.populate_make_dropdown(self.make_model_map.keys())



    def filter_make_dropdown(self, event=None):
        if self.make_selected:
            return

        text = self.entries["Make"].get().strip().lower()

        if not self.make_popup or not self.make_popup.winfo_exists():
            self.open_make_dropdown()

        if not text:
            self.populate_make_dropdown(self.make_model_map.keys())
            return

        matches = [
            make for make in self.make_model_map
            if make.lower().startswith(text)
        ]

        if matches:
            self.populate_make_dropdown(matches)
        else:
            self.close_make_dropdown()


    def populate_make_dropdown(self, makes):
        if not self.make_frame:
            return

        for widget in self.make_frame.winfo_children():
            widget.destroy()

        for make in sorted(makes):
            ctk.CTkButton(
                self.make_frame,
                text=make,
                anchor="w",
                height=26,
                fg_color=("gray95", "gray20"),
                hover_color=("gray80", "gray30"),
                text_color=("black", "white"),
                command=lambda m=make: self.select_make(m)
            ).pack(fill="x", padx=6, pady=1)

    def select_make(self, make):
        self.make_selected = True
        self.ignore_next_make_focus = True

        entry = self.entries["Make"]
        entry.delete(0, "end")
        entry.insert(0, make)

        self.on_make_selected(make)
        self.close_make_dropdown()
        

    def close_make_dropdown(self):
        if self.make_popup and self.make_popup.winfo_exists():
            try:
                self.make_popup.destroy()
            except:
                pass
        self.make_popup = None
        self.make_frame = None


    def on_make_selected(self, make):
        models = self.make_model_map.get(make, [])
        model_box = self.entries["Model"]
        model_box.configure(values=models)
        model_box.set("")

    def _global_click_handler(self, event):
        if not self.make_popup or not self.make_popup.winfo_exists():
            return
        widget = event.widget
        if widget is self.entries["Make"]:
            return
        if widget.winfo_toplevel() is self.make_popup:
            return
        self.close_make_dropdown()

    # ======================================================
    # Helper Methods
    # ======================================================

    def format_mileage(self, event):
        entry = self.entries["Mileage"]
        value = entry.get().replace(",", "")
        if value.isdigit():
            entry.delete(0, "end")
            entry.insert(0, f"{int(value):,}")

    def uppercase_stock(self, event):
        entry = self.entries["Stock Number"]
        cursor_pos = entry.index("insert")
        value = entry.get().upper()
        entry.delete(0, "end")
        entry.insert(0, value)
        entry.icursor(cursor_pos)

    def capitalize_first_letter(self, event):
        entry = self.entries["Traded In By"]
        value = entry.get()
        if value:
            entry.delete(0, "end")
            entry.insert(0, value[0].upper() + value[1:])

    def center_window(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def confirm_make_from_text(self, event=None):
        text = self.entries["Make"].get().strip().lower()
        for make in self.make_model_map:
            if make.lower() == text:
                self.select_make(make)
                return
        self.close_make_dropdown()

    # ======================================================
    # Main Add Method
    # ======================================================

    def add_vehicle(self):
        try:
            data = {f: self.entries[f].get().strip() for f in self.entries}

            for field, value in data.items():
                if not value:
                    messagebox.showerror("Missing Information", f"You must enter {field}.")
                    return

            stock = data["Stock Number"]
            if len(stock) != 8 or not stock.isalnum():
                messagebox.showerror("Invalid Stock Number", "Stock Number must be 8 characters.")
                return
            if self.db.get_vehicle_by_stock(stock):
                messagebox.showerror("Duplicate Stock Number", "Stock Number already exists.")
                return

            vin = data["VIN"].replace(" ", "").upper()
            if len(vin) != 17 or not vin.isalnum() or any(c in vin for c in ("I", "O", "Q")):
                messagebox.showerror("Invalid VIN", "VIN must be 17 alphanumeric characters and cannot contain I, O, or Q.")
                return
            if self.db.vin_exists(vin):
                messagebox.showerror("Duplicate VIN", "A vehicle with this VIN already exists.")
                return
            self.entries["VIN"].delete(0, "end")
            self.entries["VIN"].insert(0, vin)

            year = int(data["Year"])
            current_year = datetime.now().year
            max_allowed_year = current_year + 1

            if year < 1980 or year > max_allowed_year:
                messagebox.showerror(
                    "Invalid Year",
                    f"Year must be between 1980 and {max_allowed_year}."
                    )
                return

            mileage = int(data["Mileage"].replace(",", ""))

            vehicle_data = {
                "User Name": "Default",
                "Stock Number": stock,
                "VIN": vin,
                "Make": data["Make"],
                "Model": data["Model"],
                "Year": str(year),
                "Mileage": str(mileage),
                "Traded In By": data["Traded In By"],
                "Status": "Undecided",
                "Location": "Service",
                "Warranty": assign_warranty(data["Make"], year, mileage),
                "Photos Taken": "No",
            }

            self.db.add_vehicle(vehicle_data)

            if self.refresh_callback:
                self.refresh_callback()

            # Show profile popup (keep timestamp if needed)
            ProfilePopup(self.master, vehicle_data)

            messagebox.showinfo("Success", "Vehicle added successfully.")
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error", str(e))
