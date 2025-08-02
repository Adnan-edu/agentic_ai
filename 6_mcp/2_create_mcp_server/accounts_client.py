import mcp
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters
from agents import FunctionTool
import json

# Parameters we need to launch the accounts server(MCP Server)
params = StdioServerParameters(command="uv", args=["run", "accounts_server.py"], env=None)


async def list_accounts_tools():
    # Open a stdio client connection to the accounts server using the specified parameters
    async with stdio_client(params) as streams:
        # Create a new MCP client session using the opened streams
        async with mcp.ClientSession(*streams) as session:
            # Initialize the MCP session (handshake/setup)
            await session.initialize()
            # Request the list of available tools from the server
            tools_result = await session.list_tools()
            # Return the list of tool objects from the result
            return tools_result.tools
        
async def call_accounts_tool(tool_name, tool_args):
    # Open a stdio client connection to the accounts server
    async with stdio_client(params) as streams:
        # Create a new MCP client session using the opened streams
        async with mcp.ClientSession(*streams) as session:
            # Initialize the MCP session
            await session.initialize()
            # Call the specified tool on the server with the provided arguments
            result = await session.call_tool(tool_name, tool_args)
            # Return the result of the tool call
            return result
            
async def read_accounts_resource(name):
    # Open a stdio client connection to the accounts server
    async with stdio_client(params) as streams:
        # Create a new MCP client session using the opened streams
        async with mcp.ClientSession(*streams) as session:
            # Initialize the MCP session
            await session.initialize()
            # Read the account resource for the given name from the server
            result = await session.read_resource(f"accounts://accounts_server/{name}")
            # Return the text content of the first item in the resource contents
            return result.contents[0].text
        
async def read_strategy_resource(name):
    # Open a stdio client connection to the accounts server
    async with stdio_client(params) as streams:
        # Create a new MCP client session using the opened streams
        async with mcp.ClientSession(*streams) as session:
            # Initialize the MCP session
            await session.initialize()
            # Read the strategy resource for the given name from the server
            result = await session.read_resource(f"accounts://strategy/{name}")
            # Return the text content of the first item in the resource contents
            return result.contents[0].text

async def get_accounts_tools_openai():
    openai_tools = []  # Initialize an empty list to hold the OpenAI-compatible tool objects
    # Iterate over each tool returned by the list_accounts_tools function
    for tool in await list_accounts_tools():
        # Build a JSON schema for the tool's parameters, disallowing additional properties
        schema = {**tool.inputSchema, "additionalProperties": False}
        # Create a FunctionTool object for OpenAI, mapping the tool's name, description, and schema
        openai_tool = FunctionTool(
            name=tool.name,
            description=tool.description,
            params_json_schema=schema,
            # Define a lambda to invoke the tool using call_accounts_tool when called by OpenAI
            on_invoke_tool=lambda ctx, args, toolname=tool.name: call_accounts_tool(toolname, json.loads(args))
        )
        # Add the constructed FunctionTool to the list
        openai_tools.append(openai_tool)
    # Return the list of OpenAI-compatible tools
    return openai_tools