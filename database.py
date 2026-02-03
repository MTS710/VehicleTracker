import sqlite3
import os
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(__file__), "vehicles.db")


class VehicleDatabase:
    """SQLite database handler for active and sold vehicles."""

    def __init__(self, db_file=DB_FILE):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def __del__(self):
        """Ensure database connection closes cleanly."""
        try:
            self.conn.close()
        except Exception:
            pass

    # ------------------------------- Database Setup ------------------------------- #
    def _init_db(self):
        cursor = self.conn.cursor()

        # Active vehicles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT,
                stock_number TEXT UNIQUE NOT NULL,
                vin TEXT,
                make TEXT,
                model TEXT,
                year TEXT,
                mileage TEXT,
                notes TEXT,
                status TEXT,
                location TEXT,
                warranty TEXT,
                photos_taken TEXT DEFAULT 'No',
                traded_in_by TEXT,
                certification TEXT
                
            )
        """)

        # Sold vehicles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sold_vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_number TEXT,
                vin TEXT,
                make TEXT,
                model TEXT,
                year TEXT,
                mileage TEXT,
                notes TEXT,
                status TEXT,
                location TEXT,
                seller_name TEXT,
                date_sold TEXT
            )
        """)

        self.conn.commit()

    # ------------------------------- Vehicle Retrieval ------------------------------- #
    def get_vehicle_by_stock(self, stock_number):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM vehicles WHERE stock_number = ?", (stock_number,))
        return cursor.fetchone()

    def get_vehicle_by_id(self, vehicle_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,))
        return cursor.fetchone()

    def stock_exists(self, stock_number):
        return self.get_vehicle_by_stock(stock_number) is not None

    def vin_exists(self, vin: str) -> bool:
        """Check if a VIN already exists in the database."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT 1 FROM vehicles WHERE vin = ? LIMIT 1",
            (vin.upper(),)
        )
        return cursor.fetchone() is not None


    def get_vehicles(self, exclude_status=None):
        cursor = self.conn.cursor()
        query = """
            SELECT id, user_name, stock_number, vin, make, model, year,
                   mileage, notes, status, location, warranty, photos_taken,
                   traded_in_by, certification
            FROM vehicles
        """
        params = []
        if exclude_status:
            if isinstance(exclude_status, str):
                exclude_status = [exclude_status]
            placeholders = ", ".join("?" * len(exclude_status))
            query += f" WHERE status NOT IN ({placeholders})"
            params = exclude_status
        cursor.execute(query, params)
        return cursor.fetchall()

    # ------------------------------- Vehicle Updates ------------------------------- #
    def update_vehicle(self, vehicle_id, field, value):
        allowed_fields = {"status", "location", "notes"}
        if field not in allowed_fields:
            raise ValueError(f"Cannot update field '{field}'")
        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE vehicles SET {field} = ? WHERE id = ?", (value, vehicle_id))
        self.conn.commit()

    def append_note(self, vehicle_id, new_note):
        vehicle = self.get_vehicle_by_id(vehicle_id)
        if vehicle is None:
            raise ValueError(f"Vehicle ID {vehicle_id} not found")
        updated_notes = (vehicle["notes"] or "") + "\n" + new_note
        self.update_vehicle(vehicle_id, "notes", updated_notes.strip())

    # ------------------------------- Add Vehicle ------------------------------- #
    def add_vehicle(self, vehicle_data):
        cursor = self.conn.cursor()
        date_added = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO vehicles (
                user_name, stock_number, vin, make, model, year, mileage,
                notes, status, location, warranty, photos_taken, traded_in_by, certification
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            vehicle_data.get("User Name", "Default"),
            vehicle_data["Stock Number"],
            vehicle_data.get("VIN", ""),
            vehicle_data.get("Make", ""),
            vehicle_data.get("Model", ""),
            vehicle_data.get("Year", ""),
            vehicle_data.get("Mileage", ""),
            vehicle_data.get("Notes", ""),
            vehicle_data.get("Status", "Undecided"),
            vehicle_data.get("Location", "Service"),
            vehicle_data.get("Warranty", ""),
            vehicle_data.get("Photos Taken", "No"),
            vehicle_data.get("Traded In By", ""),
             vehicle_data.get("certification", "")
        ))
        self.conn.commit()

    def update_photos_taken(self, vehicle_id, value):
        """
        Update the photos_taken field for a vehicle.
        :param vehicle_id: database ID of the vehicle
        :param value: 'Yes' or 'No'
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE vehicles SET photos_taken = ? WHERE id = ?",
            (value, vehicle_id)
        )
        self.conn.commit()



    # ------------------------------- Sell Vehicle ------------------------------- #
    def sell_vehicle(self, stock_number, seller_name):
        """
        Sell a vehicle by Stock Number: move from 'vehicles' to 'sold_vehicles'.
        Returns True if successful, False if vehicle not found.
        """
        cursor = self.conn.cursor()

        # Get the vehicle by stock number
        vehicle = self.get_vehicle_by_stock(stock_number)
        if not vehicle:
            return False

        # Insert into sold_vehicles
        cursor.execute("""
            INSERT INTO sold_vehicles (
                stock_number, vin, make, model, year, mileage,
                notes, status, location, seller_name, date_sold
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            vehicle["stock_number"],
            vehicle["vin"],
            vehicle["make"],
            vehicle["model"],
            vehicle["year"],
            vehicle["mileage"],
            vehicle["notes"],
            vehicle["status"],
            vehicle["location"],
            seller_name,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # date_sold
        ))

        # Delete from active vehicles
        cursor.execute("DELETE FROM vehicles WHERE stock_number = ?", (stock_number,))
        self.conn.commit()
        return True
