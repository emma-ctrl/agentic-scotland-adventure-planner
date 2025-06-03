import modal
from typing import Dict, Any
import json
import requests

# Copy the SimpleWeatherMCP class directly into this file to avoid import issues
class SimpleWeatherMCP:
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1"
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1"
    
    def list_tools(self) -> Dict[str, Any]:
        return {
            "tools": [
                {
                    "name": "get_weather",
                    "description": "Get current weather for a location in Scotland using Open-Meteo (no API key required)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "City or location name (e.g., 'Edinburgh', 'Glasgow')"
                            }
                        },
                        "required": ["location"]
                    }
                },
                {
                    "name": "get_forecast",
                    "description": "Get multi-day weather forecast for trip planning in Scotland",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "City or location name (e.g., 'Edinburgh', 'Glasgow')"
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days to forecast (1-7, default: 3)",
                                "minimum": 1,
                                "maximum": 7,
                                "default": 3
                            }
                        },
                        "required": ["location"]
                    }
                }
            ]
        }
    
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name == "get_weather":
            return self._get_weather(arguments["location"])
        elif name == "get_forecast":
            days = arguments.get("days", 3)  # Default to 3 days
            return self._get_forecast(arguments["location"], days)
        else:
            return {"error": f"Unknown tool: {name}"}
    
    def _get_weather(self, location: str) -> Dict[str, Any]:
        try:
            coords = self._get_coordinates(location)
            if not coords:
                return {"error": f"Could not find location: {location}"}
            
            lat, lon, display_name = coords
            
            url = f"{self.base_url}/forecast"
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": [
                    "temperature_2m",
                    "relative_humidity_2m", 
                    "apparent_temperature",
                    "weather_code",
                    "wind_speed_10m",
                    "wind_direction_10m",
                    "pressure_msl"
                ],
                "timezone": "Europe/London"
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            current = data["current"]
            
            weather_descriptions = {
                0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                45: "Fog", 48: "Depositing rime fog",
                51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
                56: "Light freezing drizzle", 57: "Dense freezing drizzle",
                61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
                66: "Light freezing rain", 67: "Heavy freezing rain",
                71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
                77: "Snow grains", 80: "Slight rain showers", 81: "Moderate rain showers",
                82: "Violent rain showers", 85: "Slight snow showers", 86: "Heavy snow showers",
                95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
            }
            
            weather_desc = weather_descriptions.get(current["weather_code"], "Unknown")
            wind_dir = current["wind_direction_10m"]
            wind_compass = self._wind_direction_to_compass(wind_dir)
            
            summary = f"""Current weather in {display_name}:
- Temperature: {current['temperature_2m']}°C (feels like {current['apparent_temperature']}°C)
- Conditions: {weather_desc}
- Humidity: {current['relative_humidity_2m']}%
- Wind: {current['wind_speed_10m']} km/h from {wind_compass}
- Pressure: {current['pressure_msl']} hPa
- Last updated: {current['time']}"""
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": summary
                    }
                ]
            }
            
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to fetch weather data: {str(e)}"}
        except KeyError as e:
            return {"error": f"Unexpected weather data format: {str(e)}"}
    
    def _get_forecast(self, location: str, days: int = 3) -> Dict[str, Any]:
        """Get multi-day weather forecast for trip planning"""
        try:
            coords = self._get_coordinates(location)
            if not coords:
                return {"error": f"Could not find location: {location}"}
            
            lat, lon, display_name = coords
            
            url = f"{self.base_url}/forecast"
            params = {
                "latitude": lat,
                "longitude": lon,
                "daily": [
                    "temperature_2m_max",
                    "temperature_2m_min", 
                    "weather_code",
                    "precipitation_sum",
                    "wind_speed_10m_max",
                    "wind_gusts_10m_max"
                ],
                "timezone": "Europe/London",
                "forecast_days": days
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            daily = data["daily"]
            
            # Weather code descriptions (same as before)
            weather_descriptions = {
                0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                45: "Fog", 48: "Depositing rime fog",
                51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
                56: "Light freezing drizzle", 57: "Dense freezing drizzle",
                61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
                66: "Light freezing rain", 67: "Heavy freezing rain",
                71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
                77: "Snow grains", 80: "Slight rain showers", 81: "Moderate rain showers",
                82: "Violent rain showers", 85: "Slight snow showers", 86: "Heavy snow showers",
                95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
            }
            
            # Build forecast summary
            forecast_lines = [f"{days}-day weather forecast for {display_name}:"]
            forecast_lines.append("")
            
            for i in range(days):
                date = daily["time"][i]
                temp_max = daily["temperature_2m_max"][i]
                temp_min = daily["temperature_2m_min"][i]
                weather_code = daily["weather_code"][i]
                precipitation = daily["precipitation_sum"][i]
                wind_max = daily["wind_speed_10m_max"][i]
                wind_gusts = daily["wind_gusts_10m_max"][i]
                
                weather_desc = weather_descriptions.get(weather_code, "Unknown")
                
                # Format the day (e.g., "Mon, Jun 3")
                from datetime import datetime
                date_obj = datetime.fromisoformat(date)
                day_name = date_obj.strftime("%a, %b %d")
                
                # Build day summary
                day_summary = f"📅 {day_name}: {weather_desc}"
                day_summary += f"\n   🌡️  {temp_min}°C to {temp_max}°C"
                
                if precipitation > 0:
                    day_summary += f"\n   🌧️  Rain: {precipitation}mm"
                
                if wind_max > 20:  # Highlight strong winds (adventure relevant!)
                    day_summary += f"\n   💨 Wind: {wind_max} km/h (gusts {wind_gusts} km/h)"
                else:
                    day_summary += f"\n   💨 Wind: {wind_max} km/h"
                
                # Adventure suitability hint
                if weather_code in [0, 1, 2] and wind_max < 25 and precipitation == 0:
                    day_summary += "\n   ✅ Great for outdoor activities!"
                elif weather_code in [61, 63, 65] or precipitation > 5:
                    day_summary += "\n   ⚠️  Wet weather - plan indoor alternatives"
                elif wind_max > 40:
                    day_summary += "\n   ⚠️  Very windy - avoid exposed areas"
                
                forecast_lines.append(day_summary)
                forecast_lines.append("")
            
            summary = "\n".join(forecast_lines)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": summary
                    }
                ]
            }
            
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to fetch forecast data: {str(e)}"}
        except KeyError as e:
            return {"error": f"Unexpected forecast data format: {str(e)}"}
        except Exception as e:
            return {"error": f"Error processing forecast: {str(e)}"}
    
    def _get_coordinates(self, location: str) -> tuple:
        """Get latitude and longitude with smart geographic filtering"""
        try:
            url = f"{self.geocoding_url}/search"
            params = {
                "name": location,
                "count": 10,  # Get multiple results to filter
                "language": "en",
                "format": "json"
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("results"):
                results = data["results"]
                
                # Define your target geographic area (Scotland/UK bounds)
                # Modify these bounds for other regions
                TARGET_LAT_MIN = 50.0   # Southern England
                TARGET_LAT_MAX = 61.0   # Northern Scotland  
                TARGET_LON_MIN = -8.0   # Western Ireland
                TARGET_LON_MAX = 2.0    # Eastern England
                
                # Filter results by geographic bounds
                for result in results:
                    lat = result["latitude"]
                    lon = result["longitude"]
                    
                    # Check if coordinates are in UK/Scotland area
                    if (TARGET_LAT_MIN <= lat <= TARGET_LAT_MAX and 
                        TARGET_LON_MIN <= lon <= TARGET_LON_MAX):
                        
                        return (
                            lat, lon,
                            result["name"] + (f", {result['admin1']}" if "admin1" in result else "")
                        )
                
                # Fallback: If no results in target area, use first result
                # (This handles places outside Scotland/UK that user might search for)
                result = results[0]
                return (
                    result["latitude"], 
                    result["longitude"],
                    result["name"] + (f", {result['admin1']}" if "admin1" in result else "")
                )
            
            return None
            
        except Exception as e:
            return None
    
    def _wind_direction_to_compass(self, degrees: float) -> str:
        if degrees is None:
            return "Unknown"
        
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = round(degrees / 22.5) % 16
        return directions[index]

app = modal.App("scotland-weather-mcp")

@app.function(
    image=modal.Image.debian_slim().pip_install("requests", "fastapi", "uvicorn")
)
@modal.asgi_app()
def fastapi_app():
    from fastapi import FastAPI
    
    web_app = FastAPI()

    @web_app.post("/mcp")
    async def mcp_endpoint(request_dict: Dict[str, Any]) -> Dict[str, Any]:
        mcp_server = SimpleWeatherMCP()
        
        method = request_dict.get("method")
        
        if method == "tools/list":
            return mcp_server.list_tools()
        elif method == "tools/call":
            tool_name = request_dict.get("params", {}).get("name")
            arguments = request_dict.get("params", {}).get("arguments", {})
            return mcp_server.call_tool(tool_name, arguments)
        else:
            return {"error": f"Unsupported method: {method}"}

    @web_app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "Scotland Weather MCP"}
    
    return web_app