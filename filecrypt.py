from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext, Dispatcher
import os

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

dp = Dispatcher(bot, None, use_context=True)
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("link", link))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', '8000')))
