# Setting Up Twilio for SMS Reminders

This guide will help you set up Twilio to enable SMS reminders for your water intake in the Life Manager application.

## Step 1: Create a Twilio Account

1. Go to [Twilio's website](https://www.twilio.com/) and sign up for a free account
2. Verify your email address and phone number

## Step 2: Get Your Twilio Credentials

1. After signing in to your Twilio account, navigate to the [Twilio Console Dashboard](https://www.twilio.com/console)
2. Find your **Account SID** and **Auth Token** - you'll need these for your `.env` file
3. Note: Your Auth Token is hidden by default. Click on the eye icon to reveal it

## Step 3: Get a Twilio Phone Number

1. In the Twilio Console, navigate to [Phone Numbers](https://www.twilio.com/console/phone-numbers/incoming)
2. Click on "Buy a Number" or "Get a Trial Number"
3. Select a phone number that has SMS capabilities
4. Complete the purchase (free with trial credits)

## Step 4: Configure Your Environment Variables

1. Open the `.env` file in your Life Manager project directory
2. Update the following variables with your Twilio credentials:

```
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=your_twilio_phone_number_here
```

Example:
```
TWILIO_ACCOUNT_SID=AC1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p
TWILIO_AUTH_TOKEN=1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p
TWILIO_PHONE_NUMBER=+12345678901
```

## Step 5: Test SMS Functionality

1. Make sure you've added your own verified phone number in your user profile
2. Try sending a water reminder from the Water Tracker page
3. You should receive an SMS reminder on your phone

## Troubleshooting

- **SMS not sending**: Check your Twilio console for error messages
- **Authentication errors**: Verify your Account SID and Auth Token are correct
- **Phone number format**: Ensure phone numbers are in E.164 format (e.g., +12345678901)
- **Trial account limitations**: With a trial account, you can only send SMS to verified phone numbers

## Twilio Trial Limitations

With a Twilio trial account:
- You can only send SMS to verified phone numbers
- Your messages will include a trial prefix
- You have limited trial credits

To remove these limitations, upgrade to a paid Twilio account.

## Additional Resources

- [Twilio SMS Python Documentation](https://www.twilio.com/docs/sms/quickstart/python)
- [Twilio Console](https://www.twilio.com/console)
- [E.164 Phone Number Formatting](https://www.twilio.com/docs/glossary/what-e164)