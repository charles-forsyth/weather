#!/usr/bin/python3
import RPi.GPIO as GPIO
import requests
import time
import sys
import signal
import argparse
from .config import LATITUDE, LONGITUDE

# --- Configuration ---
RED_LED = 23
GREEN_LED = 18
BLUE_LED = 22
LED_PINS = [RED_LED, GREEN_LED, BLUE_LED]
TEMP_DEVIATION = 10
PRECIP_HEAVY = 0.30
PRECIP_MODERATE = 0.10
CHECK_INTERVAL = 1800

def graceful_exit(signum, frame):
    print("\nSignal received. Cleaning up GPIO...")
    GPIO.cleanup()
    print("GPIO cleaned up. Exiting.")
    sys.exit(0)

def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for pin in LED_PINS:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)

def get_weather_data(lat, lon):
    try:
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        headers = {'User-Agent': 'MyWeatherLED/1.0 (myemail@example.com)'}
        points_res = requests.get(points_url, headers=headers, timeout=15)
        points_res.raise_for_status()
        properties = points_res.json()['properties']
        hourly_url = properties['forecastHourly']
        grid_data_url = properties['forecastGridData']

        hourly_res = requests.get(hourly_url, headers=headers, timeout=15)
        hourly_res.raise_for_status()
        hourly_periods = hourly_res.json()['properties']['periods']
        if not hourly_periods: raise ValueError("Hourly forecast data is empty.")
        
        current_period = hourly_periods[0]
        current_temp = current_period['temperature']
        short_forecast = current_period['shortForecast'].lower()
        temps_next_24_hours = [p['temperature'] for p in hourly_periods[:24]]
        avg_temp = sum(temps_next_24_hours) / len(temps_next_24_hours)

        grid_res = requests.get(grid_data_url, headers=headers, timeout=15)
        grid_res.raise_for_status()
        precip_values = grid_res.json()['properties']['quantitativePrecipitation']['values']
        current_precip_mm = precip_values[0]['value'] if precip_values and precip_values[0]['value'] is not None else 0.0
        current_precip_in = current_precip_mm / 25.4

        print(f"Fetched: Temp={current_temp}°F, Avg={avg_temp:.1f}°F, Precip={current_precip_in:.3f} in/hr, Forecast='{short_forecast}'")
        return current_temp, avg_temp, short_forecast, current_precip_in
    except Exception as e:
        print(f"Error fetching weather data: {e}", file=sys.stderr)
        return None, None, None, None

def update_leds(current_temp, avg_temp, forecast, precip_in):
    """Set temperature LED and determine precipitation type/intensity."""
    # First, set the solid temperature LED
    if current_temp > avg_temp + TEMP_DEVIATION:
        GPIO.output(RED_LED, GPIO.HIGH)
        GPIO.output(GREEN_LED, GPIO.LOW)
        GPIO.output(BLUE_LED, GPIO.LOW)
        print("Condition: Warmer than average")
    elif current_temp < avg_temp - TEMP_DEVIATION:
        GPIO.output(RED_LED, GPIO.LOW)
        GPIO.output(GREEN_LED, GPIO.LOW)
        GPIO.output(BLUE_LED, GPIO.HIGH)
        print("Condition: Cooler than average")
    else:
        GPIO.output(RED_LED, GPIO.LOW)
        GPIO.output(GREEN_LED, GPIO.HIGH)
        GPIO.output(BLUE_LED, GPIO.LOW)
        print("Condition: About average")

    # Second, determine if there is precipitation
    precip_type = None
    if "sleet" in forecast or "freezing rain" in forecast: precip_type = "sleet"
    elif "snow" in forecast or "flurries" in forecast: precip_type = "snow"
    elif "rain" in forecast or "shower" in forecast or "thunderstorm" in forecast: precip_type = "rain"

    intensity = None
    if precip_type:
        if precip_in > PRECIP_HEAVY: intensity = "heavy"
        elif precip_in > PRECIP_MODERATE: intensity = "moderate"
        else: intensity = "light"
        print(f"Precipitation: {precip_type.capitalize()} ({intensity})")
    
    return precip_type, intensity

