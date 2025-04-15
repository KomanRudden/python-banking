import time
from datetime import datetime, timedelta

class MockAccount:
    def __init__(self, account_id, balance):
        self.account_id = account_id
        self.balance = balance

class Token:
    def __init__(self, access_token, expires_at):
        self.access_token = access_token
        self.expires_at = expires_at

class MockClient:
    def __init__(self):
        self.accounts = {
            "bankz-acc-123": MockAccount("bankz-acc-123", 1000.0),
            "bankz-acc-456": MockAccount("bankz-acc-456", 500.0),
        }
        self.client_id = "mock-client-id"
        self.client_secret = "mock-client-secret"
        self.token = None
        self.token_endpoint = "https://mock.bankz.com/oauth/token"

    def get_token(self):
        # Check if token exists and is valid
        if self.token and self.token.expires_at > datetime.utcnow():
            print(f"Using cached Bank Z token: {self.token.access_token}")  # Debug log
            return self.token.access_token

        # Simulate token request
        if self.client_id != "mock-client-id" or self.client_secret != "mock-client-secret":
            raise ValueError("Invalid client credentials")

        # Generate a new mock token
        token_id = f"token-{int(time.time_ns())}"
        self.token = Token(
            access_token=token_id,
            expires_at=datetime.utcnow() + timedelta(hours=1)  # Token valid for 1 hour
        )
        print(f"Generated new Bank Z token: {token_id}")  # Debug log
        return self.token.access_token

    def validate_token(self, token):
        if not self.token or self.token.access_token != token or self.token.expires_at <= datetime.utcnow():
            raise ValueError("Invalid or expired token")

    def get_balance(self, account_id, token):
        self.validate_token(token)
        account = self.accounts.get(account_id)
        if not account:
            raise ValueError(f"Bank Z account {account_id} not found")
        return account.balance

    def initiate_transfer(self, from_account_id, to_account_id, token, amount):
        self.validate_token(token)
        if amount <= 0:
            raise ValueError("Amount must be positive")
        # Only validate to_account_id as a Bank Z account
        to_account = self.accounts.get(to_account_id)
        if not to_account:
            raise ValueError(f"Destination Bank Z account {to_account_id} not found")
        # Simulate updating Bank Z account balance
        to_account.balance += amount
        transaction_id = f"bankz-tx-{int(time.time_ns())}"
        print(f"Bank Z transfer: from {from_account_id} to {to_account_id}, amount {amount}, txID {transaction_id}")  # Debug log
        return transaction_id