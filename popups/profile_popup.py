import customtkinter as ctk
from datetime import datetime

class ProfilePopup(ctk.CTkToplevel):
    """Popup to display a vehicle's profile information."""

    def __init__(self, master, vehicle):
        super().__init__(master)
        self.vehicle = vehicle

        self.title("Vehicle Profile")
        self.geometry("500x450")
        self.transient(master)
        self.grab_set()
        self.center_window()

        # Title
        ctk.CTkLabel(
            self,
            text="Vehicle Profile",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(20, 10))

        # ------------------ Mileage ------------------ #
        mileage_raw = vehicle.get("Mileage") or vehicle.get("mileage") or ""
        try:
            mileage_int = int(str(mileage_raw).replace(",", ""))
            mileage_display = f"{mileage_int:,}"
        except (ValueError, TypeError):
            mileage_display = str(mileage_raw)


        # ------------------ Fields ------------------ #
        self.fields = [
            ("Stock Number", vehicle.get("Stock Number") or vehicle.get("stock_number") or ""),
            ("VIN", vehicle.get("VIN") or vehicle.get("vin") or ""),
            ("Make", vehicle.get("Make") or vehicle.get("make") or ""),
            ("Model", vehicle.get("Model") or vehicle.get("model") or ""),
            ("Year", vehicle.get("Year") or vehicle.get("year") or ""),
            ("Mileage", mileage_display),
            ("Traded In By", vehicle.get("Traded In By") or vehicle.get("traded_in_by") or ""),
        ]

        self._build_fields()

    # ------------------------------- Build UI ------------------------------- #
    def _build_fields(self):
        for label_text, value_text in self.fields:
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=6)

            ctk.CTkLabel(
                row,
                text=f"{label_text}:",
                width=120,
                anchor="w",
                font=ctk.CTkFont(size=13, weight="bold")
            ).pack(side="left")

            ctk.CTkLabel(
                row,
                text=value_text,
                anchor="w",
                font=ctk.CTkFont(size=13)
            ).pack(side="left")

    # ------------------------------- Utility ------------------------------- #
    def center_window(self):
        self.update_idletasks()
        w, h = 500, 450
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
