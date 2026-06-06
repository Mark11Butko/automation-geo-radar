import sqlite3
import os
import random
from datetime import datetime, timedelta

db_dir = "database"
os.makedirs(db_dir, exist_ok=True)
db_path = os.path.join(db_dir, "radar.db")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Create price_history table
cursor.execute("""
CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    store TEXT,
    brand TEXT,
    itemName TEXT,
    price REAL
)
""")

# 2. Create visitor_logs table
cursor.execute("""
CREATE TABLE IF NOT EXISTS visitor_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event TEXT,
    ip TEXT,
    city TEXT,
    country TEXT,
    latitude REAL,
    longitude REAL,
    org TEXT,
    ua TEXT,
    lang TEXT,
    resolution TEXT,
    ref TEXT,
    timestamp TEXT
)
""")

# Generate price history mock data (last 180 days)
stores = ["Tesco", "Kaufland", "Lidl", "Billa"]
brands = {
    "monster": [
        ("Monster Energy Ultra 500ml", 1.69, 1.19),
        ("Monster Energy Original 500ml", 1.69, 1.19)
    ],
    "red bull": [
        ("Red Bull Energy Drink 250ml", 1.49, 1.09),
        ("Red Bull Sugarfree 250ml", 1.49, 1.09)
    ],
    "hell": [
        ("Hell Energy Classic 250ml", 0.69, 0.49),
        ("Hell Energy Active 250ml", 0.69, 0.49)
    ],
    "tiger": [
        ("Tiger Energy Original 250ml", 0.89, 0.59)
    ]
}

now = datetime.utcnow()
price_records = []

for day_offset in range(180):
    current_date = now - timedelta(days=day_offset)
    # Checkouts simulated twice a day (8:00 AM and 8:00 PM)
    for hour in [8, 20]:
        ts = current_date.replace(hour=hour, minute=0, second=0, microsecond=0).isoformat() + "Z"
        
        for store in stores:
            for brand, products in brands.items():
                for product_name, reg_price, promo_price in products:
                    # Every brand in a store has a cyclical promo cycle
                    # Let's seed a unique wave for each store+brand combo
                    combo_seed = (hash(store + brand) + day_offset // 10) % 3
                    
                    # 30% chance the item is currently on discount in this store
                    is_promo = (day_offset % 14 < 4) if combo_seed == 0 else (day_offset % 14 in [5, 6, 7])
                    price = promo_price if is_promo else reg_price
                    
                    # Add small random fluctuation (1-3 cents)
                    price = round(price + random.choice([-0.02, -0.01, 0.0, 0.01, 0.02]), 2)
                    
                    price_records.append((ts, store, brand, product_name, price))

cursor.executemany("""
INSERT INTO price_history (timestamp, store, brand, itemName, price)
VALUES (?, ?, ?, ?, ?)
""", price_records)

# Generate visitor logs mock data (last 180 days)
visitor_records = []
slovak_ips = ["46.34.250.", "178.41.85.", "195.91.12.", "85.237.228.", "91.127.16."]
orgs = [
    ("Slovak Telekom, a.s.", "Bratislava", 48.1486, 17.1077),
    ("Slovanet, a.s.", "Senec", 48.2198, 17.4002),
    ("SWAN, a.s.", "Trnava", 48.3775, 17.5883),
    ("UPC Broadband Slovakia, s.r.o.", "Pezinok", 48.2875, 17.2686),
    ("Orange Slovensko, a.s.", "Bratislava", 48.1601, 17.1354)
]
events = ["page_load", "cv_download", "telegram_click", "linkedin_click"]
refs = ["direct", "google.com", "linkedin.com", "mark-butko-cv.carrd.co"]
uas = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
]
resolutions = ["1920x1080", "1440x900", "390x844", "1366x768"]

for i in range(250):
    day_offset = random.randint(0, 180)
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    ts = (now - timedelta(days=day_offset)).replace(hour=hour, minute=minute, second=0, microsecond=0).isoformat() + "Z"
    
    event = random.choices(events, weights=[70, 15, 10, 5])[0]
    ip = random.choice(slovak_ips) + str(random.randint(1, 254))
    org, city, base_lat, base_lon = random.choice(orgs)
    
    # Introduce small random variations to coordinates within Bratislava surroundings
    lat = round(base_lat + random.uniform(-0.03, 0.03), 4)
    lon = round(base_lon + random.uniform(-0.03, 0.03), 4)
    
    ref = random.choice(refs)
    ua = random.choice(uas)
    res = random.choice(resolutions)
    lang = random.choice(["sk-SK", "en-US", "cs-CZ", "de-DE", "ru-RU"])
    
    visitor_records.append((event, ip, city, "Slovakia", lat, lon, org, ua, lang, res, ref, ts))

cursor.executemany("""
INSERT INTO visitor_logs (event, ip, city, country, latitude, longitude, org, ua, lang, resolution, ref, timestamp)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", visitor_records)

conn.commit()

# Print status details
cursor.execute("SELECT COUNT(*) FROM price_history")
price_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM visitor_logs")
visitor_count = cursor.fetchone()[0]

print(f"Database successfully generated at: {db_path}")
print(f"Total price history records: {price_count}")
print(f"Total visitor log records: {visitor_count}")

# Print sample geo-coordinates
cursor.execute("SELECT city, latitude, longitude, org FROM visitor_logs LIMIT 3")
samples = cursor.fetchall()
print("\n--- Geolocation Mock Samples ---")
for s in samples:
    print(f"City: {s[0]} | Lat: {s[1]} | Lon: {s[2]} | ISP: {s[3]}")

conn.close()
