## Daily Weather (Alamar, Havana)

This repo auto-updates `weather.md` and `art/weather.svg` twice a day using Open-Meteo for Alamar (La Habana, Cuba).
- Coordinates: 23.15794, -82.27837 (Alamar).
- API: Open-Meteo (no API key required).

To test locally:
- `python3 scripts/fetch_weather.py`
- Or curl the API for debugging:
  ```bash
  curl "https://api.open-meteo.com/v1/forecast?latitude=23.15794&longitude=-82.27837&current_weather=true&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&forecast_days=1&timezone=America/Havana"
  ```
