import gradio as gr
import requests
from openai import OpenAI
import json
from datetime import datetime
import re

# Your MCP server URLs
WEATHER_MCP_URL = "https://emma-ctrl--scotland-weather-mcp-fastapi-app.modal.run/mcp"
DAYLIGHT_MCP_URL = "https://emma-ctrl--scotland-daylight-mcp-fastapi-app.modal.run/mcp"
DRIVING_MCP_URL = "https://emma-ctrl--scottish-driving-mcp-fastapi-app.modal.run/mcp"

# Initialize Nebius AI Studio client
client = OpenAI(
    api_key="eyJhbGciOiJIUzI1NiIsImtpZCI6IlV6SXJWd1h0dnprLVRvdzlLZWstc0M1akptWXBvX1VaVkxUZlpnMDRlOFUiLCJ0eXAiOiJKV1QifQ.eyJzdWIiOiJnaXRodWJ8NjQxOTk5MzgiLCJzY29wZSI6Im9wZW5pZCBvZmZsaW5lX2FjY2VzcyIsImlzcyI6ImFwaV9rZXlfaXNzdWVyIiwiYXVkIjpbImh0dHBzOi8vbmViaXVzLWluZmVyZW5jZS5ldS5hdXRoMC5jb20vYXBpL3YyLyJdLCJleHAiOjE5MDY2MjYzOTgsInV1aWQiOiJiMzE1YWJiYS05NDUyLTQxYTItOTIxNy0xOGY2NjYxZDg0NTMiLCJuYW1lIjoiRW1tYSIsImV4cGlyZXNfYXQiOiIyMDMwLTA2LTAyVDEwOjI2OjM4KzAwMDAifQ.0ovoenUoRM5CctohO-0A416Z2YdlR3Nqn4W5XLmaCeE",
    base_url="https://api.studio.nebius.ai/v1"
)

