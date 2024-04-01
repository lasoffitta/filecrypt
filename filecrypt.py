from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext, Dispatcher, MessageHandler, Filters
import os
import requests
from bs4 import BeautifulSoup
import json
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = Bot(TOKEN)
bot.set_webhook('https://filecrypt.onrender.com/' + TOKEN)  # Imposta il webhook

app = Flask(__name__)

@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dp.process_update(update)
    return 'ok'

@app.route('/')
def index():
    return 'Hello World!'

@app.route('/test/<path:filecrypt_url>')
def test(filecrypt_url):
    filecrypt_url = 'https://' + filecrypt_url  # Aggiungi 'https://' all'inizio dell'URL
    links = get_links(filecrypt_url)
    return {'links': links}

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Inserisci un URL FileCrypt con /link <url>')

def process_links(update: Update, context: CallbackContext) -> None:
    filecrypt_url = update.message.text
    if "/link" in filecrypt_url:
        filecrypt_url = filecrypt_url.replace("/link ", "")
    if filecrypt_url:
        links = get_links(filecrypt_url)
        for link in links:
            update.message.reply_text(link)
    else:
        update.message.reply_text('Per favore, fornisce un URL valido.')

dp = Dispatcher(bot, None, use_context=True)
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("link", process_links))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, process_links))

def get_links(filecrypt_url):
    response = requests.get(filecrypt_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    if "/Link/" in filecrypt_url:
        script = soup.find_all('script')[-1].string
        start = script.rfind('http')
        end = script.find('id=', start) + 43
        link = script[start:end].replace('&amp;', '&')
        return [link]
    elif "/Container/" in filecrypt_url:
        dlcdownload_element = soup.find('button', class_='dlcdownload')
        if dlcdownload_element is None:
            print("Could not find the dlcdownload element.")
            return []
        dlc_id = dlcdownload_element['onclick'].split("'")[1]
        dlc_url = f"https://{filecrypt_url.split('/')[2]}/DLC/{dlc_id}.dlc"
        dlc_response = requests.get(dlc_url)
        dcrypt_url = "http://dcrypt.it/decrypt/paste"
        dcrypt_data = {"content": dlc_response.text}
        dcrypt_response = requests.post(dcrypt_url, data=dcrypt_data)
        dcrypt_json = json.loads(dcrypt_response.text)
        return dcrypt_json['success']['links']

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', '8000')))
