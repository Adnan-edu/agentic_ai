from contextlib import AsyncExitStack
from accounts_client import read_accounts_resource, read_strategy_resource
from tracers import make_trace_id
from agents import Agent, Tool, Runner, OpenAIChatCompletionsModel, trace
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import json
from agents.mcp import MCPServerStdio
from templates import (
    researcher_instructions,
    trader_instructions,
    trade_message,
    rebalance_message,
    research_tool,
)
from mcp_params import trader_mcp_server_params, researcher_mcp_server_params

load_dotenv(override=True)

deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")
grok_api_key = os.getenv("GROK_API_KEY")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
GROK_BASE_URL = "https://api.x.ai/v1"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

MAX_TURNS = 30

openrouter_client = AsyncOpenAI(base_url=OPENROUTER_BASE_URL, api_key=openrouter_api_key)
deepseek_client = AsyncOpenAI(base_url=DEEPSEEK_BASE_URL, api_key=deepseek_api_key)
grok_client = AsyncOpenAI(base_url=GROK_BASE_URL, api_key=grok_api_key)
gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)


def get_model(model_name: str):
    if "/" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=openrouter_client)
    elif "deepseek" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=deepseek_client)
    elif "grok" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=grok_client)
    elif "gemini" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=gemini_client)
    else:
        return model_name


async def get_researcher(mcp_servers, model_name) -> Agent:
    researcher = Agent(
        name="Researcher",
        instructions=researcher_instructions(),
        model=get_model(model_name),
        mcp_servers=mcp_servers,
    )
    return researcher


async def get_researcher_tool(mcp_servers, model_name) -> Tool:
    researcher = await get_researcher(mcp_servers, model_name)
    return researcher.as_tool(tool_name="Researcher", tool_description=research_tool())


class Trader:
    def __init__(self, name: str, lastname="Trader", model_name="gpt-4o-mini"):
        self.name = name
        self.lastname = lastname
        self.agent = None
        self.model_name = model_name
        self.do_trade = True

    async def create_agent(self, trader_mcp_servers, researcher_mcp_servers) -> Agent:
        tool = await get_researcher_tool(researcher_mcp_servers, self.model_name)
        self.agent = Agent(
            name=self.name,
            instructions=trader_instructions(self.name),
            model=get_model(self.model_name),
            tools=[tool],
            mcp_servers=trader_mcp_servers,
        )
        return self.agent

    async def get_account_report(self) -> str:
        account = await read_accounts_resource(self.name)
        account_json = json.loads(account)
        account_json.pop("portfolio_value_time_series", None)
        return json.dumps(account_json)

    async def run_agent(self, trader_mcp_servers, researcher_mcp_servers):
        self.agent = await self.create_agent(trader_mcp_servers, researcher_mcp_servers)
        account = await self.get_account_report()
        strategy = await read_strategy_resource(self.name)
        # Determine the message to send to the agent based on the current operation.
        # If self.do_trade is True, the agent should perform a trading operation:
        #   - Use trade_message() to generate a prompt that instructs the agent to look for new opportunities,
        #     research, and execute trades according to its strategy and current account state.
        # If self.do_trade is False, the agent should perform a rebalancing operation:
        #   - Use rebalance_message() to generate a prompt that instructs the agent to review its portfolio,
        #     research relevant news, and rebalance holdings as needed.
        # Both messages include the trader's name, their current strategy, and a summary of their account.
        message = (
            trade_message(self.name, strategy, account)
            if self.do_trade
            else rebalance_message(self.name, strategy, account)
        )

        # Run the agent using the Runner utility.
        # This sends the constructed message to the agent, which will:
        #   - Use its tools (including the researcher tool) to gather information,
        #   - Analyze the situation according to its strategy,
        #   - Make decisions and execute trades or rebalance as appropriate,
        #   - Respond with a summary and appraisal.
        # The max_turns parameter limits the number of conversational turns the agent can take in this run.
        await Runner.run(self.agent, message, max_turns=MAX_TURNS)

    async def run_with_mcp_servers(self):
        async with AsyncExitStack() as stack:
            trader_mcp_servers = [
                await stack.enter_async_context(
                    MCPServerStdio(params, client_session_timeout_seconds=120)
                )
                for params in trader_mcp_server_params
            ]
            async with AsyncExitStack() as stack:
                researcher_mcp_servers = [
                    await stack.enter_async_context(
                        MCPServerStdio(params, client_session_timeout_seconds=120)
                    )
                    for params in researcher_mcp_server_params(self.name)
                ]
                await self.run_agent(trader_mcp_servers, researcher_mcp_servers)

    async def run_with_trace(self):
        trace_name = f"{self.name}-trading" if self.do_trade else f"{self.name}-rebalancing"
        
        # Generate a unique trace ID for this run, using the trader's name as a tag.
        # This helps in associating all trace logs and spans with this specific trader and operation.
        trace_id = make_trace_id(f"{self.name.lower()}")
        
        # The 'trace' context manager starts a new trace for this agent's operation.
        # All actions performed within this context (including MCP server interactions and agent runs)
        # are recorded as part of this trace. This enables detailed observability of the agent's workflow.
        #
        # The trace system (see LogTracer in tracers.py) will:
        #   - Log when the trace starts and ends.
        #   - Log when each span (operation, such as a tool call or server interaction) starts and ends.
        #   - Attach metadata such as the trader's name, operation type, and any errors.
        #   - Persist these logs for UI display, debugging, and audit trails.
        #
        # This is crucial for understanding agent behavior, diagnosing issues, and providing real-time feedback in the UI.
        with trace(trace_name, trace_id=trace_id):
            # Run the agent's main logic (trading or rebalancing) within the trace context.
            # All tool calls, server requests, and agent decisions will be traced and logged.
            await self.run_with_mcp_servers()


    # This method is called concurrently for each trader from the run_every_n_minutes() function
    # in the trading_floor.py module. Each trader's run() executes in parallel as part of the
    # trading loop, allowing all agents to act independently on each scheduled interval.
    async def run(self):
        try:
            await self.run_with_trace()
        except Exception as e:
            print(f"Error running trader {self.name}: {e}")
        self.do_trade = not self.do_trade
