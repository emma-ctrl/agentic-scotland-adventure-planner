import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re

class ScotlandAdventureAgent:
    """
    An intelligent agent that combines weather data and hiking routes 
    to help plan adventures in Scotland
    """
    
    def __init__(self, weather_url: str, routes_url: str):
        self.weather_url = weather_url.rstrip('/')
        self.routes_url = routes_url.rstrip('/')
        self.conversation_history = []
        
    def chat(self, user_message: str) -> str:
        """Main chat interface for the agent"""
        try:
            # Add user message to history
            self.conversation_history.append({"role": "user", "content": user_message})
            
            # Analyze the user's intent
            intent = self._analyze_intent(user_message)
            
            # Generate response based on intent
            response = self._generate_response(user_message, intent)
            
            # Add assistant response to history
            self.conversation_history.append({"role": "assistant", "content": response})
            
            return response
            
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}. Please try again!"
    
    def _analyze_intent(self, message: str) -> Dict[str, Any]:
        """Analyze what the user wants to do"""
        message_lower = message.lower()
        
        intent = {
            "type": "general",
            "needs_weather": False,
            "needs_routes": False,
            "location": None,
            "time_frame": None,
            "difficulty": None,
            "specific_mountain": None
        }
        
        # Check for weather-related keywords
        weather_keywords = ["weather", "forecast", "rain", "sunny", "cloudy", "wind", "temperature", "conditions"]
        if any(word in message_lower for word in weather_keywords):
            intent["needs_weather"] = True
        
        # Check for route-related keywords
        route_keywords = ["walk", "hike", "route", "trail", "climb", "mountain", "hill", "trek", "path"]
        if any(word in message_lower for word in route_keywords):
            intent["needs_routes"] = True
        
        # Check for planning keywords (need both weather and routes)
        planning_keywords = ["plan", "trip", "adventure", "weekend", "visit", "explore", "recommend"]
        if any(word in message_lower for word in planning_keywords):
            intent["needs_weather"] = True
            intent["needs_routes"] = True
            intent["type"] = "planning"
        
        # Extract location mentions
        intent["location"] = self._extract_location(message)
        
        # Extract time references
        intent["time_frame"] = self._extract_time_frame(message)
        
        # Extract difficulty preferences
        intent["difficulty"] = self._extract_difficulty(message)
        
        # Extract specific mountains
        intent["specific_mountain"] = self._extract_mountain_names(message)
        
        return intent
    
    def _extract_location(self, message: str) -> Optional[str]:
        """Extract location mentions from the message"""
        # Common Scottish locations
        scottish_locations = [
            "highlands", "cairngorms", "trossachs", "borders", "dumfries", "galloway",
            "loch lomond", "ben nevis", "glencoe", "skye", "isle of skye", "mull",
            "edinburgh", "glasgow", "stirling", "fort william", "inverness", "perth",
            "oban", "pitlochry", "aviemore", "ballater", "braemar", "dunkeld"
        ]
        
        message_lower = message.lower()
        for location in scottish_locations:
            if location in message_lower:
                return location.title()
        
        # Look for "near X" or "around X" patterns
        near_patterns = [r"near (\w+)", r"around (\w+)", r"in (\w+)", r"at (\w+)"]
        for pattern in near_patterns:
            match = re.search(pattern, message_lower)
            if match:
                return match.group(1).title()
        
        return None
    
    def _extract_time_frame(self, message: str) -> Optional[str]:
        """Extract time references from the message"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["today", "this afternoon"]):
            return "today"
        elif any(word in message_lower for word in ["tomorrow", "tom"]):
            return "tomorrow"  
        elif any(word in message_lower for word in ["weekend", "saturday", "sunday"]):
            return "weekend"
        elif any(word in message_lower for word in ["next week", "week"]):
            return "next_week"
        elif any(word in message_lower for word in ["this week"]):
            return "this_week"
        
        return None
    
    def _extract_difficulty(self, message: str) -> Optional[int]:
        """Extract difficulty preferences"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["easy", "beginner", "gentle", "family"]):
            return 1
        elif any(word in message_lower for word in ["moderate", "medium", "intermediate"]):
            return 3
        elif any(word in message_lower for word in ["hard", "difficult", "challenging", "tough"]):
            return 4
        elif any(word in message_lower for word in ["extreme", "very difficult", "very hard"]):
            return 5
            
        return None
    
    def _extract_mountain_names(self, message: str) -> Optional[str]:
        """Extract specific mountain names"""
        mountains = [
            "ben nevis", "ben lomond", "ben more", "cairn gorm", "ben lawers",
            "ben vorlich", "ben chonzie", "schiehallion", "ben venue", "ben ledi",
            "ben aan", "ben cruachan", "ben starav", "buachaille etive mor"
        ]
        
        message_lower = message.lower()
        for mountain in mountains:
            if mountain in message_lower:
                return mountain.title()
        
        return None
    
    def _generate_response(self, message: str, intent: Dict[str, Any]) -> str:
        """Generate an appropriate response based on intent"""
        
        if intent["type"] == "planning":
            return self._handle_planning_request(message, intent)
        elif intent["needs_weather"] and intent["needs_routes"]:
            return self._handle_combined_request(message, intent)
        elif intent["needs_weather"]:
            return self._handle_weather_request(message, intent)
        elif intent["needs_routes"]:
            return self._handle_routes_request(message, intent)
        else:
            return self._handle_general_conversation(message)
    
    def _handle_planning_request(self, message: str, intent: Dict[str, Any]) -> str:
        """Handle trip planning requests that need both weather and routes"""
        location = intent["location"] or "Scotland"
        time_frame = intent["time_frame"] or "this weekend"
        
        response = f"🏔️ Let me help you plan an adventure in {location}!\n\n"
        
        # Get weather information
        weather_info = self._get_weather_info(location, time_frame)
        if weather_info:
            response += f"🌤️ **Weather for {location}:**\n{weather_info}\n\n"
        
        # Get route suggestions
        route_info = self._get_route_suggestions(intent)
        if route_info:
            response += f"🥾 **Recommended Routes:**\n{route_info}\n\n"
        
        # Add planning advice
        response += self._get_planning_advice(weather_info, time_frame)
        
        return response
    
    def _handle_combined_request(self, message: str, intent: Dict[str, Any]) -> str:
        """Handle requests that need both weather and route data"""
        location = intent["location"] or "Scotland"
        
        response = ""
        
        # Get weather
        weather_info = self._get_weather_info(location, intent["time_frame"])
        if weather_info:
            response += f"🌤️ {weather_info}\n\n"
        
        # Get routes
        route_info = self._get_route_suggestions(intent)
        if route_info:
            response += f"🥾 {route_info}"
        
        return response or "I couldn't find information for your request. Try being more specific about the location or what you're looking for!"
    
    def _handle_weather_request(self, message: str, intent: Dict[str, Any]) -> str:
        """Handle weather-only requests"""
        location = intent["location"] or "Scotland"
        time_frame = intent["time_frame"]
        
        if time_frame in ["weekend", "next_week", "this_week"]:
            weather_info = self._get_forecast(location)
        else:
            weather_info = self._get_current_weather(location)
        
        return weather_info or f"Sorry, I couldn't get weather information for {location}."
    
    def _handle_routes_request(self, message: str, intent: Dict[str, Any]) -> str:
        """Handle route-only requests"""
        route_info = self._get_route_suggestions(intent)
        return route_info or "I couldn't find routes matching your criteria. Try searching for a specific location or mountain name!"
    
    def _handle_general_conversation(self, message: str) -> str:
        """Handle general conversation"""
        greetings = ["hello", "hi", "hey", "good morning", "good afternoon"]
        if any(greeting in message.lower() for greeting in greetings):
            return ("Hello! I'm your Scotland adventure planning assistant! 🏔️\n\n"
                   "I can help you:\n"
                   "• Find hiking routes and walks\n"
                   "• Check weather conditions\n" 
                   "• Plan outdoor adventures\n\n"
                   "Try asking me something like:\n"
                   "- 'Plan a hike near Stirling this weekend'\n"
                   "- 'What's the weather like in the Cairngorms?'\n"
                   "- 'Find me an easy walk near Loch Lomond'")
        
        return ("I'm here to help with Scottish outdoor adventures! You can ask me about:\n"
               "• Hiking routes and walks\n"
               "• Weather conditions\n"
               "• Trip planning\n\n"
               "What would you like to explore?")
    
    def _get_weather_info(self, location: str, time_frame: Optional[str]) -> Optional[str]:
        """Get weather information from the weather MCP server"""
        try:
            if time_frame in ["weekend", "next_week", "this_week"]:
                # Get forecast
                payload = {
                    "method": "tools/call",
                    "params": {
                        "name": "get_forecast",
                        "arguments": {
                            "location": location,
                            "days": 5 if time_frame == "next_week" else 3
                        }
                    }
                }
            else:
                # Get current weather
                payload = {
                    "method": "tools/call", 
                    "params": {
                        "name": "get_weather",
                        "arguments": {"location": location}
                    }
                }
            
            response = requests.post(f"{self.weather_url}/mcp", json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if "content" in data and data["content"]:
                return data["content"][0]["text"]
            
        except Exception as e:
            print(f"Weather API error: {e}")
        
        return None
    
    def _get_current_weather(self, location: str) -> Optional[str]:
        """Get current weather"""
        return self._get_weather_info(location, None)
    
    def _get_forecast(self, location: str) -> Optional[str]:
        """Get weather forecast"""
        return self._get_weather_info(location, "weekend")
    
    def _get_route_suggestions(self, intent: Dict[str, Any]) -> Optional[str]:
        """Get route suggestions from the routes MCP server"""
        try:
            # Build search arguments
            arguments = {}
            
            if intent["specific_mountain"]:
                arguments["search_term"] = intent["specific_mountain"]
            elif intent["location"]:
                arguments["search_term"] = intent["location"]
            
            if intent["difficulty"]:
                arguments["difficulty"] = intent["difficulty"]
            
            arguments["max_results"] = 5  # Limit results for better display
            
            payload = {
                "method": "tools/call",
                "params": {
                    "name": "search_routes",
                    "arguments": arguments
                }
            }
            
            response = requests.post(f"{self.routes_url}/mcp", json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if "content" in data and data["content"]:
                return data["content"][0]["text"]
            
        except Exception as e:
            print(f"Routes API error: {e}")
        
        return None
    
    def _get_planning_advice(self, weather_info: Optional[str], time_frame: Optional[str]) -> str:
        """Generate planning advice based on weather and timing"""
        advice = "💡 **Planning Tips:**\n"
        
        if weather_info:
            if "rain" in weather_info.lower() or "wet" in weather_info.lower():
                advice += "• Consider waterproof gear and indoor alternatives\n"
            if "wind" in weather_info.lower() and "40" in weather_info:
                advice += "• Very windy conditions - avoid exposed ridges\n"
            if "great for outdoor" in weather_info.lower():
                advice += "• Perfect conditions for hiking!\n"
        
        advice += "• Always carry map, compass, and emergency supplies\n"
        advice += "• Check local conditions before setting out\n"
        advice += "• Let someone know your planned route\n"
        
        if time_frame == "weekend":
            advice += "• Book accommodation early for popular areas\n"
        
        return advice

# Example usage and testing
if __name__ == "__main__":
    # Initialize the agent with your actual MCP server URLs
    weather_url = "https://emma-ctrl--scotland-weather-mcp-fastapi-app.modal.run"
    routes_url = "https://emma-ctrl--scotland-walkhighlands-mcp-fastapi-app.modal.run"
    
    agent = ScotlandAdventureAgent(weather_url, routes_url)
    
    # Test conversations
    test_messages = [
        "Hello!",
        "Plan a hiking trip to the Cairngorms this weekend",
        "What's the weather like in Stirling?",
        "Find me an easy walk near Ben Nevis",
        "I want to climb Ben Lomond tomorrow - what's the forecast?"
    ]
    
    print("🏔️ Scotland Adventure Agent Test\n")
    print("=" * 50)
    
    for message in test_messages:
        print(f"\n👤 User: {message}")
        print(f"🤖 Agent: {agent.chat(message)}")
        print("-" * 50)