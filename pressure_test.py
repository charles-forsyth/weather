#!/usr/bin/python3
import requests

# --- Configuration ---
LATITUDE = 41.92919804645482
LONGITUDE = -77.05283564316002

def main():
    """Fetches grid data and prints the pressure section for debugging."""
    try:
        headers = {'User-Agent': 'MyPressureTest/1.0 (myemail@example.com)'}
        points_url = f"https://api.weather.gov/points/{LATITUDE},{LONGITUDE}"
        
        points_res = requests.get(points_url, headers=headers, timeout=15)
        points_res.raise_for_status()
        properties = points_res.json()['properties']
        
        grid_data_url = properties['forecastGridData']
        
        grid_res = requests.get(grid_data_url, headers=headers, timeout=15)
        grid_res.raise_for_status()
        grid_props = grid_res.json()['properties']
        
        # Print the relevant section of the API response
        print("--- Raw Pressure Data from API ---")
        if 'pressure' in grid_props:
            print(grid_props['pressure'])
        else:
            print("Key 'pressure' not found in grid properties.")
            print("\n--- All Available Keys ---")
            print(list(grid_props.keys()))

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

