#!/usr/bin/env python3
import json
import sys
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timedelta

def get_forecast(lat, lon):
    # Base URL
    url = "https://api.open-meteo.com/v1/forecast"
    
    # Paragliding-relevant Pressure Levels (hPa)
    # 950 (~1800ft - Tiger Launch), 925, 900, 850 (~5000ft), 800, 700 (~10k ft)
    levels = [950, 925, 900, 850, 800, 700]
    
    # 1. Surface Parameters
    hourly_params = [
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "weather_code",
        "cloud_cover",
        "cloud_cover_low",
        "cloud_cover_mid",
        "cloud_cover_high",
        "wind_speed_10m",
        "wind_direction_10m",
        "wind_gusts_10m",
        "cape",
        "lifted_index",
        "boundary_layer_height" # Great for thermal top estimation!
    ]
    
    # 2. Pressure Level Parameters (Wind & Temp for Shear/Lapse Rate)
    for lvl in levels:
        hourly_params.append(f"temperature_{lvl}hPa")
        hourly_params.append(f"wind_speed_{lvl}hPa")
        hourly_params.append(f"wind_direction_{lvl}hPa")
        hourly_params.append(f"geopotential_height_{lvl}hPa")

    # Query Params
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(hourly_params),
        "wind_speed_unit": "kn",      # Knots are standard for aviation
        "precipitation_unit": "mm",
        "timeformat": "iso8601",
        "timezone": "auto",           # Local time is easier for planning
        "models": "best_match"        # Uses GFS/ECMWF/ICON depending on location/accuracy
    }
    
    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"

    try:
        req = urllib.request.Request(full_url)
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                
                # Simplify Output: Filter to next 24-48h only to save context
                # (The API returns 7 days by default)
                return filter_forecast(data)
            else:
                return {"error": f"API Error: {response.status}", "body": response.read().decode('utf-8')}
                
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP Error: {e.code}", "body": e.read().decode('utf-8')}
    except Exception as e:
        return {"error": str(e)}

def filter_forecast(data):
    """Keep only the next 48 hours of data to keep context light."""
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    
    if not times:
        return data

    # Find index for "now" and "now + 48h"
    now_iso = datetime.now().isoformat()
    # Simple string comparison works for ISO8601 if timezone matches, 
    # but let's just take the first 48 entries (0 to 48) as API returns start=today
    
    limit = 48
    
    new_hourly = {}
    new_hourly["units"] = data.get("hourly_units", {})
    
    for key, values in hourly.items():
        if len(values) > limit:
            new_hourly[key] = values[:limit]
        else:
            new_hourly[key] = values
            
    return {
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "elevation": data.get("elevation"),
        "hourly": new_hourly
    }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: meteo.py <lat> <lon>" }))
        sys.exit(1)

    lat = sys.argv[1]
    lon = sys.argv[2]
    
    result = get_forecast(lat, lon)
    print(json.dumps(result, indent=2))
