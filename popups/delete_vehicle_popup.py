# delete_vehicle_popup.py

import customtkinter as ctk
from tkinter import messagebox, simpledialog


class DeleteVehiclePopup(ctk.CTkToplevel):
    def __init__(self, master, db, refresh_callback=None):
        """
        Popup to sell (delete) a vehicle by Stock Number.
        :param master: parent window
        :param db: database instance
        :param refresh_callback: function to refresh main list after selling
        """
        super().__init__(master)
        self.db = db
        self.refresh_callback = refresh_callback

        self.title("Sell Vehicle")
        self.geometry("400x200")
        self.transient(master)
        self.grab_set()
        self.focus_force()
        self.center_window()

        # Instruction label
        ctk.CTkLabel(
            self,
            text="Enter Stock Number to sell:",
            anchor="w"
        ).pack(pady=(20, 5), padx=20, fill="x")

        # Stock Number Entry
        self.stock_var = ctk.StringVar()
        self.stock_entry = ctk.CTkEntry(self, textvariable=self.stock_var)
        self.stock_entry.pack(pady=5, padx=20, fill="x")
        self.stock_entry.bind("<KeyRelease>", self.uppercase_stock)

        # Buttons frame
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=15)

        # Sell button
        ctk.CTkButton(
            btn_frame,
            text="Sell Vehicle",
            fg_color="#b30000",
            hover_color="#e60000",
            command=self.sell_vehicle
        ).grid(row=0, column=0, padx=5)

        # Cancel button
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.destroy
        ).grid(row=0, column=1, padx=5)

    # ---------------- Helper Methods ---------------- #
    def uppercase_stock(self, event):
        """Force stock number entry to uppercase."""
        value = self.stock_var.get().upper()
        self.stock_var.set(value)

    def center_window(self):
        """Center the popup on the screen."""
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ---------------- Sell Logic ---------------- #
    def sell_vehicle(self):
        """Validate input and sell the vehicle."""
        stock_number = self.stock_var.get().strip().upper()

        if not stock_number:
            messagebox.showerror("Error", "Stock Number is required.")
            return

        # Confirm sale
        if not messagebox.askyesno(
            "Confirm Sale",
            f"Are you sure you want to sell vehicle {stock_number}?"
        ):
            return

        # Get seller name
        seller_name = simpledialog.askstring(
            "Seller Name",
            "Enter seller's name:"
        )
        if not seller_name or not seller_name.strip():
            messagebox.showerror("Error", "Seller name is required.")
            return

        # Attempt to sell vehicle
        try:
            success = self.db.sell_vehicle(stock_number, seller_name.strip())

            if not success:
                messagebox.showerror(
                    "Not Found",
                    f"No vehicle found with Stock Number {stock_number}."
                )
                return

            messagebox.showinfo(
                "Success",
                f"Vehicle {stock_number} sold successfully."
            )

            if self.refresh_callback:
                self.refresh_callback()

            self.destroy()

        except Exception as e:
            messagebox.showerror(
                "Database Error",
                f"Failed to sell vehicle:\n{e}"
            )
