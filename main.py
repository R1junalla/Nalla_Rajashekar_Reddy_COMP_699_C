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


if __name__ == "__main__":
    app = App()
    app.mainloop()
