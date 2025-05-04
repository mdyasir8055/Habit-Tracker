from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import json
import os
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a random secret key in production

# File paths
USERS_FILE = 'users.json'
EXPENSES_FILE = 'expenses.json'

# Helper functions
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def load_expenses():
    if os.path.exists(EXPENSES_FILE):
        with open(EXPENSES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_expenses(expenses):
    with open(EXPENSES_FILE, 'w') as f:
        json.dump(expenses, f)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def home():
    if 'user_id' in session:
        return render_template('dashboard.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        users = load_users()
        user = next((user for user in users if user['email'] == email), None)
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        
        flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')
        
        users = load_users()
        
        # Check if email already exists
        if any(user['email'] == email for user in users):
            flash('Email already registered', 'error')
            return render_template('signup.html')
        
        # Create new user
        new_user = {
            'id': str(uuid.uuid4()),
            'username': username,
            'email': email,
            'password': generate_password_hash(password),
            'created_at': datetime.now().isoformat()
        }
        
        users.append(new_user)
        save_users(users)
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        users = load_users()
        
        user = next((user for user in users if user['email'] == email), None)
        
        if user:
            # In a real application, you would send a password reset email here
            flash('Password reset instructions sent to your email', 'success')
            return redirect(url_for('login'))
        
        flash('Email not found', 'error')
    
    return render_template('forgot_password.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    users = load_users()
    user = next((user for user in users if user['id'] == session['user_id']), None)
    
    if request.method == 'POST':
        username = request.form.get('username')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        
        if current_password and new_password:
            if check_password_hash(user['password'], current_password):
                user['password'] = generate_password_hash(new_password)
                flash('Password updated successfully', 'success')
            else:
                flash('Current password is incorrect', 'error')
        
        if username and username != user['username']:
            user['username'] = username
            session['username'] = username
            flash('Username updated successfully', 'success')
        
        save_users(users)
    
    return render_template('profile.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

# Expense routes
@app.route('/expenses', methods=['GET'])
@login_required
def get_expenses():
    expenses = load_expenses()
    user_expenses = [expense for expense in expenses if expense.get('user_id') == session['user_id']]
    return jsonify(user_expenses)

@app.route('/expenses/add', methods=['POST'])
@login_required
def add_expense():
    data = request.get_json()
    
    if not data or 'description' not in data or 'amount' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    expenses = load_expenses()
    
    new_expense = {
        'id': str(uuid.uuid4()),
        'user_id': session['user_id'],
        'description': data['description'],
        'amount': float(data['amount']),
        'category': data.get('category', 'Uncategorized'),
        'date': data.get('date', datetime.now().isoformat())
    }
    
    expenses.append(new_expense)
    save_expenses(expenses)
    
    return jsonify(new_expense), 201

@app.route('/expenses/<expense_id>', methods=['PUT'])
@login_required
def update_expense(expense_id):
    data = request.get_json()
    expenses = load_expenses()
    
    for expense in expenses:
        if expense.get('id') == expense_id and expense.get('user_id') == session['user_id']:
            if 'description' in data:
                expense['description'] = data['description']
            if 'amount' in data:
                expense['amount'] = float(data['amount'])
            if 'category' in data:
                expense['category'] = data['category']
            if 'date' in data:
                expense['date'] = data['date']
            
            save_expenses(expenses)
            return jsonify(expense)
    
    return jsonify({'error': 'Expense not found or unauthorized'}), 404

@app.route('/expenses/<expense_id>', methods=['DELETE'])
@login_required
def delete_expense(expense_id):
    expenses = load_expenses()
    
    for i, expense in enumerate(expenses):
        if expense.get('id') == expense_id and expense.get('user_id') == session['user_id']:
            del expenses[i]
            save_expenses(expenses)
            return jsonify({'message': 'Expense deleted successfully'})
    
    return jsonify({'error': 'Expense not found or unauthorized'}), 404

if __name__ == '__main__':
    app.run(debug=True)
