def get_share_price(symbol: str) -> float:
    """Returns the current price for the specified share symbol.
    
    Test implementation returns fixed prices for AAPL, TSLA, GOOGL.
    
    Args:
        symbol: The stock symbol to get the price for
        
    Returns:
        The current price of the specified stock
    """
    prices = {
        'AAPL': 150.0,
        'TSLA': 800.0,
        'GOOGL': 2500.0
    }
    
    return prices.get(symbol, 0.0)  # Return 0.0 for unknown symbols

class Account:
    """A class representing a user account in a trading simulation platform."""
    
    def __init__(self, username: str, initial_balance: float) -> None:
        """Initializes a new account with a username and an initial balance.
        
        Args:
            username: The name of the account holder
            initial_balance: The initial amount of money deposited in the account
        """
        if initial_balance < 0:
            raise ValueError("Initial balance cannot be negative")
            
        self.username = username
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.holdings = {}
        self.transactions = []
        
        # Record the initial deposit as a transaction
        self.transactions.append({
            'type': 'DEPOSIT',
            'amount': initial_balance,
            'balance_after': initial_balance,
            'timestamp': 'INITIAL'
        })
        
    def deposit(self, amount: float) -> None:
        """Adds the specified amount to the account balance.
        
        Args:
            amount: The amount to deposit
            
        Raises:
            ValueError: If the amount is negative
        """
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
            
        self.balance += amount
        
        # Record the transaction
        self.transactions.append({
            'type': 'DEPOSIT',
            'amount': amount,
            'balance_after': self.balance,
            'timestamp': 'NOW'  # In a real implementation, this would be a timestamp
        })
        
    def withdraw(self, amount: float) -> bool:
        """Attempts to withdraw the specified amount from the account.
        
        Args:
            amount: The amount to withdraw
            
        Returns:
            True if the withdrawal was successful, False otherwise
            
        Raises:
            ValueError: If the amount is negative
        """
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
            
        if amount > self.balance:
            return False
            
        self.balance -= amount
        
        # Record the transaction
        self.transactions.append({
            'type': 'WITHDRAWAL',
            'amount': amount,
            'balance_after': self.balance,
            'timestamp': 'NOW'  # In a real implementation, this would be a timestamp
        })
        
        return True
        
    def buy_shares(self, symbol: str, quantity: int) -> bool:
        """Attempts to buy the specified quantity of shares at the current share price.
        
        Args:
            symbol: The stock symbol to buy
            quantity: The number of shares to buy
            
        Returns:
            True if the purchase was successful, False otherwise
            
        Raises:
            ValueError: If the quantity is negative or zero
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
            
        price = get_share_price(symbol)
        total_cost = price * quantity
        
        if total_cost > self.balance:
            return False
            
        self.balance -= total_cost
        
        # Update holdings
        if symbol in self.holdings:
            self.holdings[symbol] += quantity
        else:
            self.holdings[symbol] = quantity
            
        # Record the transaction
        self.transactions.append({
            'type': 'BUY',
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'total': total_cost,
            'balance_after': self.balance,
            'timestamp': 'NOW'  # In a real implementation, this would be a timestamp
        })
        
        return True
        
    def sell_shares(self, symbol: str, quantity: int) -> bool:
        """Attempts to sell the specified quantity of shares.
        
        Args:
            symbol: The stock symbol to sell
            quantity: The number of shares to sell
            
        Returns:
            True if the sale was successful, False otherwise
            
        Raises:
            ValueError: If the quantity is negative or zero
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
            
        if symbol not in self.holdings or self.holdings[symbol] < quantity:
            return False
            
        price = get_share_price(symbol)
        total_value = price * quantity
        
        self.balance += total_value
        self.holdings[symbol] -= quantity
        
        # Remove the symbol from holdings if quantity becomes zero
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]
            
        # Record the transaction
        self.transactions.append({
            'type': 'SELL',
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'total': total_value,
            'balance_after': self.balance,
            'timestamp': 'NOW'  # In a real implementation, this would be a timestamp
        })
        
        return True
        
    def calculate_portfolio_value(self) -> float:
        """Calculates and returns the total value of the user's portfolio based on current share prices.
        
        Returns:
            The total value of the portfolio
        """
        total_value = 0.0
        
        for symbol, quantity in self.holdings.items():
            price = get_share_price(symbol)
            total_value += price * quantity
            
        return total_value
        
    def calculate_profit_or_loss(self) -> float:
        """Calculates and returns the profit or loss from the initial deposit.
        
        Returns:
            The profit or loss amount
        """
        portfolio_value = self.calculate_portfolio_value()
        current_total = portfolio_value + self.balance
        
        return current_total - self.initial_balance
        
    def get_holdings(self) -> dict:
        """Returns a dictionary of the user's current share holdings.
        
        Returns:
            A dictionary mapping stock symbols to quantities
        """
        return self.holdings.copy()
        
    def get_transactions(self) -> list:
        """Returns a list of all transactions the user has made.
        
        Returns:
            A list of transaction dictionaries
        """
        return self.transactions.copy()