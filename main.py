import telebot
import os
import sys
import json
import yfinance as yf
from pathlib import Path
import random
import threading
from datetime import datetime, timedelta

import neuralintents
from neuralintents import GenericAssistant

cwd = Path.cwd()
var_dict = json.load(open('variable.json'))
API_KEY = var_dict['API_KEY']
CHANNEL_CHAT_ID = var_dict['CHANNEL_ID']


bot = telebot.TeleBot(API_KEY)
chatbot = GenericAssistant("intents.json")
chatbot.train_model()

# Starting the bot in a new thread
def start_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=start_bot).start()

# Function to send message to channel
def send_message_to_channel(message_text):
    try:
        # Send a new message to the channel and get its message_id
        channel_message = bot.send_message(CHANNEL_CHAT_ID, message_text)
        return channel_message.message_id  # Return the message_id of the post in the channel
    except Exception as e:
        print(f"Error sending message to channel: {e}")
        return None

# Restart command
@bot.message_handler(commands=['restart'])
def restart_bot(message):
    bot.reply_to(message, "Restarting...")
    bot.stop_polling()  # Stop the polling before restarting
    os.execv(sys.executable, ['python'] + sys.argv)  # Restart the bot

# # Get channel ID command
# @bot.message_handler(commands=['get_channel_id'])
# def get_channel_id(message):
#     chat_id = message.chat.id  # This will get the channel's chat ID
#     bot.reply_to(message, f"The chat ID for this channel is: {chat_id}")


# Other bot commands
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    username = str(message.from_user.username)
    bot.reply_to(message, f"Hi {username}, I am Shaunniee. Here are some basic commands:\n"
                          "/shaun - Pings Shaun\n"
                          "/socials - Shows Shaun's socials\n"
                        #   "/selfie - A random pic of myself\n"
                          "/joke - Tell me a joke\n"
                          "/stock - Tell me stock prices\n"
                          "If you want to start a conversation with me just start off by saying Shauniee"
                          )

@bot.message_handler(commands=['shaun'])
def ping(message):
    bot.reply_to(message, "@Shaunniee")

@bot.message_handler(commands=['joke'])
def joke(message):
    joke_list = ['Your life is a joke :D', 'Ur mum', 'What\'s the hardest part of a vegetable to eat? The wheelchair.']
    random_joke = random.choice(joke_list)
    bot.reply_to(message, random_joke)

@bot.message_handler(commands=['selfie'])
def send_rand_photo(message):
    pic_in_dir = cwd / 'Pictures'
    pic_list = list(pic_in_dir.glob('*'))
    random_pic = random.choice(pic_list)
    photo = open(random_pic, 'rb')
    bot.send_photo(message.chat.id, photo)
    if not pic_list:
        bot.send_message(message.chat.id, "No photos available.")
    return

@bot.message_handler(commands=['stock'])
def get_stocks(message):
    msg = bot.reply_to(message, "Enter a stock symbol:")
    bot.register_next_step_handler(msg, fetch_stock)

def fetch_stock(message):
    try:
        stock_symbol = message.text.upper()
        end_date = datetime.today().date()
        start_date = end_date - timedelta(days=7)  # Past one week

        # Fetch stock data
        data = yf.download(tickers=stock_symbol, start=start_date, end=end_date, interval='1d')

        if data.empty:
            bot.reply_to(message, f"No data found for {stock_symbol}. Check the symbol and try again.")
            return

        # Send stock prices as a text message
        response = f"----- {stock_symbol} Stock Prices -----\n"
        for index, row in data.iterrows():
            price = round(row['Close'], 2)
            format_date = index.strftime('%Y-%m-%d')
            response += f"{format_date}: {price}\n"

        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"Error fetching stock data: {str(e)}")

# Handle incoming messages
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    # Check if the message starts with "Shauniee"
    if message.text.lower().startswith("shauniee"):
        user_input = message.text[8:].strip()

        # If the message comes from a group chat or private chat, reply to the channel comment section
        response = chatbot.request(user_input)
        if response:
            # If response is not empty or None, reply with the chatbot's response
            bot.reply_to(message, response)
        else:
            # If response is empty or None, reply with a default message
            bot.reply_to(message, "I'm sorry, I didn't get that. Could you please try again?")
