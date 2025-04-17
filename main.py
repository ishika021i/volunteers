import mysql.connector
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import smtplib
import re
from email.mime.text import MIMEText
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

# Database Setup
def create_database():
    conn = mysql.connector.connect(host="localhost", user="root", password="root")
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS disaster_management")
    cursor.close()
    conn.close()

def create_tables():
    conn = mysql.connector.connect(host="localhost", user="root", password="root", database="disaster_management")
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS volunteers (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        skills TEXT,
        address TEXT,
        latitude DECIMAL(9,6),
        longitude DECIMAL(9,6)
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS disasters (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        severity ENUM('Low', 'Medium', 'High') NOT NULL,
        address TEXT NOT NULL,
        latitude DECIMAL(9,6),
        longitude DECIMAL(9,6),
        needs TEXT
    )''')
    
    cursor.close()
    conn.close()

create_database()
create_tables()

# Database Connection
conn = mysql.connector.connect(host="localhost", user="root", password="root", database="disaster_management")
cursor = conn.cursor()

g = Nominatim(user_agent="disaster_mgmt")

def get_coordinates(address):
    location = g.geocode(address, timeout=10)
    return (location.latitude, location.longitude) if location else (None, None)

def is_valid_email(email):
    return re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email)

def register_volunteer():
    name = simpledialog.askstring("Register Volunteer", "Enter Name:")
    email = simpledialog.askstring("Register Volunteer", "Enter Email:")
    if not is_valid_email(email):
        messagebox.showerror("Error", "Invalid Email Format")
        return
    skills = simpledialog.askstring("Register Volunteer", "Enter Skills:")
    address = simpledialog.askstring("Register Volunteer", "Enter Address:")
    lat, lng = get_coordinates(address)
    if lat is None:
        messagebox.showerror("Error", "Invalid Address")
        return
    
    cursor.execute("INSERT INTO volunteers (name, email, skills, address, latitude, longitude) VALUES (%s, %s, %s, %s, %s, %s)", (name, email, skills, address, lat, lng))
    conn.commit()
    messagebox.showinfo("Success", "Volunteer Registered Successfully")

def register_disaster():
    name = simpledialog.askstring("Register Disaster", "Enter Disaster Name:")
    severity = simpledialog.askstring("Register Disaster", "Enter Severity (Low, Medium, High):").capitalize()
    address = simpledialog.askstring("Register Disaster", "Enter Address:")
    needs = simpledialog.askstring("Register Disaster", "Enter Needs:")
    lat, lng = get_coordinates(address)
    if lat is None:
        messagebox.showerror("Error", "Invalid Address")
        return
    
    cursor.execute("INSERT INTO disasters (name, severity, address, latitude, longitude, needs) VALUES (%s, %s, %s, %s, %s, %s)", (name, severity, address, lat, lng, needs))
    conn.commit()
    messagebox.showinfo("Success", "Disaster Registered Successfully")

def send_message(email, message):
    sender_email = "abc@gmail.com"  # Replace with a valid email
    sender_password = "tvvjbgjchdghbuyv"  # Replace with a valid app password

    if not sender_email or not sender_password:
        print("❌ Email credentials not found. Check your .env file or terminal variables.")
        return

    print(f"✅ Using email: {sender_email} to send messages.")

    msg = MIMEText(message)
    msg["Subject"] = "Disaster Alert!"
    msg["From"] = sender_email
    msg["To"] = email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, msg.as_string())
        server.quit()
        print(f"✅ Message sent successfully to {email}")
    except Exception as e:
        print(f"❌ Failed to send message: {e}")

def find_nearby_volunteers():
    disaster_id = simpledialog.askinteger("Find Volunteers", "Enter Disaster ID:")
    
    try:
        cursor.execute("SELECT name, latitude, longitude FROM disasters WHERE id = %s", (disaster_id,))
        disaster = cursor.fetchone()

        if not disaster:
            messagebox.showerror("Error", "No Disaster Found")
            return
        
        disaster_name, disaster_coords = disaster[0], (disaster[1], disaster[2])
        print(f"Disaster Coordinates: {disaster_coords}")

        cursor.execute("SELECT name, email, latitude, longitude FROM volunteers")
        volunteers = cursor.fetchall()

        if not volunteers:
            messagebox.showinfo("Result", "No Volunteers Registered")
            return
        
        nearby_volunteers = []
        for volunteer in volunteers:
            name, email, lat, lng = volunteer

            if lat is None or lng is None:
                print(f"Skipping {name} (Missing location data)")
                continue

            volunteer_coords = (lat, lng)
            distance = geodesic(disaster_coords, volunteer_coords).km
            print(f"Volunteer {name} is {distance:.2f} km away.")

            if distance <= 50:
                nearby_volunteers.append((name, email))
        
        if not nearby_volunteers:
            messagebox.showinfo("Result", "No Nearby Volunteers Found")
            return
        
        print("Notifying volunteers...")
        for name, email in nearby_volunteers:
            message = f"Dear {name}, a disaster has been reported nearby. Please respond if you can help."
            send_message(email, message)
        
        messagebox.showinfo("Nearby Volunteers Notified", "Emails sent successfully.")
    except mysql.connector.Error as err:
        print("Error:", err)

def list_volunteers():
    cursor.execute("SELECT id, name, email FROM volunteers")
    volunteers = cursor.fetchall()
    result = "\n".join([f"{v[0]}: {v[1]} ({v[2]})" for v in volunteers])
    messagebox.showinfo("Volunteers", result if result else "No Volunteers Registered")

def list_disasters():
    cursor.execute("SELECT id, name, severity FROM disasters")
    disasters = cursor.fetchall()
    result = "\n".join([f"{d[0]}: {d[1]} - {d[2]}" for d in disasters])
    messagebox.showinfo("Disasters", result if result else "No Disasters Recorded")

# GUI Setup
root = tk.Tk()
root.title("Disaster Volunteer Management System")
root.geometry("500x400")

tk.Label(root, text="Disaster Volunteer Management", font=("Arial", 16)).pack(pady=10)

buttons = [
    ("Register Volunteer", register_volunteer),
    ("Register Disaster", register_disaster),
    ("Find Nearby Volunteers", find_nearby_volunteers),
    ("List Volunteers", list_volunteers),
    ("List Disasters", list_disasters),
    ("Exit", root.quit)
]

for text, command in buttons:
    ttk.Button(root, text=text, command=command).pack(pady=5)

root.mainloop()
