import customtkinter as ctk
import tkinter as tk
from tkinter import font as tkfont
from datetime import datetime
from tkinter import messagebox
from popups.profile_popup import ProfilePopup

class NotesPopup(ctk.CTkToplevel):
    def __init__(self, master, db, vehicle):
        super().__init__(master)
        self.db = db
        self.vehicle = vehicle

        self.title(f"Notes – {vehicle['Stock Number']}")
        self.geometry("700x750")
        self.transient(master)
        self.grab_set()
        self.focus_force()
        self.center_window()

        self._setup_notes_display()
        self._setup_name_department()
        self._setup_note_entry()
        self._setup_buttons()

        self.load_notes()

    # ------------------------------- UI Setup ------------------------------- #
    def _setup_notes_display(self):
        ctk.CTkLabel(self, text="Notes", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10,5))

        # Base font for all note text (adjust size here)
        self.base_font = tkfont.Font(family="Segoe UI", size=14)

        self.notes_display = tk.Text(
            self,
            width=75,
            height=22,
            wrap="word",
            state="disabled",
            bg="#e6ecff",
            fg="black",
            relief="solid",
            bd=1,
            padx=8,
            pady=8,
            font=self.base_font  # <-- ensure this font object is used
        )
        self.notes_display.pack(padx=10, pady=(0,10))

        # Timestamp font
        ts_font = tkfont.Font(family="Segoe UI", size=14, weight="bold")
        self.notes_display.tag_configure("timestamp", foreground="dark red", font=ts_font)

        # Configure tag for timestamp
        self.notes_display.tag_configure(
            "timestamp",
            foreground="dark red",
            font=ts_font
        )

    def _setup_name_department(self):
        ctk.CTkLabel(
            self, text="Your Name / Department", font=ctk.CTkFont(size=16)
        ).pack(pady=(10,5), padx=10, fill="x")

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(pady=5)

        self.name_entry = ctk.CTkEntry(frame, width=200)
        self.name_entry.pack(side="left", padx=5)

        self.department_var = ctk.StringVar(value="Sales")
        self.department_menu = ctk.CTkOptionMenu(
            frame, values=["Sales", "Service", "Parts"], variable=self.department_var, width=120
        )
        self.department_menu.pack(side="left", padx=5)

    def _setup_note_entry(self):
        ctk.CTkLabel(self, text="Add Note").pack(padx=10, pady=(10,0))
        self.note_entry = ctk.CTkTextbox(self, width=460, height=100)
        self.note_entry.pack(padx=10)

    def _setup_buttons(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(pady=15)

        ctk.CTkButton(frame, text="Add Note", width=140, command=self.add_note).pack(side="left", padx=10)
        ctk.CTkButton(frame, text="Vehicle Profile", width=140, command=self.open_profile_popup).pack(side="left", padx=10)

    # ------------------------------- Notes Handling ------------------------------- #
    def load_notes(self):
        self.notes_display.configure(state="normal")
        self.notes_display.delete("1.0", "end")

        row = self.db.get_vehicle_by_id(self.vehicle["id"])
        notes = row[8] if row and len(row) > 8 else ""

        if notes:
            notes_list = notes.split("\n\n")
            notes_list.reverse()  # newest notes first

            for note in notes_list:
                note_text = note.strip()

                # Insert the note text (timestamp + content + separator)
                self.notes_display.insert("1.0", note_text + "\n\n")

                # Apply timestamp tag if exists
                if note_text.startswith("[") and "]" in note_text:
                    end_idx = note_text.find("]") + 1
                    ts_start = "1.0"
                    ts_end = f"1.0+{end_idx}c"
                    self.notes_display.tag_add("timestamp", ts_start, ts_end)

        self.notes_display.configure(state="disabled")

    def add_note(self):
        name = self.name_entry.get().strip()
        department = self.department_var.get()
        note_text = self.note_entry.get("1.0", "end").strip()

        if not name or not note_text:
            messagebox.showwarning("Missing Info", "Please enter your name and a note.")
            return

        timestamp = datetime.now().strftime("%m/%d/%Y %I:%M %p")
        # Add separator as part of the note
        formatted_note = f"[{timestamp}] {name} ({department})\n{note_text}\n---------------------------------------------"

        # Save to database
        self.db.append_note(self.vehicle["id"], formatted_note)

        # Update local vehicle notes
        if self.vehicle.get("notes"):
            self.vehicle["notes"] += "\n\n" + formatted_note
        else:
            self.vehicle["notes"] = formatted_note

        self.note_entry.delete("1.0", "end")
        self.load_notes()

    # ------------------------------- Profile ------------------------------- #
    def open_profile_popup(self):
        ProfilePopup(self, self.vehicle)

    # ------------------------------- Utility ------------------------------- #
    def center_window(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
