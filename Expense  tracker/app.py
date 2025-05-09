from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import json
import os
import uuid
import logging
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Set up Twilio for SMS reminders (we'll initialize the client later)
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logging.warning("Twilio package not installed. SMS reminders will be disabled.")

# Twilio configuration (replace with your actual credentials in production)
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', 'your_account_sid')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', 'your_auth_token')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '+1234567890')

# Initialize Twilio client if available
twilio_client = None
if TWILIO_AVAILABLE and TWILIO_ACCOUNT_SID != 'your_account_sid':
    try:
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    except Exception as e:
        logging.error(f"Failed to initialize Twilio client: {e}")
        TWILIO_AVAILABLE = False

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a random secret key in production

# File paths
USERS_FILE = 'users.json'
EXPENSES_FILE = 'expenses.json'
HABITS_FILE = 'habits.json'
WATER_FILE = 'water.json'
NOTES_FILE = 'notes.json'
FRIENDS_FILE = 'friends.json'

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

def load_friends():
    if os.path.exists(FRIENDS_FILE):
        with open(FRIENDS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_friends(friends):
    with open(FRIENDS_FILE, 'w') as f:
        json.dump(friends, f)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def send_sms_reminder(to_number, message):
    """Send an SMS reminder using Twilio"""
    if not TWILIO_AVAILABLE or not twilio_client:
        logging.warning("Twilio is not available. SMS not sent.")
        return False
    
    if not to_number:
        logging.warning("No phone number provided. SMS not sent.")
        return False
    
    try:
        message = twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_number
        )
        logging.info(f"SMS sent successfully: {message.sid}")
        return True
    except Exception as e:
        logging.error(f"Failed to send SMS: {e}")
        return False

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
        mobile = request.form.get('mobile')
        
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
            'mobile': mobile if mobile else None,
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
        mobile = request.form.get('mobile')
        
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
        
        # Handle mobile number update
        if mobile != user.get('mobile'):
            # Simple validation for mobile number format
            if mobile and not mobile.startswith('+'):
                flash('Mobile number should include country code (e.g., +1234567890)', 'error')
            else:
                user['mobile'] = mobile if mobile else None
                flash('Mobile number updated successfully', 'success')
        
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
    
    # Add activity for friends to see
    user_id = session['user_id']
    friends_data = load_friends()
    if user_id in friends_data and 'friends' in friends_data[user_id]:
        users = load_users()
        current_user = next((user for user in users if user['id'] == user_id), None)
        
        if current_user:
            # Don't show the exact amount for privacy
            activity_description = f"Added a new {transaction_type}: {data['description']} in {data.get('category', 'Uncategorized')}"
            
            # Add activity to each friend's feed
            for friend_id in friends_data[user_id]['friends']:
                if friend_id not in friends_data:
                    friends_data[friend_id] = {'friends': [], 'activities': []}
                
                if 'activities' not in friends_data[friend_id]:
                    friends_data[friend_id]['activities'] = []
                
                friends_data[friend_id]['activities'].append({
                    'username': current_user['username'],
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'description': activity_description
                })
            
            save_friends(friends_data)
    
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
    user_id = session['user_id']
    
    for habit in habits:
        if habit.get('id') == habit_id and habit.get('user_id') == user_id:
            if 'completedDates' not in habit:
                habit['completedDates'] = []
            
            completed = False
            if today in habit['completedDates']:
                habit['completedDates'].remove(today)
                # Decrease streak if it was completed today
                if habit.get('streak', 0) > 0:
                    habit['streak'] -= 1
            else:
                habit['completedDates'].append(today)
                # Increase streak
                habit['streak'] = habit.get('streak', 0) + 1
                completed = True
            
            save_habits(habits)
            
            # Add activity for friends to see
            friends_data = load_friends()
            if user_id in friends_data and 'friends' in friends_data[user_id]:
                users = load_users()
                current_user = next((user for user in users if user['id'] == user_id), None)
                
                if current_user:
                    activity_description = f"{'Completed' if completed else 'Uncompleted'} habit: {habit.get('name', 'Unknown')}"
                    
                    # Add activity to each friend's feed
                    for friend_id in friends_data[user_id]['friends']:
                        if friend_id not in friends_data:
                            friends_data[friend_id] = {'friends': [], 'activities': []}
                        
                        if 'activities' not in friends_data[friend_id]:
                            friends_data[friend_id]['activities'] = []
                        
                        friends_data[friend_id]['activities'].append({
                            'username': current_user['username'],
                            'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                            'description': activity_description
                        })
                    
                    save_friends(friends_data)
            
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
    
    old_amount = water_data[user_id]['current']
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
    
    # Add activity for friends to see if significant change (more than 250ml)
    if abs(water_data[user_id]['current'] - old_amount) >= 250:
        friends_data = load_friends()
        if user_id in friends_data and 'friends' in friends_data[user_id]:
            users = load_users()
            current_user = next((user for user in users if user['id'] == user_id), None)
            
            if current_user:
                # Calculate percentage of goal
                goal = water_data[user_id]['goal']
                current = water_data[user_id]['current']
                percentage = min(100, int((current / goal) * 100)) if goal > 0 else 0
                
                activity_description = f"Updated water intake to {current}ml ({percentage}% of daily goal)"
                
                # Add activity to each friend's feed
                for friend_id in friends_data[user_id]['friends']:
                    if friend_id not in friends_data:
                        friends_data[friend_id] = {'friends': [], 'activities': []}
                    
                    if 'activities' not in friends_data[friend_id]:
                        friends_data[friend_id]['activities'] = []
                    
                    # Add new activity
                    friends_data[friend_id]['activities'].append({
                        'username': current_user['username'],
                        'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'description': activity_description
                    })
                    
                    # Limit to most recent 50 activities
                    if len(friends_data[friend_id]['activities']) > 50:
                        friends_data[friend_id]['activities'] = sorted(
                            friends_data[friend_id]['activities'],
                            key=lambda x: x.get('time', ''),
                            reverse=True
                        )[:50]
                
                save_friends(friends_data)
    
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