def handle_precipitation(precip_type, intensity, duration):
    """Blinks LEDs for precipitation, leaving temperature LED on."""
    patterns = {"light": (1.5, 1.5), "moderate": (0.75, 0.75), "heavy": (0.25, 0.25)}
    on_time, off_time = patterns[intensity]
    
    end_time = time.time() + duration
    while time.time() < end_time:
        if precip_type == "rain":
            GPIO.output(GREEN_LED, not GPIO.input(GREEN_LED)) # Toggle Green
            time.sleep(on_time)
        elif precip_type == "snow":
            GPIO.output(BLUE_LED, not GPIO.input(BLUE_LED)) # Toggle Blue
            time.sleep(on_time)
        elif precip_type == "sleet":
            # This case is tricky, as it needs to override the solid green/blue
            # For now, we will just alternate, which will look odd with a solid color
            GPIO.output(GREEN_LED, GPIO.HIGH)
            GPIO.output(BLUE_LED, GPIO.LOW)
            time.sleep(on_time / 2)
            GPIO.output(GREEN_LED, GPIO.LOW)
            GPIO.output(BLUE_LED, GPIO.HIGH)
            time.sleep(on_time / 2)

        if time.time() >= end_time: break
        # The 'off' period is handled by the toggle, but we need to wait
        if precip_type != 'sleet':
             time.sleep(off_time)


def run_self_test():
    print("--- Starting Self-Test Mode ---")
    test_duration = 5
    try:
        print("\nTesting: Warmer (Solid Red) + Rain (Blinking Green)")
        GPIO.output(RED_LED, GPIO.HIGH)
        handle_precipitation("rain", "moderate", test_duration)
        GPIO.output(RED_LED, GPIO.LOW)

        print("\nTesting: Average (Solid Green) + Snow (Blinking Blue)")
        GPIO.output(GREEN_LED, GPIO.HIGH)
        handle_precipitation("snow", "light", test_duration)
        GPIO.output(GREEN_LED, GPIO.LOW)

        print("\nTesting: Cooler (Solid Blue) + Sleet (Alt. Green/Blue)")
        GPIO.output(BLUE_LED, GPIO.HIGH)
        handle_precipitation("sleet", "heavy", test_duration)
        GPIO.output(BLUE_LED, GPIO.LOW)
        
        print("\n--- Self-Test Complete ---")
    except KeyboardInterrupt:
        print("\nSelf-test interrupted.")

def main():
    parser = argparse.ArgumentParser(description="Run a weather indicator LED.")
    parser.add_argument('-d', '--duration', type=int, default=30, help='Duration to run in seconds.')
    parser.add_argument('-t', '--test', action='store_true', help='Run a self-test.')
    args = parser.parse_args()

    signal.signal(signal.SIGTERM, graceful_exit)
    signal.signal(signal.SIGINT, graceful_exit)
    setup_gpio()

    try:
        if args.test:
            run_self_test()
        else:
            print(f"Starting Weather LED script for {args.duration} seconds...")
            start_time = time.time()
            while time.time() - start_time < args.duration:
                remaining = args.duration - (time.time() - start_time)
                data = get_weather_data(LATITUDE, LONGITUDE)
                if all(v is not None for v in data):
                    precip_type, intensity = update_leds(*data)
                    action_duration = min(CHECK_INTERVAL, remaining)
                    if precip_type and intensity:
                        handle_precipitation(precip_type, intensity, action_duration)
                    else:
                        time.sleep(action_duration)
                else:
                    print("Retrying in 5 minutes...")
                    time.sleep(min(300, remaining))
    finally:
        graceful_exit(None, None)

if __name__ == "__main__":
    main()