from fastapi import FastAPI, UploadFile, Form, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import shutil
import os
import sqlite3
import qrcode
import numpy as np
import cv2
from deepface import DeepFace
from PIL import Image

app = FastAPI()

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database File
DB_FILE = "passengers.db"

# Initialize SQLite Database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS passengers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            image_path TEXT,
            seat TEXT,
            boarding_pass TEXT,
            verified INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

# In-memory storage for users (replace with DB in production)
users = {}
flights = [
    {"id": 1, "origin": "Bangalore", "destination": "Pune", "date": "2025-03-20", "available_seats": 5},
    {"id": 2, "origin": "Delhi", "destination": "Mumbai", "date": "2025-03-21", "available_seats": 3},
]
bookings = []

# API Key for Flight Search (Use environment variables for security)
AVIATIONSTACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")
API_URL = "http://api.aviationstack.com/v1/flights"

# Data Models
class User(BaseModel):
    username: str
    password: str

class FlightSearch(BaseModel):
    origin: str
    destination: str
    date: str  # Format: 'YYYY-MM-DD'

class BookingRequest(BaseModel):
    flight_id: int
    passenger_name: str
    email: str

# User Registration
@app.post("/register")
def register(user: User):
    if user.username in users:
        raise HTTPException(status_code=400, detail="User already exists")
    users[user.username] = user.password
    return {"message": "User registered successfully"}

# User Login
@app.post("/login")
def login(user: User):
    if user.username not in users or users[user.username] != user.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login successful", "token": "fake-jwt-token"}

# Passenger Registration (Face Storage & QR Boarding Pass)
@app.post("/register-passenger/")
async def register_passenger(
    name: str = Form(...), 
    email: str = Form(...), 
    seat: str = Form(...), 
    file: UploadFile = File(...)
):
    """Registers a passenger with face capture and generates a QR-based boarding pass."""

    save_dir = "passenger_faces"
    os.makedirs(save_dir, exist_ok=True)

    file_path = f"{save_dir}/{name}_{email}.jpg"
    
    # Save uploaded image
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Generate QR Code for Boarding Pass
    boarding_pass_path = f"boarding_passes/{name}_{email}.png"
    os.makedirs("boarding_passes", exist_ok=True)
    
    qr_data = f"Passenger: {name}\nEmail: {email}\nSeat: {seat}"
    qr = qrcode.make(qr_data)
    qr.save(boarding_pass_path)

    # Save Passenger Data to Database
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO passengers (name, email, image_path, seat, boarding_pass) VALUES (?, ?, ?, ?, ?)",
        (name, email, file_path, seat, boarding_pass_path),
    )
    conn.commit()
    conn.close()

    return {"message": "Passenger registered successfully", "boarding_pass": boarding_pass_path}

# Passenger Face Verification at Check-in
@app.post("/verify-passenger/")
async def verify_passenger(file: UploadFile = File(...)):
    """Verifies passenger using real-time face recognition and updates boarding status."""

    file_path = "D:\CODE\Full Stack Project\passenger_faces\Thomas James_7homasjames@gmail.com.jpg"
    
    # Save uploaded image temporarily
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Convert image for DeepFace processing
    img = Image.open(file_path)
    img = np.array(img)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, image_path FROM passengers WHERE verified=0")
    passengers = cursor.fetchall()
    conn.close()

    for passenger_id, name, email, image_path in passengers:
        try:
            # Perform face recognition using DeepFace
            result = DeepFace.verify(img, image_path, enforce_detection=True)

            if result["verified"]:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("UPDATE passengers SET verified=1 WHERE id=?", (passenger_id,))
                conn.commit()
                conn.close()

                return {"message": "Passenger Verified ✅", "name": name, "email": email}
        
        except Exception as e:
            print(f"Error verifying passenger: {e}")

    raise HTTPException(status_code=400, detail="Face not recognized.")

# Retrieve Boarding Pass
@app.get("/boarding-pass/{email}")
def get_boarding_pass(email: str):
    """Fetches the generated boarding pass for a passenger."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT boarding_pass FROM passengers WHERE email=?", (email,))
    passenger = cursor.fetchone()
    conn.close()

    if passenger:
        return {"boarding_pass": passenger[0]}
    else:
        raise HTTPException(status_code=404, detail="Boarding pass not found")

# Search Flights (Using AviationStack API)
@app.post("/search-flights")
def search_flights(search: FlightSearch):
    params = {
        "access_key": AVIATIONSTACK_API_KEY,
        "dep_iata": search.origin,
        "arr_iata": search.destination,
        "flight_date": search.date
    }
    
    response = requests.get(API_URL, params=params)
    response.raise_for_status()
    data = response.json()
    
    flights = data.get('data', [])
    if not flights:
        raise HTTPException(status_code=404, detail="No flights found")

    return flights

#  Book a Flight
@app.post("/book-flight")
def book_flight(booking: BookingRequest):
    flight = next((f for f in flights if f["id"] == booking.flight_id), None)
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    if flight["available_seats"] <= 0:
        raise HTTPException(status_code=400, detail="No available seats")
    
    flight["available_seats"] -= 1
    bookings.append({"flight_id": booking.flight_id, "passenger_name": booking.passenger_name, "email": booking.email})
    return {"message": "Booking successful", "flight_details": flight}
