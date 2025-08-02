from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from dotenv import load_dotenv
import os
import requests
from langchain.agents import Tool
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_experimental.tools import PythonREPLTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper



load_dotenv(override=True)
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"
serper = GoogleSerperAPIWrapper()

async def playwright_tools():
    # Initialize and start the Playwright browser automation framework
    # This creates a new Playwright instance that can control web browsers
    playwright = await async_playwright().start()
    
    # Launch a Chromium browser instance in non-headless mode (visible browser window)
    # The headless=False parameter means the browser will be visible during automation
    browser = await playwright.chromium.launch(headless=False)
    
    # Create a PlayWrightBrowserToolkit instance using the launched browser
    # This toolkit provides various tools for web automation tasks like clicking, typing, etc.
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    
    # Return three important objects:
    # 1. toolkit.get_tools() - A list of available browser automation tools
    # 2. browser - The browser instance for manual control if needed
    # 3. playwright - The Playwright instance for cleanup and management
    return toolkit.get_tools(), browser, playwright


def push(text: str):
    """Send a push notification to the user"""
    requests.post(pushover_url, data = {"token": pushover_token, "user": pushover_user, "message": text})
    return "success"


def get_file_tools():
    # Create a FileManagementToolkit instance with "sandbox" as the root directory
    # This toolkit provides tools for file operations like reading, writing, and managing files
    toolkit = FileManagementToolkit(root_dir="sandbox")
    
    # Return all the tools provided by the FileManagementToolkit
    # These tools can be used by agents to perform file-related operations
    return toolkit.get_tools()


async def other_tools():
    # Create a push notification tool that can send messages to the user
    # This tool uses the 'push' function defined earlier and provides a descriptive name and description
    push_tool = Tool(name="send_push_notification", func=push, description="Use this tool when you want to send a push notification")
    
    # Get file management tools from the FileManagementToolkit
    # These tools allow reading, writing, and managing files in the sandbox directory
    file_tools = get_file_tools()

    # Create a web search tool using the Google Serper API wrapper
    # This tool enables online web searches and returns relevant results
    tool_search =Tool(
        name="search",
        func=serper.run,
        description="Use this tool when you want to get the results of an online web search"
    )

    # Initialize the Wikipedia API wrapper for accessing Wikipedia content
    # This creates a connection to Wikipedia's API for retrieving article information
    wikipedia = WikipediaAPIWrapper()
    
    # Create a Wikipedia query tool using the API wrapper
    # This tool allows searching and retrieving information from Wikipedia articles
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)

    # Create a Python REPL (Read-Eval-Print Loop) tool
    # This tool enables executing Python code dynamically during conversations
    python_repl = PythonREPLTool()
    
    # Return all tools combined: file tools, push notification, web search, Wikipedia, and Python REPL
    # This provides a comprehensive set of tools for the agent to use
    return file_tools + [push_tool, tool_search, python_repl,  wiki_tool]

