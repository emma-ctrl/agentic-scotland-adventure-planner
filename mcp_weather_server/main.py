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
        return {
            "tools": [
                {
                    "name": "get_weather",
                    "description": "Get current weather for any location worldwide using Open-Meteo (no API key required). Automatically prioritizes UK/Scottish locations for ambiguous place names like 'Perth' or 'Cambridge'.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "Location name, coordinates, or landmark. Examples: 'Edinburgh', 'Perth' (defaults to Scotland), 'Perth, Australia' (specific), 'Isle of Canna', '55.9533,-3.1883'"
                            }
                        },
                        "required": ["location"]
                    }
                },
                {
                    "name": "get_forecast",
                    "description": "Get multi-day weather forecast for any location worldwide - perfect for trip planning. Automatically prioritizes UK/Scottish locations for ambiguous place names.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "Location name, coordinates, or landmark. For ambiguous names like 'Glasgow', 'Hamilton', system prefers Scottish locations unless specified otherwise."
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
        """Handle when the AI wants to use one of our tools"""
        if name == "get_weather":
            return self._get_weather(arguments["location"])
        elif name == "get_forecast":
            days = arguments.get("days", 3)  # Default to 3 days
            return self._get_forecast(arguments["location"], days)
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
            print(f"🌐 Response status: {response.status_code}")
            print(f"🌐 Response URL: {response.url}")
            response.raise_for_status()
            data = response.json()
            print(f"📦 Response keys: {list(data.keys())}")
            
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
        
    def _get_forecast(self, location: str, days: int = 3) -> Dict[str, Any]:
        """Get multi-day weather forecast for trip planning"""
        try:
            print(f"🔍 Looking up forecast for {location} ({days} days)...")
            
            coords = self._get_coordinates(location)
            if not coords:
                return {"error": f"Could not find location: {location}"}
            
            lat, lon, display_name = coords
            print(f"📍 Found coordinates: {lat}, {lon} for {display_name}")
            
            print("🌤️  Fetching forecast data...")
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
            print("✅ Forecast data retrieved successfully!")
            
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
            return {"error": f"Failed to fetch forecast data: {str(e)}"}
        except KeyError as e:
            print(f"❌ Data format error: {e}")
            return {"error": f"Unexpected forecast data format: {str(e)}"}
        except Exception as e:
            print(f"❌ General error: {e}")
            return {"error": f"Error processing forecast: {str(e)}"}
    #
    def _get_coordinates(self, location: str) -> tuple:
        """Smart geocoding using Open-Meteo's geocoding API with Scottish place prioritization"""
        try:
            # Handle direct coordinates first
            if self._is_coordinate_input(location):
                return self._parse_coordinates(location)
            
            # Use Open-Meteo's geocoding API
            url = f"{self.geocoding_url}/search"
            params = {
                "name": location,
                "count": 10,  # Get multiple results for scoring
                "language": "en",
                "format": "json"
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("results"):
                return None
                
            results = data["results"]
            
            # Apply intelligent scoring to select best match
            best_result = self._score_and_select_location(location, results)
            
            if not best_result:
                return None
                
            display_name = self._build_display_name(best_result)
            return (best_result["latitude"], best_result["longitude"], display_name)
            
        except Exception as e:
            return None
    
    def _wind_direction_to_compass(self, degrees: float) -> str:
        """Convert wind direction degrees to compass direction"""
        if degrees is None:
            return "Unknown"
        
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = round(degrees / 22.5) % 16
        return directions[index]
    
    #
    def _score_and_select_location(self, query: str, results: list) -> dict:
        """Score locations based on context and relevance - prioritizes Scottish/UK locations for ambiguous names"""
        if not results:
            return None
            
        # Known ambiguous place names with preferred countries (prioritize Scotland/UK)
        PLACE_PREFERENCES = {
            # Scottish places that often conflict with other countries
            "aberdeen": ["united kingdom", "scotland"],
            "alexandria": ["united kingdom", "scotland"],
            "alloa": ["united kingdom", "scotland"],
            "annan": ["united kingdom", "scotland"],
            "arbroath": ["united kingdom", "scotland"],
            "ayr": ["united kingdom", "scotland"],
            "banff": ["united kingdom", "scotland"],
            "bathgate": ["united kingdom", "scotland"],
            "bearsden": ["united kingdom", "scotland"],
            "bellshill": ["united kingdom", "scotland"],
            "berwick": ["united kingdom", "scotland"],
            "brechin": ["united kingdom", "scotland"],
            "buchanan": ["united kingdom", "scotland"],
            "callander": ["united kingdom", "scotland"],
            "campbeltown": ["united kingdom", "scotland"],
            "carlisle": ["united kingdom", "england"],  # Actually in England but close to Scotland
            "carnoustie": ["united kingdom", "scotland"],
            "clydebank": ["united kingdom", "scotland"],
            "coatbridge": ["united kingdom", "scotland"],
            "cumbernauld": ["united kingdom", "scotland"],
            "dalkeith": ["united kingdom", "scotland"],
            "denny": ["united kingdom", "scotland"],
            "dumbarton": ["united kingdom", "scotland"],
            "dumfries": ["united kingdom", "scotland"],
            "dunbar": ["united kingdom", "scotland"],
            "dunblane": ["united kingdom", "scotland"],
            "dundee": ["united kingdom", "scotland"],
            "dunfermline": ["united kingdom", "scotland"],
            "duns": ["united kingdom", "scotland"],
            "east kilbride": ["united kingdom", "scotland"],
            "edinburgh": ["united kingdom", "scotland"],
            "elgin": ["united kingdom", "scotland"],
            "falkirk": ["united kingdom", "scotland"],
            "forfar": ["united kingdom", "scotland"],
            "fort william": ["united kingdom", "scotland"],
            "fraserburgh": ["united kingdom", "scotland"],
            "galashiels": ["united kingdom", "scotland"],
            "glasgow": ["united kingdom", "scotland"],
            "glenrothes": ["united kingdom", "scotland"],
            "gourock": ["united kingdom", "scotland"],
            "grangemouth": ["united kingdom", "scotland"],
            "greenock": ["united kingdom", "scotland"],
            "hamilton": ["united kingdom", "scotland"],
            "hawick": ["united kingdom", "scotland"],
            "helensburgh": ["united kingdom", "scotland"],
            "huntly": ["united kingdom", "scotland"],
            "inveraray": ["united kingdom", "scotland"],
            "inverness": ["united kingdom", "scotland"],
            "irvine": ["united kingdom", "scotland"],
            "johnstone": ["united kingdom", "scotland"],
            "kelso": ["united kingdom", "scotland"],
            "kilmarnock": ["united kingdom", "scotland"],
            "kilwinning": ["united kingdom", "scotland"],
            "kirkcaldy": ["united kingdom", "scotland"],
            "kirkintilloch": ["united kingdom", "scotland"],
            "kirkwall": ["united kingdom", "scotland"],
            "lanark": ["united kingdom", "scotland"],
            "largo": ["united kingdom", "scotland"],
            "lerwick": ["united kingdom", "scotland"],
            "linlithgow": ["united kingdom", "scotland"],
            "livingston": ["united kingdom", "scotland"],
            "lochgelly": ["united kingdom", "scotland"],
            "melrose": ["united kingdom", "scotland"],
            "montrose": ["united kingdom", "scotland"],
            "motherwell": ["united kingdom", "scotland"],
            "nairn": ["united kingdom", "scotland"],
            "newburgh": ["united kingdom", "scotland"],
            "newton stewart": ["united kingdom", "scotland"],
            "oban": ["united kingdom", "scotland"],
            "paisley": ["united kingdom", "scotland"],
            "peebles": ["united kingdom", "scotland"],
            "perth": ["united kingdom", "scotland"],
            "peterhead": ["united kingdom", "scotland"],
            "pitlochry": ["united kingdom", "scotland"],
            "prestwick": ["united kingdom", "scotland"],
            "renfrew": ["united kingdom", "scotland"],
            "rothesay": ["united kingdom", "scotland"],
            "rutherglen": ["united kingdom", "scotland"],
            "selkirk": ["united kingdom", "scotland"],
            "st. andrews": ["united kingdom", "scotland"],
            "st andrews": ["united kingdom", "scotland"],  # Handle both with and without period
            "stirling": ["united kingdom", "scotland"],
            "stonehaven": ["united kingdom", "scotland"],
            "stornoway": ["united kingdom", "scotland"],
            "stranraer": ["united kingdom", "scotland"],
            "strathaven": ["united kingdom", "scotland"],
            "troon": ["united kingdom", "scotland"],
            "wick": ["united kingdom", "scotland"],
            "wishaw": ["united kingdom", "scotland"],
            
            # English places that often conflict
            "cambridge": ["united kingdom", "england"],
            "birmingham": ["united kingdom", "england"], 
            "manchester": ["united kingdom", "england"],
            "oxford": ["united kingdom", "england"],
            "york": ["united kingdom", "england"],
            "bath": ["united kingdom", "england"],
            "winchester": ["united kingdom", "england"],
            "exeter": ["united kingdom", "england"],
            "lancaster": ["united kingdom", "england"],
            "newcastle": ["united kingdom", "england"],
            "richmond": ["united kingdom", "england"],
            "kingston": ["united kingdom", "england"],
            "plymouth": ["united kingdom", "england"],
            "bristol": ["united kingdom", "england"],
            "london": ["united kingdom", "england"],
            "windsor": ["united kingdom", "england"],
            "dover": ["united kingdom", "england"],
            "canterbury": ["united kingdom", "england"],
            "canna": ["united kingdom", "scotland"],
            "easdale": ["united kingdom", "scotland"],
            "iona": ["united kingdom", "scotland"],
            "mull": ["united kingdom", "scotland"],
            "skye": ["united kingdom", "scotland"],
            "harris": ["united kingdom", "scotland"],
            "lewis": ["united kingdom", "scotland"],
            "barra": ["united kingdom", "scotland"],
            "uist": ["united kingdom", "scotland"],
            "orkney": ["united kingdom", "scotland"],
            "shetland": ["united kingdom", "scotland"],
            "arran": ["united kingdom", "scotland"],
            "bute": ["united kingdom", "scotland"],
            "islay": ["united kingdom", "scotland"],
            "jura": ["united kingdom", "scotland"],
            
            # Add more as you discover conflicts
        }
        
        query_lower = query.lower().strip()
        
        def score_result(result):
            score = 0
            country = result.get("country", "").lower()
            admin1 = result.get("admin1", "").lower() 
            name = result.get("name", "").lower()
            
            # Exact name match bonus
            if name == query_lower:
                score += 100
            
            # Check if this is a known ambiguous place
            if query_lower in PLACE_PREFERENCES:
                preferred_countries = PLACE_PREFERENCES[query_lower]
                for i, pref_country in enumerate(preferred_countries):
                    if pref_country in country or pref_country in admin1:
                        # Much higher score for preferred countries
                        score += 2000 - (i * 100)
                        break
            else:
                # For non-ambiguous places, still give slight preference to UK/Ireland
                if country in ["united kingdom", "ireland"]:
                    score += 100
            
            # Population bonus (capped so it doesn't override preferences)
            population = result.get("population", 0)
            if population > 0:
                score += min(population / 50000, 300)
            
            # Admin level bonus
            if result.get("admin1"):
                score += 30
            if result.get("admin2"):
                score += 15
                
            return score
        
        # Score all results and find the best one
        scored_results = [(score_result(r), r) for r in results]
        best_score, best_result = max(scored_results, key=lambda x: x[0])
        
        return best_result

    def _is_coordinate_input(self, location: str) -> bool:
        """Check if input looks like coordinates (lat,lon format)"""
        if ',' not in location:
            return False
        parts = location.split(',')
        if len(parts) != 2:
            return False
        try:
            lat, lon = float(parts[0].strip()), float(parts[1].strip())
            return -90 <= lat <= 90 and -180 <= lon <= 180
        except ValueError:
            return False

    def _parse_coordinates(self, location: str) -> tuple:
        """Parse coordinate input like '55.9533,-3.1883'"""
        parts = [part.strip() for part in location.split(',')]
        lat, lon = float(parts[0]), float(parts[1])
        return (lat, lon, f"Coordinates: {lat:.4f}, {lon:.4f}")

    def _build_display_name(self, result: dict) -> str:
        """Build a descriptive display name from geocoding result"""
        display_name = result["name"]
        if result.get("admin1"):
            display_name += f", {result['admin1']}"
        if result.get("country"):
            display_name += f", {result['country']}"
        return display_name
    
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
        print("\nChoose an option:")
        print("1. Current weather")
        print("2. Weather forecast")
        print("3. Quit")
        
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == "3" or choice.lower() in ['quit', 'exit', 'q']:
            break
        
        location = input("Enter location: ").strip()
        if not location:
            continue
        
        if choice == "1":
            print(f"\n🔍 Getting current weather for {location}...")
            result = mcp.call_tool("get_weather", {"location": location})
        elif choice == "2":
            days = input("Number of days (1-7, default 3): ").strip()
            days = int(days) if days.isdigit() and 1 <= int(days) <= 7 else 3
            print(f"\n🔍 Getting {days}-day forecast for {location}...")
            result = mcp.call_tool("get_forecast", {"location": location, "days": days})
        else:
            print("Invalid choice!")
            continue
        
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