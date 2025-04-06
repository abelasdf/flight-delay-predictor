from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import os

def scrape_arrivals():
    print("🔍 Starte Scraping...")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(), options=options)

    url = "https://www.flughafen-zuerich.ch/de/passagiere/fliegen/fluginformation/ankunft"
    driver.get(url)

    try:
        print("⏳ Warte auf Flugliste...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "flightListTable__cellFlightNumber"))
        )
        time.sleep(2)

        flights = driver.find_elements(By.CLASS_NAME, "flightListTable__cellFlightNumber")
        airports = driver.find_elements(By.CLASS_NAME, "flightListTable__cellAirport")
        planned = driver.find_elements(By.CLASS_NAME, "flightListTable__cellPlanned")
        arrival = driver.find_elements(By.CLASS_NAME, "flightListTable__cellArrival")
        statuses = driver.find_elements(By.CLASS_NAME, "flightListTable__cellStatus")
        airlines = driver.find_elements(By.CLASS_NAME, "flightListTable__cellAirline")
        baggage = driver.find_elements(By.CLASS_NAME, "flightListTable__cellBaggage")

        arrivals = []
        for i in range(len(flights)):
            arrival_data = {
                "flight": flights[i].text.strip(),
                "from": airports[i].text.strip(),
                "scheduled": planned[i].text.strip(),
                "actual": arrival[i].text.strip(),
                "status": statuses[i].text.strip(),
                "airline": airlines[i].text.strip(),
                "baggage": baggage[i].text.strip()
            }
            arrivals.append(arrival_data)

    except Exception as e:
        print("❌ Fehler beim Laden oder Scrapen:", e)
        driver.save_screenshot("error.png")
        arrivals = []

    finally:
        driver.quit()

    print(f"📦 Scraping abgeschlossen. Gefundene Einträge: {len(arrivals)}")
    for a in arrivals[:5]:
        print(a)

    # Speichern als CSV
    os.makedirs("data", exist_ok=True)
    df = pd.DataFrame(arrivals)
    df.to_csv("data/arrivals.csv", index=False, encoding="utf-8")
    print("📁 Gespeichert unter data/arrivals.csv")

    return arrivals

if __name__ == "__main__":
    arrivals = scrape_arrivals()

    df = pd.DataFrame(arrivals)
    future_df = df[~df["status"].str.contains("Gelandet", na=False)]
    print(f"🛫 Zukünftige Flüge erkannt: {len(future_df)}")
