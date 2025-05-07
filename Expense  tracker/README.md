# Life Manager App

A comprehensive personal management application with expense tracking, habit tracking, water intake monitoring, and notes.

## Features

- Expense tracking with analytics
- Habit tracking and streaks
- Water intake monitoring with reminders
- Notes and to-do lists
- User authentication
- Mobile-friendly design

## Setup

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   python app.py
   ```

## SMS Reminders with Twilio

The water tracker includes SMS reminder functionality using Twilio. To enable this feature:

1. Sign up for a Twilio account at [twilio.com](https://www.twilio.com)
2. Get your Account SID, Auth Token, and a Twilio phone number
3. Set the following environment variables:
   ```
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=your_twilio_phone_number
   ```

4. Make sure users add their mobile numbers in their profile settings (with country code, e.g., +1234567890)

## Water Goal Calculation

The daily water intake goal is calculated based on the user's weight using the formula:
```
Daily water intake (ml) = Weight (kg) × 0.033 × 1000
```

This formula is based on the general recommendation to drink 33ml of water per kg of body weight per day.