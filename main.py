import json
import telebot
import yfinance as yf

var_dict = json.load(open('variable.json'))
API_KEY = var_dict['API_KEY']

bot = telebot.TeleBot(API_KEY)

# @bot.message_handler(func=lambda message: True)
# def echo_all(message):
# 	bot.reply_to(message, message.text)

@bot.message_handler(commands = ['start', 'help'])
def welcome(message):
    bot.reply_to(message, """\
        Hi there, I am Shaunniee. Here are some basic commands.
    /everyone -- Pings everyone
    /joke -- Tell me a joke
    /wsb -- Tell me stcok prices""")

@bot.message_handler(commands = ['everyone'])
def greet(message):
    bot.reply_to(message, "@itsernesttt @m1l0p3ng")

@bot.message_handler(commands = ['joke'])
def greet(message):
    bot.reply_to(message, "Your life is a joke :)")

@bot.message_handler(commands = ['wsb'])        
def get_stocks(message):
    response = ""
    stocks = ['MSFT', 'AAPL', 'TSLA']
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

def stock_request(message):
    request = message.text.split()
    if len(request) < 2 or request[0].lower() not in "price":
        return False
    else:
        return True 
    
@bot.message_handler(func=stock_request)
def send_price(message):
    request = message.text.split()[1]
    data = yf.download(tickers=request, period='5m', interval='1m')
    if data.size > 0:
        data = data.reset_index()
        data["format_date"] = data['Datetime'].dt.strftime('%m/%d %I:%M %p')
        print(data.to_string())
        bot.send_message(message.chat.id, data['Close'].to_string(header = False))
    else:
        bot.send_message(message.chat.id, "No data!?")

bot.infinity_polling()