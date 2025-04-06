import pandas as pd
import requests
from datetime import datetime
from pymongo import MongoClient

# 🔗 MongoDB-Verbindung
client = MongoClient("mongodb+srv://flightuser:wH7hy3GLCjHlEuHg@flightcluster.ogdqixj.mongodb.net/?retryWrites=true&w=majority&appName=FlightCluster")
collection = client["flugprojekt"]["ankuenfte"]

# 📄 CSV-Datei laden
df = pd.read_csv("data/arrivals.csv")
df = df[df["scheduled"] != "Geplant"]
df.dropna(subset=["flight", "from", "scheduled"], inplace=True)

# ☁️ Wetterdaten abrufen
API_KEY = "2512ee323517f9f007da42efad0d008e"
url = "https://api.openweathermap.org/data/2.5/weather"
params = {
    "q": "Zurich,CH",
    "appid": API_KEY,
    "units": "metric"
}

response = requests.get(url, params=params)
if response.status_code == 200:
    weather = response.json()
    weather_main = weather["weather"][0]["main"]
    temperature = weather["main"]["temp"]
    wind_speed = weather["wind"]["speed"]
    timestamp = datetime.utcnow()
else:
    weather_main = None
    temperature = None
    wind_speed = None
    timestamp = None

# 🔄 MongoDB leeren und neue Daten hochladen
collection.delete_many({})
for _, row in df.iterrows():
    document = row.to_dict()
    document["weather_main"] = weather_main
    document["temperature"] = temperature
    document["wind_speed"] = wind_speed
    document["weather_updated_at"] = timestamp
    collection.insert_one(document)

print("✅ Alle Flüge mit Wetterdaten erfolgreich in MongoDB hochgeladen.")