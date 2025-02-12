import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

import os
import sys
import json

import yfinance as yf
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd

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

user_requests = {}


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
    msg = bot.reply_to(message, "Enter stock symbol and days (optional, default 30):\nExample: TSLA, 90")
    bot.register_next_step_handler(msg, ask_interval)

def ask_interval(message):
    try:
        chat_id = message.chat.id
        user_input = message.text.split(',')
        stock_symbol = user_input[0].strip().upper()
        days = int(user_input[1]) if len(user_input) > 1 and user_input[1].isdigit() else 30

        if days > 365:
            bot.reply_to(message, "Please enter a date range of **1 to 365 days**.")
            return

        user_requests[chat_id] = {"stock": stock_symbol, "days": days}

        msg = bot.reply_to(message, "Select interval:\n- '1d' (Daily) 📅\n- '1wk' (Weekly) 📆\n- '1mo' (Monthly) 📈")
        bot.register_next_step_handler(msg, ask_moving_average)

    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

def ask_moving_average(message):
    chat_id = message.chat.id
    if chat_id not in user_requests:
        bot.reply_to(message, "No request found. Use /stock to start again.")
        return

    interval = message.text.strip().lower()
    if interval not in ["1d", "1wk", "1mo"]:
        bot.reply_to(message, "Invalid interval. Type '1d', '1wk', or '1mo'. Use /stock to start again.")
        return

    user_requests[chat_id]["interval"] = interval

    msg = bot.reply_to(message, "Enter short-term & long-term SMA (e.g., 20,50):")
    bot.register_next_step_handler(msg, ask_rsi_period)

def ask_rsi_period(message):
    chat_id = message.chat.id
    if chat_id not in user_requests:
        bot.reply_to(message, "No request found. Use /stock to start again.")
        return

    try:
        sma_periods = [int(x) for x in message.text.split(',')]
        if len(sma_periods) != 2 or any(x <= 0 for x in sma_periods):
            bot.reply_to(message, "Invalid input. Enter two positive numbers (e.g., 20,50).")
            return

        user_requests[chat_id]["sma_periods"] = sma_periods

        msg = bot.reply_to(message, "Enter RSI period (e.g., 14):")
        bot.register_next_step_handler(msg, confirm_stock_request)

    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

def confirm_stock_request(message):
    chat_id = message.chat.id
    if chat_id not in user_requests:
        bot.reply_to(message, "No request found. Use /stock to start again.")
        return

    try:
        rsi_period = int(message.text.strip())
        if rsi_period <= 0:
            bot.reply_to(message, "Invalid input. Enter a positive number for RSI period.")
            return

        user_requests[chat_id]["rsi_period"] = rsi_period

        stock = user_requests[chat_id]["stock"]
        days = user_requests[chat_id]["days"]
        interval = user_requests[chat_id]["interval"]
        sma_periods = user_requests[chat_id]["sma_periods"]

        confirmation_msg = f"📈 **Stock Analysis Request**:\n- Stock: {stock}\n- Date Range: {days} days\n- Interval: {interval.upper()}\n- SMA: {sma_periods[0]} & {sma_periods[1]}\n- RSI Period: {rsi_period}\n\nType 'Yes' to proceed or 'No' to re-enter details."
        send_confirmation_with_inline_buttons(message, stock, days, interval, sma_periods, rsi_period)

    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

def send_confirmation_with_inline_buttons(message, stock, days, interval, sma_periods, rsi_period):
    confirmation_msg = f"📈 **Stock Analysis Request**:\n" \
                       f"- Stock: {stock}\n" \
                       f"- Date Range: {days} days\n" \
                       f"- Interval: {interval.upper()}\n" \
                       f"- SMA: {sma_periods[0]} & {sma_periods[1]}\n" \
                       f"- RSI Period: {rsi_period}\n\n" \
                       f"Do you want to proceed with this request?"

    # Create inline keyboard with Yes and No options
    markup = InlineKeyboardMarkup()
    yes_button = InlineKeyboardButton("Yes", callback_data="yes")
    no_button = InlineKeyboardButton("No", callback_data="no")
    markup.add(yes_button, no_button)

    # Send the message with the inline keyboard
    bot.reply_to(message, confirmation_msg, reply_markup=markup)

def handle_callback_query(call, message):
    chat_id = call.message.chat.id
    if call.data == "yes":
        user_requests[chat_id]["chat_id"] = chat_id  # Add chat_id to request
        fetch_stock(user_requests[chat_id], message)  # Pass full request
        del user_requests[chat_id]
        bot.answer_callback_query(call.id, "Confirmed!")
        bot.edit_message_text("Stock data is being fetched!", chat_id, call.message.message_id)
    elif call.data == "no":
        bot.answer_callback_query(call.id, "Cancelled.")
        bot.edit_message_text("Request cancelled. Use /stock to start again.", chat_id, call.message.message_id)
        del user_requests[chat_id]

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    message = call.message  # Get the original message
    handle_callback_query(call, message)

def fetch_stock(request, message):
    try:
        chat_id = request["chat_id"]  # Ensure chat_id exists
        stock = request["stock"]
        days = request["days"]
        interval = request["interval"]
        sma_periods = request["sma_periods"]
        rsi_period = request["rsi_period"]

        end_date = datetime.today().date()
        start_date = end_date - timedelta(days=days)

        df = yf.download(tickers=stock, start=start_date, end=end_date, interval=interval)
        if df.empty:
            bot.send_message(chat_id, f"No data found for {stock}.")
            return

        # Calculate Moving Averages
        df["SMA_Short"] = df["Close"].rolling(window=sma_periods[0]).mean()
        df["SMA_Long"] = df["Close"].rolling(window=sma_periods[1]).mean()

        # Calculate RSI
        delta = df["Close"].diff(1)
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))

        # Set up figure with 3 subplots
        fig, axes = plt.subplots(3, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1, 1]})

        # Plot Candlestick Chart
        mpf.plot(df, type='candle', style='charles', ax=axes[0],
                 addplot=[
                     mpf.make_addplot(df["SMA_Short"], ax=axes[0], color='blue', linestyle='dashed', label=f'SMA {sma_periods[0]}'),
                     mpf.make_addplot(df["SMA_Long"], ax=axes[0], color='red', linestyle='dashed', label=f'SMA {sma_periods[1]}')
                 ])
        axes[0].legend()
        axes[0].set_title(f"{stock} Stock Price with SMA")

        # Plot Volume
        axes[1].bar(df.index, df["Volume"], color="gray", alpha=0.6)
        axes[1].set_title("Volume")

        # Plot RSI
        axes[2].plot(df.index, df["RSI"], label=f'RSI {rsi_period}', color='purple')
        axes[2].axhline(70, linestyle='dashed', color='red', label='Overbought (70)')
        axes[2].axhline(30, linestyle='dashed', color='green', label='Oversold (30)')
        axes[2].set_title("Relative Strength Index (RSI)")
        axes[2].legend()

        plt.tight_layout()
        # Save figure
        file_path = 'stock_analysis.png'
        plt.savefig(file_path)
        plt.close(fig)  # Close the figure to free up memory

        # Reply to the original message with the chart
        with open(file_path, "rb") as photo:
            bot.send_photo(message.chat.id, photo, reply_to_message_id=message.message_id)  # Send photo as reply

        # Remove the image after sending
        os.remove(file_path)

    except Exception as e:
        bot.send_message(chat_id, f"Error fetching stock data: {str(e)}")

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
