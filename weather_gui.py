#!/usr/bin/python3
import requests
import sys
import textwrap
import tkinter as tk
from tkinter import font
from PIL import Image, ImageTk
import os
import time
from datetime import datetime
import io
from config import LATITUDE, LONGITUDE

# --- Determine absolute path for icons ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_DIR = os.path.join(SCRIPT_DIR, "icons")

# --- Configuration ---
UPDATE_INTERVAL = 600000  # 10 minutes in milliseconds
RADAR_IMAGE_WIDTH = 500

# --- Color Palette ---
COLOR_BG = "#2E3440"
COLOR_FG = "#ECEFF4"
COLOR_HEADER = "#88C0D0"
COLOR_YELLOW = "#EBCB8B"

def get_moon_phase():
    LUNAR_MONTH = 29.530588853
    KNOWN_NEW_MOON = datetime(2000, 1, 6, 18, 14)
    now = datetime.utcnow()
    age = (now - KNOWN_NEW_MOON).total_seconds() / (24 * 3600)
    phase_decimal = (age / LUNAR_MONTH) % 1
    if phase_decimal < 0.03 or phase_decimal > 0.97: return "New Moon", "moon_new.png"
    if phase_decimal < 0.22: return "Waxing Crescent", "moon_waxing_crescent.png"
    if phase_decimal < 0.28: return "First Quarter", "moon_first_quarter.png"
    if phase_decimal < 0.47: return "Waxing Gibbous", "moon_waxing_gibbous.png"
    if phase_decimal < 0.53: return "Full Moon", "moon_full.png"
    if phase_decimal < 0.72: return "Waning Gibbous", "moon_waning_gibbous.png"
    if phase_decimal < 0.78: return "Third Quarter", "moon_third_quarter.png"
    return "Waning Crescent", "moon_waning_crescent.png"

def get_weather_data(lat, lon):
    try:
        headers = {'User-Agent': 'MyWeatherGUI/1.0 (myemail@example.com)'}
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        points_res = requests.get(points_url, headers=headers, timeout=15)
        points_res.raise_for_status()
        properties = points_res.json()['properties']
        
        hourly_url = properties['forecastHourly']
        grid_data_url = properties['forecastGridData']
        forecast_url = properties['forecast']

        hourly_res = requests.get(hourly_url, headers=headers, timeout=15)
        hourly_res.raise_for_status()
        current_period = hourly_res.json()['properties']['periods'][0]
        
        forecast_res = requests.get(forecast_url, headers=headers, timeout=15)
        forecast_res.raise_for_status()
        detailed_forecast = forecast_res.json()['properties']['periods'][0]['detailedForecast']

        grid_res = requests.get(grid_data_url, headers=headers, timeout=15)
        grid_res.raise_for_status()
        grid_props = grid_res.json()['properties']
        
        def get_grid_value(prop, default=0.0, factor=1.0, offset=0.0):
            val = grid_props.get(prop, {}).get('values', [{}])[0].get('value')
            return (val * factor) + offset if val is not None else default

        radar_image_url = None
        try:
            stations_res = requests.get("https://api.weather.gov/radar/stations", headers=headers, timeout=15)
            stations_res.raise_for_status()
            stations = stations_res.json()['features']
            
            closest_station = min(stations, key=lambda s: ((s['geometry']['coordinates'][1] - lat)**2 + (s['geometry']['coordinates'][0] - lon)**2))
            if closest_station:
                station_id = closest_station['properties']['id']
                radar_image_url = f"https://radar.weather.gov/ridge/standard/{station_id}_0.gif"
        except Exception:
            pass

        return {
            "radar_image_url": radar_image_url,
            "current_temp": current_period['temperature'],
            "short_forecast": current_period['shortForecast'],
            "detailed_forecast": detailed_forecast,
            "dewpoint_f": get_grid_value('dewpoint', factor=1.8, offset=32),
            "humidity": get_grid_value('relativeHumidity'),
            "sky_cover": get_grid_value('skyCover'),
            "wind_speed_mph": get_grid_value('windSpeed', factor=0.621371),
            "wind_direction": get_grid_value('windDirection'),
            "wind_gust_mph": get_grid_value('windGust', factor=0.621371),
            "max_temp": get_grid_value('maxTemperature', factor=1.8, offset=32),
            "min_temp": get_grid_value('minTemperature', factor=1.8, offset=32),
            "apparent_temp": get_grid_value('apparentTemperature', factor=1.8, offset=32),
            "pressure_in": get_grid_value('surfacePressure', factor=0.02953),
            "prob_precip": get_grid_value('probabilityOfPrecipitation'),
            "hazards": [item['value'] for sub in grid_props.get('hazards', {}).get('values', []) for item in sub.get('value', [])]
        }
    except Exception as e:
        print(f"--- Debug: CRITICAL ERROR in get_weather_data: {e}") # Keep this debug for now
        return None

