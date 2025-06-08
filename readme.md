# 🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scotland Adventure Weather Planner

## agent-demo-track

A comprehensive Scottish adventure planning app that combines three custom MCP (Model Context Protocol) servers with an intelligent Gradio interface. Get weather forecasts, driving routes, daylight times, and AI-powered recommendations for your Scottish adventures.

## 🎯 Features

### 🌦️ Weather Intelligence
- **Real-time weather data** - Current conditions and 7-day forecasts for any Scottish location
- **Adventure-focused recommendations** - Activity-specific advice for hiking, photography, camping
- **Geographic disambiguation** - Automatically finds Scottish locations (not US namesakes!)
- **Weather safety alerts** - Wind warnings, precipitation alerts, visibility conditions

### 🌅 Daylight Planning  
- **Sunrise/sunset times** - Perfect for photography and outdoor activity planning
- **Golden hour calculations** - Optimal lighting times for photographers
- **Seasonal daylight tracking** - Essential for Highland adventures where daylight varies dramatically

### 🚗 Route Planning
- **Driving distances and times** - Between any Scottish locations
- **Multi-stop road trip planning** - Optimized routes with Highland driving considerations
- **Interactive route visualization** - Real driving routes displayed on maps
- **Scottish driving tips** - Single-track roads, ferry times, fuel stops

### 🤖 AI Chat Interface
- **Natural language queries** - Ask questions like "Road trip from Edinburgh to Skye"
- **Intelligent data synthesis** - Combines weather, driving, and daylight data
- **Adventure recommendations** - Personalized suggestions based on conditions
- **Interactive maps** - Visual route and location display

## 🏗️ Architecture

### Three Custom MCP Servers
1. **Weather MCP** (`scotland-weather-mcp`) - Open-Meteo API integration
2. **Daylight MCP** (`scotland-daylight-mcp`) - Sunrise-Sunset API integration  
3. **Driving MCP** (`scottish-driving-mcp`) - OpenRouteService integration

### Gradio Frontend
- **Multi-functional interface** - Chat, quick examples, interactive maps
- **Real-time data integration** - Fetches from all three MCP servers
- **AI-powered responses** - Uses Nebius AI Studio for intelligent synthesis

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.8+
Modal account (for MCP server deployment)
OpenRouteService API key (free tier: 2000 requests/day)
Nebius AI Studio API key
```

### 1. Deploy MCP Servers

#### Weather Server
```bash
# Clone and setup
git clone <repository>
cd scotland-weather-adventure

# Deploy weather MCP
modal deploy weather_server.py
# Creates: https://your-username--scotland-weather-mcp-fastapi-app.modal.run
```

#### Daylight Server  
```bash
# Deploy daylight MCP
modal deploy daylight_server.py
# Creates: https://your-username--scotland-daylight-mcp-fastapi-app.modal.run
```

#### Driving Server
```bash
# Get free API key from: https://openrouteservice.org/dev/#/signup
modal secret create openrouteservice OPENROUTESERVICE_API_KEY=your_key_here

# Deploy driving MCP
modal deploy driving_server.py
# Creates: https://your-username--scottish-driving-mcp-fastapi-app.modal.run
```

### 2. Setup Gradio Frontend
```bash
# Update MCP server URLs in app.py
WEATHER_MCP_URL = "https://your-username--scotland-weather-mcp-fastapi-app.modal.run/mcp"
DAYLIGHT_MCP_URL = "https://your-username--scotland-daylight-mcp-fastapi-app.modal.run/mcp"  
DRIVING_MCP_URL = "https://your-username--scottish-driving-mcp-fastapi-app.modal.run/mcp"

# Add your Nebius AI Studio API key
client = OpenAI(api_key="your_nebius_key_here", base_url="https://api.studio.nebius.ai/v1")

