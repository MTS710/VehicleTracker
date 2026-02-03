import customtkinter as ctk
from tkinter import messagebox

class PhotoTrackerPopup(ctk.CTkToplevel):
    """
    Photo Tracker popup with column alignment using SAFE padding offsets.
    """

    def __init__(self, master, db):
        super().__init__(master)
        self.db = db
        self.photo_widgets = {}

        self.title("Photo Tracker")
        self.geometry("900x500")
        self.transient(master)
        self.grab_set()
        self.center_window()

        self._setup_container()
        self._setup_header()
        self._setup_scrollable_rows()
        self._setup_save_button()

        self.load_vehicles()

    # ------------------------------- Setup UI ------------------------------- #
    def _setup_container(self):
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True, padx=8, pady=8)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(1, weight=1)

        # Safe padding offsets for each column
        base = 40
        self.col_pad = {
            0: base + 20,  # Stock #
            1: base + 0,   # Year
            2: base - 10,  # Make
            3: base - 12,  # Model
            4: base - 18,  # Warranty
            5: base + 0    # Photos Done
        }

    def _setup_header(self):
        self.header = ctk.CTkFrame(self.container)
        self.header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        for i in range(6):
            self.header.grid_columnconfigure(i, weight=1)

        titles = ["Stock #", "Year", "Make", "Model", "Warranty", "Photos Done?"]
        for col, text in enumerate(titles):
            lbl = ctk.CTkLabel(
                self.header,
                text=text,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="blue",
                anchor="w"
            )
            lbl.grid(row=0, column=col, sticky="w", padx=self.col_pad[col], pady=4)

    def _setup_scrollable_rows(self):
        self.scroll = ctk.CTkScrollableFrame(self.container)
        self.scroll.grid(row=1, column=0, sticky="nsew")
        for i in range(6):
            self.scroll.grid_columnconfigure(i, weight=1)

    def _setup_save_button(self):
        btn_frame = ctk.CTkFrame(self.container)
        btn_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        btn_frame.grid_columnconfigure(0, weight=1)

        save_btn = ctk.CTkButton(btn_frame, text="Save Changes", command=self.save_all)
        save_btn.grid(row=0, column=0, sticky="e", padx=10)

    # ------------------------------- Load & Display Vehicles ------------------------------- #
    def load_vehicles(self):
        # Clear old rows
        for widget in self.scroll.winfo_children():
            widget.destroy()
        self.photo_widgets.clear()

        vehicles = self.db.get_vehicles(exclude_status="Wholesale")

        for row_index, v in enumerate(vehicles):
            vehicle_id = v[0]
            stock, year, make, model, warranty, photos_done = v[2], v[6], v[4], v[5], v[11], v[12] or "No"

            # Helper to add a label
            def add_label(col, text):
                ctk.CTkLabel(self.scroll, text=text or "", anchor="w").grid(
                    row=row_index, column=col, sticky="w", padx=self.col_pad[col], pady=4
                )

            add_label(0, stock)
            add_label(1, year)
            add_label(2, make)
            add_label(3, model)
            add_label(4, warranty)

            # Photos Done dropdown
            dd = ctk.CTkComboBox(self.scroll, values=["No", "Yes"], width=95)
            dd.set(photos_done)
            dd.grid(row=row_index, column=5, sticky="w", padx=self.col_pad[5], pady=4)
            self.photo_widgets[vehicle_id] = dd

    # ------------------------------- Save ------------------------------- #
    def save_all(self):
        try:
            for vehicle_id, widget in self.photo_widgets.items():
                self.db.update_photos_taken(vehicle_id, widget.get())
            messagebox.showinfo("Saved", "Photo tracker updated successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save updates:\n{e}")

    # ------------------------------- Utility ------------------------------- #
    def center_window(self):
        self.update_idletasks()
        w, h = 900, 500
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
