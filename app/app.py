from flask import Flask, render_template, request
import joblib
import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import requests

app = Flask(__name__)

# Modell laden
model = joblib.load("model/flight_delay_model.pkl")

# MongoDB-Verbindung
client = MongoClient("mongodb+srv://flightuser:wH7hy3GLCjHlEuHg@flightcluster.ogdqixj.mongodb.net/?retryWrites=true&w=majority&appName=FlightCluster")
collection = client["flugprojekt"]["ankuenfte"]

# OpenWeatherMap API
WEATHER_API_KEY = "2512ee323517f9f007da42efad0d008e"

def get_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?q=Zürich,CH&appid={WEATHER_API_KEY}&units=metric"
    try:
        res = requests.get(url).json()
        return {
            "main": res["weather"][0]["main"],
            "temp": res["main"]["temp"],
            "wind": res["wind"]["speed"]
        }
    except Exception as e:
        print("⚠️ Wetterdaten konnten nicht geladen werden:", e)
        return {"main": "Clear", "temp": 15, "wind": 5}  # Fallback-Werte

@app.route("/", methods=["GET", "POST"])
def index():
    prediction = None
    error_message = None
    hour = None
    minute = None
    flight_number = ""
    flights = []

    # Flugdaten aus MongoDB
    try:
        df = pd.DataFrame(list(collection.find({}, {"_id": 0, "flight": 1, "from": 1, "scheduled": 1, "status": 1})))
        df = df[df["scheduled"] != "Geplant"]
        df["flight"] = df["flight"].str.split("\n").str[0]  # Nur erste Flugnummer
        future_df = df[~df["status"].str.contains("Gelandet", na=False)].reset_index(drop=True)
        flights = future_df.to_dict(orient="records")
    except Exception as e:
        print("⚠️ Fehler beim MongoDB-Lesen:", e)

    if request.method == "POST":
        try:
            hour = int(request.form["hour"])
            minute = int(request.form["minute"])
            flight_number = request.form["flight_number"].strip().upper()
            scheduled_input = f"{hour:02d}:{minute:02d}"

            matched = next(
                (f for f in flights if f["flight"] == flight_number and f["scheduled"] == scheduled_input),
                None
            )

            if not matched:
                prediction = "Flug nicht vorhanden"
            else:
                scheduled_hour = hour + (minute / 60)
                weekday = datetime.today().weekday()
                from_airport = matched["from"]

                # Wetterdaten holen
                weather = get_weather()
                weather_main = weather["main"]
                temperature = weather["temp"]
                wind_speed = weather["wind"]

                # Manuelles Label-Encoding (wie im Training!)
                airline_code_encoded = 0
                weather_map = {"Clear": 0, "Clouds": 1, "Rain": 2, "Fog": 3}
                weather_encoded = weather_map.get(weather_main, 0)

                # Herkunft kodieren (Dummy-Beispiel)
                from_map = {name: i for i, name in enumerate(df["from"].unique())}
                from_encoded = from_map.get(from_airport, 0)

                flight_number_numeric = float("".join(filter(str.isdigit, flight_number)))

                input_df = pd.DataFrame([{
                    "scheduled_hour": scheduled_hour,
                    "flight_number_numeric": flight_number_numeric,
                    "airline_code_encoded": airline_code_encoded,
                    "weekday": weekday,
                    "temperature": temperature,
                    "wind_speed": wind_speed,
                    "weather_main_encoded": weather_encoded,
                    "from_encoded": from_encoded
                }])

                prediction = model.predict(input_df)[0]
        except Exception as e:
            print("❌ Fehler:", e)
            prediction = "Fehler bei der Eingabe"

    return render_template(
        "index.html",
        prediction=prediction,
        hour=hour,
        minute=minute,
        flight_number=flight_number,
        flights=flights
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)