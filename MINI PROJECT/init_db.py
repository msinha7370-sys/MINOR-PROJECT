import sqlite3
import json
from pathlib import Path

DB = Path("tourism.db")
if DB.exists():
    DB.unlink()

conn = sqlite3.connect("tourism.db")
c = conn.cursor()

# create tables
c.execute('''
CREATE TABLE attractions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    tags TEXT,         -- comma separated
    location TEXT,
    avg_rating REAL,
    capacity INTEGER DEFAULT 100,
    crowd INTEGER DEFAULT 0,
    price REAL,
    image_url TEXT
)
''')

c.execute('''
CREATE TABLE bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    attraction_id INTEGER,
    user_id INTEGER,
    seats INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(attraction_id) REFERENCES attractions(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
)
''')

c.execute('''
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')
# sample attractions (you can add more)
sample = [
    {
        "name": "RED FORT",
        "description": "A historic fort in Delhi, a UNESCO World Heritage site.",
        "tags": "history,architecture,unesco",
        "location": "Delhi",
        "avg_rating": 4.6,
        "capacity": 150,
        "price": 500.00,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Delhi_fort.jpg/1280px-Delhi_fort.jpg"
    },
    {
        "name": "City Palace",
        "description": "A palace complex in Udaipur, situated on the bank of Lake Pichola.",
        "tags": "nature,relaxation,palace,lake",
        "location": "Udaipur",
        "avg_rating": 4.7,
        "capacity": 200,
        "price": 750.00,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b7/Udaipur_City_Palace.jpg/1280px-Udaipur_City_Palace.jpg"
    },
    {
        "name": "Solang Valley",
        "description": "A popular valley in Manali for adventure sports like paragliding and skiing.",
        "tags": "adventure,sports,thrill,nature",
        "location": "Manali",
        "avg_rating": 4.5,
        "capacity": 105,
        "price": 1200.00,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/Solang_Valley_In_April.jpg/1280px-Solang_Valley_In_April.jpg"
    },
    {
        "name": "Hawa Mahal",
        "description": "A palace in Jaipur, known for its intricate facade with 953 windows.",
        "tags": "culture,history,architecture",
        "location": "Jaipur",
        "avg_rating": 4.6,
        "capacity": 180,
        "price": 250.00,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/Hawa_Mahal_Jaipur_2008.jpg/1024px-Hawa_Mahal_Jaipur_2008.jpg"
    },
    {
        "name": "Taj Mahal",
        "description": "An ivory-white marble mausoleum on the south bank of the Yamuna river.",
        "tags": "history,architecture,unesco,romance",
        "location": "Agra",
        "avg_rating": 4.8,
        "capacity": 300,
        "price": 1100.00,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bd/Taj_Mahal%2C_Agra%2C_India_edit3.jpg/1280px-Taj_Mahal%2C_Agra%2C_India_edit3.jpg"
    },
    {
        "name": "Gateway of India",
        "description": "An arch-monument built in the early 20th century, located in Mumbai.",
        "tags": "history,monument,sea",
        "location": "Mumbai",
        "avg_rating": 4.5,
        "capacity": 250,
        "price": 0.00,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a3/Gateway_of_India_in_the_evening.jpg/1280px-Gateway_of_India_in_the_evening.jpg"
    },
    {
        "name": "Golden Temple",
        "description": "The holiest Gurdwara and the most important pilgrimage site of Sikhism, located in Amritsar.",
        "tags": "religion,culture,architecture",
        "location": "Amritsar",
        "avg_rating": 4.9,
        "capacity": 400,
        "price": 0.00,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/35/Golden_Temple_-_Amritsar.jpg/1280px-Golden_Temple_-_Amritsar.jpg"
    },
    {
        "name": "Mysore Palace",
        "description": "A historical palace and the official residence of the Wadiyar dynasty who ruled the Kingdom of Mysore.",
        "tags": "history,palace,architecture",
        "location": "Mysore",
        "avg_rating": 4.6,
        "capacity": 220,
        "price": 100.00,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Mysore_Palace_at_Dusk.jpg/1280px-Mysore_Palace_at_Dusk.jpg"
    },
    {
        "name": "Victoria Memorial",
        "description": "A large marble building in Kolkata, which was built between 1906 and 1921.",
        "tags": "history,museum,architecture",
        "location": "Kolkata",
        "avg_rating": 4.6,
        "capacity": 180,
        "price": 30.00,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Victoria_Memorial_Hall%2C_Kolkata_-_West_Bengal_-_India_-_20120105-01.jpg/1280px-Victoria_Memorial_Hall%2C_Kolkata_-_West_Bengal_-_India_-_20120105-01.jpg"
    }
]

for a in sample:
    c.execute('''
    INSERT INTO attractions (name, description, tags, location, avg_rating, capacity, price, image_url) VALUES (?,?,?,?,?,?,?,?)
    ''', (a['name'], a['description'], a['tags'], a['location'], a['avg_rating'], a['capacity'], a['price'], a['image_url']))

conn.commit()
conn.close()
print("Initialized tourism.db with sample data.")
