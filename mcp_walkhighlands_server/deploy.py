import modal
from typing import Dict, Any, List, Optional
import json
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import time

class WalkHighlandsMCP:
    def __init__(self):
        self.base_url = "https://www.walkhighlands.co.uk"
        self.search_url = f"{self.base_url}/walk-search.php"
        self.session = requests.Session()
        # Add headers to appear more like a regular browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def list_tools(self) -> Dict[str, Any]:
        return {
            "tools": [
                {
                    "name": "search_routes",
                    "description": "Search for hiking routes on Walk Highlands. Great for finding walks by region, difficulty, or specific criteria.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "search_term": {
                                "type": "string",
                                "description": "Search term for route names, locations, or features (e.g., 'Ben Nevis', 'Cairngorms', 'coastal walks')"
                            },
                            "region": {
                                "type": "string",
                                "description": "Scottish region to search in (e.g., 'Highlands', 'Southern Uplands', 'Borders', 'Trossachs')"
                            },
                            "difficulty": {
                                "type": "integer",
                                "description": "Route difficulty level (1-5 scale, where 1=easy, 5=very difficult)",
                                "minimum": 1,
                                "maximum": 5
                            },
                            "hill_type": {
                                "type": "string",
                                "description": "Type of hills/peaks to include",
                                "enum": ["munro", "corbett", "graham", "donald", "marilyn", "any"]
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results to return (default: 10)",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 50
                            }
                        }
                    }
                },
                {
                    "name": "get_route_details",
                    "description": "Get detailed information about a specific walking route including full description, GPS data, and practical information.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "route_url": {
                                "type": "string",
                                "description": "URL of the Walk Highlands route page"
                            }
                        },
                        "required": ["route_url"]
                    }
                },
                {
                    "name": "get_routes_by_location",
                    "description": "Find walking routes near a specific Scottish location or landmark.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "Location name in Scotland (e.g., 'Stirling', 'Loch Lomond', 'Isle of Skye')"
                            },
                            "max_distance": {
                                "type": "number",
                                "description": "Maximum walking distance in km (optional filter)"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results to return (default: 10)",
                                "default": 10
                            }
                        },
                        "required": ["location"]
                    }
                },
                {
                    "name": "get_munros_and_corbetts",
                    "description": "Get information about specific Munros, Corbetts, or other Scottish peaks with available walking routes.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "peak_name": {
                                "type": "string",
                                "description": "Name of the peak (e.g., 'Ben Nevis', 'Cairn Gorm', 'Ben Lomond')"
                            },
                            "peak_type": {
                                "type": "string",
                                "description": "Type of peak to search for",
                                "enum": ["munro", "corbett", "graham", "donald", "any"],
                                "default": "any"
                            }
                        },
                        "required": ["peak_name"]
                    }
                }
            ]
        }
    
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if name == "search_routes":
                return self._search_routes(arguments)
            elif name == "get_route_details":
                return self._get_route_details(arguments["route_url"])
            elif name == "get_routes_by_location":
                return self._get_routes_by_location(arguments)
            elif name == "get_munros_and_corbetts":
                return self._get_munros_and_corbetts(arguments)
            else:
                return {"error": f"Unknown tool: {name}"}
        except Exception as e:
            return {"error": f"Error in {name}: {str(e)}"}
    
    def _search_routes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for routes on Walk Highlands"""
        try:
            # First, let's get the search page to understand its structure
            response = self._safe_request(self.search_url)
            if not response:
                return {"error": "Could not access Walk Highlands search page"}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # For now, let's try a basic search approach
            # We'll improve this as we learn more about the site structure
            search_term = params.get("search_term", "")
            max_results = params.get("max_results", 10)
            
            # Try searching for routes using the site's search functionality
            routes = self._perform_basic_search(search_term, max_results)
            
            if not routes:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"No routes found for search term: '{search_term}'. Try searching for specific mountain names, regions like 'Highlands' or 'Cairngorms', or general terms like 'coastal walks'."
                    }]
                }
            
            # Format results
            result_text = f"Found {len(routes)} walking routes:\n\n"
            
            for i, route in enumerate(routes, 1):
                result_text += f"{i}. **{route['name']}**\n"
                if route.get('region'):
                    result_text += f"   📍 Region: {route['region']}\n"
                if route.get('difficulty'):
                    result_text += f"   ⭐ Difficulty: {route['difficulty']}/5\n"
                if route.get('distance'):
                    result_text += f"   📏 Distance: {route['distance']}\n"
                if route.get('time'):
                    result_text += f"   ⏱️ Time: {route['time']}\n"
                if route.get('peaks'):
                    result_text += f"   🏔️ Peaks: {route['peaks']}\n"
                if route.get('short_description'):
                    result_text += f"   📝 {route['short_description']}\n"
                result_text += f"   🔗 URL: {route['url']}\n\n"
            
            return {
                "content": [{
                    "type": "text",
                    "text": result_text
                }]
            }
            
        except Exception as e:
            return {"error": f"Error searching routes: {str(e)}"}
    
    def _perform_basic_search(self, search_term: str, max_results: int) -> List[Dict[str, Any]]:
        """Perform a basic search - this is a starting implementation"""
        routes = []
        
        # For now, let's return some example routes to test the structure
        # In a real implementation, you would scrape the actual search results
        
        if search_term.lower() in ["ben nevis", "nevis"]:
            routes.append({
                "name": "Ben Nevis via Tourist Path",
                "region": "Lochaber",
                "difficulty": 4,
                "distance": "17km",
                "time": "7-9 hours",
                "peaks": "Ben Nevis (1345m)",
                "short_description": "The classic route up Scotland's highest mountain",
                "url": f"{self.base_url}/route/example-ben-nevis"
            })
        
        if search_term.lower() in ["cairngorms", "cairn gorm"]:
            routes.append({
                "name": "Cairn Gorm from Ski Centre",
                "region": "Cairngorms",
                "difficulty": 3,
                "distance": "12km",
                "time": "5-6 hours",
                "peaks": "Cairn Gorm (1245m)",
                "short_description": "Popular Munro with excellent views",
                "url": f"{self.base_url}/route/example-cairn-gorm"
            })
        
        # This is where you would implement actual scraping
        # For now, we return example data to test the system
        
        return routes[:max_results]
    
    def _get_route_details(self, route_url: str) -> Dict[str, Any]:
        """Get detailed information about a specific route"""
        try:
            if not route_url.startswith('http'):
                route_url = urljoin(self.base_url, route_url)
            
            response = self._safe_request(route_url)
            if not response:
                return {"error": f"Could not access route page: {route_url}"}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract route details - this would need to be implemented based on
            # the actual HTML structure of Walk Highlands route pages
            route_details = self._parse_route_page(soup, route_url)
            
            if not route_details:
                return {"error": "Could not parse route information from the page"}
            
            # Format the detailed route information
            result_text = f"**{route_details['name']}**\n\n"
            
            if route_details.get('summary'):
                result_text += f"**Summary:** {route_details['summary']}\n\n"
            
            if route_details.get('details'):
                result_text += "**Route Details:**\n"
                for key, value in route_details['details'].items():
                    result_text += f"• {key}: {value}\n"
                result_text += "\n"
            
            if route_details.get('description'):
                result_text += f"**Description:**\n{route_details['description']}\n\n"
            
            if route_details.get('gpx_url'):
                result_text += f"**GPS Download:** {route_details['gpx_url']}\n\n"
            
            result_text += f"**Full Route:** {route_url}"
            
            return {
                "content": [{
                    "type": "text",
                    "text": result_text
                }]
            }
            
        except Exception as e:
            return {"error": f"Error getting route details: {str(e)}"}
    
    def _parse_route_page(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, Any]]:
        """Parse a route detail page - placeholder implementation"""
        # This would need to be implemented based on actual HTML structure
        # For now, return a basic structure
        
        title = soup.find('title')
        route_name = title.get_text() if title else "Unknown Route"
        
        return {
            "name": route_name,
            "summary": "Route details would be extracted from the actual page",
            "details": {
                "Distance": "TBD",
                "Time": "TBD", 
                "Difficulty": "TBD",
                "Start Point": "TBD"
            },
            "description": "Full route description would be extracted here",
            "gpx_url": None
        }
    
    def _get_routes_by_location(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find routes near a specific location"""
        location = params["location"]
        max_results = params.get("max_results", 10)
        
        # This would implement location-based search
        # For now, return a placeholder response
        
        result_text = f"Routes near {location}:\n\n"
        result_text += "🚧 Location-based search coming soon!\n"
        result_text += "For now, try searching by region name using the 'search_routes' tool."
        
        return {
            "content": [{
                "type": "text", 
                "text": result_text
            }]
        }
    
    def _get_munros_and_corbetts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about specific peaks"""
        peak_name = params["peak_name"]
        peak_type = params.get("peak_type", "any")
        
        # This would implement peak-specific search
        result_text = f"Information about {peak_name}:\n\n"
        result_text += "🚧 Peak-specific search coming soon!\n"
        result_text += "For now, try searching by peak name using the 'search_routes' tool."
        
        return {
            "content": [{
                "type": "text",
                "text": result_text
            }]
        }
    
    def _safe_request(self, url: str, delay: float = 1.0) -> Optional[requests.Response]:
        """Make a safe HTTP request with rate limiting"""
        try:
            time.sleep(delay)  # Be respectful to the website
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {url}: {e}")
            return None

app = modal.App("scotland-walkhighlands-mcp")

@app.function(
    image=modal.Image.debian_slim().pip_install("requests", "beautifulsoup4", "fastapi", "uvicorn", "lxml")
)
@modal.asgi_app()
def fastapi_app():
    from fastapi import FastAPI
    
    web_app = FastAPI()

    @web_app.post("/mcp")
    async def mcp_endpoint(request_dict: Dict[str, Any]) -> Dict[str, Any]:
        mcp_server = WalkHighlandsMCP()
        
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
        return {"status": "healthy", "service": "Scotland Walk Highlands MCP"}
    
    return web_app