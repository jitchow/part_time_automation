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
    '9amto3pm' : ['09:00', '10:01', '11:05', '12:03', '13:02', '14:04', '15:00'],
    '9amto6pm' : ['09:00', '10:01', '11:05', '12:03', '13:02', '14:04', '15:05', '16:03', '17:02', '18:00'],
}

scheduled_times_checkin = {
    'Monday' : time_ranges_checkin['9amto3pm'],
    'Tuesday' : time_ranges_checkin['9amto6pm'],
    'Wednesday' : time_ranges_checkin['9amto3pm'],
    'Thursday' : time_ranges_checkin['9amto3pm'],
    'Friday' : time_ranges_checkin['9amto3pm'],
    'Saturday' : time_ranges_checkin['9amto6pm'],
}

scheduled_times_login = {
    'Monday': ['09:00', '15:00'],
    'Tuesday': ['09:00', '18:00'],
    'Wednesday': ['09:00', '15:00'],
    'Thursday': ['09:00', '15:00'],
    'Friday': ['09:00', '15:00'],
    'Saturday': ['09:00', '18:00'],
}
