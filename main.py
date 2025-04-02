import tkinter as tk
from tkinter import messagebox, simpledialog

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Car Fuel Cost Calculator - User Management")
        self.geometry("800x600")
        
        # In-memory storage for users (maps email to user data)
        self.users = {}  # { email: {"password": ..., "preferred_fuel": ..., "efficiency": ...} }
        self.current_user = None
        
        self.show_login()

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

    # ---------------------- Login Screen ----------------------
    def show_login(self):
        self.clear_window()
        frame = tk.Frame(self)
        frame.pack(pady=30)
        
        tk.Label(frame, text="Login", font=("Arial", 24)).grid(row=0, column=0, columnspan=2, pady=10)
        tk.Label(frame, text="Email:").grid(row=1, column=0, sticky="e")
        email_entry = tk.Entry(frame, width=40)
        email_entry.grid(row=1, column=1, padx=5, pady=5)
        tk.Label(frame, text="Password:").grid(row=2, column=0, sticky="e")
        password_entry = tk.Entry(frame, show="*", width=40)
        password_entry.grid(row=2, column=1, padx=5, pady=5)
        
        def login_action():
            email = email_entry.get().strip()
            password = password_entry.get().strip()
            if email in self.users and self.users[email]["password"] == password:
                self.current_user = email
                messagebox.showinfo("Success", "Login successful!")
                self.show_profile()
            else:
                messagebox.showerror("Error", "Invalid email or password.")
                
        tk.Button(frame, text="Login", command=login_action, width=20).grid(row=3, column=0, pady=10)
        tk.Button(frame, text="Register", command=self.show_register, width=20).grid(row=3, column=1, pady=10)

    # ---------------------- Registration Screen ----------------------
    def show_register(self):
        self.clear_window()
        frame = tk.Frame(self)
        frame.pack(pady=30)
        
        tk.Label(frame, text="Register", font=("Arial", 24)).grid(row=0, column=0, columnspan=2, pady=10)
        tk.Label(frame, text="Email:").grid(row=1, column=0, sticky="e")
        email_entry = tk.Entry(frame, width=40)
        email_entry.grid(row=1, column=1, padx=5, pady=5)
        tk.Label(frame, text="Password:").grid(row=2, column=0, sticky="e")
        password_entry = tk.Entry(frame, show="*", width=40)
        password_entry.grid(row=2, column=1, padx=5, pady=5)
        
        def register_action():
            email = email_entry.get().strip()
            password = password_entry.get().strip()
            if not email or not password:
                messagebox.showerror("Error", "Please provide both email and password.")
                return
            if email in self.users:
                messagebox.showerror("Error", "Email already registered.")
                return
            self.users[email] = {"password": password, "preferred_fuel": None, "efficiency": None}
            messagebox.showinfo("Success", "Registration successful! Please login.")
            self.show_login()
            
        tk.Button(frame, text="Register", command=register_action, width=20).grid(row=3, column=0, pady=10)
        tk.Button(frame, text="Back", command=self.show_login, width=20).grid(row=3, column=1, pady=10)

    # ---------------------- User Profile Management ----------------------
    def show_profile(self):
        self.clear_window()
        frame = tk.Frame(self)
        frame.pack(pady=20)
        
        tk.Label(frame, text="User Profile", font=("Arial", 24)).grid(row=0, column=0, columnspan=2, pady=10)
        user_data = self.users[self.current_user]
        tk.Label(frame, text=f"Email: {self.current_user}").grid(row=1, column=0, sticky="w", padx=10)
        tk.Label(frame, text=f"Preferred Fuel Type: {user_data.get('preferred_fuel', 'Not set')}").grid(row=2, column=0, sticky="w", padx=10)
        tk.Label(frame, text=f"Vehicle Efficiency: {user_data.get('efficiency', 'Not set')}").grid(row=3, column=0, sticky="w", padx=10)
        
        tk.Label(frame, text="Update Preferred Fuel Type:").grid(row=4, column=0, sticky="e", padx=10)
        pref_entry = tk.Entry(frame, width=40)
        pref_entry.grid(row=4, column=1, padx=10, pady=5)
        tk.Label(frame, text="Update Vehicle Efficiency:").grid(row=5, column=0, sticky="e", padx=10)
        eff_entry = tk.Entry(frame, width=40)
        eff_entry.grid(row=5, column=1, padx=10, pady=5)
        
        def update_profile():
            self.users[self.current_user]["preferred_fuel"] = pref_entry.get().strip()
            self.users[self.current_user]["efficiency"] = eff_entry.get().strip()
            messagebox.showinfo("Profile", "Profile updated successfully!")
            self.show_profile()
            
        tk.Button(frame, text="Update Profile", command=update_profile, width=20).grid(row=6, column=0, pady=10)
        
        def reset_password():
            new_pw = simpledialog.askstring("Reset Password", "Enter new password:", show="*")
            if new_pw:
                self.users[self.current_user]["password"] = new_pw
                messagebox.showinfo("Password", "Password updated successfully!")
                
        tk.Button(frame, text="Reset Password", command=reset_password, width=20).grid(row=6, column=1, pady=10)
        
        def delete_account():
            if messagebox.askyesno("Delete Account", "Are you sure you want to delete your account?"):
                del self.users[self.current_user]
                self.current_user = None
                messagebox.showinfo("Account", "Account deleted successfully.")
                self.show_login()
                
        tk.Button(frame, text="Delete Account", command=delete_account, width=20).grid(row=7, column=0, pady=10)
        tk.Button(frame, text="Back to Menu", command=self.show_login, width=20).grid(row=7, column=1, pady=10)

if __name__ == "__main__":
    app = App()
    app.mainloop()
