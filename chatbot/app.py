import gradio as gr
import requests
from openai import OpenAI
import json
from datetime import datetime
import re

# Your MCP server URLs
WEATHER_MCP_URL = "https://emma-ctrl--scotland-weather-mcp-fastapi-app.modal.run/mcp"
ROUTES_MCP_URL = "https://emma-ctrl--scotland-walkhighlands-mcp-fastapi-app.modal.run/mcp"

# Initialize Nebius AI Studio client
client = OpenAI(
    api_key="api_key",
    base_url="https://api.studio.nebius.ai/v1"
)

def call_mcp_server(server_url, tool_name, arguments):
    """Call an MCP server (weather or routes)"""
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
        return {"error": f"Failed to get data from {server_url}: {str(e)}"}

def format_mcp_response(response, data_type="weather"):
    """Format MCP server responses nicely"""
    if "error" in response:
        return f"❌ {response['error']}"
    
    if "content" in response and response["content"]:
        return response["content"][0]["text"]
    
    return f"❌ No {data_type} data received"

def detect_intent_and_call_tools(message):
    """Detect what the user wants and call appropriate tools directly"""
    message_lower = message.lower()
    tool_results = []
    
    # Extract location from message
    location = extract_location_from_message(message)
    if not location:
        location = "Edinburgh"  # Default to Edinburgh if no location found
    
    # Detect if user wants weather information
    weather_keywords = ["weather", "forecast", "rain", "sunny", "cloudy", "wind", "temperature", "conditions"]
    needs_weather = any(keyword in message_lower for keyword in weather_keywords)
    
    # Detect if user wants route information  
    route_keywords = ["walk", "hike", "route", "trail", "climb", "mountain", "hill", "trek", "path", "easy", "difficult"]
    needs_routes = any(keyword in message_lower for keyword in route_keywords)
    
    # Detect planning requests (need both)
    planning_keywords = ["plan", "trip", "adventure", "weekend", "visit", "explore", "recommend", "good weather"]
    needs_planning = any(keyword in message_lower for keyword in planning_keywords)
    
    if needs_planning:
        needs_weather = True
        needs_routes = True
    
    print(f"DEBUG: Location: {location}, Weather: {needs_weather}, Routes: {needs_routes}")
    
    # Call weather tools if needed
    if needs_weather:
        if any(word in message_lower for word in ["weekend", "week", "tomorrow", "friday", "saturday", "sunday", "forecast"]):
            weather_result = call_mcp_server(WEATHER_MCP_URL, "get_forecast", {"location": location, "days": 3})
        else:
            weather_result = call_mcp_server(WEATHER_MCP_URL, "get_weather", {"location": location})
        
        weather_text = format_mcp_response(weather_result, "weather")
        tool_results.append(f"Weather for {location}: {weather_text}")
    
    # Call route tools if needed
    if needs_routes:
        # Extract difficulty preference
        difficulty = None
        if any(word in message_lower for word in ["easy", "beginner", "gentle", "family"]):
            difficulty = 1
        elif any(word in message_lower for word in ["moderate", "medium"]):
            difficulty = 3
        elif any(word in message_lower for word in ["hard", "difficult", "challenging"]):
            difficulty = 4
        
        # Build search arguments
        search_args = {"search_term": location, "max_results": 5}
        if difficulty:
            search_args["difficulty"] = difficulty
        
        routes_result = call_mcp_server(ROUTES_MCP_URL, "search_routes", search_args)
        routes_text = format_mcp_response(routes_result, "routes")
        tool_results.append(f"Routes near {location}: {routes_text}")
    
    return tool_results, location, needs_weather, needs_routes

def extract_location_from_message(message):
    """Extract location from message"""
    message_lower = message.lower()
    
    # Common Scottish locations
    scottish_locations = [
        "edinburgh", "glasgow", "stirling", "fort william", "inverness", "perth",
        "oban", "pitlochry", "aviemore", "ballater", "braemar", "dunkeld",
        "highlands", "cairngorms", "trossachs", "borders", "dumfries", "galloway",
        "loch lomond", "ben nevis", "glencoe", "skye", "isle of skye", "mull",
        "harris", "lewis", "orkney", "shetland", "arran", "bute", "islay"
    ]
    
    for location in scottish_locations:
        if location in message_lower:
            return location.title()
    
    # Look for "near X" or "in X" patterns
    patterns = [r"near (\w+)", r"in (\w+)", r"around (\w+)", r"at (\w+)"]
    for pattern in patterns:
        match = re.search(pattern, message_lower)
        if match:
            return match.group(1).title()
    
    return None

def extract_context_from_message(message, tool_results=None):
    """Extract key context from user message and tool results"""
    context = {}
    
    # Extract activity type
    activities = ["camping", "hiking", "climbing", "photography", "cycling", "walking", "fishing", 
                 "kayaking", "skiing", "snowboarding", "birdwatching", "running", "surfing", 
                 "sailing", "mountaineering", "backpacking", "trekking", "sightseeing",
                 "canoeing", "rafting", "paragliding", "rock climbing", "ice climbing", "wild swimming",
                 "munro bagging", "corbett", "munro", "scrambling", "hill walking"]
    
    message_lower = message.lower()
    for activity in activities:
        if activity in message_lower:
            context["activity"] = activity
            break
    
    # Extract time references
    time_words = ["tomorrow", "friday", "weekend", "today", "next week", "this week", "saturday", "sunday"]
    for time_word in time_words:
        if time_word in message_lower:
            context["timeframe"] = time_word
            break
    
    return context

