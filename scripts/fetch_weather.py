#!/usr/bin/env python3
# scripts/fetch_weather.py
# Fetch weather for Alamar (La Habana, Cuba) via Open-Meteo, append English entry to weather.md,
# and generate art/weather.svg visual. No external deps.

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode

# --- CONFIG: Alamar (La Habana, Cuba)
LATITUDE = 23.15794
LONGITUDE = -82.27837
TIMEZONE = "America/Havana"    # return local times for Havana
OUT_MD = Path("weather.md")
OUT_SVG = Path("art/weather.svg")
API_BASE = "https://api.open-meteo.com/v1/forecast"

# Request params: current + daily summary (today)
PARAMS = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "current_weather": "true",
    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
    "forecast_days": 1,
    "timezone": TIMEZONE,
}

TIMEOUT = 15


def try_fetch_json(url):
    req = Request(url, headers={"User-Agent": "github-actions/weather-bot"})
    try:
        with urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except Exception as e:
        print(f"[WARN] fetch error: {e}")
        return None


def fetch_weather():
    url = API_BASE + "?" + urlencode(PARAMS)
    print("[INFO] Fetching:", url)
    return try_fetch_json(url)


def weather_code_to_icon_and_text(code):
    """
    Map Open-Meteo weathercode to simple icon (emoji) and text.
    Keep mapping simple and robust.
    """
    # Codes: https://open-meteo.com/en/docs#api_form
    if code is None:
        return "❓", "Unknown"
    code = int(code)
    if code == 0:
        return "☀️", "Clear sky"
    if 1 <= code <= 3:
        return "🌤️", "Partly cloudy"
    if 45 <= code <= 48:
        return "🌫️", "Fog"
    if 51 <= code <= 67 or 80 <= code <= 82:
        return "🌧️", "Rain"
    if 71 <= code <= 77 or 85 <= code <= 86:
        return "❄️", "Snow"
    if 95 <= code <= 99:
        return "⛈️", "Thunderstorm"
    # fallback
    return "🌥️", "Cloudy"


def build_md_entry(data):
    if not data:
        return None, None
    cw = data.get("current_weather", {})
    daily = data.get("daily", {})

    # local date/time from API (they obey timezone param)
    now_time = cw.get("time") or datetime.now(timezone.utc).isoformat()
    date_part = now_time[:10]
    time_part = now_time[11:] if "T" in now_time else now_time[11:19]

    temp_now = cw.get("temperature")
    wind = cw.get("windspeed")
    wcode = cw.get("weathercode")

    tmax = None
    tmin = None
    precip = None
    try:
        tmax = daily.get("temperature_2m_max", [None])[0]
        tmin = daily.get("temperature_2m_min", [None])[0]
        precip = daily.get("precipitation_sum", [None])[0]
    except Exception:
        pass

    emoji, text = weather_code_to_icon_and_text(wcode)

    # English entry
    header = f"**{date_part} {time_part} — Alamar, Havana (Cuba)**"
    lines = [
        header,
        f"{emoji} {text}",
    ]
    if temp_now is not None:
        lines.append(f"Now: {temp_now} °C (measured at {time_part})")
    if tmax is not None and tmin is not None:
        lines.append(f"Max/Min today: {tmax} °C / {tmin} °C")
    if precip is not None:
        lines.append(f"Precipitation (today): {precip} mm")
    if wind is not None:
        lines.append(f"Wind speed: {wind} km/h")
    lines.append("_Source: Open-Meteo API_")

    entry = "\n\n".join(lines) + "\n\n---\n\n"
    # key to detect duplicates: exact timestamp
    key = f"{date_part}T{time_part}"
    return key, entry


def already_exists(key):
    if not OUT_MD.exists():
        return False
    try:
        txt = OUT_MD.read_text(encoding="utf-8")
        return key in txt
    except Exception:
        return False


def append_md(entry):
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_MD, "a", encoding="utf-8") as f:
        f.write(entry)
    print("[OK] Appended to", OUT_MD)


def build_svg(data):
    """
    Create a simple, clean SVG summarizing current weather.
    Writes to art/weather.svg
    """
    if not data:
        return None
    cw = data.get("current_weather", {})
    daily = data.get("daily", {})

    time_full = cw.get("time", "")
    time_str = time_full.replace("T", " ")[:19]
    temp_now = cw.get("temperature", "--")
    wcode = cw.get("weathercode")
    emoji, text = weather_code_to_icon_and_text(wcode)
    tmax = daily.get("temperature_2m_max", [None])[0]
    tmin = daily.get("temperature_2m_min", [None])[0]
    precip = daily.get("precipitation_sum", [None])[0]

    # SVG dimensions and simple layout
    w, h = 600, 280
    title = f"Alamar, Havana — {time_str}"
    temp_text = f"{temp_now} °C"
    extra = f"Max {tmax} °C / Min {tmin} °C  •  Precip {precip} mm"

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Weather summary">
  <style>
    .bg {{ fill: #0b1220; }}
    .card {{ fill: #0f1724; stroke: #1f2937; stroke-width:1; rx:14; }}
    .title {{ font: 20px 'Segoe UI', Roboto, Arial; fill: #e6eef8; }}
    .temp {{ font: 56px 'Segoe UI', Roboto, Arial; fill: #ffffff; font-weight:700; }}
    .emoji {{ font-size:56px; }}
    .meta {{ font: 14px 'Segoe UI', Roboto, Arial; fill: #cbd5e1; }}
    .foot {{ font: 12px 'Segoe UI', Roboto, Arial; fill: #94a3b8; }}
  </style>
  <rect class="bg" width="100%" height="100%" rx="0"/>
  <g transform="translate(20,20)">
    <rect class="card" x="0" y="0" width="{w-40}" height="{h-40}" rx="12"/>
    <text class="title" x="24" y="38">{title}</text>
    <text class="emoji" x="{w-40-160}" y="110">{emoji}</text>
    <text class="temp" x="110" y="110">{temp_text}</text>
    <text class="meta" x="24" y="160">{text} — Wind: {cw.get('windspeed','--')} km/h</text>
    <text class="meta" x="24" y="185">{extra}</text>
    <text class="foot" x="24" y="{h-48}">Source: Open-Meteo</text>
  </g>
</svg>
'''
    OUT_SVG.parent.mkdir(parents=True, exist_ok=True)
    OUT_SVG.write_text(svg, encoding="utf-8")
    print("[OK] Wrote SVG to", OUT_SVG)


def main():
    data = fetch_weather()
    if not data:
        print("[ERROR] No data from Open-Meteo.")
        return 2
    key, entry = build_md_entry(data)
    if not key:
        print("[ERROR] Could not build entry.")
        return 2
    if already_exists(key):
        print("[INFO] Entry for this timestamp already exists; skipping append.")
    else:
        append_md(entry)
    # always (re)generate SVG to reflect latest data
    build_svg(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())