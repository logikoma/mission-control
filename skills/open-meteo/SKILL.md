# Open-Meteo Skill

Provides free, detailed weather forecasts suitable for paragliding and aviation analysis using the Open-Meteo API.

## Tools

### `meteo_forecast`

Get a detailed hourly forecast including wind shear (pressure levels), thermals (CAPE, Lifted Index, Boundary Layer), and cloud cover.

**Parameters:**
- `latitude` (number, required): Location latitude.
- `longitude` (number, required): Location longitude.

**Returns:**
JSON object containing the next 48 hours of hourly data. 
- Units: Wind in **Knots**, Temp in **Celsius**.
- Levels: Surface, 950hPa (~1800ft), 900hPa (~3000ft), 850hPa (~5000ft), 800hPa, 700hPa (~10k ft).

**Usage:**
```bash
python3 skills/open-meteo/meteo.py {latitude} {longitude}
```
