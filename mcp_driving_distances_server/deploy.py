import modal
from typing import Dict, Any
import requests
from datetime import datetime
import json

class ScottishDrivingMCP:
    def __init__(self):
        # Using OpenRouteService (free tier: 2000 requests/day)
        # Alternative: GraphHopper (free tier: 2500 requests/day)
        self.routing_url = "https://api.openrouteservice.org/v2/directions/driving-car"
        self.geocoding_url = "https://api.openrouteservice.org/geocode/search"
        
        # Get free API key from: https://openrouteservice.org/dev/#/signup
        # Store in environment variable for security
        self.api_key = "YOUR_OPENROUTESERVICE_API_KEY"  # Replace with actual key
    
    def list_tools(self) -> Dict[str, Any]:
        return {
            "tools": [
                {
                    "name": "get_driving_distance",
                    "description": "Calculate driving distance and time between Scottish locations - perfect for planning road trips, camping adventures, and multi-stop tours.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "from_location": {
                                "type": "string",
                                "description": "Starting location in Scotland (e.g., 'Edinburgh', 'Fort William', 'Isle of Skye')"
                            },
                            "to_location": {
                                "type": "string",
                                "description": "Destination location in Scotland (e.g., 'Aviemore', 'Oban', 'St Andrews')"
                            },
                            "waypoints": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional stops along the way (max 3 for free tier)"
                            }
                        },
                        "required": ["from_location", "to_location"]
                    }
                },
                {
                    "name": "plan_road_trip",
                    "description": "Plan a multi-stop road trip with optimized route through Scottish destinations.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "locations": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of Scottish locations to visit (max 5 for free tier)"
                            },
                            "start_location": {
                                "type": "string",
                                "description": "Starting point (if different from first location)"
                            }
                        },
                        "required": ["locations"]
                    }
                }
            ]
        }
    
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if name == "get_driving_distance":
                return self._get_driving_distance(arguments)
            elif name == "plan_road_trip":
                return self._plan_road_trip(arguments)
            else:
                return {"error": f"Unknown tool: {name}"}
        except Exception as e:
            return {"error": f"Error in {name}: {str(e)}"}
    
    def _clarify_scottish_location(self, location: str) -> str:
        """Ensure location is clearly identified as Scottish"""
        # Same extensive mapping as your weather app
        scottish_clarifications = {
            "mull": "Isle of Mull, Scotland, UK",
            "skye": "Isle of Skye, Scotland, UK",
            "arran": "Isle of Arran, Scotland, UK",
            "harris": "Isle of Harris, Scotland, UK",
            "lewis": "Isle of Lewis, Scotland, UK",
            "perth": "Perth, Scotland, UK",
            "aberdeen": "Aberdeen, Scotland, UK",
            "dundee": "Dundee, Scotland, UK",
            "stirling": "Stirling, Scotland, UK",
            "inverness": "Inverness, Scotland, UK",
            "fort william": "Fort William, Scotland, UK",
            "aviemore": "Aviemore, Scotland, UK",
            "oban": "Oban, Scotland, UK",
            "pitlochry": "Pitlochry, Scotland, UK",
            "st andrews": "St Andrews, Scotland, UK",
            "tobermory": "Tobermory, Scotland, UK",
            "portree": "Portree, Scotland, UK",
            "mallaig": "Mallaig, Scotland, UK",
            "kyle": "Kyle of Lochalsh, Scotland, UK",
            "tarbert": "Tarbert, Scotland, UK",
            "thurso": "Thurso, Scotland, UK",
            "wick": "Wick, Scotland, UK",
            "ullapool": "Ullapool, Scotland, UK",
            "durness": "Durness, Scotland, UK",
            "john o groats": "John O'Groats, Scotland, UK",
            "kelso": "Kelso, Scotland, UK",
            "jedburgh": "Jedburgh, Scotland, UK",
            "melrose": "Melrose, Scotland, UK",
            "peebles": "Peebles, Scotland, UK",
            "north berwick": "North Berwick, Scotland, UK",
            "dunbar": "Dunbar, Scotland, UK",
            "stonehaven": "Stonehaven, Scotland, UK",
            "montrose": "Montrose, Scotland, UK",
            "arbroath": "Arbroath, Scotland, UK",
            "carnoustie": "Carnoustie, Scotland, UK",
            "dunkeld": "Dunkeld, Scotland, UK",
            "callander": "Callander, Scotland, UK",
            "balloch": "Balloch, Scotland, UK",
            "helensburgh": "Helensburgh, Scotland, UK",
            "rothesay": "Rothesay, Scotland, UK",
            "dunoon": "Dunoon, Scotland, UK",
            "inveraray": "Inveraray, Scotland, UK",
            "lochgilphead": "Lochgilphead, Scotland, UK",
            "campbeltown": "Campbeltown, Scotland, UK",
            "stranraer": "Stranraer, Scotland, UK",
            "dumfries": "Dumfries, Scotland, UK",
            "gretna": "Gretna, Scotland, UK",
            "lockerbie": "Lockerbie, Scotland, UK",
            "elgin": "Elgin, Scotland, UK",
            "forres": "Forres, Scotland, UK",
            "nairn": "Nairn, Scotland, UK",
            "grantown": "Grantown-on-Spey, Scotland, UK",
            "huntly": "Huntly, Scotland, UK",
            "keith": "Keith, Scotland, UK",
            "banff": "Banff, Scotland, UK",
            "fraserburgh": "Fraserburgh, Scotland, UK",
            "peterhead": "Peterhead, Scotland, UK",
            "turriff": "Turriff, Scotland, UK",
            "lairg": "Lairg, Scotland, UK",
            "dornoch": "Dornoch, Scotland, UK",
            "golspie": "Golspie, Scotland, UK",
            "brora": "Brora, Scotland, UK",
            "helmsdale": "Helmsdale, Scotland, UK",
            "bettyhill": "Bettyhill, Scotland, UK",
            "tongue": "Tongue, Scotland, UK"
        }
        
        location_lower = location.lower().strip()
        if location_lower in scottish_clarifications:
            return scottish_clarifications[location_lower]
        elif not any(keyword in location_lower for keyword in ["scotland", "uk", "united kingdom"]):
            return f"{location}, Scotland, UK"
        return location
    
    def _geocode_location(self, location: str) -> tuple:
        """Get coordinates for a location using OpenRouteService"""
        try:
            clarified_location = self._clarify_scottish_location(location)
            
            headers = {
                'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
                'Authorization': self.api_key
            }
            
            params = {
                'text': clarified_location,
                'boundary.country': 'GB',  # Limit to Great Britain
                'boundary.rect.min_lon': -8.5,  # Scotland bounding box
                'boundary.rect.min_lat': 54.5,
                'boundary.rect.max_lon': -0.5,
                'boundary.rect.max_lat': 61.0,
                'size': 1  # Only need the best match
            }
            
            response = requests.get(self.geocoding_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['features']:
                coords = data['features'][0]['geometry']['coordinates']
                return (coords[0], coords[1])  # lon, lat
            
            return None
            
        except Exception as e:
            return None
    
    def _get_driving_distance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate driving distance and time between two locations"""
        from_location = params["from_location"]
        to_location = params["to_location"]
        waypoints = params.get("waypoints", [])
        
        # Get coordinates for all locations
        from_coords = self._geocode_location(from_location)
        to_coords = self._geocode_location(to_location)
        
        if not from_coords:
            return {"error": f"Could not find location: {from_location}"}
        if not to_coords:
            return {"error": f"Could not find location: {to_location}"}
        
        # Build coordinate list
        coordinates = [list(from_coords)]
        
        # Add waypoints if specified
        for waypoint in waypoints[:3]:  # Limit to 3 waypoints for free tier
            waypoint_coords = self._geocode_location(waypoint)
            if waypoint_coords:
                coordinates.append(list(waypoint_coords))
        
        coordinates.append(list(to_coords))
        
        try:
            headers = {
                'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
                'Authorization': self.api_key,
                'Content-Type': 'application/json; charset=utf-8'
            }
            
            body = {
                "coordinates": coordinates,
                "radiuses": [-1] * len(coordinates),  # Use closest road
                "instructions": False,
                "units": "km"
            }
            
            response = requests.post(self.routing_url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()
            
            if 'routes' in data and data['routes']:
                route = data['routes'][0]
                distance_km = round(route['summary']['distance'] / 1000, 1)
                duration_mins = round(route['summary']['duration'] / 60)
                
                # Format duration nicely
                hours = duration_mins // 60
                mins = duration_mins % 60
                
                if hours > 0:
                    duration_str = f"{hours}h {mins}m"
                else:
                    duration_str = f"{mins}m"
                
                # Build route description
                route_desc = f"{from_location} → {to_location}"
                if waypoints:
                    waypoint_str = " → ".join(waypoints)
                    route_desc = f"{from_location} → {waypoint_str} → {to_location}"
                
                result_text = f"""🚗 **Driving Route: {route_desc}**

**Distance:** {distance_km} km
**Estimated Time:** {duration_str}

**Route Tips:**
• Plan for rest stops every 2 hours on longer journeys
• Check for roadworks or closures before you travel
• Single-track roads common in Highlands - allow extra time
• Consider ferry times if traveling to islands

**Fuel & Facilities:**
• Fill up before heading into remote areas
• Services can be limited in the Highlands
• Check opening hours for petrol stations in rural areas"""
                
                return {
                    "content": [{
                        "type": "text",
                        "text": result_text
                    }]
                }
            else:
                return {"error": "No route found between these locations"}
                
        except Exception as e:
            return {"error": f"Failed to calculate route: {str(e)}"}
    
    def _plan_road_trip(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Plan a multi-stop road trip with distance calculations"""
        locations = params["locations"]
        start_location = params.get("start_location")
        
        if len(locations) > 5:
            return {"error": "Maximum 5 locations supported on free tier"}
        
        # Use start_location if provided, otherwise start from first location
        if start_location:
            route_locations = [start_location] + locations
        else:
            route_locations = locations
        
        total_distance = 0
        total_time = 0
        segments = []
        
        # Calculate each segment
        for i in range(len(route_locations) - 1):
            from_loc = route_locations[i]
            to_loc = route_locations[i + 1]
            
            result = self._get_driving_distance({
                "from_location": from_loc,
                "to_location": to_loc
            })
            
            if "error" in result:
                return result
            
            # Parse the result to extract distance and time
            content = result["content"][0]["text"]
            
            # Simple parsing - in production, you'd store structured data
            try:
                lines = content.split('\n')
                for line in lines:
                    if line.startswith('**Distance:**'):
                        dist = float(line.split()[1])
                        total_distance += dist
                    elif line.startswith('**Estimated Time:**'):
                        time_str = line.split('**Estimated Time:**')[1].strip()
                        # Convert to minutes for calculation
                        if 'h' in time_str:
                            hours = int(time_str.split('h')[0])
                            mins = int(time_str.split('h')[1].replace('m', '').strip()) if 'm' in time_str else 0
                            total_time += hours * 60 + mins
                        else:
                            total_time += int(time_str.replace('m', ''))
                
                segments.append(f"• {from_loc} → {to_loc}: {dist}km")
                
            except:
                # Fallback if parsing fails
                segments.append(f"• {from_loc} → {to_loc}")
        
        # Format total time
        total_hours = total_time // 60
        total_mins = total_time % 60
        if total_hours > 0:
            total_time_str = f"{total_hours}h {total_mins}m"
        else:
            total_time_str = f"{total_mins}m"
        
        segments_text = "\n".join(segments)
        
        result_text = f"""🗺️ **Scottish Road Trip Plan**

**Total Route:** {" → ".join(route_locations)}

**Journey Breakdown:**
{segments_text}

**Total Distance:** {total_distance:.1f} km
**Total Driving Time:** {total_time_str}

**Planning Tips:**
• Add 25% extra time for Highland roads and stops
• Book accommodation in advance, especially in summer
• Check ferry schedules for island destinations
• Consider splitting longer journeys over multiple days
• Pack snacks and water for remote areas

**Recommended Daily Limits:**
• Highland roads: 200-250km per day max
• Island hopping: Plan for ferry times
• City to city: 300-400km comfortable"""
        
        return {
            "content": [{
                "type": "text",
                "text": result_text
            }]
        }

app = modal.App("scottish-driving-mcp")

@app.function(
    image=modal.Image.debian_slim().pip_install("requests", "fastapi", "uvicorn"),
    secrets=[modal.Secret.from_name("openrouteservice")]  # Store API key as secret
)
@modal.asgi_app()
def fastapi_app():
    from fastapi import FastAPI
    import os
    
    web_app = FastAPI()

    @web_app.post("/mcp")
    async def mcp_endpoint(request_dict: Dict[str, Any]) -> Dict[str, Any]:
        # Get API key from environment
        api_key = os.getenv("OPENROUTESERVICE_API_KEY")
        
        mcp_server = ScottishDrivingMCP()
        mcp_server.api_key = api_key  # Set the API key
        
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
        return {"status": "healthy", "service": "Scottish Driving Distances MCP"}
    
    return web_app