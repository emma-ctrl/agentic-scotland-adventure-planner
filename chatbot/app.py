import gradio as gr
import requests
from openai import OpenAI
import os

# Your MCP server URL
MCP_URL = "https://emma-ctrl--scotland-weather-mcp-fastapi-app.modal.run/mcp"

# Initialize Nebius AI Studio client
client = OpenAI(
    api_key="api key",
    base_url="https://api.studio.nebius.ai/v1"
)

def call_mcp_server(tool_name, arguments):
    """Call your MCP server"""
    payload = {
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    
    try:
        response = requests.post(MCP_URL, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"Failed to get weather data: {str(e)}"}

def format_weather_response(response):
    """Format the weather response nicely"""
    if "error" in response:
        return f"❌ Error: {response['error']}"
    
    if "content" in response and response["content"]:
        return response["content"][0]["text"]
    
    return "❌ No weather data received"

def extract_locations_from_text(text):
    """Extract Scottish location names from text using pattern matching"""
    scottish_places = [
        "Edinburgh", "Glasgow", "Aberdeen", "Dundee", "Stirling", "Inverness",
        "Fort William", "Aviemore", "Perth", "Paisley", "Greenock", "Dunfermline",
        "Kirkcaldy", "Ayr", "Kilmarnock", "Dumfries", "Oban", "Pitlochry",
        "Callander", "Balloch", "Helensburgh", "Falkirk", "Livingston",
        "Isle of Skye", "Skye", "Arran", "Mull", "Islay", "Orkney", "Shetland",
        "Ben Nevis", "Loch Lomond", "Loch Ness", "Cairngorms", "Glencoe",
        "St Andrews", "Melrose", "Jedburgh", "Galashiels", "Hawick"
    ]
    
    found_locations = []
    text_upper = text.title()
    
    for place in scottish_places:
        if place in text_upper:
            found_locations.append(place)
    
    return found_locations

def intelligent_weather_chat(message, history):
    """Enhanced chat with Nebius AI Studio + weather data"""
    try:
        locations = extract_locations_from_text(message)
        
        weather_data = {}
        for location in locations[:2]:
            current_weather = call_mcp_server("get_weather", {"location": location})
            if "content" in current_weather:
                weather_data[location] = format_weather_response(current_weather)
        
        system_prompt = """You are a helpful Scottish Adventure Weather assistant. You help people plan outdoor activities in Scotland based on weather conditions.

Your personality:
- Friendly and enthusiastic about Scottish adventures
- Knowledgeable about outdoor activities (hiking, climbing, photography, cycling, etc.)
- Practical and safety-conscious
- Use Scottish terms occasionally (like "wee bit" or "bonnie")

When providing weather information:
- Give practical advice for outdoor activities
- Mention safety considerations for bad weather
- Suggest alternative activities if weather is poor
- Be encouraging but realistic

If you have current weather data, use it. If not, ask the user to specify a location."""
        
        if weather_data:
            weather_context = "\n\nCurrent weather data:\n"
            for location, weather in weather_data.items():
                weather_context += f"\n{location}:\n{weather}\n"
            user_message = f"{message}\n\n[Weather data context: {weather_context}]"
        else:
            user_message = message
        
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        bot_response = response.choices[0].message.content
        
        if not weather_data and any(word in message.lower() for word in ["weather", "forecast", "rain", "sunny", "temperature"]):
            bot_response += "\n\n💡 Tip: Mention a specific Scottish location and I can get you real-time weather data!"
        
    except Exception as e:
        bot_response = f"Sorry, I'm having trouble connecting to my AI assistant. Error: {str(e)}\n\nBut I can still help with weather! Try asking about a specific Scottish location."
        
        locations = extract_locations_from_text(message)
        if locations:
            location = locations[0]
            result = call_mcp_server("get_weather", {"location": location})
            weather_text = format_weather_response(result)
            bot_response = f"Here's the current weather for {location}:\n\n{weather_text}"
    
    history.append([message, bot_response])
    return history, ""

# Create simplified Gradio interface - Chat only
with gr.Blocks(title="🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scotland Adventure Weather", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scotland Adventure Weather Assistant")
    gr.Markdown("Chat with AI about Scottish weather and adventure planning! Mention specific locations for real-time weather data.")
    
    chatbot = gr.Chatbot(height=600)
    msg = gr.Textbox(
        label="Ask me about Scottish weather!",
        placeholder="Try: 'Is it good for hiking in Aviemore?' or 'What's the forecast for Edinburgh this week?' or 'Compare Glasgow vs Fort William for cycling'",
        lines=2
    )
    
    # Add some example buttons for quick testing
    with gr.Row():
        example1 = gr.Button("☀️ Weather in Edinburgh", size="sm")
        example2 = gr.Button("🥾 Hiking in Aviemore?", size="sm") 
        example3 = gr.Button("📸 Photography weather Glasgow", size="sm")
        example4 = gr.Button("🗻 7-day forecast Fort William", size="sm")
    
    msg.submit(intelligent_weather_chat, [msg, chatbot], [chatbot, msg])
    
    # Example button actions
    example1.click(lambda: "What's the weather like in Edinburgh?", outputs=msg)
    example2.click(lambda: "Is it good for hiking in Aviemore today?", outputs=msg)
    example3.click(lambda: "What's the weather like for photography in Glasgow?", outputs=msg)
    example4.click(lambda: "Can you give me a 7-day forecast for Fort William?", outputs=msg)
    
    gr.Markdown("---")
    gr.Markdown("*Powered by Open-Meteo weather data, custom MCP server, and Nebius AI Studio*")

if __name__ == "__main__":
    app.launch(share=True)