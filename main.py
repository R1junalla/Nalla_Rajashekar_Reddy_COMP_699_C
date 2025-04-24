import tkinter as tk  # Standard GUI library
from tkinter import messagebox  # For pop-up dialogs
from tkinter import ttk  # Themed widget set
import json  # For data persistence in JSON format
import os  # For filesystem operations
import hashlib  # For secure password hashing
import random  # For generating reset tokens
import requests  # For HTTP requests to Google Maps APIs
import http.client  # For HTTP requests to CollectAPI
from datetime import datetime  # For timestamps

# ===== Configuration =====
GOOGLE_API_KEY = 'AIzaSyBF5itvEoV47L_Wa1lgZyznpl03HzMszCQ'  # Your Google API key
TRIPS_FILE = 'trips.json'  # File to store saved trips
NOTIFICATIONS_FILE = 'notifications.json'  # File to store watchlist settings


class UserManager:
    """
    Handles user account operations: registration, login, password reset,
    profile updates, and trip data persistence.
    """
    def __init__(self):
        self.accounts_file = 'accounts.json'
        self.resets_file = 'resets.json'
        self._load_files()

    def _load_files(self):
        """Load accounts and reset tokens from disk (or initialize empty)."""
        if os.path.exists(self.accounts_file):
            with open(self.accounts_file, 'r') as f:
                data = json.load(f)
                self.accounts = data if isinstance(data, dict) else {}
        else:
            self.accounts = {}
        if os.path.exists(self.resets_file):
            with open(self.resets_file, 'r') as f:
                data = json.load(f)
                self.resets = data if isinstance(data, dict) else {}
        else:
            self.resets = {}

    def save_accounts(self):
        """Write accounts to JSON file."""
        with open(self.accounts_file, 'w') as f:
            json.dump(self.accounts, f, indent=4)

    def save_resets(self):
        """Write reset tokens to JSON file."""
        with open(self.resets_file, 'w') as f:
            json.dump(self.resets, f, indent=4)

    def hash_password(self, pwd):
        """Return SHA-256 hash of the password."""
        return hashlib.sha256(pwd.encode()).hexdigest()

    def register(self, email, pwd):
        """
        Register a new user.
        Returns False if email already exists, True on success.
        """
        if email in self.accounts:
            return False
        self.accounts[email] = {
            'password': self.hash_password(pwd),
            'fuel_type': None,
            'efficiency': None,
            'tank_capacity': None
        }
        self.save_accounts()
        return True

    def login(self, email, pwd):
        """Check credentials for login."""
        user = self.accounts.get(email)
        return bool(user and user['password'] == self.hash_password(pwd))

    def update_profile(self, email, fuel, eff, capacity):
        """Update vehicle profile for a user."""
        user = self.accounts.get(email)
        if user:
            user['fuel_type'] = fuel
            user['efficiency'] = eff
            user['tank_capacity'] = capacity
            self.save_accounts()

    def change_email(self, old_email, new_email):
        """
        Change a user's email address.
        Returns False if the new email is already in use.
        """
        if new_email in self.accounts:
            return False
        self.accounts[new_email] = self.accounts.pop(old_email)
        if old_email in self.resets:
            self.resets[new_email] = self.resets.pop(old_email)
        self.save_accounts()
        self.save_resets()
        return True

    def delete_user(self, email):
        """Remove a user account and associated reset token."""
        if email in self.accounts:
            del self.accounts[email]
            self.save_accounts()
        if email in self.resets:
            del self.resets[email]
            self.save_resets()

    def create_reset_token(self, email):
        """
        Generate and store a 6-digit reset token for password resets.
        Returns the token, or None if email not found.
        """
        if email not in self.accounts:
            return None
        token = str(random.randint(100000, 999999))
        self.resets[email] = token
        self.save_resets()
        return token

    def verify_reset_token(self, email, token):
        """Check if provided token matches stored reset token."""
        return self.resets.get(email) == token

    def reset_password(self, email, new_pwd):
        """
        Update the user's password after a reset.
        Remove the reset token once used.
        """
        user = self.accounts.get(email)
        if not user:
            return False
        user['password'] = self.hash_password(new_pwd)
        self.save_accounts()
        if email in self.resets:
            del self.resets[email]
            self.save_resets()
        return True

    # --- Trip storage ---
    def load_trips(self):
        """Load list of trips from disk."""
        if os.path.exists(TRIPS_FILE):
            with open(TRIPS_FILE, 'r') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        return []

    def save_trips(self, trips):
        """Save list of trips to disk."""
        with open(TRIPS_FILE, 'w') as f:
            json.dump(trips, f, indent=4)

    def add_trip(self, trip):
        """Append a new trip to the stored list."""
        trips = self.load_trips()
        trips.append(trip)
        self.save_trips(trips)

    def update_trip(self, index, trip):
        """Replace an existing trip by index."""
        trips = self.load_trips()
        if 0 <= index < len(trips):
            trips[index] = trip
            self.save_trips(trips)

    def delete_trip(self, index):
        """Remove a trip by index."""
        trips = self.load_trips()
        if 0 <= index < len(trips):
            trips.pop(index)
            self.save_trips(trips)


