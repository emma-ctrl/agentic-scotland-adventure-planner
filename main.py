import json
import requests
from typing import Dict, Any
import modal

# This is our simple MCP server
class SimpleWeatherMCP:
    def __init__(self):
        # We'll use Open-Meteo API - completely free and no API key needed!
        # Great coverage for Scotland and perfect for adventure planning
        self.base_url = "https://api.open-meteo.com/v1"
        # We'll also use their geocoding API to find coordinates
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1"
    
    def list_tools(self) -> Dict[str, Any]:
        """Tell the AI what tools we have available"""
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
                }
            ]
        }
    
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle when the AI wants to use one of our tools"""
        if name == "get_weather":
            return self._get_weather(arguments["location"])
        else:
            return {"error": f"Unknown tool: {name}"}
    
    def _get_weather(self, location: str) -> Dict[str, Any]:
        """Actually fetch the weather data from Open-Meteo"""
        try:
            print(f"🔍 Looking up coordinates for {location}...")
            
            # First, get coordinates for the location
            coords = self._get_coordinates(location)
            if not coords:
                return {"error": f"Could not find location: {location}"}
            
            lat, lon, display_name = coords
            print(f"📍 Found coordinates: {lat}, {lon} for {display_name}")
            
            # Get current weather from Open-Meteo
            print("🌤️  Fetching weather data...")
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
                "timezone": "Europe/London"  # Scotland timezone
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extract current weather
            current = data["current"]
            
            # Weather code descriptions (WMO codes)
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
            
            # Convert wind direction to compass direction
            wind_dir = current["wind_direction_10m"]
            wind_compass = self._wind_direction_to_compass(wind_dir)
            
            # Format the weather information
            summary = f"""Current weather in {display_name}:
- Temperature: {current['temperature_2m']}°C (feels like {current['apparent_temperature']}°C)
- Conditions: {weather_desc}
- Humidity: {current['relative_humidity_2m']}%
- Wind: {current['wind_speed_10m']} km/h from {wind_compass}
- Pressure: {current['pressure_msl']} hPa
- Last updated: {current['time']}"""
            
            print("✅ Weather data retrieved successfully!")
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": summary
                    }
                ]
            }
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            return {"error": f"Failed to fetch weather data: {str(e)}"}
        except KeyError as e:
            print(f"❌ Data format error: {e}")
            return {"error": f"Unexpected weather data format: {str(e)}"}
    
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
            print(f"❌ Geocoding error: {e}")
            return None
    
    def _wind_direction_to_compass(self, degrees: float) -> str:
        """Convert wind direction degrees to compass direction"""
        if degrees is None:
            return "Unknown"
        
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = round(degrees / 22.5) % 16
        return directions[index]

# ==============================================
# LOCAL TESTING FUNCTIONS
# ==============================================

def test_individual_functions():
    """Test each part of the system individually"""
    print("🧪 Testing individual functions...\n")
    
    mcp = SimpleWeatherMCP()
    
    # Test 1: Coordinates lookup
    print("1️⃣ Testing coordinate lookup:")
    coords = mcp._get_coordinates("Edinburgh")
    if coords:
        lat, lon, name = coords
        print(f"   ✅ Edinburgh coordinates: {lat}, {lon} ({name})")
    else:
        print("   ❌ Failed to get coordinates")
    
    # Test 2: Wind direction conversion
    print("\n2️⃣ Testing wind direction conversion:")
    test_directions = [0, 90, 180, 270, 245]
    for deg in test_directions:
        compass = mcp._wind_direction_to_compass(deg)
        print(f"   {deg}° = {compass}")
    
    print("\n" + "="*50)

def test_mcp_protocol():
    """Test the full MCP protocol"""
    print("🔧 Testing MCP protocol...\n")
    
    mcp = SimpleWeatherMCP()
    
    # Test 1: List tools
    print("1️⃣ Testing list_tools():")
    tools = mcp.list_tools()
    print(f"   Available tools: {[tool['name'] for tool in tools['tools']]}")
    
    # Test 2: Call weather tool
    print("\n2️⃣ Testing call_tool():")
    locations = ["Edinburgh", "Glasgow", "Stirling"]
    
    for location in locations:
        print(f"\n   Testing {location}:")
        result = mcp.call_tool("get_weather", {"location": location})
        
        if "error" in result:
            print(f"   ❌ Error: {result['error']}")
        else:
            print(f"   ✅ Success!")
            # Print first few lines of the weather report
            weather_text = result["content"][0]["text"]
            lines = weather_text.split('\n')[:3]
            for line in lines:
                print(f"      {line}")
    
    print("\n" + "="*50)

def test_error_handling():
    """Test error scenarios"""
    print("🚨 Testing error handling...\n")
    
    mcp = SimpleWeatherMCP()
    
    # Test 1: Invalid location
    print("1️⃣ Testing invalid location:")
    result = mcp.call_tool("get_weather", {"location": "Atlantis"})
    if "error" in result:
        print(f"   ✅ Correctly handled error: {result['error']}")
    else:
        print(f"   ❌ Should have failed for invalid location")
    
    # Test 2: Invalid tool
    print("\n2️⃣ Testing invalid tool:")
    result = mcp.call_tool("get_lottery_numbers", {"location": "Edinburgh"})
    if "error" in result:
        print(f"   ✅ Correctly handled error: {result['error']}")
    else:
        print(f"   ❌ Should have failed for invalid tool")
    
    print("\n" + "="*50)

def interactive_test():
    """Interactive testing - let user enter locations"""
    print("🎮 Interactive testing mode")
    print("Enter Scottish locations to test (or 'quit' to exit):\n")
    
    mcp = SimpleWeatherMCP()
    
    while True:
        location = input("Enter location: ").strip()
        
        if location.lower() in ['quit', 'exit', 'q']:
            break
        
        if not location:
            continue
            
        print(f"\n🔍 Getting weather for {location}...")
        result = mcp.call_tool("get_weather", {"location": location})
        
        if "error" in result:
            print(f"❌ Error: {result['error']}\n")
        else:
            print("✅ Weather data:")
            print(result["content"][0]["text"])
            print()

# ==============================================
# MAIN TESTING FUNCTION
# ==============================================

def run_all_tests():
    """Run all tests in sequence"""
    print("🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scotland Weather MCP Server - Local Testing")
    print("="*60)
    
    test_individual_functions()
    test_mcp_protocol()
    test_error_handling()
    
    print("\n🎉 All tests completed!")
    print("\nReady to test interactively? (y/n): ", end="")
    if input().lower().startswith('y'):
        interactive_test()

# ==============================================
# RUN WHEN SCRIPT IS EXECUTED
# ==============================================

if __name__ == "__main__":
    run_all_tests()