def build_context_summary(conv_state):
    """Build a summary of conversation context"""
    if not conv_state:
        return ""
    
    summary_parts = []
    
    if conv_state.get("activity"):
        summary_parts.append(f"User is planning: {conv_state['activity']}")
    
    if conv_state.get("timeframe"):
        summary_parts.append(f"Time: {conv_state['timeframe']}")
    
    if conv_state.get("locations_discussed"):
        locations = list(set(conv_state["locations_discussed"]))
        summary_parts.append(f"Locations discussed: {', '.join(locations)}")
    
    if summary_parts:
        return "\n".join(summary_parts)
    return ""

def update_conversation_state(conv_state, message, tool_results=None, ai_response=None, location=None):
    """Update conversation state with new information"""
    if conv_state is None:
        conv_state = {
            "recent_messages": [],
            "locations_discussed": [],
            "activity": None,
            "timeframe": None
        }
    
    # Add to recent messages
    conv_state["recent_messages"].append({"user": message, "assistant": ai_response})
    if len(conv_state["recent_messages"]) > 6:
        conv_state["recent_messages"] = conv_state["recent_messages"][-6:]
    
    # Extract and update context
    new_context = extract_context_from_message(message, tool_results)
    
    if new_context.get("activity"):
        conv_state["activity"] = new_context["activity"]
    
    if new_context.get("timeframe"):
        conv_state["timeframe"] = new_context["timeframe"]
    
    # Add location to discussed locations
    if location and location not in conv_state["locations_discussed"]:
        conv_state["locations_discussed"].append(location)
    
    # Keep only recent locations
    if len(conv_state["locations_discussed"]) > 5:
        conv_state["locations_discussed"] = conv_state["locations_discussed"][-5:]
    
    return conv_state

def adventure_chat(message, history, conversation_state):
    """Enhanced chat with reliable tool calling"""
    try:
        # Step 1: Detect intent and call tools directly
        tool_results, location, needs_weather, needs_routes = detect_intent_and_call_tools(message)
        
        # Step 2: Build context for LLM response
        context_summary = build_context_summary(conversation_state)
        
        # Step 3: Create a focused prompt for interpreting the results
        if tool_results:
            system_prompt = f"""You are Scotland's most helpful Adventure Planning assistant! 

CONTEXT: {context_summary}

The user asked: "{message}"

I've already gathered this data for you:
{chr(10).join(tool_results)}

Your job: Give a friendly, enthusiastic response that:
1. Directly answers their question using the data above
2. Gives practical advice for their Scottish adventure
3. Considers safety and weather conditions
4. Builds on our conversation context
5. Is conversational and helpful

DO NOT mention tool calling or searching - just give great adventure advice!"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Based on the data you have, help me with: {message}"}
            ]
        else:
            # No tools needed, just conversation
            system_prompt = f"""You are Scotland's most helpful Adventure Planning assistant!

CONTEXT: {context_summary}

Give a friendly, helpful response about Scottish outdoor adventures. If they're asking about specific weather or hiking routes, let them know you can help with that too."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
        
        # Step 4: Get LLM response (no tool calling needed)
        response = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-70B-Instruct",
            messages=messages,
            temperature=0.7,
            max_tokens=600
        )
        
        bot_response = response.choices[0].message.content
        
        # Step 5: Update conversation state
        conversation_state = update_conversation_state(
            conversation_state, message, tool_results, bot_response, location
        )
        
    except Exception as e:
        bot_response = f"I'm having some trouble right now. Error: {str(e)}"
        conversation_state = update_conversation_state(conversation_state, message, None, bot_response)
    
    history.append([message, bot_response])
    return history, "", conversation_state

# Create Gradio interface
with gr.Blocks(title="🏔️ Scotland Adventure Planner", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🏔️ Scotland Adventure Planning Assistant")
    gr.Markdown("Your intelligent companion for planning amazing Scottish adventures! I automatically check weather and find hiking routes based on what you ask.")
    
    conversation_state = gr.State(None)
    
    chatbot = gr.Chatbot(height=600)
    msg = gr.Textbox(
        label="Plan your Scottish adventure!",
        placeholder="Try: 'Find me easy walks near Edinburgh with good weather', 'Plan a trip to Ben Nevis', 'What's the weather like in Skye?'",
        lines=2
    )
    
    # Example buttons
    gr.Markdown("### 🎯 Try These Examples:")
    
    with gr.Row():
        example1 = gr.Button("🥾 Easy walks near Edinburgh with good weather", size="sm")
        example2 = gr.Button("🏔️ Plan a weekend trip to Cairngorms", size="sm")
    
    with gr.Row():
        example3 = gr.Button("☀️ Weather forecast for Skye", size="sm")
        example4 = gr.Button("⛰️ Challenging hikes near Fort William", size="sm")
    
    msg.submit(adventure_chat, [msg, chatbot, conversation_state], [chatbot, msg, conversation_state])
    
    # Example button actions
    example1.click(lambda: "Find me easy walks near Edinburgh with good weather", outputs=msg)
    example2.click(lambda: "Plan a weekend hiking trip to the Cairngorms", outputs=msg)
    example3.click(lambda: "What's the weather forecast for Skye?", outputs=msg)
    example4.click(lambda: "Show me challenging hikes near Fort William", outputs=msg)
    
    gr.Markdown("---")
    gr.Markdown("*Powered by Walk Highlands route data, Open-Meteo weather data, and intelligent MCP servers*")

if __name__ == "__main__":
    app.launch(share=True)