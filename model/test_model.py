import joblib
import pandas as pd

# Modell laden
model = joblib.load("model/flight_delay_model.pkl")

# Beispielhafte Eingabe – nutze dieselben Feature-Namen wie beim Training!
sample = pd.DataFrame([{
    "scheduled_hour": 18,
    "flight_number_numeric": 1175,
    "airline_code_encoded": 4
}])

# Vorhersage
pred = model.predict(sample)
print(f"✈️ Vorhergesagte Verspätung: {pred[0]:.2f} Minuten")