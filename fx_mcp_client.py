"""
FX MCP Client - CLI Interface
Connects to MCP server and uses Claude for tool orchestration
"""
import subprocess
import json
import sys
import anthropic

# Initialize Anthropic client
client = anthropic.Anthropic()

# MCP Server process
mcp_process = None

def start_mcp_server():
    """Start the MCP server as subprocess"""
    global mcp_process
    mcp_process = subprocess.Popen(
        [sys.executable, "app/fx_mcp_api_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    print("MCP Server started")

def send_mcp_request(method: str, params: dict = None) -> dict:
    """Send JSON-RPC request to MCP server"""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {}
    }
    
    mcp_process.stdin.write(json.dumps(request) + "\n")
    mcp_process.stdin.flush()
    
    response_line = mcp_process.stdout.readline()
    if response_line:
        return json.loads(response_line)
    return {}

def initialize_mcp():
    """Initialize MCP connection"""
    response = send_mcp_request("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "fx-cli-client", "version": "1.0.0"}
    })
    
    # Send initialized notification
    send_mcp_request("notifications/initialized")
    return response

def list_tools() -> list:
    """Get list of available tools"""
    response = send_mcp_request("tools/list")
    return response.get("result", {}).get("tools", [])

def call_tool(name: str, arguments: dict) -> str:
    """Call an MCP tool"""
    response = send_mcp_request("tools/call", {
        "name": name,
        "arguments": arguments
    })
    
    result = response.get("result", {})
    content = result.get("content", [])
    
    if content and len(content) > 0:
        return content[0].get("text", "")
    return json.dumps(result)

def get_tools_for_claude(tools: list) -> list:
    """Convert MCP tools to Claude tool format"""
    claude_tools = []
    for tool in tools:
        claude_tools.append({
            "name": tool["name"],
            "description": tool.get("description", ""),
            "input_schema": tool.get("inputSchema", {"type": "object", "properties": {}})
        })
    return claude_tools

# System prompt
SYSTEM_PROMPT = """You are an FX Smart Routing Agent powered by Fintaar.ai. 

You have access to tools to help users with:
- FX rates for currency pairs (USDINR, EURUSD, GBPINR, etc.)
- Route recommendations for optimal execution
- CBDC information (e-INR, e-CNY, e-HKD, e-THB, e-AED, e-SGD)
- Stablecoin conversions (USDC, USDT, EURC, PYUSD, XSGD)
- Customer tier pricing (PLATINUM, GOLD, SILVER, BRONZE, RETAIL)
- Routing objectives (BEST_RATE, OPTIMUM, FASTEST_EXECUTION, MAX_STP)

Always use the tools to get accurate, real-time data. Be concise and helpful."""


def chat(user_message: str, tools: list, conversation_history: list) -> str:
    """Process user message with Claude"""
    
    claude_tools = get_tools_for_claude(tools)
    conversation_history.append({"role": "user", "content": user_message})
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=claude_tools,
        messages=conversation_history
    )
    
    # Handle tool use
    while response.stop_reason == "tool_use":
        tool_results = []
        assistant_content = response.content
        
        for block in response.content:
            if block.type == "tool_use":
                print(f"\n[Calling tool: {block.name}]")
                
                # Call MCP tool
                result = call_tool(block.name, block.input)
                print(f"[Tool result received]")
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })
        
        conversation_history.append({"role": "assistant", "content": assistant_content})
        conversation_history.append({"role": "user", "content": tool_results})
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=claude_tools,
            messages=conversation_history
        )
    
    # Extract final response
    final_response = ""
    for block in response.content:
        if hasattr(block, "text"):
            final_response += block.text
    
    conversation_history.append({"role": "assistant", "content": response.content})
    return final_response


def main():
    print("=" * 60)
    print("FX Smart Routing Agent - MCP Client")
    print("=" * 60)
    
    # Start MCP server
    print("\nStarting MCP server...")
    start_mcp_server()
    
    # Initialize
    print("Initializing MCP connection...")
    initialize_mcp()
    
    # Get tools
    print("Loading tools...")
    tools = list_tools()
    print(f"Loaded {len(tools)} tools:")
    for t in tools:
        print(f"  - {t['name']}")
    
    print("\n" + "=" * 60)
    print("Ready! Ask me about FX rates, routes, CBDCs, stablecoins...")
    print("Type 'quit' to exit, 'tools' to list tools")
    print("=" * 60 + "\n")
    
    conversation_history = []
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["quit", "exit", "bye"]:
                print("\nGoodbye!")
                break
            
            if user_input.lower() == "tools":
                print("\nAvailable tools:")
                for t in tools:
                    print(f"  - {t['name']}: {t.get('description', '')[:60]}...")
                print()
                continue
            
            print("\nAgent: ", end="")
            response = chat(user_input, tools, conversation_history)
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again.\n")
    
    # Cleanup
    if mcp_process:
        mcp_process.terminate()


if __name__ == "__main__":
    main()
