# Import the Trader class, which represents an autonomous trading agent
from traders import Trader

# Import List type for type hinting
from typing import List

# Import asyncio for asynchronous event loop management
import asyncio

# Import LogTracer for custom trace logging of agent activity
from tracers import LogTracer

# Import function to register a trace processor with the agent system
from agents import add_trace_processor

# Import function to check if the market is currently open
from market import is_market_open

# Import dotenv loader to read environment variables from a .env file
from dotenv import load_dotenv

# Import os module to access environment variables and system functions
import os

# Load environment variables from a .env file, overriding existing ones if present
load_dotenv(override=True)

# Read the interval (in minutes) between each trading run from environment variables, defaulting to 60 if not set
RUN_EVERY_N_MINUTES = int(os.getenv("RUN_EVERY_N_MINUTES", "60"))

# Determine whether to run the trading loop even when the market is closed, based on environment variable (default: false)
RUN_EVEN_WHEN_MARKET_IS_CLOSED = (
    os.getenv("RUN_EVEN_WHEN_MARKET_IS_CLOSED", "true").strip().lower() == "true"
)

# Decide whether to use multiple different models for the traders, based on environment variable (default: false)
USE_MANY_MODELS = os.getenv("USE_MANY_MODELS", "false").strip().lower() == "true"

# List of trader first names, each representing a unique trading persona
names = ["Warren", "George", "Ray", "Cathie"]

# List of trader last names, each reflecting the trader's strategy or style
lastnames = ["Patience", "Bold", "Systematic", "Crypto"]

# If using multiple models, assign a different model to each trader
if USE_MANY_MODELS:
    model_names = [
        "gpt-4.1-mini",                    # Model for Warren
        "deepseek-chat",                   # Model for George
        "gemini-2.5-flash-preview-04-17",  # Model for Ray
        "grok-3-mini-beta",                # Model for Cathie
    ]
    # Human-readable short names for each model, for display or logging
    short_model_names = ["GPT 4.1 Mini", "DeepSeek V3", "Gemini 2.5 Flash", "Grok 3 Mini"]
else:
    # If not using multiple models, assign the same model to all traders
    model_names = ["gpt-4o-mini"] * 4
    short_model_names = ["GPT 4o mini"] * 4

# Function to create a list of Trader instances, one for each persona
def create_traders() -> List[Trader]:
    traders = []
    # Iterate over the zipped lists of names, lastnames, and model_names to instantiate each Trader
    for name, lastname, model_name in zip(names, lastnames, model_names):
        traders.append(Trader(name, lastname, model_name))
    return traders

# Asynchronous function to run the trading loop at a fixed interval
async def run_every_n_minutes():
    # Register the LogTracer to capture and log trace events for observability
    # We want openai agent sdk to record any traces using LogTracer
    add_trace_processor(LogTracer())
    # Create the list of trader agents
    traders = create_traders()
    # Enter an infinite loop to repeatedly execute trading logic
    while True:
        # Check if trading should proceed (either market is open, or override is enabled)
        if RUN_EVEN_WHEN_MARKET_IS_CLOSED or is_market_open():
            # Run all traders concurrently using asyncio.gather
            await asyncio.gather(*[trader.run() for trader in traders])
        else:
            # If market is closed and override is not enabled, skip this run
            print("Market is closed, skipping run")
        # Wait for the specified interval before the next run
        await asyncio.sleep(RUN_EVERY_N_MINUTES * 60)

# Entry point: if this script is run directly, start the trading scheduler
if __name__ == "__main__":
    # Print a message indicating the scheduler's interval
    print(f"Starting scheduler to run every {RUN_EVERY_N_MINUTES} minutes")
    # Start the asynchronous trading loop
    asyncio.run(run_every_n_minutes())
