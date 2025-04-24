# Nalla_Rajashekar_Reddy_COMP_699_C

Car Fuel Cost Calculator - Build & Run Instructions
These instructions will help you set up, configure, and run the Car Fuel Cost Calculator application.

1.	Prerequisites
o	Python 3.8+
Verify installation: python --version
o	Tkinter (bundled with most Python distributions)
Test import: python -c "import tkinter; print('Tkinter OK')"
o	Internet Access (required for Google Maps Geocoding/Directions and CollectAPI calls)
2.	Clone or Copy the Repository
o	If using Git:
git clone https://github.com/R1junalla/Nalla_Rajashekar_Reddy_COMP_699_C.git
o	Otherwise:
	Create a new folder anywhere on your machine.
	Save the provided script as app.py inside that folder.
3.	Create & Activate a Virtual Environment (Recommended)
Create
python -m venv venv

macOS/Linux
source venv/bin/activate

Windows
venv\Scripts\activate

4.	Install Dependencies
Only one external package is required:
pip install requests
(All other modules—tkinter, json, hashlib, http.client, etc.—are in the Python standard library.)

5.	File Structure
After first run, your project folder will look like:
./  
├── app.py              # Main application script  
├── accounts.json       # Auto-created (user profiles)  
├── resets.json         # Auto-created (password-reset tokens)  
├── trips.json          # Auto-created (saved trip records)  
└── notifications.json  # Auto-created (watchlist data)  
You do not need to create the JSON files manually.

6.	Running the Application
With your virtual environment active: python app.py
A window titled Car Fuel Cost Calculator will launch.

7.	Usage Overview
a.	Register / Login
i.	New users: click Register, enter email & password.
ii.	Returning users: enter credentials and click Login.
b.	Profile Tab
i.	Change email/password, delete account, or logout.
c.	Trip Planner Tab
i.	Update vehicle details (fuel type, mpg, tank capacity).
ii.	Enter Origin, Destination, optional Stops.
iii.	Calculate Route → view total distance/duration & states along the way.
iv.	Get Prices → fetch fuel prices for the selected state.
v.	Calculate Fuel Cost → compute total trip cost based on your profile.
vi.	Save Trip → record to history.
d.	Trip History & Reports Tab
i.	View saved trips, delete entries, or generate a total fuel-expense report.
e.	Notifications & Alerts Tab
i.	Select a state, frequency (min), and % price-change threshold.
ii.	Add to Watchlist → begins monitoring that state’s fuel price.
iii.	Remove entries or view your current watchlist.

8.	Troubleshooting
a.	“Invalid credentials” → Double-check email/password or use “Forgot Password.”
b.	API errors → Verify network connectivity and that your API keys are valid and enabled.
c.	Missing modules → Run pip install requests and retry.
d.	GUI rendering issues → Ensure you’re running with a supported version of Tkinter (most standard Python installs include it).
