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
HABITS_FILE = 'habits.json'
WATER_FILE = 'water.json'
NOTES_FILE = 'notes.json'

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

def load_habits():
    if os.path.exists(HABITS_FILE):
        with open(HABITS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_habits(habits):
    with open(HABITS_FILE, 'w') as f:
        json.dump(habits, f)

def load_water():
    if os.path.exists(WATER_FILE):
        with open(WATER_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_water(water_data):
    with open(WATER_FILE, 'w') as f:
        json.dump(water_data, f)
        
def load_notes():
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_notes(notes):
    with open(NOTES_FILE, 'w') as f:
        json.dump(notes, f)

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
        return render_template('main_dashboard.html')
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
        weight = request.form.get('weight')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')
        
        # Validate weight
        try:
            weight = float(weight)
            if weight < 30 or weight > 300:
                flash('Please enter a valid weight between 30 and 300 kg', 'error')
                return render_template('signup.html')
        except ValueError:
            flash('Please enter a valid weight', 'error')
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
            'weight': weight,
            'created_at': datetime.now().isoformat()
        }
        
        users.append(new_user)
        save_users(users)
        
        # Calculate water goal based on weight (weight in kg * 0.033 = liters, convert to ml)
        water_goal = int(weight * 0.033 * 1000)
        
        # Initialize water data for the new user
        water_data = load_water()
        water_data[new_user['id']] = {
            'goal': water_goal,
            'current': 0,
            'history': [],
            'last_update_date': datetime.now().strftime('%Y-%m-%d')
        }
        save_water(water_data)
        
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
        weight = request.form.get('weight')
        
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
        
        # Handle weight update
        if weight:
            try:
                weight_value = float(weight)
                if weight_value < 30 or weight_value > 300:
                    flash('Please enter a valid weight between 30 and 300 kg', 'error')
                else:
                    old_weight = user.get('weight', 70)
                    user['weight'] = weight_value
                    
                    # Update water goal based on new weight
                    if old_weight != weight_value:
                        water_data = load_water()
                        if user['id'] in water_data:
                            water_goal = int(weight_value * 0.033 * 1000)
                            water_data[user['id']]['goal'] = water_goal
                            save_water(water_data)
                            flash(f'Weight updated and daily water goal adjusted to {water_goal} ml', 'success')
                        else:
                            flash('Weight updated successfully', 'success')
            except ValueError:
                flash('Please enter a valid weight', 'error')
        
        save_users(users)
    
    return render_template('profile.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

# Expense routes
@app.route('/expenses')
@login_required
def expenses_page():
    return render_template('expenses.html')

@app.route('/expenses/data', methods=['GET'])
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
    
    # Handle transaction type (expense or income)
    transaction_type = data.get('type', 'expense')
    # For income, store the amount as a negative value to differentiate
    amount = float(data['amount'])
    if transaction_type == 'income':
        amount = -amount  # Store income as negative to differentiate from expenses
    
    new_expense = {
        'id': str(uuid.uuid4()),
        'user_id': session['user_id'],
        'description': data['description'],
        'amount': amount,
        'category': data.get('category', 'Uncategorized'),
        'date': data.get('date', datetime.now().isoformat()),
        'type': transaction_type
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

# Habit routes
@app.route('/habits')
@login_required
def habits_page():
    return render_template('habits.html')

@app.route('/habits/data', methods=['GET'])
@login_required
def get_habits():
    habits = load_habits()
    user_habits = [habit for habit in habits if habit.get('user_id') == session['user_id']]
    return jsonify(user_habits)

@app.route('/habits/add', methods=['POST'])
@login_required
def add_habit():
    data = request.get_json()
    
    if not data or 'name' not in data or 'category' not in data or 'frequency' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    habits = load_habits()
    
    new_habit = {
        'id': str(uuid.uuid4()),
        'user_id': session['user_id'],
        'name': data['name'],
        'category': data['category'],
        'frequency': data['frequency'],
        'created_at': datetime.now().isoformat(),
        'completedDates': [],
        'streak': 0
    }
    
    habits.append(new_habit)
    save_habits(habits)
    
    return jsonify(new_habit), 201

@app.route('/habits/<habit_id>/toggle', methods=['POST'])
@login_required
def toggle_habit(habit_id):
    habits = load_habits()
    today = datetime.now().strftime('%Y-%m-%d')
    
    for habit in habits:
        if habit.get('id') == habit_id and habit.get('user_id') == session['user_id']:
            if 'completedDates' not in habit:
                habit['completedDates'] = []
            
            if today in habit['completedDates']:
                habit['completedDates'].remove(today)
                # Decrease streak if it was completed today
                if habit.get('streak', 0) > 0:
                    habit['streak'] -= 1
            else:
                habit['completedDates'].append(today)
                # Increase streak
                habit['streak'] = habit.get('streak', 0) + 1
            
            save_habits(habits)
            return jsonify(habit)
    
    return jsonify({'error': 'Habit not found or unauthorized'}), 404

@app.route('/habits/<habit_id>', methods=['DELETE'])
@login_required
def delete_habit(habit_id):
    habits = load_habits()
    
    for i, habit in enumerate(habits):
        if habit.get('id') == habit_id and habit.get('user_id') == session['user_id']:
            del habits[i]
            save_habits(habits)
            return jsonify({'message': 'Habit deleted successfully'})
    
    return jsonify({'error': 'Habit not found or unauthorized'}), 404

# Water tracker routes
@app.route('/water')
@login_required
def water_page():
    return render_template('water.html')

@app.route('/water/data', methods=['GET'])
@login_required
def get_water_data():
    water_data = load_water()
    user_id = session['user_id']
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get user data to access weight
    users = load_users()
    current_user = next((user for user in users if user['id'] == user_id), None)
    
    if user_id not in water_data:
        # Calculate water goal based on weight if available
        water_goal = 2000  # Default goal in ml
        if current_user and 'weight' in current_user:
            water_goal = int(float(current_user['weight']) * 0.033 * 1000)
        
        water_data[user_id] = {
            'goal': water_goal,
            'current': 0,
            'history': [],
            'last_update_date': today
        }
        save_water(water_data)
    else:
        # Update goal if user weight has changed
        if current_user and 'weight' in current_user:
            calculated_goal = int(float(current_user['weight']) * 0.033 * 1000)
            if water_data[user_id]['goal'] != calculated_goal:
                water_data[user_id]['goal'] = calculated_goal
                save_water(water_data)
    
    # Check if it's a new day and reset water count if needed
    if water_data[user_id].get('last_update_date') != today:
        water_data[user_id]['current'] = 0
        water_data[user_id]['last_update_date'] = today
        save_water(water_data)
    
    return jsonify(water_data[user_id])

@app.route('/water/update', methods=['POST'])
@login_required
def update_water():
    data = request.get_json()
    
    if not data or 'amount' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    water_data = load_water()
    user_id = session['user_id']
    today = datetime.now().strftime('%Y-%m-%d')
    
    if user_id not in water_data:
        water_data[user_id] = {
            'goal': 2000,  # Default goal in ml
            'current': 0,
            'history': [],
            'last_update_date': today
        }
    
    # Check if it's a new day and reset water count if needed
    if water_data[user_id].get('last_update_date') != today:
        water_data[user_id]['current'] = 0
        # Don't update with the old amount if it's a new day
        water_data[user_id]['last_update_date'] = today
    
    water_data[user_id]['current'] = int(data['amount'])
    water_data[user_id]['last_update_date'] = today
    
    # Update history
    history_entry = next((entry for entry in water_data[user_id]['history'] if entry['date'] == today), None)
    
    if history_entry:
        history_entry['amount'] = water_data[user_id]['current']
    else:
        water_data[user_id]['history'].append({
            'date': today,
            'amount': water_data[user_id]['current']
        })
    
    save_water(water_data)
    
    return jsonify(water_data[user_id])

@app.route('/water/goal', methods=['POST'])
@login_required
def update_water_goal():
    data = request.get_json()
    
    if not data or 'goal' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    water_data = load_water()
    user_id = session['user_id']
    today = datetime.now().strftime('%Y-%m-%d')
    
    if user_id not in water_data:
        water_data[user_id] = {
            'goal': 2000,
            'current': 0,
            'history': [],
            'last_update_date': today
        }
    
    # Check if it's a new day and reset water count if needed
    if water_data[user_id].get('last_update_date') != today:
        water_data[user_id]['current'] = 0
        water_data[user_id]['last_update_date'] = today
    
    water_data[user_id]['goal'] = int(data['goal'])
    save_water(water_data)
    
    return jsonify(water_data[user_id])

# Notes routes
@app.route('/notes')
@login_required
def notes_page():
    return render_template('notes.html')

@app.route('/notes/data', methods=['GET'])
@login_required
def get_notes():
    notes = load_notes()
    user_notes = [note for note in notes if note.get('user_id') == session['user_id']]
    return jsonify(user_notes)

@app.route('/notes/add', methods=['POST'])
@login_required
def add_note():
    data = request.get_json()
    
    if not data or 'content' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    notes = load_notes()
    
    new_note = {
        'id': str(uuid.uuid4()),
        'user_id': session['user_id'],
        'content': data['content'],
        'title': data.get('title', 'Untitled Note'),
        'color': data.get('color', '#f9ca24'),
        'position': data.get('position', {'x': 0, 'y': 0}),
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    notes.append(new_note)
    save_notes(notes)
    
    return jsonify(new_note), 201

@app.route('/notes/<note_id>', methods=['PUT'])
@login_required
def update_note(note_id):
    data = request.get_json()
    notes = load_notes()
    
    for note in notes:
        if note.get('id') == note_id and note.get('user_id') == session['user_id']:
            if 'content' in data:
                note['content'] = data['content']
            if 'title' in data:
                note['title'] = data['title']
            if 'color' in data:
                note['color'] = data['color']
            if 'position' in data:
                note['position'] = data['position']
            
            note['updated_at'] = datetime.now().isoformat()
            save_notes(notes)
            return jsonify(note)
    
    return jsonify({'error': 'Note not found or unauthorized'}), 404

@app.route('/notes/<note_id>', methods=['DELETE'])
@login_required
def delete_note(note_id):
    notes = load_notes()
    
    for i, note in enumerate(notes):
        if note.get('id') == note_id and note.get('user_id') == session['user_id']:
            del notes[i]
            save_notes(notes)
            return jsonify({'message': 'Note deleted successfully'})
    
    return jsonify({'error': 'Note not found or unauthorized'}), 404

if __name__ == '__main__':
    app.run(debug=True)
