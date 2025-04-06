import pandas as pd
from pymongo import MongoClient
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder
import joblib
import numpy as np
import os

print("🧠 Trainiere Modell mit erweiterten Features...")

# MongoDB-Verbindung
client = MongoClient("mongodb+srv://flightuser:wH7hy3GLCjHlEuHg@flightcluster.ogdqixj.mongodb.net/?retryWrites=true&w=majority&appName=FlightCluster")
collection = client["flugprojekt"]["ankuenfte"]

# Daten laden
df = pd.DataFrame(list(collection.find({}, {"_id": 0, "flight": 1, "from": 1, "scheduled": 1})))
df = df[df["scheduled"] != "Geplant"]
df.dropna(subset=["flight", "from", "scheduled"], inplace=True)

# Feature Engineering
df["airline_code"] = df["flight"].str.extract(r"([A-Z]{2})")[0]
df["flight_number_numeric"] = df["flight"].str.extract(r"(\d+)")[0].astype(float)
df["scheduled_time"] = pd.to_datetime(df["scheduled"], format="%H:%M", errors="coerce")
df.dropna(subset=["scheduled_time"], inplace=True)
df["scheduled_hour"] = df["scheduled_time"].dt.hour
df["weekday"] = df["scheduled_time"].dt.weekday

# Simulierte Wetterdaten
np.random.seed(42)
df["temperature"] = np.random.normal(loc=15, scale=5, size=len(df))
df["wind_speed"] = np.random.normal(loc=10, scale=2, size=len(df))
df["weather_main"] = np.random.choice(["Clear", "Clouds", "Rain", "Fog"], size=len(df))

# Simulierte Zielvariable
df["delay_minutes"] = np.random.randint(0, 30, size=len(df))

# NaN entfernen nach Feature-Erstellung
df.dropna(subset=[
    "airline_code", "flight_number_numeric", "scheduled_hour",
    "delay_minutes", "weekday", "weather_main", "temperature", "wind_speed"
], inplace=True)

# Label-Encoding
le_airline = LabelEncoder()
le_weather = LabelEncoder()
le_from = LabelEncoder()

df["airline_code_encoded"] = le_airline.fit_transform(df["airline_code"])
df["weather_main_encoded"] = le_weather.fit_transform(df["weather_main"])
df["from_encoded"] = le_from.fit_transform(df["from"])

# Features und Target
features = [
    "scheduled_hour", "flight_number_numeric", "airline_code_encoded",
    "weekday", "temperature", "wind_speed", "weather_main_encoded", "from_encoded"
]
X = df[features]
y = df["delay_minutes"]

# Modell trainieren
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluation
y_pred = model.predict(X_test)
print(f"📈 MAE: {mean_absolute_error(y_test, y_pred):.2f} Minuten")
print(f"🎯 R² Score: {r2_score(y_test, y_pred):.2f}")

# Modell speichern
os.makedirs("model", exist_ok=True)
joblib.dump(model, "model/flight_delay_model.pkl")
print("💾 Modell gespeichert unter model/flight_delay_model.pkl")