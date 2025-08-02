import gradio as gr
from accounts import Account, get_share_price

# Initialize account with a default user
account = None

def create_account(username, initial_balance):
    global account
    try:
        initial_balance = float(initial_balance)
        account = Account(username, initial_balance)
        return f"Account created for {username} with initial balance of ${initial_balance:.2f}"
    except ValueError as e:
        return f"Error: {str(e)}"

def deposit_funds(amount):
    global account
    if account is None:
        return "Please create an account first"
    
    try:
        amount = float(amount)
        account.deposit(amount)
        return f"Deposited ${amount:.2f}. New balance: ${account.balance:.2f}"
    except ValueError as e:
        return f"Error: {str(e)}"

def withdraw_funds(amount):
    global account
    if account is None:
        return "Please create an account first"
    
    try:
        amount = float(amount)
        if account.withdraw(amount):
            return f"Withdrew ${amount:.2f}. New balance: ${account.balance:.2f}"
        else:
            return f"Insufficient funds. Current balance: ${account.balance:.2f}"
    except ValueError as e:
        return f"Error: {str(e)}"

def buy_shares(symbol, quantity):
    global account
    if account is None:
        return "Please create an account first"
    
    try:
        quantity = int(quantity)
        price = get_share_price(symbol)
        
        if price == 0.0:
            return f"Unknown symbol: {symbol}"
        
        if account.buy_shares(symbol, quantity):
            return f"Bought {quantity} shares of {symbol} at ${price:.2f} each. New balance: ${account.balance:.2f}"
        else:
            return f"Insufficient funds to buy {quantity} shares of {symbol} at ${price:.2f} each. Current balance: ${account.balance:.2f}"
    except ValueError as e:
        return f"Error: {str(e)}"

def sell_shares(symbol, quantity):
    global account
    if account is None:
        return "Please create an account first"
    
    try:
        quantity = int(quantity)
        price = get_share_price(symbol)
        
        if price == 0.0:
            return f"Unknown symbol: {symbol}"
        
        if account.sell_shares(symbol, quantity):
            return f"Sold {quantity} shares of {symbol} at ${price:.2f} each. New balance: ${account.balance:.2f}"
        else:
            holdings = account.get_holdings()
            current_quantity = holdings.get(symbol, 0)
            return f"Insufficient shares to sell. You have {current_quantity} shares of {symbol}."
    except ValueError as e:
        return f"Error: {str(e)}"

def get_portfolio_value():
    global account
    if account is None:
        return "Please create an account first"
    
    portfolio_value = account.calculate_portfolio_value()
    profit_loss = account.calculate_profit_or_loss()
    
    result = f"Current Cash Balance: ${account.balance:.2f}\n"
    result += f"Portfolio Value: ${portfolio_value:.2f}\n"
    result += f"Total Value: ${(account.balance + portfolio_value):.2f}\n"
    result += f"Profit/Loss: ${profit_loss:.2f}"
    
    if profit_loss > 0:
        result += " (Profit)"
    elif profit_loss < 0:
        result += " (Loss)"
    else:
        result += " (Break even)"
    
    return result

def get_current_holdings():
    global account
    if account is None:
        return "Please create an account first"
    
    holdings = account.get_holdings()
    
    if not holdings:
        return "No current holdings"
    
    result = "Current Holdings:\n"
    total_value = 0.0
    
    for symbol, quantity in holdings.items():
        price = get_share_price(symbol)
        value = price * quantity
        total_value += value
        result += f"{symbol}: {quantity} shares at ${price:.2f} = ${value:.2f}\n"
    
    result += f"\nTotal Holdings Value: ${total_value:.2f}"
    return result

def get_transaction_history():
    global account
    if account is None:
        return "Please create an account first"
    
    transactions = account.get_transactions()
    
    if not transactions:
        return "No transactions found"
    
    result = "Transaction History:\n"
    
    for i, t in enumerate(transactions):
        result += f"[{i+1}] {t['type']}: "
        
        if t['type'] == 'DEPOSIT':
            result += f"${t['amount']:.2f}, Balance: ${t['balance_after']:.2f}\n"
        elif t['type'] == 'WITHDRAWAL':
            result += f"${t['amount']:.2f}, Balance: ${t['balance_after']:.2f}\n"
        elif t['type'] in ['BUY', 'SELL']:
            result += f"{t['quantity']} {t['symbol']} at ${t['price']:.2f} (${t['total']:.2f}), Balance: ${t['balance_after']:.2f}\n"
    
    return result

def get_available_symbols():
    return "Available symbols for testing: AAPL ($150.00), TSLA ($800.00), GOOGL ($2500.00)"

# Create Gradio interface
with gr.Blocks(title="Trading Simulation Platform") as demo:
    gr.Markdown("# Trading Simulation Platform")
    
    with gr.Tab("Account Management"):
        with gr.Group():
            gr.Markdown("### Create Account")
            with gr.Row():
                username_input = gr.Textbox(label="Username")
                initial_balance_input = gr.Textbox(label="Initial Balance")
            create_account_btn = gr.Button("Create Account")
            create_account_output = gr.Textbox(label="Result")
            
            create_account_btn.click(
                create_account,
                inputs=[username_input, initial_balance_input],
                outputs=create_account_output
            )
        
        with gr.Group():
            gr.Markdown("### Deposit & Withdraw")
            with gr.Row():
                deposit_input = gr.Textbox(label="Deposit Amount")
                withdraw_input = gr.Textbox(label="Withdraw Amount")
            
            with gr.Row():
                deposit_btn = gr.Button("Deposit")
                withdraw_btn = gr.Button("Withdraw")
            
            funds_output = gr.Textbox(label="Result")
            
            deposit_btn.click(
                deposit_funds,
                inputs=deposit_input,
                outputs=funds_output
            )
            
            withdraw_btn.click(
                withdraw_funds,
                inputs=withdraw_input,
                outputs=funds_output
            )
    
    with gr.Tab("Trading"):
        gr.Markdown("### Buy & Sell Shares")
        available_symbols = gr.Textbox(label="Available Symbols", value=get_available_symbols())
        
        with gr.Row():
            symbol_input = gr.Textbox(label="Symbol")
            quantity_input = gr.Textbox(label="Quantity")
        
        with gr.Row():
            buy_btn = gr.Button("Buy Shares")
            sell_btn = gr.Button("Sell Shares")
        
        trading_output = gr.Textbox(label="Result")
        
        buy_btn.click(
            buy_shares,
            inputs=[symbol_input, quantity_input],
            outputs=trading_output
        )
        
        sell_btn.click(
            sell_shares,
            inputs=[symbol_input, quantity_input],
            outputs=trading_output
        )
    
    with gr.Tab("Portfolio"):
        with gr.Row():
            portfolio_btn = gr.Button("Get Portfolio Value")
            holdings_btn = gr.Button("Get Current Holdings")
            transactions_btn = gr.Button("Get Transaction History")
        
        portfolio_output = gr.Textbox(label="Portfolio Information", lines=10)
        
        portfolio_btn.click(
            get_portfolio_value,
            inputs=[],
            outputs=portfolio_output
        )
        
        holdings_btn.click(
            get_current_holdings,
            inputs=[],
            outputs=portfolio_output
        )
        
        transactions_btn.click(
            get_transaction_history,
            inputs=[],
            outputs=portfolio_output
        )

# Launch the app
if __name__ == "__main__":
    demo.launch()