def call_mcp_server(server_url, tool_name, arguments):
    """Call any MCP server with Scottish location validation"""
    
    # Define Scottish clarifications dictionary once for all uses
    scottish_clarifications = {
        # Major cities that exist elsewhere
        "aberdeen": "Aberdeen, Scotland, UK",
        "dundee": "Dundee, Scotland, UK", 
        "perth": "Perth, Scotland, UK",
        "hamilton": "Hamilton, Scotland, UK",
        "glasgow": "Glasgow, Scotland, UK",
        "edinburgh": "Edinburgh, Scotland, UK",
        "stirling": "Stirling, Scotland, UK",
        "inverness": "Inverness, Scotland, UK",
        "paisley": "Paisley, Scotland, UK",
        "greenock": "Greenock, Scotland, UK",
        "ayr": "Ayr, Scotland, UK",
        "kilmarnock": "Kilmarnock, Scotland, UK",
        "dumfries": "Dumfries, Scotland, UK",
        "falkirk": "Falkirk, Scotland, UK",
        "livingston": "Livingston, Scotland, UK",
        "kirkcaldy": "Kirkcaldy, Scotland, UK",
        "dunfermline": "Dunfermline, Scotland, UK",
        
        # Islands (very commonly confused)
        "mull": "Isle of Mull, Scotland, UK",
        "isle of mull": "Isle of Mull, Scotland, UK",
        "skye": "Isle of Skye, Scotland, UK", 
        "isle of skye": "Isle of Skye, Scotland, UK",
        "arran": "Isle of Arran, Scotland, UK",
        "isle of arran": "Isle of Arran, Scotland, UK",
        "harris": "Isle of Harris, Scotland, UK",
        "isle of harris": "Isle of Harris, Scotland, UK",
        "lewis": "Isle of Lewis, Scotland, UK",
        "isle of lewis": "Isle of Lewis, Scotland, UK",
        "orkney": "Orkney Islands, Scotland, UK",
        "orkney islands": "Orkney Islands, Scotland, UK",
        "shetland": "Shetland Islands, Scotland, UK",
        "shetland islands": "Shetland Islands, Scotland, UK",
        "islay": "Isle of Islay, Scotland, UK",
        "isle of islay": "Isle of Islay, Scotland, UK",
        "jura": "Isle of Jura, Scotland, UK",
        "isle of jura": "Isle of Jura, Scotland, UK",
        "bute": "Isle of Bute, Scotland, UK",
        "isle of bute": "Isle of Bute, Scotland, UK",
        "iona": "Isle of Iona, Scotland, UK",
        "isle of iona": "Isle of Iona, Scotland, UK",
        "tiree": "Isle of Tiree, Scotland, UK",
        "isle of tiree": "Isle of Tiree, Scotland, UK",
        "coll": "Isle of Coll, Scotland, UK",
        "isle of coll": "Isle of Coll, Scotland, UK",
        "muck": "Isle of Muck, Scotland, UK",
        "eigg": "Isle of Eigg, Scotland, UK",
        "rum": "Isle of Rum, Scotland, UK",
        "rhum": "Isle of Rum, Scotland, UK",
        "canna": "Isle of Canna, Scotland, UK",
        "staffa": "Isle of Staffa, Scotland, UK",
        "ulva": "Isle of Ulva, Scotland, UK",
        
        # Highland towns/villages that could be confused
        "fort william": "Fort William, Scotland, UK",
        "aviemore": "Aviemore, Scotland, UK",
        "oban": "Oban, Scotland, UK",
        "pitlochry": "Pitlochry, Scotland, UK",
        "callander": "Callander, Scotland, UK",
        "balloch": "Balloch, Scotland, UK",
        "helensburgh": "Helensburgh, Scotland, UK",
        "mallaig": "Mallaig, Scotland, UK",
        "kyle": "Kyle of Lochalsh, Scotland, UK",
        "kyle of lochalsh": "Kyle of Lochalsh, Scotland, UK",
        "portree": "Portree, Scotland, UK",
        "tobermory": "Tobermory, Scotland, UK",
        "tarbert": "Tarbert, Scotland, UK",
        "campbeltown": "Campbeltown, Scotland, UK",
        "stranraer": "Stranraer, Scotland, UK",
        "thurso": "Thurso, Scotland, UK",
        "wick": "Wick, Scotland, UK",
        "dornoch": "Dornoch, Scotland, UK",
        "golspie": "Golspie, Scotland, UK",
        "brora": "Brora, Scotland, UK",
        "ullapool": "Ullapool, Scotland, UK",
        "gairloch": "Gairloch, Scotland, UK",
        "kinlochewe": "Kinlochewe, Scotland, UK",
        "torridon": "Torridon, Scotland, UK",
        "applecross": "Applecross, Scotland, UK",
        "plockton": "Plockton, Scotland, UK",
        "lochinver": "Lochinver, Scotland, UK",
        "durness": "Durness, Scotland, UK",
        "tongue": "Tongue, Scotland, UK",
        "bettyhill": "Bettyhill, Scotland, UK",
        "john o groats": "John O'Groats, Scotland, UK",
        "john o'groats": "John O'Groats, Scotland, UK",
        
        # Border towns that exist elsewhere
        "kelso": "Kelso, Scotland, UK",
        "jedburgh": "Jedburgh, Scotland, UK",
        "hawick": "Hawick, Scotland, UK",
        "galashiels": "Galashiels, Scotland, UK",
        "selkirk": "Selkirk, Scotland, UK",
        "melrose": "Melrose, Scotland, UK",
        "peebles": "Peebles, Scotland, UK",
        "biggar": "Biggar, Scotland, UK",
        "moffat": "Moffat, Scotland, UK",
        "sanquhar": "Sanquhar, Scotland, UK",
        "langholm": "Langholm, Scotland, UK",
        "annan": "Annan, Scotland, UK",
        "gretna": "Gretna, Scotland, UK",
        "gretna green": "Gretna Green, Scotland, UK",
        "lockerbie": "Lockerbie, Scotland, UK",
        
        # Eastern Scotland towns
        "st andrews": "St Andrews, Scotland, UK",
        "saint andrews": "St Andrews, Scotland, UK",
        "cupar": "Cupar, Scotland, UK",
        "anstruther": "Anstruther, Scotland, UK",
        "crail": "Crail, Scotland, UK",
        "elie": "Elie, Scotland, UK",
        "pittenweem": "Pittenweem, Scotland, UK",
        "north berwick": "North Berwick, Scotland, UK",
        "dunbar": "Dunbar, Scotland, UK",
        "haddington": "Haddington, Scotland, UK",
        "linlithgow": "Linlithgow, Scotland, UK",
        "bathgate": "Bathgate, Scotland, UK",
        "armadale": "Armadale, Scotland, UK",
        "stonehaven": "Stonehaven, Scotland, UK",
        "montrose": "Montrose, Scotland, UK",
        "arbroath": "Arbroath, Scotland, UK",
        "carnoustie": "Carnoustie, Scotland, UK",
        "forfar": "Forfar, Scotland, UK",
        "brechin": "Brechin, Scotland, UK",
        "kirriemuir": "Kirriemuir, Scotland, UK",
        "blairgowrie": "Blairgowrie, Scotland, UK",
        "crieff": "Crieff, Scotland, UK",
        "aberfeldy": "Aberfeldy, Scotland, UK",
        "dunkeld": "Dunkeld, Scotland, UK",
        "birnam": "Birnam, Scotland, UK",
        
        # Western Scotland and Argyll
        "rothesay": "Rothesay, Scotland, UK",
        "dunoon": "Dunoon, Scotland, UK",
        "inveraray": "Inveraray, Scotland, UK",
        "lochgilphead": "Lochgilphead, Scotland, UK",
        "ardrishaig": "Ardrishaig, Scotland, UK",
        "crinan": "Crinan, Scotland, UK",
        "kilmartin": "Kilmartin, Scotland, UK",
        "dalmally": "Dalmally, Scotland, UK",
        "tyndrum": "Tyndrum, Scotland, UK",
        "crianlarich": "Crianlarich, Scotland, UK",
        "killin": "Killin, Scotland, UK",
        "lochearnhead": "Lochearnhead, Scotland, UK",
        "st fillans": "St Fillans, Scotland, UK",
        "comrie": "Comrie, Scotland, UK",
        "auchterarder": "Auchterarder, Scotland, UK",
        "gleneagles": "Gleneagles, Scotland, UK",
        
        # Central Scotland
        "bridge of allan": "Bridge of Allan, Scotland, UK",
        "alloa": "Alloa, Scotland, UK",
        "clackmannan": "Clackmannan, Scotland, UK",
        "tillicoultry": "Tillicoultry, Scotland, UK",
        "dollar": "Dollar, Scotland, UK",
        "alva": "Alva, Scotland, UK",
        "menstrie": "Menstrie, Scotland, UK",
        "denny": "Denny, Scotland, UK",
        "bonnybridge": "Bonnybridge, Scotland, UK",
        "larbert": "Larbert, Scotland, UK",
        "stenhousemuir": "Stenhousemuir, Scotland, UK",
        "grangemouth": "Grangemouth, Scotland, UK",
        "bo'ness": "Bo'ness, Scotland, UK",
        "blackness": "Blackness, Scotland, UK",
        "queensferry": "South Queensferry, Scotland, UK",
        "south queensferry": "South Queensferry, Scotland, UK",
        
        # Famous landmarks and areas
        "ben nevis": "Ben Nevis, Scotland, UK",
        "ben lomond": "Ben Lomond, Scotland, UK",
        "ben more": "Ben More, Scotland, UK",
        "cairngorms": "Cairngorms, Scotland, UK",
        "glencoe": "Glencoe, Scotland, UK",
        "glen coe": "Glencoe, Scotland, UK",
        "loch lomond": "Loch Lomond, Scotland, UK",
        "loch ness": "Loch Ness, Scotland, UK",
        "loch katrine": "Loch Katrine, Scotland, UK",
        "loch earn": "Loch Earn, Scotland, UK",
        "loch tay": "Loch Tay, Scotland, UK",
        "loch tummel": "Loch Tummel, Scotland, UK",
        "loch rannoch": "Loch Rannoch, Scotland, UK",
        "loch awe": "Loch Awe, Scotland, UK",
        "loch fyne": "Loch Fyne, Scotland, UK",
        "loch long": "Loch Long, Scotland, UK",
        "loch goil": "Loch Goil, Scotland, UK",
        "the trossachs": "The Trossachs, Scotland, UK",
        "trossachs": "The Trossachs, Scotland, UK",
        "queen elizabeth forest park": "Queen Elizabeth Forest Park, Scotland, UK",
        "cairngorms national park": "Cairngorms National Park, Scotland, UK",
        "loch lomond and trossachs national park": "Loch Lomond and Trossachs National Park, Scotland, UK",
        
        # Northern Scotland - abbreviated for space
        "elgin": "Elgin, Scotland, UK",
        "forres": "Forres, Scotland, UK",
        "nairn": "Nairn, Scotland, UK",
        "grantown": "Grantown-on-Spey, Scotland, UK",
        "kingussie": "Kingussie, Scotland, UK",
        "newtonmore": "Newtonmore, Scotland, UK",
        "dalwhinnie": "Dalwhinnie, Scotland, UK",
        "carrbridge": "Carrbridge, Scotland, UK",
        "boat of garten": "Boat of Garten, Scotland, UK",
        "tomintoul": "Tomintoul, Scotland, UK",
        "aberlour": "Aberlour, Scotland, UK",
        "dufftown": "Dufftown, Scotland, UK",
        "keith": "Keith, Scotland, UK",
        "huntly": "Huntly, Scotland, UK",
        "inverurie": "Inverurie, Scotland, UK",
        "banff": "Banff, Scotland, UK",
        "fraserburgh": "Fraserburgh, Scotland, UK",
        "peterhead": "Peterhead, Scotland, UK",
        "lairg": "Lairg, Scotland, UK",
        "dornoch": "Dornoch, Scotland, UK",
        "helmsdale": "Helmsdale, Scotland, UK",
        "bettyhill": "Bettyhill, Scotland, UK",
        "tongue": "Tongue, Scotland, UK",
        
        # Common abbreviations and variations
        "fort bill": "Fort William, Scotland, UK",
        "the fort": "Fort William, Scotland, UK",
        "malky": "Mallaig, Scotland, UK",
        "toby": "Tobermory, Scotland, UK",
    }
    
    # Handle single location field
    if "location" in arguments:
        location = arguments["location"].lower().strip()
        if location in scottish_clarifications:
            arguments["location"] = scottish_clarifications[location]
        elif not any(keyword in location for keyword in ["scotland", "uk", "united kingdom"]):
            arguments["location"] = f"{arguments['location']}, Scotland, UK"
    
    # Handle multiple location fields for driving
    for field in ["from_location", "to_location", "start_location"]:
        if field in arguments:
            location = arguments[field].lower().strip()
            if location in scottish_clarifications:
                arguments[field] = scottish_clarifications[location]
            elif not any(keyword in location for keyword in ["scotland", "uk", "united kingdom"]):
                arguments[field] = f"{arguments[field]}, Scotland, UK"
    
    # Handle locations array for road trips
    if "locations" in arguments and isinstance(arguments["locations"], list):
        clarified_locations = []
        for location in arguments["locations"]:
            location_lower = location.lower().strip()
            if location_lower in scottish_clarifications:
                clarified_locations.append(scottish_clarifications[location_lower])
            elif not any(keyword in location_lower for keyword in ["scotland", "uk", "united kingdom"]):
                clarified_locations.append(f"{location}, Scotland, UK")
            else:
                clarified_locations.append(location)
        arguments["locations"] = clarified_locations
    
    payload = {
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    
    try:
        response = requests.post(server_url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"Failed to get data from {tool_name}: {str(e)}"}

def format_response(response, data_type="data"):
    """Format the response nicely"""
    if "error" in response:
        return f"❌ {response['error']}"
    
    if "content" in response and response["content"]:
        return response["content"][0]["text"]
    
    return f"❌ No {data_type} data received"

# Replace the extract_locations_from_text function with this enhanced version:

def extract_locations_from_text(text):
    """Extract Scottish location names with better journey order detection"""
    scottish_places = [
        "Edinburgh", "Glasgow", "Aberdeen", "Dundee", "Stirling", "Inverness",
        "Fort William", "Aviemore", "Perth", "Paisley", "Greenock", "Dunfermline",
        "Kirkcaldy", "Ayr", "Kilmarnock", "Dumfries", "Oban", "Pitlochry",
        "Callander", "Balloch", "Helensburgh", "Falkirk", "Livingston",
        "Isle of Skye", "Skye", "Isle of Mull", "Mull", "Isle of Arran", "Arran", 
        "Isle of Islay", "Islay", "Isle of Jura", "Jura", "Harris", "Lewis",
        "Orkney", "Shetland", "Orkney Islands", "Shetland Islands",
        "Ben Nevis", "Loch Lomond", "Loch Ness", "Cairngorms", "Glencoe",
        "St Andrews", "Melrose", "Jedburgh", "Galashiels", "Hawick",
        "Mallaig", "Kyle of Lochalsh", "Kyle", "Portree", "Tobermory",
        "Tarbert", "Campbeltown", "Stranraer", "Thurso", "Wick",
        "Ullapool", "Durness", "John O'Groats", "Lochinver", "Tongue",
        "North Berwick", "Dunbar", "Stonehaven", "Montrose", "Arbroath",
        "Dunkeld", "Crieff", "Aberfeldy", "Rothesay", "Dunoon", "Inveraray",
        "Tyndrum", "Crianlarich", "Killin", "The Trossachs", "Trossachs"
    ]
    
    # ENHANCED: Look for journey order keywords
    text_lower = text.lower()
    
    # Check for journey order patterns
    journey_patterns = [
        r'start in (.*?) and then (?:go to |visit )(.*?) and then (.*?)(?:\.|$)',
        r'from (.*?) to (.*?) (?:via |through |and then )(.*?)(?:\.|$)',
        r'(.*?) to (.*?) to (.*?)(?:\.|$)',
        r'(.*?) → (.*?) → (.*?)(?:\.|$)',
        r'(.*?) then (.*?) then (.*?)(?:\.|$)'
    ]
    
    # Try to extract ordered journey
    for pattern in journey_patterns:
        match = re.search(pattern, text_lower)
        if match:
            ordered_locations = []
            for group in match.groups():
                group_clean = group.strip().replace(' and', '').replace(',', '')
                # Find matching Scottish place
                for place in scottish_places:
                    if place.lower() in group_clean:
                        if place not in ordered_locations:
                            ordered_locations.append(place)
                            break
            
            if len(ordered_locations) >= 2:
                print(f"DEBUG: Found journey order: {ordered_locations}")
                return ordered_locations
    
    # Fallback to original method if no journey pattern found
    found_locations = []
    text_upper = text.title()
    
    # Sort by length (descending) to match longer names first
    sorted_places = sorted(scottish_places, key=len, reverse=True)
    
    for place in sorted_places:
        if place in text_upper and place not in found_locations:
            found_locations.append(place)
    
    # Try to reorder based on position in text for common journey words
    if len(found_locations) >= 2:
        journey_indicators = ['start', 'begin', 'first', 'then', 'next', 'finally', 'end']
        
        # Look for starting location
        for indicator in ['start in', 'begin in', 'from']:
            if indicator in text_lower:
                for location in found_locations:
                    location_pos = text_lower.find(location.lower())
                    indicator_pos = text_lower.find(indicator)
                    if location_pos > indicator_pos and location_pos - indicator_pos < 50:
                        # Move this location to the front
                        if location in found_locations:
                            found_locations.remove(location)
                            found_locations.insert(0, location)
                        break
    
    print(f"DEBUG: Extracted locations (fallback): {found_locations}")
    return found_locations

def extract_date_from_text(text):
    """Enhanced date extraction"""
    import re
    from datetime import datetime, timedelta
    
    # Look for YYYY-MM-DD format
    date_match = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', text)
    if date_match:
        return date_match.group(1)
    
    # Handle relative dates
    text_lower = text.lower()
    if 'tomorrow' in text_lower:
        return (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    elif 'yesterday' in text_lower:
        return (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    elif 'next week' in text_lower:
        return (datetime.now() + timedelta(weeks=1)).strftime('%Y-%m-%d')
    elif 'this weekend' in text_lower:
        days_until_saturday = (5 - datetime.now().weekday()) % 7
        return (datetime.now() + timedelta(days=days_until_saturday)).strftime('%Y-%m-%d')
    
    return None  # Default to today

def should_get_daylight_data(message):
    """Determine if the user is specifically asking about daylight/sunrise/sunset times"""
    specific_daylight_keywords = [
        'sunrise', 'sunset', 'golden hour', 'photography', 'dawn', 'dusk', 
        'sun up', 'sun down', 'light for photos', 'early morning light', 
        'evening light', 'when does it get dark', 'when does sun rise',
        'best time for photos', 'photo timing', 'blue hour', 'magic hour'
    ]
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in specific_daylight_keywords)

def should_get_weather_data(message):
    """Determine if the user is asking about weather"""
    weather_keywords = [
        'weather', 'forecast', 'rain', 'sunny', 'temperature', 'wind',
        'cloudy', 'snow', 'storm', 'humid', 'cold', 'warm', 'hot',
        'precipitation', 'degrees', 'celsius', 'fahrenheit', 'conditions',
        'next week', 'this week', 'tomorrow', 'weekend', '7 day', 'weekly',
        'camping', 'hiking', 'outdoor', 'adventure'
    ]
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in weather_keywords)

def should_get_driving_data(message):
    """Determine if user is asking about distances/routes"""
    driving_keywords = [
        'drive', 'driving', 'distance', 'how far', 'route', 'directions',
        'road trip', 'travel time', 'journey', 'miles', 'km', 'kilometers',
        'how long to drive', 'car journey', 'road', 'travel to', 'get to',
        'from', 'to', 'via', 'through', 'stop at', 'visit', 'tour'
    ]
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in driving_keywords)

