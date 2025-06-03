import modal

# Create Modal app
app = modal.App("scotland-weather-chat-only")

# Create the image with all dependencies
image = modal.Image.debian_slim().pip_install(
    "gradio>=4.0.0",
    "requests>=2.31.0", 
    "openai>=1.0.0"
)

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("nebius-api-key")],
    timeout=3600,
    min_containers=1
)
@modal.asgi_app()
def create_app():
    import gradio as gr
    import requests
    from openai import OpenAI
    import os
    
    # Your MCP server URL
    MCP_URL = "https://emma-ctrl--scotland-weather-mcp-fastapi-app.modal.run/mcp"
    
    # Initialize Nebius AI Studio client
    client = OpenAI(
        api_key=os.getenv("NEBIUS_API_KEY"),
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
        """Extract Scottish location names from text"""
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
    
    def chat_with_ai(message, history):
        """Chat function with weather integration"""
        try:
            # Extract locations from message
            locations = extract_locations_from_text(message)
            
            # Get weather data for found locations
            weather_data = {}
            for location in locations[:2]:  # Limit to 2 locations
                if "forecast" in message.lower() or "days" in message.lower() or "week" in message.lower():
                    # User wants forecast
                    days = 3
                    if "7" in message or "week" in message.lower():
                        days = 7
                    elif "5" in message:
                        days = 5
                    
                    weather_result = call_mcp_server("get_forecast", {"location": location, "days": days})
                else:
                    # User wants current weather
                    weather_result = call_mcp_server("get_weather", {"location": location})
                
                if "content" in weather_result:
                    weather_data[location] = format_weather_response(weather_result)
            
            # System prompt for the AI
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
            
            # Prepare message with weather context
            if weather_data:
                weather_context = "\n\nCurrent weather data:\n"
                for location, weather in weather_data.items():
                    weather_context += f"\n{location}:\n{weather}\n"
                user_message = f"{message}\n\n[Weather data context: {weather_context}]"
            else:
                user_message = message
            
            # Call the AI
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
            
            # Add tip if no weather data found
            if not weather_data and any(word in message.lower() for word in ["weather", "forecast", "rain", "sunny", "temperature"]):
                bot_response += "\n\n💡 Tip: Mention a specific Scottish location and I can get you real-time weather data!"
            
        except Exception as e:
            bot_response = f"Sorry, I'm having trouble with my AI connection. But I can still help with weather! Try asking about a specific Scottish location."
            
            # Fallback weather lookup
            locations = extract_locations_from_text(message)
            if locations:
                location = locations[0]
                result = call_mcp_server("get_weather", {"location": location})
                weather_text = format_weather_response(result)
                bot_response = f"Here's the current weather for {location}:\n\n{weather_text}"
        
        # Return updated history
        history.append([message, bot_response])
        return history, ""
    
    # Create simple interface
    with gr.Blocks(title="Scotland Adventure Weather", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scotland Adventure Weather Assistant")
        gr.Markdown("Chat with AI about Scottish weather and adventure planning! Mention locations for real-time weather data.")
        
        chatbot = gr.Chatbot(height=500)
        
        with gr.Row():
            msg = gr.Textbox(
                label="Ask me about Scottish weather!",
                placeholder="Try: 'Is it good for hiking in Aviemore?' or 'Edinburgh forecast this week'",
                scale=4
            )
            send_btn = gr.Button("Send", variant="primary", scale=1)
        
        # Quick example buttons
        with gr.Row():
            btn1 = gr.Button("☀️ Edinburgh weather", size="sm")
            btn2 = gr.Button("🥾 Hiking Aviemore?", size="sm") 
            btn3 = gr.Button("📸 Glasgow forecast", size="sm")
            btn4 = gr.Button("🗻 Fort William 7 days", size="sm")
        
        # Set up interactions
        msg.submit(chat_with_ai, [msg, chatbot], [chatbot, msg])
        send_btn.click(chat_with_ai, [msg, chatbot], [chatbot, msg])
        
        # Example button functions
        btn1.click(lambda: "What's the weather like in Edinburgh?", outputs=msg)
        btn2.click(lambda: "Is it good for hiking in Aviemore today?", outputs=msg)
        btn3.click(lambda: "What's the forecast for Glasgow this week?", outputs=msg)
        btn4.click(lambda: "Give me a 7-day forecast for Fort William", outputs=msg)
        
        gr.Markdown("*Powered by Open-Meteo weather data, custom MCP server, and Nebius AI Studio*")
    
    return demo