@app.route('/water/send-reminder', methods=['POST'])
@login_required
def send_water_reminder():
    """Send an SMS reminder to drink water"""
    users = load_users()
    user = next((user for user in users if user['id'] == session['user_id']), None)
    
    if not user or not user.get('mobile'):
        return jsonify({'success': False, 'message': 'No mobile number found'}), 400
    
    water_data = load_water()
    user_id = session['user_id']
    
    if user_id not in water_data:
        return jsonify({'success': False, 'message': 'Water data not found'}), 404
    
    # Calculate remaining water needed
    current = water_data[user_id]['current']
    goal = water_data[user_id]['goal']
    remaining = max(0, goal - current)
    
    # Create a personalized message
    message = f"Hi {user['username']}! 💧 Time to hydrate! You've had {current}ml of water today. "
    
    if remaining > 0:
        message += f"You still need {remaining}ml to reach your daily goal of {goal}ml."
    else:
        message += f"Great job! You've reached your daily goal of {goal}ml."
    
    # Send the SMS
    success = send_sms_reminder(user['mobile'], message)
    
    if success:
        return jsonify({'success': True, 'message': 'Reminder sent successfully'})
    else:
        return jsonify({'success': False, 'message': 'Failed to send reminder'}), 500

# Community routes
@app.route('/community')
@login_required
def community_page():
    friends_data = load_friends()
    user_id = session['user_id']
    
    # Initialize friends data if not exists
    if user_id not in friends_data:
        friends_data[user_id] = {
            'friends': [],
            'activities': []
        }
        save_friends(friends_data)
    
    # Get user data for all friends
    users = load_users()
    water_data = load_water()
    habits_data = load_habits()
    
    friends = []
    for friend_id in friends_data[user_id]['friends']:
        friend = next((user for user in users if user['id'] == friend_id), None)
        if friend:
            # Get friend's habit streak
            habit_streak = 0
            for habit in habits_data:
                if habit.get('user_id') == friend_id:
                    habit_streak = max(habit_streak, habit.get('streak', 0))
            
            # Get friend's water percentage
            water_percentage = 0
            if friend_id in water_data:
                water_goal = water_data[friend_id].get('goal', 2000)
                water_current = water_data[friend_id].get('current', 0)
                water_percentage = min(100, int((water_current / water_goal) * 100)) if water_goal > 0 else 0
            
            friends.append({
                'id': friend_id,
                'username': friend['username'],
                'added_at': friends_data[user_id].get('added_dates', {}).get(friend_id, 'Unknown'),
                'habit_streak': habit_streak,
                'water_percentage': water_percentage
            })
    
    # Get friend activities (limit to most recent 20)
    activities = friends_data[user_id].get('activities', [])
    activities = sorted(activities, key=lambda x: x.get('time', ''), reverse=True)[:20]
    
    return render_template('community.html', 
                          user_id=user_id, 
                          friends=friends, 
                          activities=activities)

