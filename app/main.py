from datetime import datetime
import os
import logging

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# -- wczytanie .env ----------------------------------------------------------
load_dotenv()

AUTHOR = "Paweł Peterwas"
PORT   = int(os.getenv("PORT", 8000))
API_KEY = os.getenv("WEATHERAPI_KEY")

# -- logging ----------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logging.info("Start aplikacji | Autor: %s | PORT: %s", AUTHOR, PORT)

# -- inicjalizacja FastAPI -------------------------------------------------
app = FastAPI(title="Pogodynka FastAPI")
templates = Jinja2Templates(directory="templates")

# -- lista lokalizacji ------------------------------------------------------
LOCATIONS = {
    "Polska":   ["Warszawa", "Kraków", "Gdańsk"],
    "Niemcy":   ["Berlin", "Munich", "Hamburg"],
    "USA":      ["New York", "Chicago", "San Francisco"],
}

# -- pobieranie pogody przez WeatherAPI.com ---------------------------------
async def fetch_weather(city: str, country: str) -> dict:
    query = f"{city},{country}"
    url = (
        "https://api.weatherapi.com/v1/current.json"
        f"?key={API_KEY}&q={query}&lang=pl"
    )
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=502, detail=exc.response.text)
        data = resp.json()

    current = data["current"]
    return {
        "temperatura": f"{current['temp_c']}°C",
        "odczuwalna":  f"{current['feelslike_c']}°C",
        "wilgotność":  f"{current['humidity']} %",
        "ciśnienie":   f"{current['pressure_mb']} hPa",
        "wiatr":       f"{current['wind_kph'] / 3.6:.1f} m/s",
        "opis":        current["condition"]["text"],
    }

# -- endpoint wyboru lokalizacji -------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def form_select(request: Request):
    return templates.TemplateResponse(
        "form.html",
        {"request": request, "locations": LOCATIONS},
    )

# -- endpoint wyświetlenia pogody ------------------------------------------
@app.post("/pogoda", response_class=HTMLResponse)
async def show_weather(
    request: Request,
    country: str = Form(...),
    city: str = Form(...),
):
    weather = await fetch_weather(city, country)
    return templates.TemplateResponse(
        "weather.html",
        {
            "request": request,
            "city": city,
            "country": country,
            "weather": weather,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    )
