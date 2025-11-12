# Weather Monitoring Suite

This project provides a suite of Python tools for monitoring and displaying weather information from the U.S. National Weather Service API. It includes a graphical desktop application, a Raspberry Pi LED indicator, and utility scripts for icon generation.

## Features

*   **Graphical Weather App (`weather_gui.py`)**:
    *   Displays current temperature, humidity, wind speed, and more.
    *   Shows a detailed multi-day forecast.
    *   Includes a live weather radar image.
    *   Displays the current moon phase using custom-generated icons.
    *   Automatically refreshes data every 10 minutes.

*   **Raspberry Pi LED Indicator (`weather_leds.py`)**:
    *   Provides a simple, at-a-glance weather status using colored LEDs.
    *   Indicates temperature relative to the 24-hour average (warmer, cooler, or average).
    *   Blinks to indicate precipitation (rain, snow, or sleet) with varying intensity.

*   **Icon Generation (`generate_icons.py`)**:
    *   A utility script to create the PNG icons used by the GUI, ensuring a consistent visual style.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone git@github.com:charles-forsyth/weather.git
    cd weather
    ```

2.  **Install the required Python libraries:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Weather GUI

To launch the graphical weather application, run:
```bash
python3 weather_gui.py
```
The application will run as a background process.

### Weather LEDs (for Raspberry Pi)

To run the LED indicator on a Raspberry Pi:
```bash
python3 weather_leds.py
```
You can also run it for a specific duration or in self-test mode:
```bash
# Run for one hour
python3 weather_leds.py --duration 3600

# Run a self-test of the LEDs
python3 weather_leds.py --test
```

## Configuration

The latitude and longitude for the weather data are now managed in `config.py`. You can change the `LATITUDE` and `LONGITUDE` constants in `config.py` to get weather for your desired location.
