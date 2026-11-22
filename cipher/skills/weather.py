import requests

from cipher.skills import skill


def _sky(code):
    if code == 0:
        return "clear ☀️"
    if code in (1, 2, 3):
        return "partly cloudy ⛅"
    if code in (45, 48):
        return "fog 🌫️"
    if 51 <= code <= 57:
        return "drizzle 🌦️"
    if 61 <= code <= 67 or 80 <= code <= 82:
        return "rain 🌧️"
    if 71 <= code <= 77 or code in (85, 86):
        return "snow ❄️"
    if code >= 95:
        return "thunderstorm ⛈️"
    return "mixed"


def _geocode(city):
    words = city.replace("<", " ").replace(">", " ").replace(",", " ").split()
    for cut in range(len(words), 0, -1):
        name = " ".join(words[:cut])
        hint = " ".join(words[cut:]).lower()
        results = requests.get("https://geocoding-api.open-meteo.com/v1/search",
                               params={"name": name, "count": 10},
                               timeout=15).json().get("results") or []
        if not results:
            continue
        if not hint:
            return results[0]
        for p in results:
            if hint in f"{p.get('country', '')} {p.get('admin1', '')}".lower():
                return p
    return None


@skill("get_weather", "Get current weather and a 3-day forecast for a city.",
       {"city": {"type": "string"}}, ["city"])
def get_weather(city):
    try:
        p = _geocode(city)
        if not p:
            return ("City not found. Try just the town name, or the nearest bigger town.")
        w = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": p["latitude"], "longitude": p["longitude"],
            "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone": "auto", "forecast_days": 3}, timeout=15).json()
        c, d = w["current"], w["daily"]
        out = [f"{p['name']}, {p.get('country', '')}",
               f"Now: {c['temperature_2m']}°C (feels {c['apparent_temperature']}°C), "
               f"{_sky(c['weather_code'])}, wind {c['wind_speed_10m']} km/h"]
        for i in range(3):
            out.append(f"{d['time'][i]}: {d['temperature_2m_min'][i]} to "
                       f"{d['temperature_2m_max'][i]}°C, rain chance "
                       f"{d['precipitation_probability_max'][i]}%")
        return "\n".join(out)
    except Exception as e:
        return f"Weather lookup failed: {e}"
