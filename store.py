from threading import Lock

class Store:
    def __init__(self):
        self.customers = {}
        self.accounts = {}
        self.transactions = {}
        self.lock = Lock()

    def add_customer(self, customer):
        with self.lock:
            self.customers[customer.id] = customer

    def get_customer_by_id(self, customer_id):
        with self.lock:
            return self.customers.get(customer_id)

    def add_account(self, account):
        with self.lock:
            self.accounts[account.id] = account

    def get_account_by_id(self, account_id):
        with self.lock:
            return self.accounts.get(account_id)

    def update_account(self, account):
        with self.lock:
            self.accounts[account.id] = account

    def get_accounts_by_customer_id(self, customer_id):
        with self.lock:
            return [account for account in self.accounts.values() if account.customer_id == customer_id]

    def add_transaction(self, transaction):
        with self.lock:
            self.transactions[transaction.id] = transaction

    def get_transactions_by_customer_id(self, customer_id):
        with self.lock:
            # Get all account IDs for the customer
            account_ids = {account.id for account in self.accounts.values() if account.customer_id == customer_id}
            # Return transactions for those accounts
            return [tx for tx in self.transactions.values() if tx.account_id in account_ids]

global_store = Store()