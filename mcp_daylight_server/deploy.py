import modal
from typing import Dict, Any
import requests
from datetime import datetime, timedelta
import json

class SimpleDaylightMCP:
    def __init__(self):
        self.api_url = "https://api.sunrise-sunset.org/json"
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1"
    
    def list_tools(self) -> Dict[str, Any]:
        return {
            "tools": [
                {
                    "name": "get_daylight_times",
                    "description": "Get sunrise, sunset, and daylight duration for Scottish locations - perfect for planning outdoor activities, photography, and camping.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "Scottish location name (e.g., 'Edinburgh', 'Ben Nevis', 'Cairngorms', 'Skye')"
                            },
                            "date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format (optional, defaults to today)"
                            }
                        },
                        "required": ["location"]
                    }
                }
            ]
        }
    
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if name == "get_daylight_times":
                return self._get_daylight_times(arguments)
            else:
                return {"error": f"Unknown tool: {name}"}
        except Exception as e:
            return {"error": f"Error in {name}: {str(e)}"}
    
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
            
            # Apply intelligent scoring to select best match (prioritize Scottish locations)
            best_result = self._score_and_select_location(location, results)
            
            if not best_result:
                return None
                
            return (best_result["latitude"], best_result["longitude"])
            
        except Exception as e:
            return None
    
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
        return (lat, lon)
    
    def _score_and_select_location(self, query: str, results: list) -> dict:
        """Score locations based on context and relevance - prioritizes Scottish/UK locations"""
        if not results:
            return None
            
        # Known Scottish places (prioritize these)
        SCOTTISH_PLACES = {
            "edinburgh": ["united kingdom", "scotland"],
            "glasgow": ["united kingdom", "scotland"],
            "aberdeen": ["united kingdom", "scotland"],
            "dundee": ["united kingdom", "scotland"],
            "stirling": ["united kingdom", "scotland"],
            "inverness": ["united kingdom", "scotland"],
            "fort william": ["united kingdom", "scotland"],
            "aviemore": ["united kingdom", "scotland"],
            "perth": ["united kingdom", "scotland"],
            "oban": ["united kingdom", "scotland"],
            "pitlochry": ["united kingdom", "scotland"],
            "skye": ["united kingdom", "scotland"],
            "isle of skye": ["united kingdom", "scotland"],
            "cairngorms": ["united kingdom", "scotland"],
            "ben nevis": ["united kingdom", "scotland"],
            "glencoe": ["united kingdom", "scotland"],
            "loch lomond": ["united kingdom", "scotland"],
            "st andrews": ["united kingdom", "scotland"],
            "arran": ["united kingdom", "scotland"],
            "mull": ["united kingdom", "scotland"],
            "harris": ["united kingdom", "scotland"],
            "lewis": ["united kingdom", "scotland"],
            "orkney": ["united kingdom", "scotland"],
            "shetland": ["united kingdom", "scotland"]
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
            
            # Check if this is a known Scottish place
            if query_lower in SCOTTISH_PLACES:
                preferred_countries = SCOTTISH_PLACES[query_lower]
                for i, pref_country in enumerate(preferred_countries):
                    if pref_country in country or pref_country in admin1:
                        # Much higher score for Scottish locations
                        score += 2000 - (i * 100)
                        break
            else:
                # For unknown places, still give preference to UK/Scotland
                if "scotland" in admin1 or "scotland" in country:
                    score += 1000
                elif country in ["united kingdom", "ireland"]:
                    score += 500
            
            # Population bonus (capped so it doesn't override Scottish preference)
            population = result.get("population", 0)
            if population > 0:
                score += min(population / 50000, 200)
            
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
    
    def _get_daylight_times(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get sunrise, sunset, and daylight duration"""
        location = params["location"]
        date = params.get("date", "")
        
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        coords = self._get_coordinates(location)
        if not coords:
            return {"error": f"Could not find location: {location}"}
        
        lat, lng = coords
        
        try:
            response = requests.get(
                self.api_url,
                params={
                    "lat": lat,
                    "lng": lng,
                    "date": date,
                    "formatted": 0  # Get ISO format
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if data["status"] != "OK":
                return {"error": f"Could not get daylight times for {location}"}
            
            results = data["results"]
            
            # Convert to local UK time (add 1 hour for BST)
            sunrise = datetime.fromisoformat(results["sunrise"].replace("Z", "+00:00"))
            sunset = datetime.fromisoformat(results["sunset"].replace("Z", "+00:00"))
            
            # Convert to UK time (approximate - BST in summer)
            sunrise_local = sunrise + timedelta(hours=1)
            sunset_local = sunset + timedelta(hours=1)
            
            daylight_duration = sunset_local - sunrise_local
            hours = int(daylight_duration.total_seconds() // 3600)
            minutes = int((daylight_duration.total_seconds() % 3600) // 60)
            
            # Golden hour times (approximately)
            golden_hour_morning = sunrise_local + timedelta(minutes=30)
            golden_hour_evening = sunset_local - timedelta(minutes=60)
            
            result_text = f"""🌅 **Daylight Times for {location.title()}** ({date}):

**Sunrise:** {sunrise_local.strftime('%H:%M')}
**Sunset:** {sunset_local.strftime('%H:%M')}
**Daylight Duration:** {hours}h {minutes}m

**For Photography:**
• Golden hour morning: Around {golden_hour_morning.strftime('%H:%M')}
• Golden hour evening: {golden_hour_evening.strftime('%H:%M')} - {sunset_local.strftime('%H:%M')}

**For Outdoor Activities:**
• Best light for hiking: After {sunrise_local.strftime('%H:%M')}
• Plan to finish by: {(sunset_local - timedelta(minutes=30)).strftime('%H:%M')}
• Set up camp before: {sunset_local.strftime('%H:%M')}"""
            
            return {
                "content": [{
                    "type": "text",
                    "text": result_text
                }]
            }
            
        except Exception as e:
            return {"error": f"Failed to get daylight times: {str(e)}"}

app = modal.App("scotland-daylight-mcp")

@app.function(
    image=modal.Image.debian_slim().pip_install("requests", "fastapi", "uvicorn")
)
@modal.asgi_app()
def fastapi_app():
    from fastapi import FastAPI
    
    web_app = FastAPI()

    @web_app.post("/mcp")
    async def mcp_endpoint(request_dict: Dict[str, Any]) -> Dict[str, Any]:
        mcp_server = SimpleDaylightMCP()
        
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
        return {"status": "healthy", "service": "Scotland Daylight Times MCP"}
    
    return web_app