def decode_polyline(polyline_str):
    """
    Decode a Google Maps encoded polyline into a list of (lat, lng) tuples.
    """
    index, lat, lng = 0, 0, 0
    coords = []
    while index < len(polyline_str):
        shift, result = 0, 0
        # Decode latitude
        while True:
            b = ord(polyline_str[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlat = ~(result >> 1) if (result & 1) else (result >> 1)
        lat += dlat

        # Decode longitude
        shift, result = 0, 0
        while True:
            b = ord(polyline_str[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlng = ~(result >> 1) if (result & 1) else (result >> 1)
        lng += dlng

        coords.append((lat * 1e-5, lng * 1e-5))
    return coords


class App(tk.Tk):
    """Main application class inheriting from Tkinter root window."""
    def __init__(self):
        super().__init__()
        self.title('Car Fuel Cost Calculator')
        self.geometry('900x650')
        self.um = UserManager()  # Instantiate user manager
        self.current_user = None
        self.show_login()  # Start with login screen

    def clear(self):
        """Destroy all child widgets (for screen transitions)."""
        for w in self.winfo_children():
            w.destroy()

    # --- Authentication Screens ---
    def show_login(self):
        """Build login screen UI."""
        self.clear()
        tk.Label(self, text='Login', font=('Arial', 16)).pack(pady=10)
        self.email_var = tk.StringVar()
        self.pwd_var = tk.StringVar()
        tk.Label(self, text='Email').pack()
        tk.Entry(self, textvariable=self.email_var, width=40).pack(pady=5)
        tk.Label(self, text='Password').pack()
        tk.Entry(self, textvariable=self.pwd_var, show='*', width=40).pack(pady=5)
        tk.Button(self, text='Login', width=20, command=self.login_action).pack(pady=5)
        tk.Button(self, text='Register', width=20, command=self.show_register).pack(pady=5)
        tk.Button(self, text='Forgot Password', width=20, command=self.show_reset_request).pack(pady=5)

    def login_action(self):
        """Handle login button click."""
        if self.um.login(self.email_var.get(), self.pwd_var.get()):
            self.current_user = self.email_var.get()
            messagebox.showinfo('Success', 'Logged in successfully.')
            self.show_main()
        else:
            messagebox.showerror('Error', 'Invalid credentials')

    def show_register(self):
        """Build registration screen UI."""
        self.clear()
        tk.Label(self, text='Register', font=('Arial', 16)).pack(pady=10)
        self.reg_email = tk.StringVar()
        self.reg_pwd1 = tk.StringVar()
        self.reg_pwd2 = tk.StringVar()
        for txt, var, show in [
            ('Email', self.reg_email, False),
            ('Password', self.reg_pwd1, True),
            ('Confirm Password', self.reg_pwd2, True)
        ]:
            tk.Label(self, text=txt).pack()
            tk.Entry(self, textvariable=var, show='*' if show else '', width=40).pack(pady=5)
        tk.Button(self, text='Register', width=20, command=self.register_action).pack(pady=5)
        tk.Button(self, text='Back', width=20, command=self.show_login).pack(pady=5)

    def register_action(self):
        """Handle registration logic and feedback."""
        e = self.reg_email.get()
        p1 = self.reg_pwd1.get()
        p2 = self.reg_pwd2.get()
        if not e or not p1 or p1 != p2:
            messagebox.showerror('Error', 'Complete fields correctly')
            return
        if self.um.register(e, p1):
            messagebox.showinfo('Success', 'Registered')
            self.show_login()
        else:
            messagebox.showerror('Error', 'Email exists')

    def show_reset_request(self):
        """Build initial password reset screen."""
        self.clear()
        tk.Label(self, text='Reset Password', font=('Arial', 16)).pack(pady=10)
        self.reset_email = tk.StringVar()
        tk.Label(self, text='Email').pack()
        tk.Entry(self, textvariable=self.reset_email, width=40).pack(pady=5)
        tk.Button(self, text='Generate Token', width=20, command=self.send_token).pack(pady=5)
        tk.Button(self, text='Back', width=20, command=self.show_login).pack(pady=5)

    def send_token(self):
        """Generate and display reset token (saved in resets.json)."""
        token = self.um.create_reset_token(self.reset_email.get())
        if token:
            messagebox.showinfo('Token', 'Check resets.json for your token.')
            self.show_reset_confirm()
        else:
            messagebox.showerror('Error', 'Email not found')

    def show_reset_confirm(self):
        """Build screen to input reset token and new password."""
        self.clear()
        tk.Label(self, text='Confirm Reset', font=('Arial', 16)).pack(pady=10)
        self.token_var = tk.StringVar()
        self.new1 = tk.StringVar()
        self.new2 = tk.StringVar()
        for lbl, var in [('Token', self.token_var), ('New Password', self.new1), ('Confirm', self.new2)]:
            tk.Label(self, text=lbl).pack()
            tk.Entry(self, textvariable=var, show='*', width=40).pack(pady=5)
        tk.Button(self, text='Reset', width=20, command=self.reset_action).pack(pady=5)

    def reset_action(self):
        """Validate token and reset the password."""
        if self.new1.get() != self.new2.get():
            messagebox.showerror('Error', 'Password mismatch')
            return
        if self.um.verify_reset_token(self.reset_email.get(), self.token_var.get()):
            self.um.reset_password(self.reset_email.get(), self.new1.get())
            messagebox.showinfo('Success', 'Password updated')
            self.show_login()
        else:
            messagebox.showerror('Error', 'Invalid token')

    # --- Main UI with Tabs ---
    def show_main(self):
        """Build the main application interface with tabs."""
        self.clear()
        NB = ttk.Notebook(self)
        NB.pack(expand=True, fill='both')

        pF = ttk.Frame(NB)  # Profile tab
        tF_page = ttk.Frame(NB)  # Trip planner tab
        history_page = ttk.Frame(NB)  # History & reports tab
        notif_page = ttk.Frame(NB)  # Notifications & alerts tab

        NB.add(pF, text='Profile')
        NB.add(tF_page, text='Trip Planner')
        NB.add(history_page, text='Trip History & Reports')
        NB.add(notif_page, text='Notifications & Alerts')

        self.build_profile(pF)

        # Trip Planner with scrollable canvas
        canvas = tk.Canvas(tF_page)
        scrollbar = ttk.Scrollbar(tF_page, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        tF = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=tF, anchor="nw")
        tF.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        self.build_trip(tF)
        self.build_history(history_page)
        self.build_notifications(notif_page)

    def build_profile(self, frame):
        """Create profile management UI."""
        tk.Label(frame, text=f'Hello, {self.current_user}', font=('Arial', 14)).pack(pady=10)
        tk.Button(frame, text='Change Password', width=20, command=self.show_change_password).pack(pady=5)
        tk.Button(frame, text='Change Email', width=20, command=self.show_change_email).pack(pady=5)
        tk.Button(frame, text='Delete Account', width=20, command=self.delete_account_action).pack(pady=5)
        tk.Button(frame, text='Logout', width=20, command=self.logout).pack(pady=5)

    def show_change_password(self):
        """Open dialog to change current password."""
        w = tk.Toplevel(self)
        w.title('Change Password')
        cv = tk.StringVar()
        n1 = tk.StringVar()
        n2 = tk.StringVar()
        for txt, var in [('Current Password', cv), ('New Password', n1), ('Confirm', n2)]:
            tk.Label(w, text=txt).pack(pady=2)
            tk.Entry(w, textvariable=var, show='*', width=30).pack(pady=5)
        tk.Button(w, text='Submit', command=lambda: self.change_password_action(w, cv.get(), n1.get(), n2.get())).pack(pady=10)

    def change_password_action(self, win, old, new1, new2):
        """Validate and apply password change."""
        if new1 != new2:
            messagebox.showerror('Error', 'Password mismatch')
            return
        if not self.um.login(self.current_user, old):
            messagebox.showerror('Error', 'Current password incorrect')
            return
        self.um.reset_password(self.current_user, new1)
        messagebox.showinfo('Success', 'Password updated')
        win.destroy()

    def show_change_email(self):
        """Open dialog to change current email."""
        w = tk.Toplevel(self)
        w.title('Change Email')
        ne = tk.StringVar()
        pw = tk.StringVar()
        tk.Label(w, text='New Email').pack(pady=2)
        tk.Entry(w, textvariable=ne, width=30).pack(pady=5)
        tk.Label(w, text='Password').pack(pady=2)
        tk.Entry(w, textvariable=pw, show='*', width=30).pack(pady=5)
        tk.Button(w, text='Submit', command=lambda: self.change_email_action(w, ne.get(), pw.get())).pack(pady=10)

    def change_email_action(self, win, new_email, pwd):
        """Validate password and apply email change."""
        if not self.um.login(self.current_user, pwd):
            messagebox.showerror('Error', 'Password incorrect')
            return
        if self.um.change_email(self.current_user, new_email):
            messagebox.showinfo('Success', 'Email changed')
            win.destroy()
            self.logout()
        else:
            messagebox.showerror('Error', 'New email already in use')

    def delete_account_action(self):
        """Confirm and delete the current user account."""
        if messagebox.askyesno('Confirm', 'Delete account permanently?'):
            self.um.delete_user(self.current_user)
            messagebox.showinfo('Deleted', 'Account deleted')
            self.logout()

    def logout(self):
        """Log out and return to login screen."""
        self.current_user = None
        self.show_login()

    def build_trip(self, frame):
        """Build the trip planner UI (vehicle profile and route settings)."""
        # Vehicle profile inputs
        labels = ['Fuel Type', 'Efficiency (mpg)', 'Tank Capacity (gal)']
        vars_ = [
            tk.StringVar(value=self.um.accounts[self.current_user].get(field, '') or '')
            for field in ['fuel_type', 'efficiency', 'tank_capacity']
        ]
        for i, lab in enumerate(labels):
            tk.Label(frame, text=lab).grid(row=i, column=0, pady=5, sticky='e')
            tk.Entry(frame, textvariable=vars_[i], width=30).grid(row=i, column=1, pady=5, sticky='w')
        tk.Button(
            frame, text='Update Vehicle',
            command=lambda: [
                self.um.update_profile(
                    self.current_user,
                    vars_[0].get(),
                    float(vars_[1].get()),
                    float(vars_[2].get())
                ),
                messagebox.showinfo('OK', 'Vehicle updated')
            ]
        ).grid(row=3, column=1, pady=10, sticky='w')

        # Route inputs
        rlabels = ['Start Location', 'Destination', 'Stops (comma-separated)']
        rvars = [tk.StringVar() for _ in rlabels]
        for i, lab in enumerate(rlabels):
            tk.Label(frame, text=lab).grid(row=4 + i, column=0, pady=5, sticky='e')
            tk.Entry(frame, textvariable=rvars[i], width=50).grid(row=4 + i, column=1, pady=5, sticky='w')
        tk.Button(
            frame, text='Calculate Route',
            command=lambda: self.calculate_route(
                rvars[0].get(), rvars[1].get(), rvars[2].get()
            )
        ).grid(row=7, column=1, pady=10)

        # Display route summary
        self.route_result = tk.Text(frame, height=6, width=80, state='disabled')
        self.route_result.grid(row=8, column=0, columnspan=2, padx=10)

        # Display the list of states along the route
        tk.Label(frame, text='States Along Route').grid(row=9, column=0, columnspan=2, sticky='w', padx=10)
        self.state_result = tk.Text(frame, height=8, width=80, state='disabled')
        self.state_result.grid(row=10, column=0, columnspan=2, padx=10)

        # State selection for price lookup
        tk.Label(frame, text='Select State').grid(row=11, column=0, sticky='e', padx=10, pady=5)
        self.state_var = tk.StringVar()
        self.state_dropdown = ttk.Combobox(frame, textvariable=self.state_var, state='readonly', width=28)
        self.state_dropdown.grid(row=11, column=1, sticky='w', pady=5)
        tk.Button(frame, text='Get Prices', width=20, command=self.show_prices).grid(row=11, column=2, padx=5, pady=5)

        # Display price results for selected state
        self.price_result = tk.Text(frame, height=6, width=80, state='disabled')
        self.price_result.grid(row=12, column=0, columnspan=3, padx=10, pady=5)

        # Buttons for cost calculation and saving trip
        tk.Button(frame, text='Calculate Fuel Cost for the Trip', width=30, command=self.calculate_cost)\
            .grid(row=13, column=0, pady=10)
        tk.Button(frame, text='Save Trip', width=30, command=self.save_current_trip)\
            .grid(row=13, column=1, pady=10)

        # Display calculated cost results
        self.cost_result = tk.Text(frame, height=4, width=80, state='disabled')
        self.cost_result.grid(row=14, column=0, columnspan=3, padx=10, pady=5)

    def save_current_trip(self):
        """Save the last calculated trip to history."""
        if not hasattr(self, 'last_distance') or not hasattr(self, 'route_states'):
            messagebox.showerror('Error', 'No trip to save')
            return
        record = {
            'timestamp': datetime.now().isoformat(),
            'origin': self.origin,
            'destination': self.destination,
            'states': self.route_states,
            'distance_km': self.last_distance,
            'fuel_efficiency': self.um.accounts[self.current_user]['efficiency'],
            'fuel_type': self.um.accounts[self.current_user]['fuel_type'],
            'total_cost': self.current_cost
        }
        self.um.add_trip(record)
        messagebox.showinfo('Saved', 'Trip saved to history')
        self.refresh_history()

    def build_history(self, frame):
        """Create trip history table and actions."""
        cols = ('Date', 'From', 'To', 'Cost')
        self.history_tv = ttk.Treeview(frame, columns=cols, show='headings')
        for c in cols:
            self.history_tv.heading(c, text=c)
        self.history_tv.pack(expand=True, fill='both')
        btnf = ttk.Frame(frame)
        btnf.pack(fill='x')
        ttk.Button(btnf, text='Delete Trip', command=self.delete_selected_trip).pack(side='left', padx=5)
        ttk.Button(btnf, text='Generate Report', command=self.generate_report).pack(side='left', padx=5)
        self.refresh_history()

    def refresh_history(self):
        """Reload trip history into the table."""
        for i in self.history_tv.get_children():
            self.history_tv.delete(i)
        for idx, trip in enumerate(self.um.load_trips()):
            dt = trip['timestamp'].split('T')[0]
            self.history_tv.insert(
                '', 'end', iid=idx,
                values=(dt, trip['origin'], trip['destination'], f"{trip['total_cost']:.2f}")
            )

    def delete_selected_trip(self):
        """Delete the trip currently selected in history."""
        sel = self.history_tv.selection()
        if not sel:
            return
        idx = int(sel[0])
        self.um.delete_trip(idx)
        self.refresh_history()

    def generate_report(self):
        """Show total fuel expenses across all saved trips."""
        total = sum(t['total_cost'] for t in self.um.load_trips())
        messagebox.showinfo('Fuel Expense Report', f'Total spent on fuel: {total:.2f}')

    # --- Notifications & Alerts Tab ---
    def load_watchlist(self):
        """Load price watchlist from disk."""
        if os.path.exists(NOTIFICATIONS_FILE):
            try:
                with open(NOTIFICATIONS_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('watchlist', [])
            except:
                return []
        return []

    def save_watchlist(self):
        """Persist watchlist to disk."""
        try:
            with open(NOTIFICATIONS_FILE, 'w') as f:
                json.dump({'watchlist': self.watchlist}, f, indent=4)
        except Exception as e:
            messagebox.showerror('Error', f'Could not save watchlist: {e}')

    def build_notifications(self, frame):
        """Build the UI for price change watchlist management."""
        self.watchlist = self.load_watchlist()

        # Fetch list of all states for dropdown
        states_list = []
        try:
            conn = http.client.HTTPSConnection("api.collectapi.com")
            headers = {
                'content-type': 'application/json',
                'authorization': 'apikey 0zJdI2HWc9CA41EoOevtOO:5nSi8IbSVVL4D4ALGK2N8b'
            }
            conn.request("GET", "/gasPrice/allUsaPrice", headers=headers)
            res = conn.getresponse()
            prices = json.loads(res.read().decode()).get('result', [])
            states_list = [item.get('name') for item in prices]
        except:
            pass

        # State selection
        tk.Label(frame, text='State').grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.notif_state_var = tk.StringVar()
        ttk.Combobox(
            frame, textvariable=self.notif_state_var,
            values=states_list, state='readonly', width=30
        ).grid(row=0, column=1, sticky='w', padx=5, pady=5)

        # Frequency input (minutes)
        tk.Label(frame, text='Frequency (min)').grid(row=1, column=0, sticky='e', padx=5, pady=5)
        self.freq_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.freq_var, width=10).grid(row=1, column=1, sticky='w', padx=5, pady=5)

        # Threshold input (% change)
        tk.Label(frame, text='Price Change (%)').grid(row=2, column=0, sticky='e', padx=5, pady=5)
        self.threshold_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.threshold_var, width=10).grid(row=2, column=1, sticky='w', padx=5, pady=5)

        # Add to watchlist button
        tk.Button(frame, text='Add to Watchlist', command=self.add_to_watchlist)\
            .grid(row=3, column=0, columnspan=2, pady=10)

        # Display current watchlist entries
        cols = ('State', 'Frequency(min)', 'Change(%)')
        self.watch_tv = ttk.Treeview(frame, columns=cols, show='headings', height=8)
        for c in cols:
            self.watch_tv.heading(c, text=c)
            self.watch_tv.column(c, width=120)
        self.watch_tv.grid(row=4, column=0, columnspan=3, padx=10, pady=5)

        # Remove selected watchlist entries button
        tk.Button(frame, text='Remove Selected', command=self.remove_selected_watchlist)\
            .grid(row=5, column=0, columnspan=2, pady=5)

        self.refresh_watchlist()

    def add_to_watchlist(self):
        """Add a new entry to the price watchlist."""
        state = self.notif_state_var.get()
        freq = self.freq_var.get()
        thresh = self.threshold_var.get()
        if not state or not freq or not thresh:
            messagebox.showerror('Error', 'Complete all fields')
            return
        try:
            freq_i = int(freq)
            thresh_f = float(thresh)
        except:
            messagebox.showerror('Error', 'Invalid frequency or threshold')
            return
        for item in self.watchlist:
            if item['state'] == state:
                messagebox.showerror('Error', 'State already in watchlist')
                return
        entry = {'state': state, 'frequency': freq_i, 'threshold': thresh_f}
        self.watchlist.append(entry)
        self.save_watchlist()
        self.refresh_watchlist()

    def remove_selected_watchlist(self):
        """Remove selected entries from the watchlist."""
        sel = self.watch_tv.selection()
        if not sel:
            return
        for iid in sel:
            vals = self.watch_tv.item(iid, 'values')
            for item in self.watchlist:
                if (item['state'], str(item['frequency']), str(item['threshold'])) == vals:
                    self.watchlist.remove(item)
                    break
        self.save_watchlist()
        self.refresh_watchlist()

    def refresh_watchlist(self):
        """Reload watchlist entries into the table."""
        for i in self.watch_tv.get_children():
            self.watch_tv.delete(i)
        for item in self.watchlist:
            self.watch_tv.insert(
                '', 'end',
                values=(item['state'], item['frequency'], item['threshold'])
            )

    def calculate_route(self, origin, destination, stops):
        """
        Query Google Directions API to compute the best route based on
        distance, duration, or fuel efficiency.
        Decode the polyline to get intermediate points, reverse geocode to
        determine states along the path.
        """
        if not origin or not destination:
            messagebox.showerror('Error', 'Enter origin and destination')
            return
        self.origin = origin
        self.destination = destination
        route_type = 'fastest'  # Can be extended to 'shortest' or 'most fuel-efficient'

        def geocode(address):
            """Convert address string to latitude/longitude."""
            resp = requests.get(
                'https://maps.googleapis.com/maps/api/geocode/json',
                params={'address': address, 'key': GOOGLE_API_KEY}
            ).json()
            if resp.get('status') != 'OK':
                raise Exception(f"Geocode failed: {resp.get('status')}")
            loc = resp['results'][0]['geometry']['location']
            return loc['lat'], loc['lng']

        def reverse_geocode(lat, lng):
            """Convert lat/lng to state name."""
            rev = requests.get(
                'https://maps.googleapis.com/maps/api/geocode/json',
                params={'latlng': f"{lat},{lng}", 'key': GOOGLE_API_KEY}
            ).json()
            if rev.get('status') == 'OK':
                for comp in rev['results'][0]['address_components']:
                    if 'administrative_area_level_1' in comp['types']:
                        return comp['long_name']
            return 'Unknown'

        try:
            # Request directions with optional waypoints
            url = 'https://maps.googleapis.com/maps/api/directions/json'
            params = {'origin': origin, 'destination': destination,
                      'key': GOOGLE_API_KEY, 'alternatives': 'true'}
            if stops:
                params['waypoints'] = '|'.join(s.strip() for s in stops.split(','))
            data = requests.get(url, params=params).json()
            if data.get('status') != 'OK':
                raise Exception(f"Directions API error: {data.get('status')}")

            # Select best route based on chosen metric
            best_route = None
            best_val = None
            eff = self.um.accounts[self.current_user].get('efficiency') or 1.0
            for r in data['routes']:
                dist_km = sum(leg['distance']['value'] for leg in r['legs']) / 1000
                dur_min = sum(leg['duration']['value'] for leg in r['legs']) / 60
                metrics = {
                    'fastest': dur_min,
                    'shortest': dist_km,
                    'most fuel-efficient': dist_km / (eff * 1.60934)
                }
                val = metrics[route_type]
                if best_val is None or val < best_val:
                    best_val, best_route = val, r

            # Summarize route
            dist_km = sum(leg['distance']['value'] for leg in best_route['legs']) / 1000
            dur_min = sum(leg['duration']['value'] for leg in best_route['legs']) / 60
            txt = f"Total Distance: {dist_km:.2f} km\nTotal Duration: {dur_min:.1f} min"
            if route_type == 'most fuel-efficient':
                miles = dist_km * 0.621371
                est_gal = miles / eff
                txt += f"\nEstimated Fuel: {est_gal:.2f} gal"
            self.route_result.config(state='normal')
            self.route_result.delete('1.0', tk.END)
            self.route_result.insert(tk.END, txt)
            self.route_result.config(state='disabled')

            # Decode polyline and sample points for reverse geocoding
            coords = decode_polyline(best_route['overview_polyline']['points'])
            step = max(1, len(coords) // 20)
            samples = coords[::step]
            states = [reverse_geocode(lat, lng) for lat, lng in samples]
            end_leg = best_route['legs'][-1]['end_location']
            states.append(reverse_geocode(end_leg['lat'], end_leg['lng']))
            # Deduplicate states
            uniq = []
            for s in states:
                if s not in uniq:
                    uniq.append(s)
            # Display states along route
            self.state_result.config(state='normal')
            self.state_result.delete('1.0', tk.END)
            for s in uniq:
                self.state_result.insert(tk.END, s + '\n')
            self.state_result.config(state='disabled')
            # Populate state dropdown for price lookup
            self.state_dropdown['values'] = uniq
            self.state_var.set(uniq[0] if uniq else '')
            self.route_states = uniq
            self.last_distance = dist_km

        except Exception as e:
            messagebox.showerror('Error', f'Route failed: {e}')

    def show_prices(self):
        """
        Fetch current fuel prices for the selected state from CollectAPI
        and display them.
        """
        state = self.state_var.get()
        if not state:
            messagebox.showerror('Error', 'Please select a state')
            return
        try:
            conn = http.client.HTTPSConnection("api.collectapi.com")
            headers = {
                'content-type': 'application/json',
                'authorization': 'apikey 0zJdI2HWc9CA41EoOevtOO:5nSi8IbSVVL4D4ALGK2N8b'
            }
            conn.request("GET", "/gasPrice/allUsaPrice", headers=headers)
            res = conn.getresponse()
            data = res.read()
            prices = json.loads(data.decode()).get('result', [])
            # Find data for the selected state
            state_data = next((item for item in prices if item.get('name') == state), None)
            if not state_data:
                messagebox.showerror('Error', f'No price data for {state}')
                return
            # Build display text
            txt = (
                f"Gasoline: {state_data.get('gasoline')} {state_data.get('currency')}\n"
                f"MidGrade: {state_data.get('midGrade')} {state_data.get('currency')}\n"
                f"Premium: {state_data.get('premium')} {state_data.get('currency')}\n"
                f"Diesel: {state_data.get('diesel')} {state_data.get('currency')}"
            )
            self.price_result.config(state='normal')
            self.price_result.delete('1.0', tk.END)
            self.price_result.insert(tk.END, txt)
            self.price_result.config(state='disabled')
        except Exception as e:
            messagebox.showerror('Error', f'Failed to fetch prices: {e}')

    def calculate_cost(self):
        """
        Compute total fuel cost for the trip based on distance, efficiency,
        and average price across states along the route.
        """
        if not getattr(self, 'last_distance', None) or not getattr(self, 'route_states', None):
            messagebox.showerror('Error', 'Please calculate route first')
            return
        try:
            prices = getattr(self, 'all_prices', None)
            if prices is None:
                # Fetch prices if not already loaded
                conn = http.client.HTTPSConnection("api.collectapi.com")
                headers = {
                    'content-type': 'application/json',
                    'authorization': 'apikey 0zJdI2HWc9CA41EoOevtOO:5nSi8IbSVVL4D4ALGK2N8b'
                }
                conn.request("GET", "/gasPrice/allUsaPrice", headers=headers)
                res = conn.getresponse()
                prices = json.loads(res.read().decode()).get('result', [])
        except Exception as e:
            messagebox.showerror('Error', f'Could not fetch prices: {e}')
            return

        user = self.um.accounts[self.current_user]
        ft = user.get('fuel_type')
        eff = user.get('efficiency')
        if not ft or not eff:
            messagebox.showerror('Error', 'Please update your vehicle profile first')
            return

        # Map fuel type to JSON keys
        key_mapping = {
            'gasoline': 'gasoline',
            'petrol': 'gasoline',
            'midgrade': 'midGrade',
            'mid grade': 'midGrade',
            'premium': 'premium',
            'diesel': 'diesel'
        }
        key = key_mapping.get(ft.strip().lower(), ft)
        vals = []
        currency = ''
        # Collect prices for each state on route
        for s in self.route_states:
            sd = next((i for i in prices if i.get('name') == s), None)
            if sd and key in sd:
                try:
                    v = float(sd[key])
                    vals.append(v)
                    currency = sd.get('currency', currency)
                except:
                    pass
        if not vals:
            messagebox.showerror('Error', 'No price data for those states')
            return

        # Compute average price and total cost
        avg_price = sum(vals) / len(vals)
        miles = self.last_distance * 0.621371  # Convert km to miles
        gallons_needed = miles / eff
        cost = gallons_needed * avg_price
        self.current_cost = cost

        # Display cost breakdown
        self.cost_result.config(state='normal')
        self.cost_result.delete('1.0', tk.END)
        self.cost_result.insert(
            tk.END,
            f'Fuel Needed: {gallons_needed:.2f} gal\n'
            f'Avg. Price/gal: {avg_price:.2f} {currency}\n'
            f'Total Cost: {cost:.2f} {currency}'
        )
        self.cost_result.config(state='disabled')


if __name__ == '__main__':
    App().mainloop()  # Launch the application