def decode_polyline(polyline_str):
    """Decode Google polyline string into lat/lon coordinates"""
    try:
        index = 0
        lat = 0
        lng = 0
        coordinates = []
        
        while index < len(polyline_str):
            # Decode latitude
            shift = 0
            result = 0
            while True:
                byte = ord(polyline_str[index]) - 63
                index += 1
                result |= (byte & 0x1f) << shift
                shift += 5
                if byte < 0x20:
                    break
            
            dlat = ~(result >> 1) if result & 1 else result >> 1
            lat += dlat
            
            # Decode longitude
            shift = 0
            result = 0
            while True:
                byte = ord(polyline_str[index]) - 63
                index += 1
                result |= (byte & 0x1f) << shift
                shift += 5
                if byte < 0x20:
                    break
            
            dlng = ~(result >> 1) if result & 1 else result >> 1
            lng += dlng
            
            coordinates.append([lat / 1e5, lng / 1e5])
        
        return coordinates
    except Exception as e:
        print(f"DEBUG: Polyline decode error: {e}")
        return []

def extract_route_geometry_from_mcp(mcp_response, locations):
    """Extract real driving route coordinates from OpenRouteService API"""
    try:
        if len(locations) >= 2:
            start_lat = float(locations[0][1])
            start_lon = float(locations[0][2]) 
            end_lat = float(locations[1][1])
            end_lon = float(locations[1][2])
            
            # Use your actual API key here
            api_key = "5b3ce3597851110001cf62487be29d335d954da6b7329026e1ffd83c"  # ← Your real key
            
            url = "https://api.openrouteservice.org/v2/directions/driving-car"
            headers = {
                'Accept': 'application/json',
                'Authorization': api_key
            }
            
            body = {
                "coordinates": [[start_lon, start_lat], [end_lon, end_lat]],
                "format": "geojson",
                "radiuses": [5000, 5000]
            }
            
            response = requests.post(url, headers=headers, json=body, timeout=10)
            print(f"DEBUG: Got response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if 'routes' in data and len(data['routes']) > 0:
                    route = data['routes'][0]
                    
                    if isinstance(route, dict) and 'geometry' in route:
                        geometry = route['geometry']
                        
                        if isinstance(geometry, str):
                            # It's an encoded polyline - decode it!
                            print(f"DEBUG: Decoding polyline of length: {len(geometry)}")
                            decoded_coords = decode_polyline(geometry)
                            print(f"DEBUG: SUCCESS! Decoded {len(decoded_coords)} route points")
                            return decoded_coords
                        else:
                            print(f"DEBUG: Geometry is not a string: {type(geometry)}")
                    else:
                        print(f"DEBUG: Route structure issue: {route}")
                else:
                    print(f"DEBUG: No routes in response")
                    
    except Exception as e:
        print(f"DEBUG: Exception: {e}")
        import traceback
        traceback.print_exc()
    
    # Fallback to straight line
    return [[locations[0][1], locations[0][2]], [locations[1][1], locations[1][2]]]

def get_scottish_coordinates():
    """Return coordinates for Scottish locations"""
    return {
        "edinburgh": [55.9533, -3.1883],
        "glasgow": [55.8642, -4.2518],
        "aberdeen": [57.1497, -2.0943],
        "dundee": [56.4620, -2.9707],
        "stirling": [56.1165, -3.9369],
        "inverness": [57.4778, -4.2247],
        "fort william": [56.8198, -5.1052],
        "aviemore": [57.1952, -3.8263],
        "perth": [56.3956, -3.4309],
        "oban": [56.4154, -5.4713],
        "pitlochry": [56.7028, -3.7340],
        "isle of skye": [57.2740, -6.2149],
        "skye": [57.2740, -6.2149],
        "isle of mull": [56.4504, -5.8037],
        "mull": [56.4504, -5.8037],
        "isle of arran": [55.5836, -5.2489],
        "arran": [55.5836, -5.2489],
        "mallaig": [57.0067, -5.8283],
        "portree": [57.4123, -6.1956],
        "tobermory": [56.6229, -6.0679],
        "glencoe": [56.6756, -5.1019],
        "glen coe": [56.6756, -5.1019],
        "ben nevis": [56.7969, -5.0037],
        "st andrews": [56.3398, -2.7967],
        "cairngorms": [57.0833, -3.6667],
        "loch lomond": [56.1000, -4.6000],
        "loch ness": [57.3229, -4.4244],
        "kyle of lochalsh": [57.2785, -5.7127],
        "kyle": [57.2785, -5.7127],
        "thurso": [58.5944, -3.5267],
        "wick": [58.4394, -3.0956],
        "ullapool": [57.8952, -5.1587],
        "durness": [58.5667, -4.7167],
        "cairngorms": [57.0833, -3.6667],
        "cairngorms national park": [57.1952, -3.8263]
    }

def create_map_html(locations=[], routes=[], center_lat=56.8, center_lon=-4.2, zoom=6):
    """Generate interactive map using Folium with real driving routes"""
    try:
        import folium
        
        if locations:
            center_lat = locations[0][1]
            center_lon = locations[0][2]
            zoom = 8
        
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom,
            tiles='OpenStreetMap'
        )
        
        # Add markers
        colors = ['red', 'blue', 'green', 'purple', 'orange']
        for i, (name, lat, lon) in enumerate(locations):
            folium.Marker(
                [lat, lon],
                popup=f"<b>{name}</b>",
                tooltip=name,
                icon=folium.Icon(color=colors[i % len(colors)], icon='info-sign')
            ).add_to(m)
        
        # Add actual driving route if available
        if routes and len(routes) > 1:
            folium.PolyLine(
                routes,
                color='red',
                weight=4,
                opacity=0.8,
                popup="🚗 Driving Route"
            ).add_to(m)
            
            # Fit bounds to show entire route
            m.fit_bounds(routes, padding=(20, 20))
        
        return m._repr_html_()
        
    except ImportError:
        return "<div>Install folium for interactive maps</div>"

