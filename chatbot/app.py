import gradio as gr
import requests
from openai import OpenAI
import json
from datetime import datetime

# Your MCP server URL
MCP_URL = "https://emma-ctrl--scotland-weather-mcp-fastapi-app.modal.run/mcp"

# Initialize Nebius AI Studio client
client = OpenAI(
    api_key="eyJhbGciOiJIUzI1NiIsImtpZCI6IlV6SXJWd1h0dnprLVRvdzlLZWstc0M1akptWXBvX1VaVkxUZlpnMDRlOFUiLCJ0eXAiOiJKV1QifQ.eyJzdWIiOiJnaXRodWJ8NjQxOTk5MzgiLCJzY29wZSI6Im9wZW5pZCBvZmZsaW5lX2FjY2VzcyIsImlzcyI6ImFwaV9rZXlfaXNzdWVyIiwiYXVkIjpbImh0dHBzOi8vbmViaXVzLWluZmVyZW5jZS5ldS5hdXRoMC5jb20vYXBpL3YyLyJdLCJleHAiOjE5MDY2MjYzOTgsInV1aWQiOiJiMzE1YWJiYS05NDUyLTQxYTItOTIxNy0xOGY2NjYxZDg0NTMiLCJuYW1lIjoiRW1tYSIsImV4cGlyZXNfYXQiOiIyMDMwLTA2LTAyVDEwOjI2OjM4KzAwMDAifQ.0ovoenUoRM5CctohO-0A416Z2YdlR3Nqn4W5XLmaCeE",
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
        return f"❌ {response['error']}"
    
    if "content" in response and response["content"]:
        return response["content"][0]["text"]
    
    return "❌ No weather data received"

def extract_context_from_message(message, weather_results=None):
    """Extract key context from user message and weather results"""
    context = {}
    
    # Extract activity type - expanded list
    activities = ["camping", "hiking", "climbing", "photography", "cycling", "walking", "fishing", 
                 "kayaking", "skiing", "snowboarding", "birdwatching", "running", "surfing", 
                 "sailing", "mountaineering", "backpacking", "trekking", "sightseeing", "climbing",
                 "canoeing", "rafting", "paragliding", "rock climbing", "ice climbing", "wild swimming"]
    
    for activity in activities:
        if activity in message.lower():
            context["activity"] = activity
            break
    
    # Fallback to general outdoor activity if no specific activity found
    if "activity" not in context:
        outdoor_keywords = ["trip", "adventure", "outdoor", "visit", "travel", "explore", "tour", "excursion"]
        for keyword in outdoor_keywords:
            if keyword in message.lower():
                context["activity"] = "outdoor activity"
                break
    
    # Extract time references
    time_words = ["tomorrow", "friday", "weekend", "today", "next week", "this week"]
    for time_word in time_words:
        if time_word in message.lower():
            context["timeframe"] = time_word
            break
    
    # Extract weather preferences
    if any(word in message.lower() for word in ["bad weather", "good weather", "dry", "sunny"]):
        context["weather_preference"] = "good weather preferred"
    
    # Extract locations mentioned in weather results
    if weather_results:
        locations = []
        for result in weather_results:
            if ":" in result:
                location = result.split(":")[0].strip()
                locations.append(location)
        context["locations_checked"] = locations
    
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
        locations = list(set(conv_state["locations_discussed"]))  # Remove duplicates
        summary_parts.append(f"Locations discussed: {', '.join(locations)}")
    
    if conv_state.get("weather_preference"):
        summary_parts.append(f"Weather preference: {conv_state['weather_preference']}")
    
    if conv_state.get("previous_recommendations"):
        summary_parts.append(f"Previous advice: {conv_state['previous_recommendations']}")
    
    if summary_parts:
        return "\n".join(summary_parts)
    return ""

def update_conversation_state(conv_state, message, weather_results=None, ai_response=None):
    """Update conversation state with new information"""
    if conv_state is None:
        conv_state = {
            "recent_messages": [],
            "locations_discussed": [],
            "activity": None,
            "timeframe": None,
            "weather_preference": None,
            "previous_recommendations": None
        }
    
    # Add to recent messages (keep last 6 exchanges)
    conv_state["recent_messages"].append({"user": message, "assistant": ai_response})
    if len(conv_state["recent_messages"]) > 6:
        conv_state["recent_messages"] = conv_state["recent_messages"][-6:]
    
    # Extract and update context
    new_context = extract_context_from_message(message, weather_results)
    
    # Update activity
    if new_context.get("activity"):
        conv_state["activity"] = new_context["activity"]
    
    # Update timeframe
    if new_context.get("timeframe"):
        conv_state["timeframe"] = new_context["timeframe"]
    
    # Update weather preference
    if new_context.get("weather_preference"):
        conv_state["weather_preference"] = new_context["weather_preference"]
    
    # Add new locations
    if new_context.get("locations_checked"):
        for location in new_context["locations_checked"]:
            if location not in conv_state["locations_discussed"]:
                conv_state["locations_discussed"].append(location)
    
    # Keep only recent locations (last 8)
    if len(conv_state["locations_discussed"]) > 8:
        conv_state["locations_discussed"] = conv_state["locations_discussed"][-8:]
    
    # Store key recommendations
    if ai_response and any(word in ai_response.lower() for word in ["recommend", "suggest", "better", "alternative"]):
        # Extract a brief summary of the recommendation
        sentences = ai_response.split(".")[:2]  # First 2 sentences
        conv_state["previous_recommendations"] = ".".join(sentences)
    
    return conv_state

def build_messages_with_context(message, conv_state, system_prompt):
    """Build message array including conversation context"""
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add context summary if available
    context_summary = build_context_summary(conv_state)
    if context_summary:
        context_message = f"CONVERSATION CONTEXT:\n{context_summary}\n\n"
        messages.append({"role": "system", "content": context_message})
    
    # Add recent conversation history
    if conv_state and conv_state.get("recent_messages"):
        for msg in conv_state["recent_messages"][-3:]:  # Last 3 exchanges
            messages.append({"role": "user", "content": msg["user"]})
            if msg["assistant"]:
                messages.append({"role": "assistant", "content": msg["assistant"]})
    
    # Add current message
    messages.append({"role": "user", "content": message})
    
    return messages

def weather_chat(message, history, conversation_state):
    """Enhanced chat interface with conversation memory"""
    try:
        system_prompt = """You are a helpful Scottish Adventure Weather assistant. You help people plan outdoor activities based on weather conditions.

You have access to two weather tools:
- get_weather(location): Get current weather for any location worldwide
- get_forecast(location, days): Get multi-day forecast (1-7 days, default 3)

Your weather tools are intelligent - they automatically prioritize Scottish locations for ambiguous names (e.g., "Perth" → Scotland), work worldwide, and handle remote places like Scottish islands.

IMPORTANT: You have conversation memory. Use the conversation context provided to maintain continuity. When users ask follow-up questions, refer back to previously discussed locations, activities, and preferences.

When you receive weather data, interpret it conversationally and give practical advice. Don't just repeat the raw data - analyze it and give helpful recommendations in a natural, friendly way.

Your personality:
- Friendly and enthusiastic about Scottish adventures
- Conversational and natural (not robotic)
- Knowledgeable about outdoor activities
- Practical and safety-conscious
- Use Scottish terms occasionally but don't overdo it
- Remember and build on previous parts of the conversation

Always give specific, actionable advice and recommendations based on the weather conditions and conversation context."""

        # Build messages with conversation context
        messages = build_messages_with_context(message, conversation_state, system_prompt)

        # Try function calling with Qwen (reliable)
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-72B-Instruct", 
            messages=messages,
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "description": "Get current weather for any location. Automatically prioritizes Scottish locations.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "location": {"type": "string", "description": "Location name"}
                            },
                            "required": ["location"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_forecast",
                        "description": "Get multi-day weather forecast for planning",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "location": {"type": "string", "description": "Location name"},
                                "days": {"type": "integer", "description": "Number of days (1-7)", "default": 3}
                            },
                            "required": ["location"]
                        }
                    }
                }
            ],
            tool_choice="auto",
            temperature=0.7,
            max_tokens=600
        )
        
        message_obj = response.choices[0].message
        
        if message_obj.tool_calls:
            # AI wants to call weather tools
            weather_results = []
            
            for tool_call in message_obj.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                
                # Call our MCP server
                result = call_mcp_server(func_name, func_args)
                weather_text = format_weather_response(result)
                weather_results.append(f"{func_args.get('location', 'Unknown')}: {weather_text}")
            
            # Use Llama for better conversational interpretation with full context
            interpretation_prompt = """Now interpret this weather data conversationally, keeping in mind the conversation context. Don't just repeat the raw data - analyze it and give practical, friendly advice that builds on our previous discussion."""
            
            # Build messages for interpretation including context
            interpretation_messages = build_messages_with_context(message, conversation_state, system_prompt + "\n\n" + interpretation_prompt)
            interpretation_messages.append({
                "role": "user", 
                "content": f"Here's the weather data I found:\n\n{chr(10).join(weather_results)}\n\nPlease interpret this data conversationally and give me practical advice, keeping in mind our previous conversation."
            })
            
            follow_up_response = client.chat.completions.create(
                model="meta-llama/Meta-Llama-3.1-70B-Instruct",  # Better at conversation
                messages=interpretation_messages,
                temperature=0.7,
                max_tokens=600
            )
            
            bot_response = follow_up_response.choices[0].message.content
            
            # Update conversation state with weather results
            conversation_state = update_conversation_state(conversation_state, message, weather_results, bot_response)
        else:
            # No weather tools needed, just conversation with context
            bot_response = message_obj.content
            
            # Update conversation state
            conversation_state = update_conversation_state(conversation_state, message, None, bot_response)
            
    except Exception as e:
        # Fallback to simple response
        bot_response = f"I'm having some trouble right now. You can try asking about specific locations like 'weather in Canna' or 'forecast for Edinburgh'. Error: {str(e)}"
        conversation_state = update_conversation_state(conversation_state, message, None, bot_response)
    
    history.append([message, bot_response])
    return history, "", conversation_state