class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Weather Report")
        self.configure(bg=COLOR_BG, padx=15, pady=15)
        self.last_update_time = 0
        self.radar_image = None
        self.radar_visible = True
        self.after_id = None

        self.bold_font = font.Font(family="Helvetica", size=12, weight="bold")
        self.normal_font = font.Font(family="Helvetica", size=11)
        self.small_font = font.Font(family="Helvetica", size=10)
        self.tiny_font = font.Font(family="Helvetica", size=8)

        self.load_icons()
        self.create_widgets()
        self.update_weather()
        self.update_countdown()

    def load_icons(self):
        self.icons = {}
        icon_files = {
            "temp": "temp.png", "humidity": "humidity.png", "wind": "wind.png", 
            "sky": "sky.png", "hazard": "hazard.png", "pressure": "pressure.png",
            "moon_new": "moon_new.png", "moon_waxing_crescent": "moon_waxing_crescent.png",
            "moon_first_quarter": "moon_first_quarter.png", "moon_waxing_gibbous": "moon_waxing_gibbous.png",
            "moon_full": "moon_full.png", "moon_waning_gibbous": "moon_waning_gibbous.png",
            "moon_third_quarter": "moon_third_quarter.png", "moon_waning_crescent": "moon_waning_crescent.png"
        }
        for name, filename in icon_files.items():
            path = os.path.join(ICON_DIR, filename)
            if os.path.exists(path):
                self.icons[name] = ImageTk.PhotoImage(Image.open(path).resize((20, 20), Image.LANCZOS))

    def create_widgets(self):
        tk.Label(self, text=f"Weather Report: {LATITUDE:.2f}, {LONGITUDE:.2f}", font=self.bold_font, bg=COLOR_BG, fg=COLOR_HEADER).grid(row=0, column=0, columnspan=2, pady=(0, 10))
        cond_frame = tk.Frame(self, bg=COLOR_BG, bd=1, relief="solid", padx=10, pady=10)
        cond_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        tk.Label(cond_frame, text="Current Conditions", font=self.bold_font, bg=COLOR_BG, fg=COLOR_FG).grid(row=0, column=0, columnspan=3, sticky="w")
        self.create_icon_label(cond_frame, "temp", 1, "Temp: ...")
        self.feels_var = self.create_info_label(cond_frame, 1, 2, "Feels Like: ...")
        self.create_icon_label(cond_frame, "humidity", 2, "Humidity: ...")
        self.dewpoint_var = self.create_info_label(cond_frame, 2, 2, "Dewpoint: ...")
        self.create_icon_label(cond_frame, "wind", 3, "Wind: ...")
        self.gust_var = self.create_info_label(cond_frame, 3, 2, "Gusts: ...")
        self.create_icon_label(cond_frame, "sky", 4, "Sky Cover: ...")
        self.precip_var = self.create_info_label(cond_frame, 4, 2, "Precip Chance: ...")
        self.pressure_frame = self.create_icon_label(cond_frame, "pressure", 5, "Pressure: ...") # Added pressure icon label
        self.fore_frame = tk.Frame(self, bg=COLOR_BG, bd=1, relief="solid", padx=10, pady=10)
        self.fore_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
        tk.Label(self.fore_frame, text="Forecast", font=self.bold_font, bg=COLOR_BG, fg=COLOR_FG).grid(row=0, column=0, sticky="w")
        self.high_low_var = tk.StringVar(value="High: ... Low: ...")
        tk.Label(self.fore_frame, textvariable=self.high_low_var, font=self.normal_font, bg=COLOR_BG, fg=COLOR_FG).grid(row=1, column=0, sticky="w")
        self.summary_var = tk.StringVar(value="Summary: ...")
        tk.Label(self.fore_frame, textvariable=self.summary_var, font=self.normal_font, bg=COLOR_BG, fg=COLOR_FG).grid(row=2, column=0, sticky="w")
        
        moon_frame = tk.Frame(self.fore_frame, bg=COLOR_BG)
        moon_frame.grid(row=3, column=0, sticky="w")
        self.moon_phase_var = tk.StringVar(value="Moon Phase: ...")
        tk.Label(moon_frame, textvariable=self.moon_phase_var, font=self.normal_font, bg=COLOR_BG, fg=COLOR_FG).pack(side="left")
        self.moon_icon_label = tk.Label(moon_frame, bg=COLOR_BG)
        self.moon_icon_label.pack(side="left", padx=5)

        self.detail_var = tk.StringVar(value="...")
        tk.Label(self.fore_frame, textvariable=self.detail_var, font=self.small_font, bg=COLOR_BG, fg=COLOR_FG, wraplength=450, justify="left").grid(row=4, column=0, sticky="w", pady=(5,0))
        self.hazards_frame = tk.Frame(self, bg=COLOR_BG, bd=1, relief="solid", padx=10, pady=10)
        self.radar_frame = tk.Frame(self, bg=COLOR_BG, bd=1, relief="solid", padx=10, pady=10)
        self.footer_frame = tk.Frame(self, bg=COLOR_BG)
        self.hazards_label = tk.Label(self.hazards_frame, image=self.icons.get("hazard"), text=" Hazards", font=self.bold_font, bg=COLOR_BG, fg=COLOR_YELLOW, compound="left")
        self.hazards_label.pack(anchor="w")
        self.hazards_var = tk.StringVar(value="")
        tk.Label(self.hazards_frame, textvariable=self.hazards_var, font=self.small_font, bg=COLOR_BG, fg=COLOR_YELLOW, wraplength=450, justify="left").pack(anchor="w")
        tk.Label(self.radar_frame, text="Live Radar", font=self.bold_font, bg=COLOR_BG, fg=COLOR_FG).pack()
        self.radar_label = tk.Label(self.radar_frame, bg=COLOR_BG)
        self.radar_label.pack()
        
        # --- Footer Widgets ---
        status_frame = tk.Frame(self.footer_frame, bg=COLOR_BG)
        status_frame.pack(side="left", expand=True, fill="x")
        self.last_updated_var = tk.StringVar(value="Last Updated: Never")
        tk.Label(status_frame, textvariable=self.last_updated_var, font=self.tiny_font, bg=COLOR_BG, fg=COLOR_FG).pack(side="left")
        self.next_update_var = tk.StringVar(value="Next update in: ...")
        tk.Label(status_frame, textvariable=self.next_update_var, font=self.tiny_font, bg=COLOR_BG, fg=COLOR_FG).pack(side="right")

        button_frame = tk.Frame(self.footer_frame, bg=COLOR_BG)
        button_frame.pack(side="right")
        tk.Button(button_frame, text="Toggle Radar", command=self.toggle_radar, font=self.tiny_font).pack(side="right", padx=5)
        tk.Button(button_frame, text="Refresh Now", command=self.refresh_now, font=self.tiny_font).pack(side="right")

    def update_layout(self, has_hazards, has_radar):
        next_row = 3
        if has_hazards:
            self.hazards_frame.grid(row=next_row, column=0, columnspan=2, sticky="ew", pady=5); next_row += 1
        else: self.hazards_frame.grid_forget()
        if has_radar and self.radar_visible:
            self.radar_frame.grid(row=next_row, column=0, columnspan=2, sticky="ew", pady=10); next_row += 1
        else: self.radar_frame.grid_forget()
        self.footer_frame.grid(row=next_row, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.update_idletasks()
        self.geometry(f"{self.winfo_reqwidth()}x{self.winfo_reqheight()}")

    def create_icon_label(self, parent, icon_name, row, text):
        frame = tk.Frame(parent, bg=COLOR_BG)
        frame.grid(row=row, column=0, columnspan=2, sticky="w")
        var = tk.StringVar(value=text)
        tk.Label(frame, image=self.icons.get(icon_name), bg=COLOR_BG).pack(side="left")
        tk.Label(frame, textvariable=var, font=self.normal_font, bg=COLOR_BG, fg=COLOR_FG).pack(side="left")
        setattr(self, f"{icon_name}_var", var)
        return frame

    def create_info_label(self, parent, row, col, text):
        var = tk.StringVar(value=text)
        tk.Label(parent, textvariable=var, font=self.small_font, bg=COLOR_BG, fg=COLOR_FG).grid(row=row, column=col, sticky="w", padx=10)
        return var

    def refresh_now(self):
        if self.after_id: self.after_cancel(self.after_id)
        self.update_weather()

    def toggle_radar(self):
        self.radar_visible = not self.radar_visible
        self.refresh_now()

    def update_weather(self):
        data = get_weather_data(LATITUDE, LONGITUDE)
        moon_name, moon_emoji = get_moon_phase()
        if not data:
            self.title("Error"); self.temp_var.set("Could not fetch weather data.")
            self.update_layout(has_hazards=False, has_radar=False)
        else:
            self.last_update_time = time.time()
            self.last_updated_var.set(f"Last Updated: {time.strftime('%H:%M:%S')}")
            self.title("Weather Report")
            self.temp_var.set(f"Temp: {data['current_temp']}°F")
            self.feels_var.set(f"Feels Like: {data['apparent_temp']:.1f}°F")
            self.humidity_var.set(f"Humidity: {data['humidity']:.1f}%")
            self.dewpoint_var.set(f"Dewpoint: {data['dewpoint_f']:.1f}°F")
            self.wind_var.set(f"Wind: {data['wind_speed_mph']:.1f} mph from {data['wind_direction']}°")
            self.gust_var.set(f"Gusts: {data['wind_gust_mph']:.1f} mph")
            self.sky_var.set(f"Sky Cover: {data['sky_cover']:.1f}%")
            self.precip_var.set(f"Precip Chance: {data['prob_precip']:.1f}%")
            
            if data['pressure_in'] and data['pressure_in'] > 0:
                self.pressure_var.set(f"Pressure: {data['pressure_in']:.2f} inHg")
                self.pressure_frame.grid(row=5, column=0, columnspan=2, sticky="w")
            else:
                self.pressure_frame.grid_forget()

            self.high_low_var.set(f"High: {data['max_temp']:.1f}°F   Low: {data['min_temp']:.1f}°F")
            self.summary_var.set(f"Summary: {data['short_forecast']}")
            
            moon_name, moon_icon_name = get_moon_phase()
            self.moon_phase_var.set(f"Moon Phase: {moon_name}")
            moon_icon_key = moon_icon_name.split('.')[0] # a bit fragile, but works for now
            if moon_icon_key in self.icons:
                self.moon_icon_label.config(image=self.icons[moon_icon_key])
            
            self.detail_var.set(data['detailed_forecast'])
            has_hazards = bool(data['hazards'])
            if has_hazards: self.hazards_var.set("\n".join(data['hazards']))
            has_radar = self.update_radar_image(data['radar_image_url'])
            self.update_layout(has_hazards, has_radar)
        self.after_id = self.after(UPDATE_INTERVAL, self.update_weather)

    def update_radar_image(self, image_url):
        if not image_url: return False
        try:
            response = requests.get(image_url, timeout=15)
            response.raise_for_status()
            image_data = io.BytesIO(response.content)
            img = Image.open(image_data)
            w_percent = (RADAR_IMAGE_WIDTH / float(img.size[0]))
            h_size = int((float(img.size[1]) * float(w_percent)))
            img = img.resize((RADAR_IMAGE_WIDTH, h_size), Image.LANCZOS)
            self.radar_image = ImageTk.PhotoImage(img)
            self.radar_label.config(image=self.radar_image)
            return True
        except Exception:
            return False

    def update_countdown(self):
        if self.last_update_time > 0:
            remaining = (self.last_update_time + UPDATE_INTERVAL / 1000) - time.time()
            if remaining > 0:
                minutes, seconds = divmod(int(remaining), 60)
                self.next_update_var.set(f"Next update in: {minutes:02d}:{seconds:02d}")
        self.after(1000, self.update_countdown)

def main():
    """Fork the process and run the Tkinter app in the background."""
    if os.fork() > 0: sys.exit(0)
    os.chdir("/")
    os.setsid()
    os.umask(0)
    if os.fork() > 0: sys.exit(0)
    with open(os.devnull, 'r') as f_read, open(os.devnull, 'a+') as f_write:
        os.dup2(f_read.fileno(), sys.stdin.fileno())
        os.dup2(f_write.fileno(), sys.stdout.fileno())
        os.dup2(f_write.fileno(), sys.stderr.fileno())
    app = WeatherApp()
    app.mainloop()

if __name__ == "__main__":
    main()
