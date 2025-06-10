# app.py
from flask import Flask, jsonify, Response, render_template
from flask_cors import CORS # Import CORS for handling cross-origin requests
import random
from datetime import datetime, timedelta
import os
import datetime
import configparser

# Import all necessary components from our weather logic file
from weather import (
    CITIES, HUMIDITY_RANGE, WIND_SPEED_RANGE, SEASONAL_CONDITIONS,
    MONTHLY_TEMPERATURE_RANGES, WEATHER_ASCII_ART, TEMP_UNIT, WIND_UNIT,
    TEMP_UNIT_CHAR, WIND_UNIT_CHAR, API_PORT, # Import API_PORT for app.run
    celsius_to_fahrenheit, kmh_to_mph,
    generate_fake_weather_data, build_aligned_weather_line # Also import the line builder
)

app = Flask(__name__)
# Enable CORS for all routes, allowing your HTML page to fetch from this API
CORS(app) 

# Ensure the config.cfg file exists. This check is also in fake_weather_logic.py
# but helpful to have here in case app.py is run directly first.
config_file_path = 'config.cfg'
if not os.path.exists(config_file_path):
    print(f"Error: Configuration file '{config_file_path}' not found.")
    print("Please create a 'config.cfg' file in the same directory as app.py.")
    exit(1)

# --- Routes ---

# This route serves your HTML presentation page
@app.route('/')
def index():
    # render_template looks for 'index.html' in a 'templates' folder by default.
    # For a minimalist example, we'll explicitly load it from the current directory.
    # In a larger project, you'd put index.html in a 'templates' subfolder.
    return render_template('index.html')


@app.route('/weather/<city_name>')
def get_weather_for_city(city_name):
    """
    Returns fake weather data for a specific city, formatted as plain text like the image.
    Case-insensitive search.
    """
    normalized_city_name = city_name.replace('-', ' ').title() 
    
    if normalized_city_name not in CITIES:
        # Return a plain text error for consistency with the main endpoint
        return Response(f"Error: City '{city_name}' not found. Available cities: {', '.join(CITIES)}", mimetype='text/plain', status=404)

    weather_data = generate_fake_weather_data(normalized_city_name)

    display_temp = weather_data['temperature_celsius']
    display_feels_like = weather_data['feels_like_celsius']
    display_wind_speed = weather_data['wind_speed_kmh']

    if TEMP_UNIT == 'imperial':
        display_temp = celsius_to_fahrenheit(display_temp)
        display_feels_like = celsius_to_fahrenheit(display_feels_like)
    
    if WIND_UNIT == 'imperial':
        display_wind_speed = kmh_to_mph(display_wind_speed)

    display_time = weather_data['timestamp'].strftime('%I:%M %p')

    display_temp = round(display_temp)
    display_feels_like = round(display_feels_like)
    display_wind_speed = round(display_wind_speed)

    # --- Format strings for output components ---
    temp_str = f"{display_temp}°{TEMP_UNIT_CHAR}"
    feels_like_str = f"feels like {display_feels_like}°{TEMP_UNIT_CHAR}"
    wind_speed_str = f"wind speed {display_wind_speed} {WIND_UNIT_CHAR}"
    
    condition_str = weather_data['condition']
    time_str = display_time
    thanks_str = f"Humidity {weather_data['humidity_percent']}%"

    # --- Construct lines with precise alignment using the imported builder ---
    art_lines = weather_data['ascii_art_lines']

    line1 = build_aligned_weather_line(art_lines[0], temp_str, feels_like_str)
    line2 = build_aligned_weather_line(art_lines[1], condition_str, wind_speed_str)
    line3 = build_aligned_weather_line(art_lines[2], time_str, thanks_str)

    plain_text_output = f"{line1}\n{line2}\n{line3}\n"

    return Response(plain_text_output, mimetype='text/plain')


@app.route('/weather/all')
def get_all_weather():
    """Returns fake weather data for all predefined cities (JSON)."""
    all_weather_data = [generate_fake_weather_data(city) for city in CITIES]
    for data in all_weather_data:
        data['ascii_art'] = "\n".join(data['ascii_art_lines'])
        del data['ascii_art_lines']
        data['timestamp'] = data['timestamp'].isoformat()
    return jsonify(all_weather_data)

@app.route('/weather/forecast/<city_name>')
def get_forecast_for_city(city_name):
    """
    Returns a simple 3-day fake forecast for a specific city (JSON).
    """
    normalized_city_name = city_name.replace('-', ' ').title()
    
    if normalized_city_name not in CITIES:
        return jsonify({"error": f"City '{city_name}' not found. Available cities: {', '.join(CITIES)}"}), 404

    forecast_data = []
    for i in range(1, 4):
        future_date = datetime.now() + timedelta(days=i)
        forecast_month = future_date.month
        
        forecast_temp_min, forecast_temp_max = MONTHLY_TEMPERATURE_RANGES.get(forecast_month, (-10, 25))
        forecast_temperature = round(random.uniform(forecast_temp_min, forecast_temp_max), 1)
        
        forecast_season = None #get_season(forecast_month)
        forecast_season_conditions = SEASONAL_CONDITIONS.get(forecast_season, {})
        if not forecast_season_conditions:
            forecast_condition = random.choice(list(SEASONAL_CONDITIONS.get('summer', {'Sunny':1}).keys()))
        else:
            pass
            #forecast_condition = select_weather_condition(forecast_season_conditions)

        forecast_ascii_art_raw = WEATHER_ASCII_ART.get(forecast_condition, "")
        
        forecast_data.append({
            "date": future_date.strftime("%Y-%m-%d"),
            "city": normalized_city_name,
            "temperature_celsius": forecast_temperature,
            "condition": forecast_condition,
            "ascii_art": forecast_ascii_art_raw
        })
    return jsonify({"city": normalized_city_name, "forecast": forecast_data})


if __name__ == '__main__':
    print(f"Starting Fake Weather API on port {API_PORT}...")
    # Flask will by default look for templates in a 'templates' folder.
    # To serve index.html from the current directory, we need to tell Flask.
    # For a simple local setup, we can explicitly point the template_folder.
    app.run(debug=True, port=API_PORT)