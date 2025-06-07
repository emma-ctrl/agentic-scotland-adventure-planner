import requests
import json

# Your MCP server URLs
WEATHER_MCP_URL = "https://emma-ctrl--scotland-weather-mcp-fastapi-app.modal.run/mcp"
ROUTES_MCP_URL = "https://emma-ctrl--scotland-walkhighlands-mcp-fastapi-app.modal.run/mcp"

def test_mcp_server(url, server_name):
    """Test an MCP server"""
    print(f"\n🧪 Testing {server_name} at {url}")
    print("="*50)
    
    # Test 1: List tools
    try:
        payload = {"method": "tools/list"}
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print("✅ Tools list successful!")
        if "tools" in data:
            for tool in data["tools"]:
                print(f"  - {tool['name']}: {tool['description'][:60]}...")
        else:
            print("❌ No tools found in response")
            print(f"Response: {data}")
    except Exception as e:
        print(f"❌ Tools list failed: {e}")
        return False
    
    return True

def test_weather_tools():
    """Test weather MCP server tools"""
    if not test_mcp_server(WEATHER_MCP_URL, "Weather MCP"):
        return
    
    print(f"\n🌤️ Testing weather tool call...")
    try:
        payload = {
            "method": "tools/call",
            "params": {
                "name": "get_weather",
                "arguments": {"location": "Edinburgh"}
            }
        }
        response = requests.post(WEATHER_MCP_URL, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if "content" in data and data["content"]:
            print("✅ Weather tool call successful!")
            print(f"Sample response: {data['content'][0]['text'][:100]}...")
        else:
            print("❌ Weather tool call failed")
            print(f"Response: {data}")
    except Exception as e:
        print(f"❌ Weather tool call failed: {e}")

def test_routes_tools():
    """Test routes MCP server tools"""
    if not test_mcp_server(ROUTES_MCP_URL, "Routes MCP"):
        return
        
    print(f"\n🥾 Testing routes tool call...")
    try:
        payload = {
            "method": "tools/call",
            "params": {
                "name": "search_routes",
                "arguments": {
                    "search_term": "Edinburgh",
                    "difficulty": 1,
                    "max_results": 3
                }
            }
        }
        response = requests.post(ROUTES_MCP_URL, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if "content" in data and data["content"]:
            print("✅ Routes tool call successful!")
            print(f"Sample response: {data['content'][0]['text'][:200]}...")
        else:
            print("❌ Routes tool call failed")
            print(f"Response: {data}")
    except Exception as e:
        print(f"❌ Routes tool call failed: {e}")

def test_combined_request():
    """Test the kind of request your chatbot would make"""
    print(f"\n🏔️ Testing combined adventure planning request...")
    
    # Test weather
    print("Getting weather for Edinburgh...")
    try:
        weather_payload = {
            "method": "tools/call",
            "params": {
                "name": "get_forecast",
                "arguments": {"location": "Edinburgh", "days": 3}
            }
        }
        weather_response = requests.post(WEATHER_MCP_URL, json=weather_payload, timeout=15)
        weather_response.raise_for_status()
        weather_data = weather_response.json()
        
        if "content" in weather_data:
            print("✅ Weather data retrieved")
        else:
            print("❌ Weather data failed")
            print(f"Weather response: {weather_data}")
    except Exception as e:
        print(f"❌ Weather request failed: {e}")
        return
    
    # Test routes
    print("Getting routes near Edinburgh...")
    try:
        routes_payload = {
            "method": "tools/call",
            "params": {
                "name": "search_routes", 
                "arguments": {
                    "search_term": "Edinburgh",
                    "difficulty": 1,
                    "max_results": 3
                }
            }
        }
        routes_response = requests.post(ROUTES_MCP_URL, json=routes_payload, timeout=15)
        routes_response.raise_for_status()
        routes_data = routes_response.json()
        
        if "content" in routes_data:
            print("✅ Routes data retrieved")
            print("\n🎉 Combined request successful! Your adventure chatbot should work!")
        else:
            print("❌ Routes data failed")
            print(f"Routes response: {routes_data}")
    except Exception as e:
        print(f"❌ Routes request failed: {e}")

if __name__ == "__main__":
    print("🏔️ Testing Scotland Adventure MCP Servers")
    print("This will test both your weather and routes servers")
    
    # Test individual servers
    test_weather_tools()
    test_routes_tools()
    
    # Test combined request
    test_combined_request()
    
    print(f"\n" + "="*50)
    print("✅ Testing complete! Check the results above.")
    print("If both servers work, your enhanced chatbot should work perfectly!")