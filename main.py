from flask import Flask, request, jsonify
from flask_cors import CORS
from models import Customer, Account, Transaction
from store import global_store
from bankz import MockClient
import uuid
from datetime import datetime
import re

# Flask is a lightweight web application framework in Python. 
# Flask provides tools, libraries, and technologies to build web applications, including routing, request handling, and templating.
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
bankz_client = MockClient()  # Global client for simplicity

@app.route('/api/customers', methods=['POST'])
def create_customer():
    data = request.get_json()
    if not data or 'name' not in data or 'email' not in data:
        return jsonify({"errors": ["Invalid request body"]}), 400

    name = data['name']
    email = data['email']

    errors = []
    if not name:
        errors.append("Name cannot be empty")
    if name and not re.match(r'^[a-zA-Z\s]+$', name):
        errors.append("Name must contain only letters and spaces")
    if not email:
        errors.append("Email cannot be empty")
    if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        errors.append("Invalid email format")
    if errors:
        return jsonify({"errors": errors}), 400

    customer_id = str(uuid.uuid4())
    current_account_id = str(uuid.uuid4())
    savings_account_id = str(uuid.uuid4())
    bonus_transaction_id = str(uuid.uuid4())
    now = datetime.now()

    customer = Customer(
        id=customer_id,
        name=name,
        email=email
    )
    global_store.add_customer(customer)

    current_account = Account(
        id=current_account_id,
        customer_id=customer_id,
        type="current",
        balance=0.0,
        created_at=now
    )
    global_store.add_account(current_account)

    savings_account = Account(
        id=savings_account_id,
        customer_id=customer_id,
        type="savings",
        balance=500.0,
        created_at=now
    )
    global_store.add_account(savings_account)

    bonus_transaction = Transaction(
        id=bonus_transaction_id,
        account_id=savings_account_id,
        customer_id=customer_id,
        type="bonus",
        amount=500.0,
        created_at=now
    )
    global_store.add_transaction(bonus_transaction)

    response = {
        "customerId": customer_id,
        "currentAccountId": current_account_id,
        "savingsAccountId": savings_account_id
    }
    print(f"Created customer: {response}")  # Debug log
    return jsonify(response), 201

