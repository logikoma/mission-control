import json
import sys

with open('meteo_output.json', 'r') as f:
    data = json.load(f)

hourly = data['hourly']
times = hourly['time']

# Indices for tomorrow 10am to 4pm
# Assuming index 0 is today 00:00
start_idx = 34
end_idx = 41

print(f"{'Time':<20} | {'Sfc Wind':<8} | {'Gust':<5} | {'Launch':<8} | {'Dir':<4} | {'CAPE':<5} | {'Prec':<5} | {'T_2m':<5}")
print("-" * 80)

for i in range(start_idx, end_idx):
    time = times[i]
    sfc_wind = hourly['wind_speed_10m'][i]
    gust = hourly['wind_gusts_10m'][i]
    launch_wind = hourly['wind_speed_950hPa'][i]
    launch_dir = hourly['wind_direction_950hPa'][i]
    cape = hourly['cape'][i]
    prec = hourly['precipitation'][i]
    temp = hourly['temperature_2m'][i]
    
    print(f"{time:<20} | {sfc_wind:>8} | {gust:>5} | {launch_wind:>8} | {launch_dir:>4} | {cape:>5} | {prec:>5} | {temp:>5}")

# Stability/Lapse Rate
# Let's look at 950hPa vs 850hPa
t_950 = hourly['temperature_950hPa'][start_idx+3] # ~1pm
t_850 = hourly['temperature_850hPa'][start_idx+3]
h_950 = hourly['geopotential_height_950hPa'][start_idx+3]
h_850 = hourly['geopotential_height_850hPa'][start_idx+3]

lapse_rate = (t_950 - t_850) / ((h_850 - h_950) / 100) # C per 100m
print(f"\nLapse Rate (950-850hPa) at 1pm: {lapse_rate:.2f} C/100m")
