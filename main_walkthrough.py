import json
import requests
from typing import Dict, Any

# This is our simple MCP server - it creates our weather specialist
class SimpleWeatherMCP:
    def __init__(self):
        #using open meteo api (no API key needed)
        self.base_url = "https://api.open-meteo.com/v1"
        # geocoding API to find coordinates
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1"
    
    #a menu of all the tools we have available
    #when an AI asks out MCP "what can you do?", our specialist says 
    #I can get weather for locations using my get_weather tool
    def list_tools(self) -> Dict[str, Any]:
        """Tell the AI what tools we have available"""
        return {
            "tools": [
                {
                    "name": "get_weather",
                    "description": "Get current weather for a location in Scotland using Open-Meteo",
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
                }
            ]
        }
    

    #handling tool calls
    #when an AI says "please use your get_weather tool for Glasgow"
    #this method receives that request and calls the right function
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle when the AI wants to use one of our tools"""
        if name == "get_weather":
            return self._get_weather(arguments["location"])
        else:
            return {"error": f"Unknown tool: {name}"}
    
    #main weather function
    #actually fetch the weather data from Open Meteo
    def _get_weather(self, location: str) -> Dict[str, Any]:
        try:
            #Step 1: get coordinates for the location ie. convert "Glasgow" into GPS coordinates
            coords = self._get_coordinates(location)
            if not coords:
                return {"error": f"Could not find location: {location}"}
            
            lat, lon, display_name = coords
            
            #Step2: get weather data using these coordinates
            url = f"{self.base_url}/forecast"
            #building the API request
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
                "timezone": "Europe/London"  # Scotland timezone
            }
            
            #this handles the response json that we will get back from open meteo
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extract current weather data
            current = data["current"]

            #will look something like
            # current["temperature_2m"] = 12.3
            # current["weather_code"] = 61
            # current["wind_direction_10m"] = 245
            # etc.
            
            #python dictionary to store weather codes and their corresponsing human descriptions
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
            
            #converts weather code to human descriptionß=
            weather_desc = weather_descriptions.get(current["weather_code"], "Unknown")
            
            # Convert wind direction to compass direction, ie. 245deg to SW
            wind_dir = current["wind_direction_10m"]
            wind_compass = self._wind_direction_to_compass(wind_dir)
            
            #Step 3: Format the weather information into human readable text (the final response)
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
    
    #helper function
    def _get_coordinates(self, location: str) -> tuple:
        """Get latitude and longitude for a location using Open-Meteo geocoding"""
        try:
            url = f"{self.geocoding_url}/search"
            params = {
                "name": location,
                "count": 1,
                "language": "en",
                "format": "json"
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("results"):
                result = data["results"][0]
                return (
                    result["latitude"], 
                    result["longitude"],
                    result["name"] + (f", {result['admin1']}" if "admin1" in result else "")
                )
            
            return None
            
        except Exception as e:
            print(f"Error getting coordinates: {e}")
            return None
    
    #helper function
    def _wind_direction_to_compass(self, degrees: float) -> str:
        """Convert wind direction degrees to compass direction"""
        if degrees is None:
            return "Unknown"
        
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = round(degrees / 22.5) % 16
        return directions[index]

# Test function - run this locally to make sure it works
def test_locally():
    mcp = SimpleWeatherMCP()
    
    # Test listing tools
    tools = mcp.list_tools()
    print("Available tools:", json.dumps(tools, indent=2))
    
    # Test getting weather for a Scottish location
    result = mcp.call_tool("get_weather", {"location": "Edinburgh"})
    print("\nWeather result:", json.dumps(result, indent=2))
    
    # Test another location
    result2 = mcp.call_tool("get_weather", {"location": "Glasgow"})
    print("\nGlasgow weather:", json.dumps(result2, indent=2))

if __name__ == "__main__":
    test_locally()