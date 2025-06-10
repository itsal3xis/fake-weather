# fake_weather_logic.py
import random
from datetime import datetime, timedelta
import configparser
import os

# --- Configuration Loading ---
config = configparser.ConfigParser()
config_file_path = 'config.cfg'

if not os.path.exists(config_file_path):
    # In a real app, you might want to log this or raise a more specific error
    # For now, we'll just print and exit, as app.py will rely on these globals
    print(f"Error: Configuration file '{config_file_path}' not found.")
    print("Please create a 'config.cfg' file in the same directory as app.py and fake_weather_logic.py.")
    exit(1)

config.read(config_file_path)

# Global variables to store parsed config data - these will be imported by app.py
CITIES = []
HUMIDITY_RANGE = (0, 0)
WIND_SPEED_RANGE = (0, 0)
SEASONAL_CONDITIONS = {}
MONTHLY_TEMPERATURE_RANGES = {}
WEATHER_ASCII_ART = {}
TEMP_UNIT = 'celsius'
WIND_UNIT = 'km/h'
TEMP_UNIT_CHAR = 'C'
WIND_UNIT_CHAR = 'km/h'
API_PORT = 5000 # Default, will be overridden by app.py's config loading

try:
    CITIES = [city.strip() for city in config.get('Weather', 'cities').split(',')]
    HUMIDITY_RANGE = tuple(map(int, config.get('Weather', 'humidity_range').split(',')))
    WIND_SPEED_RANGE = tuple(map(int, config.get('Weather', 'wind_speed_range').split(',')))
    
    TEMP_UNIT = config.get('Units', 'temperature_unit').lower()
    WIND_UNIT = config.get('Units', 'wind_speed_unit').lower()

    if TEMP_UNIT == 'imperial':
        TEMP_UNIT_CHAR = 'F'
    else:
        TEMP_UNIT_CHAR = 'C'

    if WIND_UNIT == 'imperial':
        WIND_UNIT_CHAR = 'mph'
    else:
        WIND_UNIT_CHAR = 'km/h'

    for season_key in ['summer_conditions', 'autumn_conditions', 'winter_conditions', 'spring_conditions']:
        conditions_str = config.get('WeatherConditions', season_key)
        parsed_conditions = {}
        for item in conditions_str.split(','):
            condition, weight = item.strip().split(':')
            parsed_conditions[condition.strip()] = int(weight.strip())
        SEASONAL_CONDITIONS[season_key.replace('_conditions', '')] = parsed_conditions

    for month_num in range(1, 13):
        month_name = datetime(2000, month_num, 1).strftime('%B').lower()
        temp_range_str = config.get('TemperatureRanges', month_name)
        MONTHLY_TEMPERATURE_RANGES[month_num] = tuple(map(int, temp_range_str.split(',')))

    for condition_key in config.options('ASCIIArt'):
        WEATHER_ASCII_ART[condition_key.replace('_', ' ').title()] = config.get('ASCIIArt', condition_key)

    API_PORT = config.getint('API', 'port') # This will be the default, but app.py will use its own config.getint

except configparser.Error as e:
    print(f"Error reading configuration from 'config.cfg': {e}")
    print("Please ensure all required sections and keys are present and correctly formatted.")
    exit(1)

# --- Column Alignment Settings ---
# These values are chosen based on typical lengths and desired visual spacing.
# Adjust these numbers to fine-tune alignment in your terminal.
ASCII_ART_COLUMN_WIDTH = 9  # Max width of an ASCII art line itself (e.g., "_ O _")
SPACING_AFTER_ART = 3       # Spaces between ASCII art column and the next (temp/condition/time)
LEFT_COLUMN_CONTENT_MAX_WIDTH = 15 # Max expected width for 'condition' field (e.g., 'Partly Cloudy' is 13)
SPACING_AFTER_LEFT_COLUMN = 2 # Spaces between the left column and the right column (feels like/wind speed/thanks)

