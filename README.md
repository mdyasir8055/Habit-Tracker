# Life Manager - Expense Tracker

A comprehensive personal life management application that helps you track expenses, build habits, monitor water intake, take notes, and connect with friends.

## Features

### 1. Expense Tracking
- Record and categorize your expenses and income
- Visualize spending patterns with interactive charts
- Set and monitor monthly budgets
- Filter expenses by date range and categories
- Track recurring expenses

### 2. Habit Tracking
- Create and track daily habits
- Monitor habit streaks and completion rates
- Categorize habits (personal, work, health, fitness)
- Visual progress indicators

### 3. Water Intake Tracker
- Set daily water intake goals
- Quick-add buttons for common amounts
- Visual progress indicator
- SMS reminders for hydration (via Twilio)

### 4. Notes
- Create, edit, and organize sticky notes
- Color-code notes for better organization
- Drag and drop interface

### 5. Community Features
- Connect with friends
- Share activity updates
- View friends' progress
- Leaderboards for habits and water tracking

### 6. User Profile
- Customize personal information
- Set notification preferences
- Mobile number for SMS reminders

## Setup Instructions

### Prerequisites
- Python 3.7+
- Flask
- Twilio account (optional, for SMS reminders)

### Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/expenses-tracker.git
cd expenses-tracker
```

2. Install required packages:
```
pip install -r requirements.txt
```

3. Configure environment variables:
   - Create a `.env` file in the project root
   - Add your Twilio credentials (if using SMS features):
   ```
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=your_twilio_phone_number
   ```

4. Run the application:
```
python "Expense tracker/app.py"
```

5. Access the application:
   - Open your browser and navigate to `http://localhost:5000`
   - Register a new account to get started

## Usage Guide

### Expense Tracking
- Add new expenses from the Expenses page
- Select categories, add descriptions, and enter amounts
- View spending analytics on the dashboard
- Set monthly budgets and track progress

### Habit Tracking
- Create new habits with the "Add Habit" button
- Check off completed habits daily
- View streaks and statistics on the dashboard

### Water Tracking
- Update your daily water intake with quick-add buttons
- Set custom goals in your profile
- Enable SMS reminders for regular hydration

### Notes
- Create new notes with the "+" button
- Edit by clicking on a note
- Change colors using the color picker
- Organize by dragging and repositioning

### Community
- Add friends using their email or username
- View your friends' activities in the feed
- Compare progress on the leaderboards

## Data Storage
The application stores all data locally in JSON files:
- `users.json`: User account information
- `expenses.json`: Expense records
- `habits.json`: Habit tracking data
- `water.json`: Water intake records
- `notes.json`: Notes data
- `friends.json`: Community connections and activity feed

## Customization
- Toggle between dark and light themes using the moon/sun icon
- Customize notification preferences in your profile
- Set personal goals for water intake and habits

## Security
- Passwords are securely hashed
- Session-based authentication
- Environment variables for sensitive credentials

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments
- Icons and animations provided by custom CSS
- Chart visualizations powered by Chart.js