def extract_locations_and_routes_from_conversation(message, locations_mentioned):
    """Extract locations and potential routes from current message and conversation context"""
    coords_db = get_scottish_coordinates()
    
    # Get coordinates for mentioned locations
    location_coords = []
    for location in locations_mentioned:
        location_key = location.lower().strip()
        if location_key in coords_db:
            lat, lon = coords_db[location_key]
            location_coords.append((location, lat, lon))
        else:
            print(f"DEBUG: Location '{location}' not found in coordinates database")
    
    # Detect route patterns
    routes = []
    message_lower = message.lower()
    
    route_patterns = ["from", "to", "drive", "route", "road trip", "journey", "travel", "start in", "then go", "then"]
    
    if any(pattern in message_lower for pattern in route_patterns) and len(location_coords) >= 2:
        routes.append(location_coords)
    
    return location_coords, routes

# Replace your intelligent_weather_chat function with this stabilized version

def intelligent_weather_chat(message, history):
    """Comprehensive chat with weather + daylight + driving data - STABILIZED VERSION"""
    try:
        # MAKE SURE THESE VARIABLES ARE INITIALIZED AT THE TOP
        locations = extract_locations_from_text(message)
        date = extract_date_from_text(message)
        route_geometry = []
        location_coords = []  # ← ADD THIS LINE

        print(f"DEBUG: Extracted locations: {locations}")
        
        # Determine what data to fetch based on the user's question
        get_weather = should_get_weather_data(message)
        get_daylight = should_get_daylight_data(message)
        get_driving = should_get_driving_data(message)
        
        # Smart defaults based on number of locations
        if locations and not get_weather and not get_daylight and not get_driving:
            if len(locations) >= 2:
                get_weather = True
                get_driving = True
            else:
                get_weather = True
        
        weather_data = {}
        daylight_data = {}
        driving_data = {}
        
        # Fetch weather data for up to 2 locations (reduced from 3)
        if get_weather:
            for location in locations[:2]:
                current_weather = call_mcp_server(WEATHER_MCP_URL, "get_weather", {"location": location})
                if "content" in current_weather:
                    weather_data[location] = format_response(current_weather, "weather")
        
        # Fetch daylight data for up to 2 locations
        if get_daylight:
            for location in locations[:2]:
                daylight_args = {"location": location}
                if date:
                    daylight_args["date"] = date
                
                daylight_times = call_mcp_server(DAYLIGHT_MCP_URL, "get_daylight_times", daylight_args)
                if "content" in daylight_times:
                    daylight_data[location] = format_response(daylight_times, "daylight")
        
        # Fetch driving data for 2+ locations
        if get_driving and len(locations) >= 2:
            try:
                # GET LOCATION COORDINATES FIRST
                location_coords, _ = extract_locations_and_routes_from_conversation(message, locations)
                print(f"DEBUG: location_coords for route: {location_coords}")
                
                if len(locations) == 2:
                    print(f"DEBUG: About to call driving MCP for {locations}")
                    driving_result = call_mcp_server(
                        DRIVING_MCP_URL, 
                        "get_driving_distance", 
                        {
                            "from_location": locations[0],
                            "to_location": locations[1]
                        }
                    )
                    if "content" in driving_result:
                        driving_data[f"{locations[0]} → {locations[1]}"] = format_response(driving_result, "driving")
                        # Extract route geometry
                        route_geometry = extract_route_geometry_from_mcp(driving_result, location_coords)
                        print(f"DEBUG: Final route_geometry: {len(route_geometry)} points")
                    else:
                        print(f"DEBUG: No content in driving result: {driving_result}")
                
                elif len(locations) >= 3:
                    # ENHANCED: Get wiggly routes for 3+ locations by creating segments
                    print(f"DEBUG: Multi-location route with {len(locations)} stops")
                    all_route_points = []
                    driving_segments = []
                    
                    # Create route segments between consecutive locations
                    for i in range(len(locations) - 1):
                        from_loc = locations[i]
                        to_loc = locations[i + 1]
                        
                        print(f"DEBUG: Getting segment {from_loc} → {to_loc}")
                        
                        driving_result = call_mcp_server(
                            DRIVING_MCP_URL, 
                            "get_driving_distance", 
                            {
                                "from_location": from_loc,
                                "to_location": to_loc
                            }
                        )
                        
                        if "content" in driving_result:
                            segment_info = format_response(driving_result, "driving")
                            driving_segments.append(f"**{from_loc} → {to_loc}:** {segment_info}")
                            
                            # Get wiggly route for this segment
                            if i < len(location_coords) - 1:
                                segment_coords = [location_coords[i], location_coords[i + 1]]
                                segment_route = extract_route_geometry_from_mcp(driving_result, segment_coords)
                                
                                if len(segment_route) > 2:  # We got actual route data
                                    print(f"DEBUG: Segment {i+1} has {len(segment_route)} route points")
                                    all_route_points.extend(segment_route)
                                else:
                                    print(f"DEBUG: Segment {i+1} using straight line fallback")
                                    # Add straight line for this segment
                                    all_route_points.extend([
                                        [location_coords[i][1], location_coords[i][2]],
                                        [location_coords[i+1][1], location_coords[i+1][2]]
                                    ])
                    
                    # Combine all segments into one route
                    if all_route_points:
                        route_geometry = all_route_points
                        print(f"DEBUG: Combined route has {len(route_geometry)} total points")
                    
                    # Combine driving info
                    if driving_segments:
                        driving_data["Multi-Stop Route"] = "\n\n".join(driving_segments)
                    else:
                        # Fallback to road trip planner
                        driving_result = call_mcp_server(
                            DRIVING_MCP_URL,
                            "plan_road_trip",
                            {"locations": locations[:4]}
                        )
                        if "content" in driving_result:
                            driving_data["Road Trip Plan"] = format_response(driving_result, "driving")
                            # Use straight lines as last resort
                            if location_coords:
                                route_geometry = [[lat, lon] for _, lat, lon in location_coords]
            except Exception as e:
                print(f"Driving data error: {e}")
                route_geometry = []
        
        # SIMPLIFIED SYSTEM PROMPT - much shorter to prevent token issues
        system_prompt = """You are a helpful Scottish adventure assistant. 

        Be conversational, practical, and enthusiastic about Scottish adventures.

        If you have weather data, focus on that first - interpret conditions for their activity and give gear advice.
        If you have daylight data, mention it for photography or camping timing.  
        If you have driving data, include route advice and Highland driving tips.

        Keep responses natural and under 200 words. Focus on practical advice for their Scottish adventure."""
        
        # Build MUCH SHORTER context
        context_parts = []
        if weather_data:
            context_parts.append("WEATHER:")
            for location, weather in weather_data.items():
                # Truncate weather data to prevent token overflow
                short_weather = weather[:300] + "..." if len(weather) > 300 else weather
                context_parts.append(f"• {location}: {short_weather}")
        
        if daylight_data:
            context_parts.append("\nDAYLIGHT:")
            for location, daylight in daylight_data.items():
                short_daylight = daylight[:200] + "..." if len(daylight) > 200 else daylight
                context_parts.append(f"• {location}: {short_daylight}")
        
        if driving_data:
            context_parts.append("\nDRIVING:")
            for route, info in driving_data.items():
                short_driving = info[:300] + "..." if len(info) > 300 else info
                context_parts.append(f"• {route}: {short_driving}")
        
        if context_parts:
            comprehensive_context = "\n".join(context_parts)
            user_message = f"""User: "{message}"

{comprehensive_context}

Give a helpful, natural response under 200 words focusing on their Scottish adventure needs."""
        else:
            user_message = message
        
        print(f"DEBUG: Context length: {len(user_message)} chars")
        
        # SEVERELY LIMIT conversation history to prevent token overflow
        recent_history = history[-2:] if len(history) > 2 else history
        
        messages = [{"role": "system", "content": system_prompt}]
        
        for user_msg, bot_msg in recent_history:
            # Truncate long messages
            truncated_user = user_msg[:100] + "..." if len(user_msg) > 100 else user_msg
            truncated_bot = bot_msg[:200] + "..." if len(bot_msg) > 200 else bot_msg
            messages.append({"role": "user", "content": truncated_user})
            messages.append({"role": "assistant", "content": truncated_bot})
        
        messages.append({"role": "user", "content": user_message})
        
        # STABILIZED AI PARAMETERS
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3",
            messages=messages,
            max_tokens=300,  # Severely reduced
            temperature=0.1,  # Much more conservative
            top_p=0.9,       # Add top_p for stability
            frequency_penalty=0.3,  # Prevent repetition
            presence_penalty=0.1
        )
        
        bot_response = response.choices[0].message.content
        
        # RESPONSE VALIDATION - catch broken responses
        if (
            "correct answer" in bot_response.lower() or 
            len(bot_response.split()) < 5 or
            len(set(bot_response.split()[-10:])) < 3 or  # Detect repetition
            bot_response.count("16°C") > 5  # Detect specific repetition
        ):
            print("DEBUG: Detected broken AI response, using fallback")
            
            # FALLBACK: Simple data summary
            fallback_parts = []
            if weather_data:
                for location, weather in weather_data.items():
                    # Extract key info manually
                    lines = weather.split('\n')
                    temp_line = next((line for line in lines if '°C' in line), "")
                    fallback_parts.append(f"**{location}:** {temp_line}")
            
            if driving_data:
                for route, info in driving_data.items():
                    lines = info.split('\n')
                    distance_line = next((line for line in lines if 'km' in line or 'Distance' in line), "")
                    time_line = next((line for line in lines if 'Time' in line or 'hour' in line), "")
                    fallback_parts.append(f"**{route}:** {distance_line} {time_line}")
            
            if fallback_parts:
                bot_response = "Here's your Scottish adventure info:\n\n" + "\n".join(fallback_parts)
                bot_response += "\n\nFor detailed planning, try asking about specific aspects like weather or routes separately!"
            else:
                bot_response = "I can help you plan your Scottish adventure! Try asking about specific locations like 'weather in Edinburgh' or 'drive from Glasgow to Skye'."
        
        print(f"DEBUG: Final response length: {len(bot_response)} chars")
        
        # ========== MAP UPDATE LOGIC ==========
        # Extract locations and routes for map
        if not location_coords and locations:
            location_coords, routes = extract_locations_and_routes_from_conversation(message, locations)
        
        # Create updated map HTML
        if location_coords:
            updated_map_html = create_map_html(
                locations=location_coords,
                routes=route_geometry,
                center_lat=location_coords[0][1] if location_coords else 56.8,
                center_lon=location_coords[0][2] if location_coords else -4.2,
                zoom=8 if len(location_coords) <= 2 else 7
            )
        else:
            # Default Scotland overview map
            updated_map_html = create_map_html(
                locations=[],
                routes=[],
                center_lat=56.8,
                center_lon=-4.2,
                zoom=6
            )
        
        print(f"DEBUG: Map updated with {len(location_coords)} locations")
        
    except Exception as e:
        print(f"ERROR: {e}")
        bot_response = "I'm having technical difficulties. Please try a simpler question like 'weather in Edinburgh' or let me know specific Scottish locations you're interested in!"
        # Default map for error case
        updated_map_html = create_map_html()
        location_coords = []  # ← ADD THIS LINE
    
    history.append([message, bot_response])
    return history, "", updated_map_html