# Install dependencies and run
pip install gradio requests openai folium
python app.py
```

## 📁 Project Structure

```
scotland-weather-adventure/
├── README.md                    # This file
├── app.py                      # Main Gradio web interface
├── weather_server.py           # Weather MCP server (Modal deployment)
├── daylight_server.py          # Daylight MCP server (Modal deployment)  
├── driving_server.py           # Driving MCP server (Modal deployment)
└── requirements.txt            # Dependencies
```

## 🛠️ MCP Server APIs

### Weather MCP Tools

#### `get_weather`
Get current weather conditions for any Scottish location.
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
Get 1-7 day weather forecast with adventure planning insights.
```json
{
  "method": "tools/call", 
  "params": {
    "name": "get_forecast",
    "arguments": {"location": "Fort William", "days": 5}
  }
}
```

### Daylight MCP Tools

#### `get_daylight_times`
Get sunrise, sunset, and golden hour times for photography planning.
```json
{
  "method": "tools/call",
  "params": {
    "name": "get_daylight_times", 
    "arguments": {"location": "Glencoe", "date": "2024-07-15"}
  }
}
```

### Driving MCP Tools

#### `get_driving_distance`
Calculate driving distance and time between locations.
```json
{
  "method": "tools/call",
  "params": {
    "name": "get_driving_distance",
    "arguments": {
      "from_location": "Edinburgh", 
      "to_location": "Isle of Skye"
    }
  }
}
```

#### `plan_road_trip`
Plan multi-stop road trips with optimized Scottish routes.
```json
{
  "method": "tools/call",
  "params": {
    "name": "plan_road_trip",
    "arguments": {
      "locations": ["Glasgow", "Fort William", "Isle of Skye", "Inverness"]
    }
  }
}
```

## 🎮 Gradio Interface Features

### 💬 Intelligent Chat
- Natural language adventure planning
- Combines weather, driving, and daylight data automatically
- Scottish location recognition and disambiguation
- Activity-specific recommendations

### 📍 Interactive Maps
- Real driving route visualization using OpenRouteService
- Multiple location support with markers
- Route geometry display (not just straight lines!)
- Automatic map centering and zoom

### 🎯 Quick Examples
Pre-built example queries:
- "☀️ Weather Edinburgh"
- "🚗 Drive Edinburgh→Skye" 
- "📸 Golden hour Glencoe"
- "🗺️ Road trip Glasgow→Skye"
- And more...

## 🌦️ Intelligent Features

### Scottish Geographic Intelligence
The system automatically handles location disambiguation:
- **"Perth"** → Finds Perth, Scotland (not Australia)
- **"Hamilton"** → Finds Hamilton, Scotland (not Ontario)  
- **"Arran"** → Finds Isle of Arran, Scotland (not Ireland)

### Adventure-Specific Recommendations
- **Hiking**: Wind warnings, precipitation alerts, visibility
- **Photography**: Golden hour times, clear sky recommendations
- **Driving**: Highland road conditions, single-track warnings
- **Camping**: Daylight hours, weather suitability

### Scottish Driving Considerations
- Single-track Highland roads (allow extra time)
- Ferry schedules for island destinations
- Remote area fuel stop planning
- Highland weather driving safety

## 🚢 Deployment Options

### MCP Servers (Modal - Recommended)
```bash
# All three servers deploy to Modal's serverless platform
modal deploy weather_server.py
modal deploy daylight_server.py  
modal deploy driving_server.py
```

### Gradio Frontend
- **Local Development**: `python app.py`
- **Gradio Sharing**: Built-in public demo links (`share=True`)
- **Production**: Deploy to Hugging Face Spaces, Modal, Railway, etc.

## 🔧 Configuration

### Environment Variables
```bash
# Required for driving server
OPENROUTESERVICE_API_KEY=your_openroute_key

# Required for AI chat  
NEBIUS_API_KEY=your_nebius_key
```

### API Keys Needed
1. **OpenRouteService** (Free: 2000 requests/day) - For driving routes
2. **Nebius AI Studio** - For intelligent chat responses
3. **No API keys needed** for weather (Open-Meteo) or daylight (Sunrise-Sunset API)

## 🏔️ Example Use Cases

### Weekend Trip Planning
- **Query**: "Should I go to Aviemore or Cairngorms this weekend?"
- **Response**: Weather comparison, driving times, daylight hours, activity recommendations

### Photography Expeditions  
- **Query**: "Golden hour photography spots near Fort William"
- **Response**: Sunrise/sunset times, weather conditions, recommended locations

### Multi-Day Adventures
- **Query**: "5-day road trip from Edinburgh to Skye with camping"
- **Response**: Route planning, weather forecast, camping suitability, daily recommendations

### Safety Planning
- **Query**: "Are there wind warnings for climbing in Glencoe?"
- **Response**: Wind speed alerts, weather safety assessment, alternative suggestions

## 🤝 Contributing

This project was built for adventure planning and learning! Contributions welcome:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Submit a pull request

### Ideas for Enhancement
- [ ] Add tide times for coastal adventures
- [ ] Include mountain weather conditions (snow, ice)
- [ ] Ferry schedule integration
- [ ] Accommodation booking suggestions
- [ ] Trail condition reports

## 📄 License

Open source - built for Scottish adventure enthusiasts and outdoor learning!

## 🙏 Credits

- **Weather Data**: [Open-Meteo](https://open-meteo.com/) (free weather API)
- **Daylight Data**: [Sunrise-Sunset.org](https://sunrise-sunset.org/) API
- **Routing**: [OpenRouteService](https://openrouteservice.org/) 
- **Deployment**: [Modal](https://modal.com/) serverless platform
- **AI**: [Nebius AI Studio](https://studio.nebius.ai/) 
- **Interface**: [Gradio](https://gradio.app/) web framework
- **Maps**: [Folium](https://python-visualization.github.io/folium/) Python mapping

---

*Built with ❤️ for Scottish outdoor enthusiasts and powered by multiple free APIs for maximum accessibility*ß