@app.route('/community/add-friend', methods=['POST'])
@login_required
def add_friend():
    data = request.get_json()
    friend_id = data.get('friend_id')
    user_id = session['user_id']
    
    if not friend_id:
        return jsonify({'success': False, 'message': 'Friend ID is required'}), 400
    
    # Check if friend ID exists
    users = load_users()
    friend = next((user for user in users if user['id'] == friend_id), None)
    
    if not friend:
        return jsonify({'success': False, 'message': 'User not found with this ID'}), 404
    
    # Check if trying to add self
    if friend_id == user_id:
        return jsonify({'success': False, 'message': 'You cannot add yourself as a friend'}), 400
    
    # Load friends data
    friends_data = load_friends()
    
    # Initialize if not exists
    if user_id not in friends_data:
        friends_data[user_id] = {
            'friends': [],
            'activities': [],
            'added_dates': {}
        }
    
    # Check if already friends
    if friend_id in friends_data[user_id]['friends']:
        return jsonify({'success': False, 'message': 'Already friends with this user'}), 400
    
    # Add friend
    friends_data[user_id]['friends'].append(friend_id)
    
    # Add date when added
    if 'added_dates' not in friends_data[user_id]:
        friends_data[user_id]['added_dates'] = {}
    
    friends_data[user_id]['added_dates'][friend_id] = datetime.now().strftime('%Y-%m-%d')
    
    # Add activity
    if 'activities' not in friends_data[user_id]:
        friends_data[user_id]['activities'] = []
    
    friends_data[user_id]['activities'].append({
        'username': friend['username'],
        'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'description': f"You added {friend['username']} as a friend"
    })
    
    # Also add the current user as a friend to the other user (bidirectional)
    if friend_id not in friends_data:
        friends_data[friend_id] = {
            'friends': [],
            'activities': [],
            'added_dates': {}
        }
    
    current_user = next((user for user in users if user['id'] == user_id), None)
    
    if user_id not in friends_data[friend_id]['friends']:
        friends_data[friend_id]['friends'].append(user_id)
        
        if 'added_dates' not in friends_data[friend_id]:
            friends_data[friend_id]['added_dates'] = {}
        
        friends_data[friend_id]['added_dates'][user_id] = datetime.now().strftime('%Y-%m-%d')
        
        if 'activities' not in friends_data[friend_id]:
            friends_data[friend_id]['activities'] = []
        
        friends_data[friend_id]['activities'].append({
            'username': current_user['username'],
            'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'description': f"{current_user['username']} added you as a friend"
        })
    
    save_friends(friends_data)
    
    return jsonify({'success': True, 'message': 'Friend added successfully'})

@app.route('/community/remove-friend', methods=['POST'])
@login_required
def remove_friend():
    data = request.get_json()
    friend_id = data.get('friend_id')
    user_id = session['user_id']
    
    if not friend_id:
        return jsonify({'success': False, 'message': 'Friend ID is required'}), 400
    
    # Load friends data
    friends_data = load_friends()
    
    # Check if user has friends data
    if user_id not in friends_data or 'friends' not in friends_data[user_id]:
        return jsonify({'success': False, 'message': 'No friends data found'}), 404
    
    # Check if they are friends
    if friend_id not in friends_data[user_id]['friends']:
        return jsonify({'success': False, 'message': 'Not friends with this user'}), 400
    
    # Get usernames for activity
    users = load_users()
    friend = next((user for user in users if user['id'] == friend_id), None)
    current_user = next((user for user in users if user['id'] == user_id), None)
    
    # Remove friend
    friends_data[user_id]['friends'].remove(friend_id)
    
    # Add activity
    if 'activities' not in friends_data[user_id]:
        friends_data[user_id]['activities'] = []
    
    if friend:
        friends_data[user_id]['activities'].append({
            'username': friend['username'],
            'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'description': f"You removed {friend['username']} from your friends"
        })
    
    # Also remove the current user from the other user's friends (bidirectional)
    if friend_id in friends_data and 'friends' in friends_data[friend_id]:
        if user_id in friends_data[friend_id]['friends']:
            friends_data[friend_id]['friends'].remove(user_id)
            
            if 'activities' not in friends_data[friend_id]:
                friends_data[friend_id]['activities'] = []
            
            if current_user:
                friends_data[friend_id]['activities'].append({
                    'username': current_user['username'],
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'description': f"{current_user['username']} removed you from their friends"
                })
    
    save_friends(friends_data)
    
    return jsonify({'success': True, 'message': 'Friend removed successfully'})

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