# Create the ultimate Scottish adventure planning interface
with gr.Blocks(title="🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scotland Adventure Planner", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scotland Adventure Planner")
    gr.Markdown("**Your complete Scottish adventure assistant!** Get weather, driving distances, recommendations.")
    
    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(height=400, type='tuples')
            msg = gr.Textbox(
                label="Plan your Scottish adventure!",
                placeholder="Try: 'Road trip from Edinburgh to Skye' or 'Photography spots near Fort William'",
                lines=2
            )
        
        with gr.Column(scale=2):
            # Simplified map display
            map_display = gr.HTML(
                value="""
                <div style="width: 100%; height: 400px; border: 2px solid #ddd; background: #f5f5f5; display: flex; align-items: center; justify-content: center;">
                    <div style="text-align: center;">
                        <h3>🗺️ Interactive Map</h3>
                        <p>Map will show locations from your conversation</p>
                    </div>
                </div>
                """,
                label="📍 Interactive Map"
            )
    
    # Compact example buttons
    gr.Markdown("### 🎯 Quick Examples")
    with gr.Row():
        example1 = gr.Button("☀️ Weather Edinburgh", size="sm")
        example2 = gr.Button("🚗 Drive Edinburgh→Skye", size="sm") 
        example3 = gr.Button("📸 Golden hour Glencoe", size="sm")
        example4 = gr.Button("🏕️ Camping Cairngorms", size="sm")

    with gr.Row():
        example5 = gr.Button("🗺️ Road trip Glasgow→Skye", size="sm")
        example6 = gr.Button("🌄 Photography Isle of Mull", size="sm")
        example7 = gr.Button("⛅ Weather + route Perth→Fort William", size="sm")
        example8 = gr.Button("🥾 Hiking weather Ben Nevis", size="sm")
    
    # IMPORTANT: Update the submit function to also update the map
    msg.submit(intelligent_weather_chat, [msg, chatbot], [chatbot, msg, map_display])
    
    # Button actions
    example1.click(lambda: "What's the weather like in Edinburgh?", outputs=msg)
    example2.click(lambda: "How long to drive from Edinburgh to Skye?", outputs=msg)
    example3.click(lambda: "Golden hour photography times in Glencoe?", outputs=msg)
    example4.click(lambda: "Good camping weather in Cairngorms?", outputs=msg)
    example5.click(lambda: "Road trip from Glasgow to Skye with stops", outputs=msg)
    example6.click(lambda: "Best photography spots on Isle of Mull", outputs=msg)
    example7.click(lambda: "Weather and driving route from Perth to Fort William", outputs=msg)
    example8.click(lambda: "Hiking weather around Ben Nevis area", outputs=msg)
    
    gr.Markdown("*Powered by Open-Meteo weather data, Sunrise-Sunset API, OpenRouteService routing, custom MCP servers, and Nebius AI Studio*")

if __name__ == "__main__":
    app.launch(share=True)