# Calculate the precise starting position for the "feels like" / "wind speed" / "thanks" column
RIGHT_COLUMN_START_POS = ASCII_ART_COLUMN_WIDTH + SPACING_AFTER_ART + LEFT_COLUMN_CONTENT_MAX_WIDTH + SPACING_AFTER_LEFT_COLUMN


# --- Unit Conversion Functions ---
def celsius_to_fahrenheit(celsius):
    return (celsius * 9/5) + 32

def kmh_to_mph(kmh):
    return kmh * 0.621371

def get_season(month):
    """Determines the season based on the month (Northern Hemisphere)."""
    if 6 <= month <= 8:
        return 'summer'
    elif 9 <= month <= 11:
        return 'autumn'
    elif 12 == month or 1 <= month <= 2:
        return 'winter'
    else: # 3 <= month <= 5
        return 'spring'

def select_weather_condition(season_conditions_with_weights):
    """Selects a weather condition based on its probability weights."""
    conditions = list(season_conditions_with_weights.keys())
    weights = list(season_conditions_with_weights.values())
    return random.choices(conditions, weights=weights, k=1)[0]


def generate_fake_weather_data(city):
    """Generates a dictionary of fake weather data for a given city based on current month/season."""
    
    current_month = datetime.now().month
    
    temp_min, temp_max = MONTHLY_TEMPERATURE_RANGES.get(current_month, (-10, 25))
    temperature_celsius = round(random.uniform(temp_min, temp_max), 1)

    humidity = random.randint(HUMIDITY_RANGE[0], HUMIDITY_RANGE[1])
    wind_speed_kmh = round(random.uniform(WIND_SPEED_RANGE[0], WIND_SPEED_RANGE[1]), 1)
    
    current_season = get_season(current_month)
    season_conditions = SEASONAL_CONDITIONS.get(current_season, {})
    if not season_conditions:
        condition = random.choice(list(SEASONAL_CONDITIONS.get('summer', {'Sunny':1}).keys()))
    else:
        condition = select_weather_condition(season_conditions)
    
    feels_like_celsius = temperature_celsius
    if temperature_celsius > 25 and wind_speed_kmh > 20: 
        feels_like_celsius = round(temperature_celsius + (wind_speed_kmh * 0.05), 1) 
    elif temperature_celsius < 10 and wind_speed_kmh > 10: 
        feels_like_celsius = round(temperature_celsius - (wind_speed_kmh * 0.2), 1) 
    elif temperature_celsius < 0 and wind_speed_kmh > 5: 
        feels_like_celsius = round(temperature_celsius - (wind_speed_kmh * 0.3), 1)

    ascii_art_raw = WEATHER_ASCII_ART.get(condition, "")
    ascii_art_lines = ascii_art_raw.splitlines()
    while len(ascii_art_lines) < 3: # Ensure exactly 3 lines for consistent output
        ascii_art_lines.append("")
    ascii_art_lines = ascii_art_lines[:3]


    return {
        "city": city,
        "temperature_celsius": temperature_celsius,
        "feels_like_celsius": feels_like_celsius,
        "humidity_percent": humidity,
        "wind_speed_kmh": wind_speed_kmh,
        "condition": condition,
        "ascii_art_lines": ascii_art_lines,
        "timestamp": datetime.now()
    }

# Function to build a line with fixed column positions
def build_aligned_weather_line(art_part, left_content, right_content):
    # Pad art_part to ASCII_ART_COLUMN_WIDTH
    formatted_art = art_part.ljust(ASCII_ART_COLUMN_WIDTH)
    
    # Ensure left_content is not longer than its max allowed width, or it will push out alignment
    left_content_padded = left_content.ljust(LEFT_COLUMN_CONTENT_MAX_WIDTH)

    return (
        f"{formatted_art}" 
        f"{' '*SPACING_AFTER_ART}" 
        f"{left_content_padded}"
        f"{' '*SPACING_AFTER_LEFT_COLUMN}" 
        f"{right_content}"
    )