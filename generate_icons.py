#!/usr/bin/python3
from PIL import Image, ImageDraw
import os

# --- Configuration ---
ICON_DIR = "icons"
ICON_SIZE = (24, 24)
COLOR_FG = "#ECEFF4"
COLOR_RED = "#BF616A"
COLOR_BLUE = "#5E81AC"
COLOR_YELLOW = "#EBCB8B"

def create_icon(filename, draw_func):
    """Creates a single icon image."""
    image = Image.new("RGBA", ICON_SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw_func(draw)
    filepath = os.path.join(ICON_DIR, filename)
    image.save(filepath)
    print(f"Generated {filepath}")

def draw_temp(draw):
    draw.rectangle((8, 4, 16, 16), fill=None, outline=COLOR_FG, width=2)
    draw.line((12, 16, 12, 20), fill=COLOR_FG, width=2)
    draw.ellipse((10, 18, 14, 22), fill=COLOR_RED, outline=COLOR_RED)

def draw_humidity(draw):
    draw.polygon([(12, 2), (6, 12), (12, 22), (18, 12)], fill=COLOR_BLUE)

def draw_wind(draw):
    draw.line((4, 8, 18, 8), fill=COLOR_FG, width=2)
    draw.line((6, 16, 20, 16), fill=COLOR_FG, width=2)

def draw_sky(draw):
    draw.ellipse((4, 10, 16, 22), fill=COLOR_FG, outline=COLOR_FG)
    draw.ellipse((10, 6, 22, 18), fill=COLOR_FG, outline=COLOR_FG)

def draw_high_temp(draw):
    draw.line((6, 18, 18, 6), fill=COLOR_RED, width=2)
    draw.polygon([(18, 10), (18, 2), (14, 6)], fill=COLOR_RED)

def draw_low_temp(draw):
    draw.line((6, 6, 18, 18), fill=COLOR_BLUE, width=2)
    draw.polygon([(18, 14), (18, 22), (14, 18)], fill=COLOR_BLUE)

def draw_hazard(draw):
    draw.polygon([(12, 2), (2, 20), (22, 20)], fill=COLOR_YELLOW)
    draw.text((10, 8), "!", fill="black", font_size=12)

def draw_pressure(draw):
    draw.ellipse((2, 2, 22, 22), fill=None, outline=COLOR_FG, width=2)
    draw.line((12, 4, 12, 12), fill=COLOR_FG, width=2)
    draw.polygon([(12, 12), (8, 16), (16, 16)], fill=COLOR_FG)

def draw_new_moon(draw):
    draw.ellipse((2, 2, 22, 22), fill=None, outline=COLOR_YELLOW, width=1)

def draw_waxing_crescent(draw):
    draw.ellipse((2, 2, 22, 22), fill=COLOR_YELLOW)
    draw.ellipse((0, 2, 20, 22), fill="#000000") # Blackout

def draw_first_quarter(draw):
    draw.arc((2, 2, 22, 22), start=270, end=90, fill=COLOR_YELLOW)
    draw.line((12, 2, 12, 22), fill=COLOR_YELLOW, width=1)

def draw_waxing_gibbous(draw):
    draw.ellipse((2, 2, 22, 22), fill=COLOR_YELLOW)
    draw.ellipse((6, 2, 26, 22), fill="#000000") # Blackout

def draw_full_moon(draw):
    draw.ellipse((2, 2, 22, 22), fill=COLOR_YELLOW)

def draw_waning_gibbous(draw):
    draw.ellipse((2, 2, 22, 22), fill=COLOR_YELLOW)
    draw.ellipse((-2, 2, 18, 22), fill="#000000") # Blackout

def draw_third_quarter(draw):
    draw.arc((2, 2, 22, 22), start=90, end=270, fill=COLOR_YELLOW)
    draw.line((12, 2, 12, 22), fill=COLOR_YELLOW, width=1)

def draw_waning_crescent(draw):
    draw.ellipse((2, 2, 22, 22), fill=COLOR_YELLOW)
    draw.ellipse((4, 2, 24, 22), fill="#000000") # Blackout

def main():
    """Generates simple geometric PNG icons."""
    if not os.path.exists(ICON_DIR):
        os.makedirs(ICON_DIR)

    create_icon("temp.png", draw_temp)
    create_icon("humidity.png", draw_humidity)
    create_icon("wind.png", draw_wind)
    create_icon("sky.png", draw_sky)
    create_icon("high_temp.png", draw_high_temp)
    create_icon("low_temp.png", draw_low_temp)
    create_icon("hazard.png", draw_hazard)
    create_icon("pressure.png", draw_pressure)

    # --- Moon Phase Icons ---
    create_icon("moon_new.png", draw_new_moon)
    create_icon("moon_waxing_crescent.png", draw_waxing_crescent)
    create_icon("moon_first_quarter.png", draw_first_quarter)
    create_icon("moon_waxing_gibbous.png", draw_waxing_gibbous)
    create_icon("moon_full.png", draw_full_moon)
    create_icon("moon_waning_gibbous.png", draw_waning_gibbous)
    create_icon("moon_third_quarter.png", draw_third_quarter)
    create_icon("moon_waning_crescent.png", draw_waning_crescent)

if __name__ == "__main__":
    main()
