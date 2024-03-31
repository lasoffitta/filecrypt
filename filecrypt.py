import requests
from bs4 import BeautifulSoup
import json
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import os

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

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

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Inserisci un URL FileCrypt con /link <url>')

def link(update: Update, context: CallbackContext) -> None:
    filecrypt_url = ' '.join(context.args)
    if filecrypt_url:
        links = get_links(filecrypt_url)
        for link in links:
            update.message.reply_text(link)
    else:
        update.message.reply_text('Per favore, fornisce un URL valido.')

def main():
    updater = Updater(token=TOKEN, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("link", link))

    updater.start_polling()

    updater.idle()

if __name__ == "__main__":
    main()
