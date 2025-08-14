import csv
import os
import json
from flask import Flask, jsonify, request, render_template_string
from datetime import datetime

# Initialize the Flask application
app = Flask(__name__)

# --- Data Persistence ---
FILENAME = "transactions.csv"
FIELDNAMES = ['id', 'date', 'type', 'category', 'amount']

def initialize_file():
    """Creates the CSV file with a header if it doesn't exist."""
    if not os.path.exists(FILENAME):
        with open(FILENAME, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()

def load_transactions():
    """Loads all transactions from the CSV file."""
    initialize_file()
    with open(FILENAME, mode='r', newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def save_transactions(transactions):
    """Saves a list of transactions to the CSV file."""
    with open(FILENAME, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(transactions)

# --- HTML & JavaScript Front-End ---
# We are embedding the HTML, CSS, and JS in a single file for simplicity.
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Personal Finance Tracker</title>
    <!-- Tailwind CSS for styling -->
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* Simple style for better readability on smaller screens */
        body { font-family: 'Inter', sans-serif; }
        .table-cell { padding: 0.75rem; }
    </style>
</head>
<body class="bg-gray-100 text-gray-800">

    <div class="container mx-auto p-4 md:p-8 max-w-4xl">
        <header class="text-center mb-8">
            <h1 class="text-4xl font-bold text-gray-900">Personal Finance Tracker</h1>
            <p class="text-gray-600 mt-2">A simple way to manage your income and expenses.</p>
        </header>

        <main class="grid grid-cols-1 md:grid-cols-3 gap-8">
            
            <!-- Add Transaction Form -->
            <div class="md:col-span-1 bg-white p-6 rounded-lg shadow-md">
                <h2 class="text-2xl font-semibold mb-4 border-b pb-2">Add Transaction</h2>
                <form id="transaction-form">
                    <div class="mb-4">
                        <label for="type" class="block text-sm font-medium text-gray-700 mb-1">Type</label>
                        <select id="type" name="type" required class="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500">
                            <option value="income">Income</option>
                            <option value="expense">Expense</option>
                        </select>
                    </div>
                    <div class="mb-4">
                        <label for="category" class="block text-sm font-medium text-gray-700 mb-1">Category</label>
                        <input type="text" id="category" name="category" required placeholder="e.g., Salary, Groceries" class="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500">
                    </div>
                    <div class="mb-4">
                        <label for="amount" class="block text-sm font-medium text-gray-700 mb-1">Amount</label>
                        <input type="number" id="amount" name="amount" required step="0.01" min="0.01" placeholder="e.g., 50.99" class="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500">
                    </div>
                    <button type="submit" class="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition duration-150 ease-in-out">
                        Add Transaction
                    </button>
                </form>
            </div>

            <!-- Transactions List & Summary -->
            <div class="md:col-span-2 bg-white p-6 rounded-lg shadow-md">
                <!-- Summary Section -->
                <div id="summary" class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6 text-center">
                    <div class="bg-green-100 p-4 rounded-lg">
                        <h3 class="text-sm font-medium text-green-800">Total Income</h3>
                        <p id="total-income" class="text-2xl font-bold text-green-900">$0.00</p>
                    </div>
                    <div class="bg-red-100 p-4 rounded-lg">
                        <h3 class="text-sm font-medium text-red-800">Total Expenses</h3>
                        <p id="total-expenses" class="text-2xl font-bold text-red-900">$0.00</p>
                    </div>
                    <div class="bg-blue-100 p-4 rounded-lg">
                        <h3 class="text-sm font-medium text-blue-800">Net Balance</h3>
                        <p id="net-balance" class="text-2xl font-bold text-blue-900">$0.00</p>
                    </div>
                </div>
                
                <!-- Transactions Table -->
                <h2 class="text-2xl font-semibold mb-4 border-b pb-2">History</h2>
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="table-cell text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                                <th class="table-cell text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                                <th class="table-cell text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                                <th class="table-cell text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                                <th class="table-cell text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
                            </tr>
                        </thead>
                        <tbody id="transaction-list" class="bg-white divide-y divide-gray-200">
                            <!-- JS will populate this section -->
                            <tr><td colspan="5" class="text-center py-4 text-gray-500">Loading transactions...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </main>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const form = document.getElementById('transaction-form');
            const transactionList = document.getElementById('transaction-list');
            
            // --- Fetch and Display Data ---
            const fetchAndDisplayTransactions = async () => {
                try {
                    const response = await fetch('/api/transactions');
                    const transactions = await response.json();
                    
                    displayTransactions(transactions);
                    displaySummary(transactions);
                } catch (error) {
                    console.error('Error fetching transactions:', error);
                    transactionList.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-red-500">Failed to load data.</td></tr>';
                }
            };
            
            const displayTransactions = (transactions) => {
                transactionList.innerHTML = ''; // Clear current list
                if (transactions.length === 0) {
                    transactionList.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-gray-500">No transactions yet.</td></tr>';
                    return;
                }
                
                transactions.slice().reverse().forEach(t => {
                    const row = document.createElement('tr');
                    const amountColor = t.type === 'income' ? 'text-green-600' : 'text-red-600';
                    
                    row.innerHTML = `
                        <td class="table-cell whitespace-nowrap">${t.date}</td>
                        <td class="table-cell whitespace-nowrap"><span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${t.type === 'income' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">${t.type}</span></td>
                        <td class="table-cell whitespace-nowrap">${t.category}</td>
                        <td class="table-cell whitespace-nowrap text-right font-medium ${amountColor}">$${parseFloat(t.amount).toFixed(2)}</td>
                        <td class="table-cell text-center"><button onclick="deleteTransaction('${t.id}')" class="text-red-500 hover:text-red-700 text-xs">Delete</button></td>
                    `;
                    transactionList.appendChild(row);
                });
            };

            const displaySummary = (transactions) => {
                const totalIncome = transactions.filter(t => t.type === 'income').reduce((sum, t) => sum + parseFloat(t.amount), 0);
                const totalExpenses = transactions.filter(t => t.type === 'expense').reduce((sum, t) => sum + parseFloat(t.amount), 0);
                const netBalance = totalIncome - totalExpenses;

                document.getElementById('total-income').textContent = `$${totalIncome.toFixed(2)}`;
                document.getElementById('total-expenses').textContent = `$${totalExpenses.toFixed(2)}`;
                document.getElementById('net-balance').textContent = `$${netBalance.toFixed(2)}`;
            };

            // --- Form Submission ---
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = {
                    type: document.getElementById('type').value,
                    category: document.getElementById('category').value,
                    amount: parseFloat(document.getElementById('amount').value)
                };

                try {
                    const response = await fetch('/api/transactions', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(formData)
                    });

                    if (response.ok) {
                        form.reset();
                        fetchAndDisplayTransactions();
                    } else {
                        alert('Failed to add transaction.');
                    }
                } catch (error) {
                    console.error('Error submitting form:', error);
                    alert('An error occurred.');
                }
            });
            
            // --- Delete Transaction ---
            window.deleteTransaction = async (id) => {
                if (!confirm('Are you sure you want to delete this transaction?')) {
                    return;
                }
                try {
                    const response = await fetch(`/api/transactions/${id}`, { method: 'DELETE' });
                    if (response.ok) {
                        fetchAndDisplayTransactions();
                    } else {
                        alert('Failed to delete transaction.');
                    }
                } catch (error) {
                    console.error('Error deleting transaction:', error);
                    alert('An error occurred while deleting.');
                }
            };

            // Initial load
            fetchAndDisplayTransactions();
        });
    </script>
