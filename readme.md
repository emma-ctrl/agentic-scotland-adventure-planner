# 🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scotland Adventure Weather Planner

A Scottish adventure planning app combining a custom MCP (Model Context Protocol) server with an intelligent Gradio interface for weather-based trip planning.

## 🎯 Features

- **Real-time Scottish weather data** - Current conditions and 7-day forecasts
- **Adventure-focused recommendations** - Activity-specific weather advice
- **Location comparison** - Compare weather between multiple Scottish locations
- **Intelligent geographic filtering** - Automatically finds Scottish locations (not US namesakes!)
- **Interactive chat interface** - Natural language weather queries
- **Custom MCP server** - RESTful API following MCP protocol standards

## 🏗️ Architecture

### MCP Weather Server
- **Technology**: FastAPI + Modal (serverless deployment)
- **Data Source**: Open-Meteo API (free, no API keys required)
- **Geographic Focus**: Scotland/UK with intelligent location disambiguation
- **Protocol**: Model Context Protocol for AI assistant integration

### Gradio Frontend
- **Interface**: Multi-tab web application
- **Features**: Current weather, forecasts, location comparison, chat
- **Intelligence**: Activity-specific recommendations and trip planning advice

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.8+
Modal account (for MCP server deployment)
```

### Setup MCP Server
```bash
# Install dependencies
pip install -r requirements.txt

# Test locally
python main.py

# Deploy to Modal
modal setup  # First time only
modal deploy deploy.py
```

### Setup Gradio App
```bash
cd chatbot
pip install -r requirements.txt
python app.py
```

## 📁 Project Structure

```
scotland-weather-adventure/
├── main.py              # Local MCP server testing
├── deploy.py            # Modal deployment configuration  
├── requirements.txt     # MCP server dependencies
├── chatbot/
│   ├── app.py          # Gradio web interface
│   └── requirements.txt # Chatbot dependencies
└── README.md           # This file
```

## 🛠️ MCP Server API

### Available Tools

#### `get_weather`
Get current weather conditions for a Scottish location.

```json
{
  "method": "tools/call",
  "params": {
    "name": "get_weather",
    "arguments": {"location": "Edinburgh"}
  }
}
```

#### `get_forecast` 
Get multi-day weather forecast (1-7 days) with adventure planning insights.

```json
{
  "method": "tools/call",
  "params": {
    "name": "get_forecast", 
    "arguments": {"location": "Fort William", "days": 5}
  }
}
```

### Geographic Intelligence
The server automatically handles location disambiguation:
- **"Dunfermline"** → Finds Dunfermline, Scotland (not Illinois)
- **"Perth"** → Finds Perth, Scotland (not Australia)  
- **"Glencoe"** → Searches for Scottish Highland locations

## 🎮 Gradio Interface Features

### 📍 Current Weather Tab
- Real-time weather conditions
- Activity-specific advice (hiking, photography, etc.)
- Wind warnings for outdoor activities

### 📅 Forecast Tab  
- 1-7 day weather forecasts
- Trip planning recommendations
- Good weather day counting

### ⚖️ Compare Tab
- Side-by-side location comparison
- Intelligent recommendations based on activity type
- Best location suggestions

### 💬 Chat Tab
- Natural language weather queries
- Conversational adventure planning
- Scottish location recognition

## 🌦️ Weather Features

### Adventure-Specific Intelligence
- **Hiking**: Wind speed warnings, precipitation alerts, visibility conditions
- **Photography**: Light condition assessments, clear sky recommendations  
- **Climbing**: Wind gust warnings, rock condition considerations
- **General Tourism**: Overall comfort and activity suitability

### Scottish Weather Considerations
- **Highland vs Lowland** conditions
- **Coastal vs Inland** variations  
- **Seasonal considerations** (daylight hours, temperature ranges)
- **Activity safety alerts** (high winds, wet conditions)

## 🚢 Deployment

### MCP Server (Modal)
```bash
modal deploy deploy.py
# Creates: https://your-username--scotland-weather-mcp-fastapi-app.modal.run
```

### Gradio App (Multiple Options)
```bash
# Local development
python chatbot/app.py

# Gradio sharing (public demo link)  
python chatbot/app.py  # share=True is already set

# Deploy to Hugging Face Spaces, Modal, or other platforms
```

## 🤝 Contributing

Built for the Gradio Hackathon! Contributions welcome:

1. Fork the repository
2. Create a feature branch
3. Make your changes  
4. Submit a pull request

## 📄 License

Open source - built for learning and Scottish adventure planning!

## 🏔️ Example Use Cases

- **Weekend Trip Planning**: "Should I go to Aviemore or Cairngorms this weekend?"
- **Activity-Specific Planning**: "Is it good weather for photography in Edinburgh?"
- **Multi-Day Adventures**: "What's the 5-day forecast for the West Highland Way?"
- **Safety Planning**: "Are there wind warnings for climbing in Glencoe?"

---

*Built with ❤️ for Scottish outdoor enthusiasts and powered by Open-Meteo weather data*