from mcp.server.fastmcp import FastMCP  # Import the FastMCP server class from the mcp.server.fastmcp module
from accounts import Account  # Import the Account class from the accounts module
from datetime import date

mcp = FastMCP("accounts_server")  # Create a FastMCP server instance named "accounts_server"

@mcp.tool()
async def get_balance(name: str) -> float:
    """Get the cash balance of the given account name.

    Args:
        name: The name of the account holder
    """
    # Retrieve the Account object for the given name and return its balance
    return Account.get(name).balance

@mcp.tool()
async def get_current_date() -> str:
    """Return the current date in ISO format (YYYY-MM-DD)."""
    return date.today().isoformat()


@mcp.tool()
async def get_holdings(name: str) -> dict[str, int]:
    """Get the holdings of the given account name.

    Args:
        name: The name of the account holder
    """
    # Retrieve the Account object for the given name and return its holdings dictionary
    return Account.get(name).holdings

@mcp.tool()
async def buy_shares(name: str, symbol: str, quantity: int, rationale: str) -> float:
    """Buy shares of a stock.

    Args:
        name: The name of the account holder
        symbol: The symbol of the stock
        quantity: The quantity of shares to buy
        rationale: The rationale for the purchase and fit with the account's strategy
    """
    # Call the buy_shares method on the Account object for the given name, passing symbol, quantity, and rationale
    return Account.get(name).buy_shares(symbol, quantity, rationale)


@mcp.tool()
async def sell_shares(name: str, symbol: str, quantity: int, rationale: str) -> float:
    """Sell shares of a stock.

    Args:
        name: The name of the account holder
        symbol: The symbol of the stock
        quantity: The quantity of shares to sell
        rationale: The rationale for the sale and fit with the account's strategy
    """
    # Call the sell_shares method on the Account object for the given name, passing symbol, quantity, and rationale
    return Account.get(name).sell_shares(symbol, quantity, rationale)

@mcp.tool()
async def change_strategy(name: str, strategy: str) -> str:
    """At your discretion, if you choose to, call this to change your investment strategy for the future.

    Args:
        name: The name of the account holder
        strategy: The new strategy for the account
    """
    # Call the change_strategy method on the Account object for the given name, passing the new strategy
    return Account.get(name).change_strategy(strategy)

# The following decorator registers the function as an MCP (Multi-Channel Protocol) resource endpoint.
# This means that when a client requests the resource URI pattern "accounts://accounts_server/{name}",
# the decorated function (read_account_resource) will be invoked with the 'name' parameter extracted from the URI.
# The purpose of this resource is to provide access to a report of the specified account, allowing clients
# to retrieve detailed information about an account by its name via the MCP protocol.
@mcp.resource("accounts://accounts_server/{name}")
async def read_account_resource(name: str) -> str:
    # Retrieve the Account object for the given name (converted to lowercase)
    account = Account.get(name.lower())
    # Return a report string for the account
    return account.report()

@mcp.resource("accounts://strategy/{name}")
async def read_strategy_resource(name: str) -> str:
    # Retrieve the Account object for the given name (converted to lowercase)
    account = Account.get(name.lower())
    # Return the strategy string for the account
    return account.get_strategy()

if __name__ == "__main__":
    mcp.run(transport='stdio')  # If this script is run directly, start the MCP server using stdio transport