@app.route('/api/customers/<customer_id>/accounts', methods=['GET'])
def get_customer_accounts(customer_id):
    customer = global_store.get_customer_by_id(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    accounts = global_store.get_accounts_by_customer_id(customer_id)
    if not accounts:
        return jsonify({"error": "No accounts found for customer"}), 404

    response = {
        "customerId": customer_id,
        "accounts": [
            {
                "id": account.id,
                "customerId": account.customer_id,
                "type": account.type,
                "balance": account.balance,
                "createdAt": account.created_at.isoformat()
            } for account in accounts
        ]
    }
    print(f"Fetched accounts for customer {customer_id}: {[acc.id for acc in accounts]}")  # Debug log
    return jsonify(response), 200

@app.route('/api/customers/<customer_id>/transfers', methods=['POST'])
def transfer_money(customer_id):
    data = request.get_json()
    if not data or 'fromAccountId' not in data or 'toAccountId' not in data or 'amount' not in data:
        return jsonify({"errors": ["Invalid request body"]}), 400

    from_account_id = data['fromAccountId']
    to_account_id = data['toAccountId']
    amount = data['amount']

    errors = []
    if not from_account_id:
        errors.append("From account ID cannot be empty")
    if not to_account_id:
        errors.append("To account ID cannot be empty")
    if not isinstance(amount, (int, float)) or amount <= 0:
        errors.append("Amount must be positive")
    if from_account_id == to_account_id and from_account_id:
        errors.append("Cannot transfer to the same account")
    if errors:
        return jsonify({"errors": errors}), 400

    customer = global_store.get_customer_by_id(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    # Get OAuth token
    try:
        token = bankz_client.get_token()
    except ValueError as e:
        return jsonify({"error": "Failed to authenticate with Bank Z"}), 500

    # Check fromAccount
    from_account = global_store.get_account_by_id(from_account_id)
    print(f"Looking up fromAccountID {from_account_id}: found={from_account is not None}")  # Debug log
    if not from_account:
        return jsonify({"error": f"Source account {from_account_id} not found"}), 400
    if from_account.customer_id != customer_id:
        return jsonify({"error": "Source account does not belong to the customer"}), 400

    # Check toAccount
    is_external_transfer = False
    to_account = global_store.get_account_by_id(to_account_id)
    print(f"Looking up toAccountID {to_account_id}: found={to_account is not None}")  # Debug log
    if not to_account:
        try:
            bankz_client.get_balance(to_account_id, token)
            is_external_transfer = True
        except ValueError:
            return jsonify({"error": f"Destination account {to_account_id} not found"}), 400
    elif to_account.customer_id != customer_id:
        return jsonify({"error": "Destination account does not belong to the customer"}), 400

    if is_external_transfer:
        # Bank Z transfer
        if from_account.balance < amount:
            return jsonify({"error": "Insufficient funds"}), 400
        try:
            transaction_id = bankz_client.initiate_transfer(from_account_id, to_account_id, token, amount)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        # Update local account balance
        from_account.balance -= amount
        global_store.update_account(from_account)

        # Record transaction
        now = datetime.now()
        global_store.add_transaction(Transaction(
            id=transaction_id,
            account_id=from_account_id,
            customer_id=customer_id,
            type="bankz_transfer",
            amount=amount,
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            created_at=now
        ))

        response = {
            "transactionId": transaction_id,
            "status": "success"
        }
        print(f"Bank Z transfer successful: {response}")  # Debug log
        return jsonify(response), 201

    # Internal transfer
    fee = 0.0
    if from_account.type == "current":
        fee = amount * 0.0005

    total_deduction = amount + fee
    if from_account.balance < total_deduction:
        return jsonify({"error": "Insufficient funds"}), 400

    interest = 0.0
    if to_account.type == "savings":
        interest = amount * 0.005

    from_account.balance -= total_deduction
    to_account.balance += amount + interest
    global_store.update_account(from_account)
    global_store.update_account(to_account)

    now = datetime.now()
    transfer_transaction_id = str(uuid.uuid4())
    global_store.add_transaction(Transaction(
        id=transfer_transaction_id,
        account_id=from_account_id,
        customer_id=customer_id,
        type="transfer",
        amount=amount,
        from_account_id=from_account_id,
        to_account_id=to_account_id,
        created_at=now
    ))

    if fee > 0:
        fee_transaction_id = str(uuid.uuid4())
        global_store.add_transaction(Transaction(
            id=fee_transaction_id,
            account_id=from_account_id,
            customer_id=customer_id,
            type="fee",
            amount=fee,
            created_at=now
        ))

    if interest > 0:
        interest_transaction_id = str(uuid.uuid4())
        global_store.add_transaction(Transaction(
            id=interest_transaction_id,
            account_id=to_account_id,
            customer_id=customer_id,
            type="interest",
            amount=interest,
            created_at=now
        ))

    response = {
        "transactionId": transfer_transaction_id,
        "status": "success"
    }
    print(f"Internal transfer successful: {response}")  # Debug log
    return jsonify(response), 201

@app.route('/api/customers/<customer_id>/bankz/balances', methods=['GET'])
def get_bankz_balances(customer_id):
    customer = global_store.get_customer_by_id(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    try:
        token = bankz_client.get_token()
    except ValueError as e:
        return jsonify({"error": "Failed to authenticate with Bank Z"}), 500

    linked_account_ids = ["bankz-acc-123", "bankz-acc-456"]

    balances = []
    for account_id in linked_account_ids:
        try:
            balance = bankz_client.get_balance(account_id, token)
            balances.append({
                "accountId": account_id,
                "balance": balance
            })
        except ValueError:
            continue

    response = {
        "customerId": customer_id,
        "balances": balances
    }
    return jsonify(response), 200

@app.route('/api/customers/<customer_id>/transactions', methods=['GET'])
def get_customer_transactions(customer_id):
    customer = global_store.get_customer_by_id(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    # Get query parameters for filtering
    account_id = request.args.get('accountId')
    transaction_type = request.args.get('type')

    # Fetch transactions
    transactions = global_store.get_transactions_by_customer_id(customer_id)
    if not transactions:
        return jsonify({
            "customerId": customer_id,
            "transactions": []
        }), 200

    # Filter transactions
    filtered = [
        tx for tx in transactions
        if (not account_id or tx.account_id == account_id) and
           (not transaction_type or tx.type == transaction_type)
    ]

    # Convert to response format
    response_transactions = [
        {
            "id": tx.id,
            "accountId": tx.account_id,
            "customerId": tx.customer_id,
            "type": tx.type,
            "amount": tx.amount,
            "fromAccountId": tx.from_account_id or "",
            "toAccountId": tx.to_account_id or "",
            "createdAt": tx.created_at.isoformat()
        } for tx in filtered
    ]

    response = {
        "customerId": customer_id,
        "transactions": response_transactions
    }
    print(f"Fetched {len(response_transactions)} transactions for customer {customer_id}")  # Debug log
    return jsonify(response), 200

if __name__ == "__main__":
    print("Starting python-banking server on :8080...")
    app.run(host='0.0.0.0', port=8080, debug=True)