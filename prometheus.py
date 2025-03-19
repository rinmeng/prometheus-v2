import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime, timedelta
import config
from chronos import initialize_driver, login, book_room
from tkinter import filedialog
import json

class PrometheusGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Prometheus Room Booking System")
        
        # Configure weight for root window grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        self.driver = None  # Initialize driver as None
        
        # Initialize default configuration
        self.config_data = {
            "area": 6,
            "room": 17,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "start_time": "06:00",
            "end_time": "07:00",
            "room_title": "",
            "room_description": "",
            "phone_number": "",
            "email": ""
        }
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure column weights in main_frame
        self.main_frame.grid_columnconfigure(1, weight=1)
        
        # Create form elements first
        self.create_form()
        
        # Create config buttons frame
        self.config_frame = ttk.Frame(self.main_frame)
        self.config_frame.grid(row=11, column=0, columnspan=2, pady=10)
        
        # Add Save/Load config buttons
        self.save_config_button = ttk.Button(self.config_frame, text="Save Config", command=self.save_config)
        self.save_config_button.grid(row=0, column=0, padx=5)
        
        self.load_config_button = ttk.Button(self.config_frame, text="Load Config", command=self.load_config_file)
        self.load_config_button.grid(row=0, column=1, padx=5)
        
        # Load existing config after creating form elements
        self.load_config()
        
        # Optional: Center the window on screen
        self.center_window()

    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'+{x}+{y}')

    def load_config(self):
        """Load configuration from config.py"""
        try:
            if os.path.exists('config.py'):
                import importlib
                importlib.reload(config)  # Reload config module
                
                # Update GUI elements with loaded configuration
                if hasattr(config, 'config'):
                    # Convert seconds since midnight to HH:MM format
                    start_seconds = config.config["start_time"]
                    end_seconds = config.config["end_time"]
                    
                    start_time = f"{start_seconds // 3600:02d}:{(start_seconds % 3600) // 60:02d}"
                    end_time = f"{end_seconds // 3600:02d}:{(end_seconds % 3600) // 60:02d}"
                    
                    # Update self.config_data with loaded configuration
                    self.config_data.update({
                        "area": config.config["area"],
                        "room": config.config["room"],
                        "date": config.config["date"],
                        "start_time": start_time,
                        "end_time": end_time,
                        "room_title": config.config.get("room_title", ""),
                        "room_description": config.config.get("room_description", ""),
                        "phone_number": config.config.get("phone_number", ""),
                        "email": config.config.get("email", "")
                    })
                    
                    # Find area name from area ID
                    area_name = next((k for k, v in config.area_map.items() 
                                    if v == config.config["area"]), "")
                    self.area_var.set(area_name)
                    self.update_rooms()
                    
                    # Find room name from room ID
                    room_name = next((k for k, v in config.rooms_map.items() 
                                    if v == config.config["room"]), "")
                    self.room_var.set(room_name)
                    
                    self.date_entry.delete(0, tk.END)
                    self.date_entry.insert(0, config.config.get("date", ""))
                    self.start_time_var.set(start_time)
                    self.update_end_times()  # Update end time options
                    self.end_time_var.set(end_time)
                    self.title_entry.delete(0, tk.END)
                    self.title_entry.insert(0, config.config.get("room_title", ""))
                    self.desc_entry.delete(0, tk.END)
                    self.desc_entry.insert(0, config.config.get("room_description", ""))
                    self.phone_entry.delete(0, tk.END)
                    self.phone_entry.insert(0, config.config.get("phone_number", ""))
                    self.email_entry.delete(0, tk.END)
                    self.email_entry.insert(0, config.config.get("email", ""))
                    
                    self.status_label.config(text="Configuration loaded successfully!")
                else:
                    messagebox.showinfo("Info", "No configuration data found in file.")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
    
    def create_form(self):
        # Area Selection
        ttk.Label(self.main_frame, text="Building:").grid(row=0, column=0, sticky=tk.W)
        self.area_var = tk.StringVar()
        self.area_combo = ttk.Combobox(self.main_frame, textvariable=self.area_var, state="readonly")
        self.area_combo['values'] = list(config.area_map.keys())
        self.area_combo.grid(row=0, column=1, sticky=(tk.W, tk.E))
        self.area_combo.bind('<<ComboboxSelected>>', self.update_rooms)
        
        # Room Selection
        ttk.Label(self.main_frame, text="Room:").grid(row=1, column=0, sticky=tk.W)
        self.room_var = tk.StringVar()
        self.room_combo = ttk.Combobox(self.main_frame, textvariable=self.room_var, state="readonly")
        self.room_combo.grid(row=1, column=1, sticky=(tk.W, tk.E))
        
        # Date Selection (replace the existing date selection code)
        self.day_label = ttk.Label(self.main_frame, text="Date:")  # Store label for updating
        self.day_label.grid(row=2, column=0, sticky=tk.W)
        self.date_entry = ttk.Entry(self.main_frame)
        self.date_entry.grid(row=2, column=1, sticky=(tk.W, tk.E))
        self.date_entry.insert(0, self.config_data["date"])
        
        # Bind the date entry to update day label when changed
        self.date_entry.bind('<KeyRelease>', self.update_day_label)
        self.update_day_label()  # Initialize the day label
        
        # Time Selection
        ttk.Label(self.main_frame, text="Start Time:").grid(row=3, column=0, sticky=tk.W)
        self.start_time_var = tk.StringVar()
        self.start_time_combo = ttk.Combobox(self.main_frame, textvariable=self.start_time_var)
        start_slots, _ = self.generate_time_slots()
        self.start_time_combo['values'] = start_slots
        self.start_time_combo.grid(row=3, column=1, sticky=(tk.W, tk.E))
        self.start_time_combo.bind('<<ComboboxSelected>>', self.update_end_times)
        
        ttk.Label(self.main_frame, text="End Time:").grid(row=4, column=0, sticky=tk.W)
        self.end_time_var = tk.StringVar()
        self.end_time_combo = ttk.Combobox(self.main_frame, textvariable=self.end_time_var)
        self.end_time_combo.grid(row=4, column=1, sticky=(tk.W, tk.E))
        
        # Booking Details
        ttk.Label(self.main_frame, text="Title (*):").grid(row=5, column=0, sticky=tk.W)
        self.title_entry = ttk.Entry(self.main_frame)
        self.title_entry.insert(0, self.config_data["room_title"])
        self.title_entry.grid(row=5, column=1, sticky=(tk.W, tk.E))
        
        ttk.Label(self.main_frame, text="Description:").grid(row=6, column=0, sticky=tk.W)
        self.desc_entry = ttk.Entry(self.main_frame, state="disabled")
        self.desc_entry.insert(0, config.config.get("room_description", "prometheus v2 by https://rinm.dev"))
        self.desc_entry.grid(row=6, column=1, sticky=(tk.W, tk.E))
        
        ttk.Label(self.main_frame, text="Phone:").grid(row=7, column=0, sticky=tk.W)
        self.phone_entry = ttk.Entry(self.main_frame, state="disabled")
        self.phone_entry.insert(0, config.config.get("phone_number", "000-000-0000"))
        self.phone_entry.grid(row=7, column=1, sticky=(tk.W, tk.E))
        
        ttk.Label(self.main_frame, text="Email (*):").grid(row=8, column=0, sticky=tk.W)
        self.email_entry = ttk.Entry(self.main_frame)
        self.email_entry.insert(0, self.config_data["email"])
        self.email_entry.grid(row=8, column=1, sticky=(tk.W, tk.E))
        
        # Book Button
        self.book_button = ttk.Button(self.main_frame, text="Book Room", command=self.book_room)
        self.book_button.grid(row=9, column=0, columnspan=2, pady=20)
        
        # Status Label
        self.status_label = ttk.Label(self.main_frame, text="")
        self.status_label.grid(row=10, column=0, columnspan=2)
    
    def generate_time_slots(self):
        """Generate time slots based on selected area"""
        start_slots = []
        selected_area = self.area_var.get()
        
        # Set time restrictions based on area
        if selected_area and ("EME:" in selected_area):  # Check for any EME area
            start_time = "07:00"  # 7 AM
            end_time = "20:00"    # 8 PM
        elif selected_area and selected_area == "Library":
            start_time = "07:00"  # 7 AM
            end_time = "21:30"    # 9:30 PM
        else:
            start_time = "06:00"  # 6 AM default
            end_time = "23:30"    # 11:30 PM default
        
        # Convert to datetime objects
        current = datetime.strptime(start_time, "%H:%M")
        end = datetime.strptime(end_time, "%H:%M")
        
        # Generate all possible start time slots
        while current <= end:
            start_slots.append(current.strftime("%H:%M"))
            current += timedelta(minutes=30)
        
        return start_slots, []  # Return empty list for end_slots as they're now dynamic

    def update_end_times(self, event=None):
        """Update end time options based on selected start time and area"""
        selected_start = self.start_time_var.get()
        selected_area = self.area_var.get()
        
        if not selected_start:
            return
            
        # Convert start time to datetime for calculations
        start_time = datetime.strptime(selected_start, "%H:%M")
        
        # Set end time limits based on area
        if selected_area and ("EME:" in selected_area):  # Check for any EME area
            end_limit = datetime.strptime("20:30", "%H:%M")  # 8:30 PM
        elif selected_area and selected_area == "Library":
            end_limit = datetime.strptime("22:00", "%H:%M")  # 10:00 PM
        else:
            end_limit = datetime.strptime("00:30", "%H:%M") + timedelta(days=1)
        
        # Calculate end times (up to 6 hours from start time)
        end_slots = []
        current = start_time + timedelta(minutes=30)  # First slot is 30 mins after start
        max_end = min(start_time + timedelta(hours=6), end_limit)  # Use the earlier of 6 hours or area limit
        
        # Generate valid end time slots
        while current <= max_end:
            end_slots.append(current.strftime("%H:%M"))
            current += timedelta(minutes=30)
        
        # Update end time dropdown
        self.end_time_combo['values'] = end_slots
        if end_slots:  # Set first available slot as default
            self.end_time_var.set(end_slots[0])
    
    def update_rooms(self, event=None):
        """Update room list based on selected area"""
        selected_area = self.area_var.get()
        
        # Clear current room selection
        self.room_var.set('')
        
        if selected_area:
            area_id = config.area_map[selected_area]
            
            # Define special cases for EME Tower 2 rooms
            eme_tower2_special = ["EME 1252", "EME 1254"]
            
            # Filter rooms for selected area
            if selected_area == "EME: Tower 2":
                # Include both EME 2 rooms and special EME 1 rooms that belong to Tower 2
                area_rooms = [room for room in config.rooms_map.keys() 
                             if (room.startswith("EME 2") or 
                                 any(room.startswith(special) for special in eme_tower2_special))]
            elif selected_area == "EME: Tower 1":
                # Exclude the special EME 1 rooms that belong to Tower 2
                area_rooms = [room for room in config.rooms_map.keys() 
                             if (room.startswith("EME 1") and 
                                 not any(room.startswith(special) for special in eme_tower2_special))]
            else:
                # Handle other areas normally
                area_rooms = [room for room in config.rooms_map.keys() 
                             if room.startswith(self.get_area_prefix(selected_area))]
            
            self.room_combo['values'] = area_rooms
            
            # Automatically select the first room if available
            if area_rooms:
                self.room_var.set(area_rooms[0])
        else:
            # Clear room options if no area is selected
            self.room_combo['values'] = []
    
    def get_area_prefix(self, area_name):
        """Get room prefix based on area name"""
        prefixes = {
            "Library": "LIB",
            "Commons: Floor 0": "COM 0",
            "Commons: Floor 1": "COM 1",
            "Commons: Floor 3": "COM 3",
            "EME: Tower 1": "EME 1",
            "EME: Tower 2": "EME 2"
        }
        return prefixes.get(area_name, "")
    
    def time_to_seconds(self, time_str):
        """Convert HH:MM time to seconds since midnight"""
        try:
            hours, minutes = map(int, time_str.split(":"))
            return hours * 3600 + minutes * 60
        except (ValueError, TypeError, AttributeError):
            return 0  # Return 0 seconds as fallback
    
    def book_room(self):
        """Handle room booking"""
        try:
            # Validate required fields
            if not self.title_entry.get().strip():
                messagebox.showerror("Error", "Title is required!")
                return
                
            if not self.email_entry.get().strip():
                messagebox.showerror("Error", "Email is required!")
                return

            # Save configuration first
            self.save_config()
            
            if self.driver is None:
                self.driver = initialize_driver()
                login(self.driver)

            # Update config with form data
            config.config.update({
                "area": config.area_map[self.area_var.get()],
                "room": config.rooms_map[self.room_var.get()],
                "start_time": self.time_to_seconds(self.start_time_var.get()),
                "end_time": self.time_to_seconds(self.end_time_var.get()),
                "date": self.date_entry.get(),
                "room_title": self.title_entry.get(),
                "room_description": "prometheus v2 by https://rinm.dev",  # Default description
                "phone_number": "000-000-0000",  # Default phone
                "email": self.email_entry.get()
            })
            
            # Call the booking function with the driver
            book_room(self.driver)
            
            self.status_label.config(text="Room booked and configuration saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Booking failed: {str(e)}")
            self.status_label.config(text="Booking failed!")
    
    def save_config(self):
        """Save current configuration to config.py"""
        try:
            config_data = {
                "area": config.area_map[self.area_var.get()],
                "room": config.rooms_map[self.room_var.get()],
                "date": self.date_entry.get(),
                "start_time": self.time_to_seconds(self.start_time_var.get()),
                "end_time": self.time_to_seconds(self.end_time_var.get()),
                "room_title": self.title_entry.get(),
                "room_description": self.desc_entry.get(),
                "phone_number": self.phone_entry.get(),
                "email": self.email_entry.get()
            }
            
            # Write to config.py
            with open('config.py', 'w') as f:
                f.write("config = " + json.dumps(config_data, indent=4))
                f.write("\n\n# Room mappings\n")
                f.write("rooms_map = " + json.dumps(config.rooms_map, indent=4))
                f.write("\n\n# Area mappings\n")
                f.write("area_map = " + json.dumps(config.area_map, indent=4))
                
            self.status_label.config(text="Configuration saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
    
    def load_config_file(self):
        """Load configuration from a JSON file"""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Configuration"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r') as f:
                loaded_config = json.load(f)
            
            # Update GUI elements with loaded configuration
            if loaded_config:
                self.area_var.set(loaded_config.get("area", ""))
                self.update_rooms()  # Update room list based on selected area
                self.room_var.set(loaded_config.get("room", ""))
                self.date_entry.delete(0, tk.END)
                self.date_entry.insert(0, loaded_config.get("date", ""))
                
                # Convert seconds to HH:MM format for time fields
                start_seconds = loaded_config.get("start_time", 0)
                end_seconds = loaded_config.get("end_time", 0)
                start_time = datetime.fromtimestamp(start_seconds).strftime("%H:%M")
                end_time = datetime.fromtimestamp(end_seconds).strftime("%H:%M")
                
                self.start_time_var.set(start_time)
                self.update_end_times()  # Update end time options
                self.end_time_var.set(end_time)
                
                self.title_entry.delete(0, tk.END)
                self.title_entry.insert(0, loaded_config.get("room_title", ""))
                self.desc_entry.delete(0, tk.END)
                self.desc_entry.insert(0, loaded_config.get("room_description", ""))
                self.phone_entry.delete(0, tk.END)
                self.phone_entry.insert(0, loaded_config.get("phone_number", ""))
                self.email_entry.delete(0, tk.END)
                self.email_entry.insert(0, loaded_config.get("email", ""))
                
                self.status_label.config(text="Configuration loaded successfully!")
            else:
                messagebox.showinfo("Info", "No configuration data found in file.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")

    def update_day_label(self, event=None):
        """Update the date label to include the day of week"""
        try:
            date_str = self.date_entry.get()
            if date_str:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                day_name = date_obj.strftime("%a")  # Get abbreviated day name
                self.day_label.config(text=f"Date ({day_name}):")
            else:
                self.day_label.config(text="Date:")
        except ValueError:
            self.day_label.config(text="Date:")

def main():
    root = tk.Tk()
    app = PrometheusGUI(root)
    root.mainloop()
    
    # Clean up
    if app.driver:
        app.driver.quit()

def display_prometheus_banner():
    banner = r"""
  _____                          _   _                     __     _____  
 |  __ \                        | | | |                   /  \   / __  \ 
 | |__) | __ ___  _ __ ___   ___| |_| |__   ___ _   _ ___ \__/   `' / /' 
 |  ___/ '__/ _ \| '_ ` _ \ / _ \ __| '_ \ / _ \ | | / __|         / /    
 | |   | | | (_) | | | | | |  __/ |_| | | |  __/ |_| \__ \       ./ /___  
 |_|   |_|  \___/|_| |_| |_|\___|\__|_| |_|\___|\__,_|___/       \_____/  
                                                                       
          ╔════════════════════════════════════════════════╗
          ║                  PROMETHEUS v2                 ║
          ║                https://rinm.dev                ║
          ╚════════════════════════════════════════════════╝
    """
    print(banner)

if __name__ == "__main__":
    display_prometheus_banner()
    print("prometheus has started, please do not close this window")
    print("Use the GUI to book rooms, this panel is for messages only.")
    print("Make sure you check https://github.com/rinmeng/prometheus-v2 for updates & setups.")
    main()