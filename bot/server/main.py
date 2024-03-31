from quart import Blueprint, Response, request, render_template, redirect
from .error import abort
from bot import TelegramBot
from bot.config import Telegram, Server
from math import ceil, floor
from bot.modules.telegram import get_message, get_file_properties
from telethon.sync import TelegramClient
from urllib.parse import urlparse, parse_qs

bp = Blueprint('main', __name__)

async def get_message_with_logging(chat_id, message_id):
    message = await get_message(chat_id, ids=message_id)
    if message is None:
        print(f"No message found with chat_id {chat_id} and message_id {message_id}")
    return message

@bp.route('/')
async def home():
    return await render_template('home.html')

@bp.route('/bot')
async def bot():
    return redirect(f'https://t.me/{Telegram.BOT_USERNAME}')

@bp.route('/dl/<int:chat_id>/<int:file_id>')
async def transmit_file(chat_id, file_id):
    file = await get_message_with_logging(chat_id, message_id=int(file_id)) or abort(404)
    # il resto del tuo codice rimane lo stesso

@bp.route('/stream/<int:chat_id>/<int:file_id>')
async def stream_file(chat_id, file_id):
    # Recupera il file da Telegram
    file = await get_message_with_logging(chat_id, message_id=int(file_id))
    if file is None:
        print(f"No file found with chat_id {chat_id} and file_id {file_id}")
        abort(404)
    # Restituisci il file come stream
    return await send_file(file, as_attachment=True)

@bp.route('/file/<int:chat_id>/<int:file_id>')
async def file_deeplink(chat_id, file_id):
    code = request.args.get('code') or abort(401)

    return redirect(f'https://t.me/{Telegram.BOT_USERNAME}?start=file_{chat_id}_{file_id}_{code}')
    
@bp.route('/get_code/<int:chat_id>/<int:file_id>')
async def get_code(chat_id, file_id):
    # Recupera il messaggio dalla chat specificata
    message = await get_message_with_logging(chat_id, message_id=file_id)
    if message is None:
        abort(404)

    # Restituisci il codice del messaggio
    return message.raw_text

@bp.route('/forward_message/<int:chat_id>/<int:file_id>', methods=['POST'])
async def forward_message(chat_id, file_id):
    # Inizializza il client
    client = TelegramClient('bot', Telegram.API_ID, Telegram.API_HASH)

    # Avvia il client
    await client.start()

    # Inoltra il messaggio
    await client.forward_messages('@streamingsoffitta_bot', file_id, 'https://t.me/c/' + str(chat_id))

    # Arresta il client
    await client.stop()

    return 'Message forwarded'
    
@bp.route('/generate_stream_link', methods=['POST'])
async def generate_stream_link():
    # Estrai l'URL di Telegram dal corpo della richiesta
    data = await request.get_json()
    telegram_url = data.get('telegram_url')

    # Analizza l'URL di Telegram per ottenere chat_id e file_id
    parsed_url = urlparse(telegram_url)
    path_parts = parsed_url.path.split('/')
    chat_id = path_parts[2]
    file_id = path_parts[3]

    # Genera l'URL di streaming
    stream_url = f"{request.url_root}stream/{chat_id}/{file_id}"

    return {'stream_url': stream_url}
