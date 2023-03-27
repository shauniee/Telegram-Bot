import telebot
from telebot import apihelper
from telebot import types
import json
import yfinance as yf
from pathlib import Path
import random

cwd = Path.cwd()

var_dict = json.load(open('variable.json'))
API_KEY = var_dict['API_KEY']

bot = telebot.TeleBot(API_KEY)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    username = str(message.from_user.username)
    bot.reply_to(message, f"""\
        Hi {username}, I am Shaunniee. Here are some basic commands.
/shaun -- Pings Shaun
/selfie -- A random pic of myself
/unglam -- Sends a random unglam
/joke -- Tell me a joke
/stock -- Tell me stock prices""")

@bot.message_handler(commands = ['shaun'])
def ping(message):
    bot.reply_to(message, f"@Shaunniee")


@bot.message_handler(commands = ['joke'])
def joke(message):
    joke_list = ['Your life is a joke :D', 
                 'Ur mum', 
                 'Whats the hardest part of a vegetable to eat ----- the wheelchair',
                 'What do you call a group of disabled kids ----- Special forces']
    random_joke = random.choice(joke_list)
    bot.reply_to(message, random_joke)

@bot.message_handler(commands=['photo', 'pic', 'selfie'])
def send_rand_photo(message):
    pic_in_dir = cwd/'Pictures'
    pic_list = []
    for pic in pic_in_dir.iterdir():
        pic_str = str(pic)
        pic_list.append(pic_str)
    random_pic = random.choice(pic_list)
    print(random_pic, 'hi')
    photo = open(random_pic, 'rb')
    bot.send_photo(message.chat.id, photo)

@bot.message_handler(commands=['xtphoto', 'xtpic', 'couplepic'])
def send_rand_xtphoto(message):
    pic_in_dir = cwd/'Our_Pictures'
    pic_list = []
    for pic in pic_in_dir.iterdir():
        pic_str = str(pic)
        pic_list.append(pic_str)
    random_pic = random.choice(pic_list)
    print(random_pic, 'hi')
    photo = open(random_pic, 'rb')
    bot.send_photo(message.chat.id, photo)

@bot.message_handler(commands=['unglam', 'unglams'])
def send_rand_unglam(message):
    pic_in_dir = cwd/'Unglams'
    pic_list = []
    for pic in pic_in_dir.iterdir():
        pic_str = str(pic)
        pic_list.append(pic_str)
    random_pic = random.choice(pic_list)
    print(random_pic, 'hi')
    photo = open(random_pic, 'rb')
    bot.send_photo(message.chat.id, photo)


@bot.message_handler(commands=['stock'])        
def get_stocks(message):
    msg = bot.send_message(message.chat.id, "Choose your stock to view:")
    bot.register_next_step_handler(msg, stock_price)

def stock_price(message):
    response = ""
    stocks = [message.text]
    stock_data = []
    for stock in stocks:
        data = yf.download(tickers = stock, period = '2d', interval = '1d')
        data = data.reset_index()
        response += f"-----{stock}-----\n"
        stock_data.append([stock])
        columns = ['stock']
        for index, row in data.iterrows():
            stock_position = len(stock_data) - 1
            price = round(row['Close'], 2)
            format_date = row['Date'].strftime('%m/%d')
            response += f"{format_date}: {price}\n"
            stock_data[stock_position].append(price)
            columns.append(format_date)
        print()

    response = f"{columns[0] : <10}{columns[1] : ^10}{columns[2] : >10}\n"
    for row in stock_data:
        response += f"{row[0] : <10}{row[1] : ^10}{row[2] : >10}\n"
    response += "\nStock Data"
    print(response)
    bot.send_message(message.chat.id, response)

# def stock_request(message):
#     request = message.text.split()
#     if len(request) < 2 or request[0].lower() not in "price":
#         return False
#     else:
#         return True 
    
# @bot.message_handler(func=stock_request)
# def send_price(message):
#     request = message.text.split()[1]
#     data = yf.download(tickers=request, period='5m', interval='1m')
#     if data.size > 0:
#         data = data.reset_index()
#         data["format_date"] = data['Datetime'].dt.strftime('%m/%d %I:%M %p')
#         print(data.to_string())
#         bot.send_message(message.chat.id, data['Close'].to_string(header = False))
#     else:
#         bot.send_message(message.chat.id, "No data!?")


bot.infinity_polling()