# Create Gradio interface with conversation state
with gr.Blocks(title="🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scotland Adventure Weather", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scotland Adventure Weather Assistant")
    gr.Markdown("Chat naturally about weather and adventure planning! I'll remember our conversation and automatically get weather data when needed.")
    
    # Conversation state (invisible to user)
    conversation_state = gr.State(None)
    
    chatbot = gr.Chatbot(height=600)
    msg = gr.Textbox(
        label="Ask me about weather anywhere!",
        placeholder="Try: 'Weather in Canna?', 'Is it good for camping in Canna tomorrow and Friday?', 'Find me a better spot'",
        lines=2
    )
    
    # Example buttons
    with gr.Row():
        example1 = gr.Button("☀️ Weather in Edinburgh", size="sm")
        example2 = gr.Button("🏝️ Weather in Canna", size="sm")
        example3 = gr.Button("🏕️ Camping in Canna this weekend?", size="sm")
        example4 = gr.Button("📸 Photography weather Skye", size="sm")
    
    msg.submit(weather_chat, [msg, chatbot, conversation_state], [chatbot, msg, conversation_state])
    
    # Example button actions
    example1.click(lambda: "What's the weather like in Edinburgh?", outputs=msg)
    example2.click(lambda: "What's the weather like in Canna?", outputs=msg)
    example3.click(lambda: "I'm planning to go camping in Canna tomorrow and Friday. What's the weather like? I will go somewhere else if the weather is bad", outputs=msg)
    example4.click(lambda: "What's the weather like for photography in Skye?", outputs=msg)
    
    gr.Markdown("---")
    gr.Markdown("*Powered by Open-Meteo weather data, intelligent MCP server with conversation memory, and Nebius AI Studio*")

if __name__ == "__main__":
    app.launch(share=True)