</body>
</html>
"""

# --- Flask API Endpoints ---

@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """API endpoint to get all transactions."""
    transactions = load_transactions()
    return jsonify(transactions)

@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    """API endpoint to add a new transaction."""
    data = request.json
    transactions = load_transactions()

    new_transaction = {
        'id': datetime.now().strftime('%Y%m%d%H%M%S%f'), # Unique ID based on timestamp
        'date': datetime.now().strftime('%Y-%m-%d'),
        'type': data['type'],
        'category': data['category'],
        'amount': data['amount']
    }
    
    transactions.append(new_transaction)
    save_transactions(transactions)
    
    return jsonify({'status': 'success', 'transaction': new_transaction}), 201

@app.route('/api/transactions/<transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    """API endpoint to delete a transaction by its ID."""
    transactions = load_transactions()
    
    # Find the transaction to delete
    transaction_to_delete = next((t for t in transactions if t['id'] == transaction_id), None)
    
    if not transaction_to_delete:
        return jsonify({'status': 'error', 'message': 'Transaction not found'}), 404
        
    # Create a new list without the deleted transaction
    updated_transactions = [t for t in transactions if t['id'] != transaction_id]
    
    save_transactions(updated_transactions)
    
    return jsonify({'status': 'success', 'message': 'Transaction deleted'})

# --- Main execution ---
if __name__ == '__main__':
    # Using debug=True will auto-reload the server when you make changes
    app.run(debug=True)
