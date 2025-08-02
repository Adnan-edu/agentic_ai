import unittest
from accounts import Account, get_share_price

class TestGetSharePrice(unittest.TestCase):
    def test_known_symbols(self):
        self.assertEqual(get_share_price('AAPL'), 150.0)
        self.assertEqual(get_share_price('TSLA'), 800.0)
        self.assertEqual(get_share_price('GOOGL'), 2500.0)
        
    def test_unknown_symbol(self):
        self.assertEqual(get_share_price('UNKNOWN'), 0.0)

class TestAccount(unittest.TestCase):
    def setUp(self):
        self.account = Account('testuser', 10000.0)
        
    def test_initialization(self):
        self.assertEqual(self.account.username, 'testuser')
        self.assertEqual(self.account.initial_balance, 10000.0)
        self.assertEqual(self.account.balance, 10000.0)
        self.assertEqual(self.account.holdings, {})
        self.assertEqual(len(self.account.transactions), 1)
        
    def test_negative_initial_balance(self):
        with self.assertRaises(ValueError):
            Account('testuser', -100.0)
            
    def test_deposit(self):
        self.account.deposit(500.0)
        self.assertEqual(self.account.balance, 10500.0)
        self.assertEqual(len(self.account.transactions), 2)
        
    def test_invalid_deposit(self):
        with self.assertRaises(ValueError):
            self.account.deposit(-100.0)
            
    def test_withdraw_success(self):
        result = self.account.withdraw(1000.0)
        self.assertTrue(result)
        self.assertEqual(self.account.balance, 9000.0)
        self.assertEqual(len(self.account.transactions), 2)
        
    def test_withdraw_failure(self):
        result = self.account.withdraw(20000.0)
        self.assertFalse(result)
        self.assertEqual(self.account.balance, 10000.0)
        self.assertEqual(len(self.account.transactions), 1)
        
    def test_invalid_withdraw(self):
        with self.assertRaises(ValueError):
            self.account.withdraw(-100.0)
            
    def test_buy_shares_success(self):
        result = self.account.buy_shares('AAPL', 10)
        self.assertTrue(result)
        self.assertEqual(self.account.balance, 10000.0 - (150.0 * 10))
        self.assertEqual(self.account.holdings, {'AAPL': 10})
        self.assertEqual(len(self.account.transactions), 2)
        
    def test_buy_shares_failure(self):
        result = self.account.buy_shares('AAPL', 1000)
        self.assertFalse(result)
        self.assertEqual(self.account.balance, 10000.0)
        self.assertEqual(self.account.holdings, {})
        self.assertEqual(len(self.account.transactions), 1)
        
    def test_invalid_buy(self):
        with self.assertRaises(ValueError):
            self.account.buy_shares('AAPL', -10)
            
    def test_sell_shares_success(self):
        self.account.buy_shares('AAPL', 10)
        result = self.account.sell_shares('AAPL', 5)
        self.assertTrue(result)
        self.assertEqual(self.account.balance, 10000.0 - (150.0 * 10) + (150.0 * 5))
        self.assertEqual(self.account.holdings, {'AAPL': 5})
        self.assertEqual(len(self.account.transactions), 3)
        
    def test_sell_all_shares(self):
        self.account.buy_shares('AAPL', 10)
        result = self.account.sell_shares('AAPL', 10)
        self.assertTrue(result)
        self.assertEqual(self.account.balance, 10000.0)
        self.assertEqual(self.account.holdings, {})
        self.assertEqual(len(self.account.transactions), 3)
        
    def test_sell_shares_failure(self):
        result = self.account.sell_shares('AAPL', 5)
        self.assertFalse(result)
        self.assertEqual(self.account.balance, 10000.0)
        self.assertEqual(self.account.holdings, {})
        self.assertEqual(len(self.account.transactions), 1)
        
    def test_invalid_sell(self):
        with self.assertRaises(ValueError):
            self.account.sell_shares('AAPL', -5)
            
    def test_calculate_portfolio_value(self):
        self.account.buy_shares('AAPL', 10)
        self.account.buy_shares('TSLA', 5)
        expected_value = (150.0 * 10) + (800.0 * 5)
        self.assertEqual(self.account.calculate_portfolio_value(), expected_value)
        
    def test_calculate_profit_or_loss(self):
        self.account.buy_shares('AAPL', 10)
        portfolio_value = 150.0 * 10
        cash_balance = 10000.0 - (150.0 * 10)
        expected_profit = (portfolio_value + cash_balance) - 10000.0
        self.assertEqual(self.account.calculate_profit_or_loss(), expected_profit)
        
    def test_get_holdings(self):
        self.account.buy_shares('AAPL', 10)
        holdings = self.account.get_holdings()
        self.assertEqual(holdings, {'AAPL': 10})
        # Test that it's a copy
        holdings['AAPL'] = 5
        self.assertEqual(self.account.holdings, {'AAPL': 10})
        
    def test_get_transactions(self):
        transactions = self.account.get_transactions()
        self.assertEqual(len(transactions), 1)
        # Test that it's a copy
        transactions.append({'test': 'data'})
        self.assertEqual(len(self.account.transactions), 1)

if __name__ == '__main__':
    unittest.main()