# -------------------------------
# IMPORTS
# -------------------------------
import customtkinter as ctk
from datetime import datetime
import os
from database import VehicleDatabase
from utils import assign_warranty
from popups.add_vehicle_popup import AddVehiclePopup
from popups.delete_vehicle_popup import DeleteVehiclePopup
from popups.notes_popup import NotesPopup
from popups.photo_tracker_popup import PhotoTrackerPopup
from functools import partial

# -------------------------------
# GLOBAL CONFIGURATION
# -------------------------------
DB_FILE = os.path.join(os.path.dirname(__file__), "vehicles.db")
ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

# -------------------------------
# MAIN APPLICATION CLASS
# -------------------------------
class VehicleTracker(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Used Vehicle Tracker")
        self.geometry("900x600")
        self.after(100, lambda: self.state("zoomed"))

        # Columns: Stock, Make, Model, Year, Status, Location, Notes
        self.COL_WIDTHS = [130, 160, 160, 80, 110, 140, 90]
        self.COL_COUNT = len(self.COL_WIDTHS)
        self.ROW_FONT = ctk.CTkFont(size=14)

        # UI constants
        self.DROPDOWN_W = 90
        self.NOTES_W = 60
        self.NOTES_PAD_RIGHT = 12
        self.ROW_PADY = 6

        # Vehicles list and database
        self.vehicles = []
        self.db = VehicleDatabase()

        # Dashboard label
        self.label = ctk.CTkLabel(self, text="Tracker Dashboard",
                                   font=ctk.CTkFont(size=20, weight="bold"))
        self.label.grid(row=0, column=0, padx=20, pady=(20, 0), sticky="w")

        # Feedback label
        self.feedback_label = ctk.CTkLabel(self, text="", text_color="green",
                                           font=ctk.CTkFont(size=12))
        self.feedback_label.grid(row=1, column=0, padx=20, pady=(0,5), sticky="w")

        # Buttons
        self.setup_buttons()

        # Container for header and vehicle list
        self.container_frame = ctk.CTkFrame(self)
        self.container_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=(10,0))
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.container_frame.grid_rowconfigure(1, weight=1)
        self.container_frame.grid_columnconfigure(0, weight=1)

        # Header and vehicle list frames
        self.setup_header()
        self.setup_vehicle_list_frame()

        self.current_view = "ALL"
        # Load vehicles from database
        self.load_vehicles()


    # -------------------------------
    # HELPER METHODS
    # -------------------------------
    def show_feedback(self, message, duration=1000):
        """Display a temporary feedback message."""
        self.feedback_label.configure(text=message)
        self.after(duration, lambda: self.feedback_label.configure(text=""))

    def get_retail_category(self, vehicle):
        make = vehicle.get("Make", "").lower()
        cert = vehicle.get("Certification", "").lower()  # or however you store CPO / As-Is
        status = vehicle.get("Status", "Undecided")

        if status == "Wholesale":
            return None

        is_kia = "kia" in make

        if is_kia and cert == "cpo":
            return "KIA_CPO"
        if is_kia and cert == "limited":
            return "KIA_LIMITED"
        if is_kia and cert == "as-is":
            return "KIA_ASIS"
        if not is_kia and cert == "limited":
            return "NON_KIA_LIMITED"
        if not is_kia and cert == "as-is":
            return "NON_KIA_ASIS"

        return None



    # -------------------------------
    # UI SETUP
    # -------------------------------
    def setup_buttons(self):
        """Create top dashboard buttons and view buttons."""

        # Top bar container
        top_bar = ctk.CTkFrame(self)
        top_bar.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        top_bar.grid_columnconfigure(0, weight=1)
        top_bar.grid_columnconfigure(1, weight=1)

        # LEFT: Action buttons
        action_button_frame = ctk.CTkFrame(top_bar)
        action_button_frame.grid(row=0, column=0, sticky="w")

        self.add_vehicle_button = ctk.CTkButton(
            action_button_frame,
            text="Add Vehicle",
            command=self.open_add_vehicle_popup
        )
        self.add_vehicle_button.grid(row=0, column=0, padx=10, pady=10)

        self.sell_vehicle_button = ctk.CTkButton(
            action_button_frame,
            text="Sell Vehicle",
            command=self.open_delete_vehicle_popup
        )
        self.sell_vehicle_button.grid(row=0, column=1, padx=10)

        self.photos_button = ctk.CTkButton(
            action_button_frame,
            text="Photo Tracker",
            command=self.open_photo_tracker
        )
        self.photos_button.grid(row=0, column=2, padx=10, pady=10)

        # RIGHT: View buttons
        view_button_frame = ctk.CTkFrame(top_bar)
        view_button_frame.grid(row=0, column=1, sticky="e")

        self.all_view_button = ctk.CTkButton(
            view_button_frame,
            text="All",
            command=lambda: self.set_view("ALL")
        )
        self.all_view_button.grid(row=0, column=0, padx=6, pady=10)

        self.retail_view_button = ctk.CTkButton(
            view_button_frame,
            text="Retail",
            command=lambda: self.set_view("RETAIL")
        )
        self.retail_view_button.grid(row=0, column=1, padx=6)

        self.wholesale_view_button = ctk.CTkButton(
            view_button_frame,
            text="Wholesale",
            command=lambda: self.set_view("WHOLESALE")
        )
        self.wholesale_view_button.grid(row=0, column=2, padx=6)


    # -------------------------------
    # SET VIEW
    # -------------------------------
    def set_view(self, view_type):
        """Set the current view and refresh the vehicle list."""
        self.current_view = view_type
        self.refresh_vehicle_list()


    # -------------------------------
    # HEADER / LIST SETUP
    # -------------------------------
    def setup_header(self):
        """Create table headers."""
        self.header_frame = ctk.CTkFrame(self.container_frame)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        for col, minw in enumerate(self.COL_WIDTHS):
            self.header_frame.grid_columnconfigure(col, weight=1, minsize=minw, uniform="fullwidth")

        headers = ["Stock#", "Make", "Model", "Year", "Status", "Location", "Notes"]
        for col, text in enumerate(headers):
            lbl = ctk.CTkLabel(self.header_frame, text=text,
                               font=ctk.CTkFont(weight="bold"))
            lbl.grid(row=0, column=col, padx=8, pady=8, sticky="w")

    def setup_vehicle_list_frame(self):
        """Scrollable frame to display vehicles."""
        self.list_frame = ctk.CTkFrame(self.container_frame)
        self.list_frame.grid(row=1, column=0, sticky="nsew")
        self.list_frame.grid_rowconfigure(0, weight=1)
        self.list_frame.grid_columnconfigure(0, weight=1)

        self.scrollable_frame = ctk.CTkScrollableFrame(self.list_frame)
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew")


    # -------------------------------
    # DATABASE / LOADING
    # -------------------------------
    def load_vehicles(self):
        """Load vehicles from database into memory and refresh list."""
        self.vehicles.clear()
        rows = self.db.get_vehicles()

        for row in rows:
            vehicle_data = {
                "id": row["id"],
                "Stock Number": row["stock_number"],
                "VIN": row["vin"],
                "Make": row["make"],
                "Model": row["model"],
                "Year": row["year"],
                "Mileage": row["mileage"],
                "Certification": row["certification"] or "",
                "notes": row["notes"] or "",
                "Status": row["status"] or "Undecided",
                "Location": row["location"] or "Service",
                "Traded In By": row["traded_in_by"] or "",
                "warranty": assign_warranty(row["make"], int(row["year"] or datetime.now().year),
                                            int(row["mileage"] or 0)),
                "photos_taken": row["photos_taken"] or "No"
            }
            self.vehicles.append(vehicle_data)

        self.refresh_vehicle_list()


    # -------------------------------
    # REFRESH VEHICLE LIST
    # -------------------------------
    def refresh_vehicle_list(self):
        # Clear existing rows
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.status_vars = {}
        self.location_vars = {}

        for col, minw in enumerate(self.COL_WIDTHS):
            self.scrollable_frame.grid_columnconfigure(
                col, weight=1, minsize=minw, uniform="fullwidth"
            )

        row_idx = 0

        # -------------------------------
        # ALL VIEW
        # -------------------------------
        if self.current_view == "ALL":
            buckets = {
                "kia_cpo": [],
                "kia_limited": [],
                "kia_as_is": [],
                "non_kia_limited": [],
                "non_kia_as_is": [],
                "wholesale": []
            }

            for vehicle in self.vehicles:
                status = vehicle.get("Status", "")
                warranty = vehicle.get("warranty", "")
                make = vehicle.get("Make", "").lower()

                if status == "Wholesale":
                    buckets["wholesale"].append(vehicle)
                    continue

                # Retail ordering
                if "kia" in make:
                    if warranty == "CPO":
                        buckets["kia_cpo"].append(vehicle)
                    elif warranty == "Limited":
                        buckets["kia_limited"].append(vehicle)
                    else:
                        buckets["kia_as_is"].append(vehicle)
                else:
                    if warranty == "Limited":
                        buckets["non_kia_limited"].append(vehicle)
                    else:
                        buckets["non_kia_as_is"].append(vehicle)

            display_order = [
                "kia_cpo",
                "kia_limited",
                "kia_as_is",
                "non_kia_limited",
                "non_kia_as_is"
            ]

            row_idx = 0
            # Draw all retail vehicles first
            for key in display_order:
                for vehicle in buckets[key]:
                    self.draw_vehicle_row(vehicle, row_idx)
                    row_idx += 1

            # -------------------------------
            # Separator for Wholesale
            # -------------------------------
            sep_text = "Wholesale"
            # Create a label that looks like a thin line with text in the center
            sep_label = ctk.CTkLabel(
                self.scrollable_frame,
                text=f"--------------------------------------------------------------------------------------------------------------------------- {sep_text}-------------------------------------------------------------------------------------------------- ",
                text_color="blue",
                font=ctk.CTkFont(size=12, weight="bold")
            )
            sep_label.grid(row=row_idx, column=0, columnspan=self.COL_COUNT, sticky="ew", pady=6)
            row_idx += 1


            # Draw all wholesale vehicles below separator
            for vehicle in buckets["wholesale"]:
                self.draw_vehicle_row(vehicle, row_idx)
                row_idx += 1

            return

        # -------------------------------
        # RETAIL VIEW
        # -------------------------------
        if self.current_view == "RETAIL":
            for vehicle in self.vehicles:
                if vehicle.get("Status") in ("Retail", "Undecided"):
                    self.draw_vehicle_row(vehicle, row_idx)
                    row_idx += 1
            return

        # -------------------------------
        # WHOLESALE VIEW
        # -------------------------------
        if self.current_view == "WHOLESALE":
            for vehicle in self.vehicles:
                if vehicle.get("Status") == "Wholesale":
                    self.draw_vehicle_row(vehicle, row_idx)
                    row_idx += 1
            return



    def draw_vehicle_row(self, vehicle, row_idx, is_separator=False):
        """
        Draw a vehicle row in the scrollable frame.
        If is_separator=True, draws a thin blue line with 'WHOLESALE' text.
        """
        if is_separator:
            # Separator row
            sep_label = ctk.CTkLabel(
                self.scrollable_frame,
                text="-------- WHOLESALE --------",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="blue"
            )
            sep_label.grid(
                row=row_idx,
                column=0,
                columnspan=self.COL_COUNT,
                sticky="ew",
                pady=4
            )
            return

        # -------------------------------
        # TEXT COLUMNS
        # -------------------------------
        texts = [
            vehicle.get("Stock Number", ""),
            vehicle.get("Make", ""),
            vehicle.get("Model", ""),
            vehicle.get("Year", "")
        ]

        for col, text in enumerate(texts):
            ctk.CTkLabel(
                self.scrollable_frame,
                text=text,
                font=self.ROW_FONT
            ).grid(
                row=row_idx,
                column=col,
                padx=8,
                pady=self.ROW_PADY,
                sticky="w"
            )

        # -------------------------------
        # STATUS DROPDOWN
        # -------------------------------
        status_var = ctk.StringVar(value=vehicle.get("Status", "Undecided"))
        self.status_vars[vehicle["id"]] = status_var

        status_menu = ctk.CTkOptionMenu(
            self.scrollable_frame,
            values=["Undecided", "Retail", "Wholesale"],
            variable=status_var,
            width=self.DROPDOWN_W
        )
        status_menu.grid(
            row=row_idx,
            column=4,
            padx=8,
            pady=self.ROW_PADY,
            sticky="w"
        )

        status_var.trace_add(
            "write",
            lambda *args, vid=vehicle["id"], var=status_var: self._on_status_change(vid=vid, var=var)
        )

        # -------------------------------
        # LOCATION DROPDOWN
        # -------------------------------
        location_var = ctk.StringVar(value=vehicle.get("Location", "Service"))
        self.location_vars[vehicle["id"]] = location_var

        location_menu = ctk.CTkOptionMenu(
            self.scrollable_frame,
            values=["Service", "Detail", "Retail lot", "Wholesale lot"],
            variable=location_var,
            width=self.DROPDOWN_W
        )
        location_menu.grid(
            row=row_idx,
            column=5,
            padx=8,
            pady=self.ROW_PADY,
            sticky="w"
        )

        location_var.trace_add(
            "write",
            lambda *args, vid=vehicle["id"], var=location_var: self._on_location_change(vid=vid, var=var)
        )

        # -------------------------------
        # NOTES BUTTON
        # -------------------------------
        notes_btn = ctk.CTkButton(
            self.scrollable_frame,
            text="Notes",
            width=self.NOTES_W,
            command=lambda v=vehicle: self.open_notes_popup(v)
        )
        notes_btn.grid(
            row=row_idx,
            column=6,
            padx=(0, self.NOTES_PAD_RIGHT),
            pady=self.ROW_PADY,
            sticky="w"
        )



    # -------------------------------
    # STATUS / LOCATION CHANGES
    # -------------------------------
    def _on_status_change(self, *args, vid, var):
        new_status = var.get()
        for v in self.vehicles:
            if v["id"] == vid:
                v["Status"] = new_status
                break
        try:
            self.db.update_vehicle(vid, "status", new_status)
            self.show_feedback("Status saved!")
        except Exception:
            pass

        # Only switch view if not in ALL
        if self.current_view != "ALL":
            if new_status.lower() in ("retail", "undecided"):
                self.set_view("RETAIL")
            elif new_status.lower() == "wholesale":
                self.set_view("WHOLESALE")

    def _on_location_change(self, *args, vid, var):
        new_location = var.get()

        # Update in-memory vehicle list
        for v in self.vehicles:
            if v["id"] == vid:
                v["Location"] = new_location
                break

        # Update in database
        try:
            self.db.update_vehicle(vid, "location", new_location)
            self.show_feedback("Location saved!")
        except Exception:
            pass

        # Refresh ALL view if needed so the row moves correctly
        if self.current_view == "ALL":
            self.refresh_vehicle_list()



    # -------------------------------
    # POPUPS
    # -------------------------------
    def open_add_vehicle_popup(self):
        AddVehiclePopup(self, self.db, refresh_callback=self.load_vehicles)

    def open_delete_vehicle_popup(self):
        DeleteVehiclePopup(self, self.db, refresh_callback=self.load_vehicles)

    def open_notes_popup(self, vehicle):
        NotesPopup(self, self.db, vehicle)

    def open_photo_tracker(self):
        PhotoTrackerPopup(self, self.db)


# -------------------------------
# MAIN EXECUTION
# -------------------------------
if __name__ == "__main__":
    app = VehicleTracker()
    app.mainloop()
