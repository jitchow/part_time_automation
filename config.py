import telebot
import os
import constants
from dotenv import load_dotenv
load_dotenv()

# Bot Instance
telegram_bot = telebot.TeleBot(constants.TELEGRAM_BOT_TOKEN)

# Back-End
MODE = 'front' # front / back
PAGES_TO_DO = 3

# Check In 
time_ranges_checkin = {
    '9amto6pm' : ['09:00', '10:01', '11:05', '12:03', '13:02', '14:04', '15:05', '16:03', '17:02', '18:00'],
    '3pmto9pm' : ['15:00', '16:03', '17:05', '18:02', '19:04', '20:00', '21:00'],
    '6pmto11pm' : ['18:00', '19:03', '20:04', '21:01', '22:05', '23:02'],
    'midnight' : ['00:03', '01:05', '02:04', '03:00'],
}

scheduled_times_checkin = {
    'Monday' : time_ranges_checkin['3pmto9pm'],
    'Tuesday' : time_ranges_checkin['6pmto11pm'],
    'Wednesday' : time_ranges_checkin['midnight'] + time_ranges_checkin['3pmto9pm'],
    'Thursday' : time_ranges_checkin['3pmto9pm'],
    'Friday' : time_ranges_checkin['3pmto9pm'],
    'Saturday' : time_ranges_checkin['9amto6pm'],
}

# Login
login_days_midnight = ['Wednesday']

scheduled_times_login = {
    'Monday': ['15:00', '21:00'],
    'Tuesday': ['18:00', '23:58'],
    'Wednesday': ['15:00', '21:00'],
    'Thursday': ['15:00', '21:00'],
    'Friday': ['15:00', '21:00'],
    'Saturday': ['09:00', '18:00'],
}
