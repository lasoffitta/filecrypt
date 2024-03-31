from quart import Blueprint, Response, request, render_template, redirect
from .error import abort
from bot import TelegramBot
from bot.config import Telegram, Server
from math import ceil, floor
from bot.modules.telegram import get_message, get_file_properties
from telethon.sync import TelegramClient
from urllib.parse import urlparse, parse_qs

bp = Blueprint('main', __name__)

@bp.route('/')
async def home():
    return await render_template('home.html')

@bp.route('/bot')
async def bot():
    return redirect(f'https://t.me/{Telegram.BOT_USERNAME}')

@bp.route('/dl/<int:chat_id>/<int:file_id>')
async def transmit_file(chat_id, file_id):
    file = await get_message(chat_id, message_id=int(file_id)) or abort(404)
    code = request.args.get('code') or abort(401)
    stream = request.args.get('stream', default='false')

    if code != file.raw_text:
        abort(403)

    if stream.lower() == 'true':
        # Restituisci il template player.html con l'URL del file come parametro
        return await render_template('player.html', mediaLink=f"/dl/{chat_id}/{file_id}?code={code}")
    
    if range_header:
        from_bytes, until_bytes = range_header.replace("bytes=", "").split("-")
        from_bytes = int(from_bytes)
        until_bytes = int(until_bytes) if until_bytes else file_size - 1
    else:
        from_bytes = 0
        until_bytes = file_size - 1

    if (until_bytes > file_size) or (from_bytes < 0) or (until_bytes < from_bytes):
        abort(416, 'Invalid range.')

    chunk_size = 1024 * 1024
    until_bytes = min(until_bytes, file_size - 1)

    offset = from_bytes - (from_bytes % chunk_size)
    first_part_cut = from_bytes - offset
    last_part_cut = until_bytes % chunk_size + 1

    req_length = until_bytes - from_bytes + 1
    part_count = ceil(until_bytes / chunk_size) - floor(offset / chunk_size)
    
    headers = {
            "Content-Type": f"{mime_type}",
            "Content-Range": f"bytes {from_bytes}-{until_bytes}/{file_size}",
            "Content-Length": str(req_length),
            "Content-Disposition": f'attachment; filename="{file_name}"',
            "Accept-Ranges": "bytes",
        }

    async def file_generator():
        current_part = 1
        async for chunk in TelegramBot.iter_download(file, offset=offset, chunk_size=chunk_size, stride=chunk_size, file_size=file_size):
            if not chunk:
                break
            elif part_count == 1:
                yield chunk[first_part_cut:last_part_cut]
            elif current_part == 1:
                yield chunk[first_part_cut:]
            elif current_part == part_count:
                yield chunk[:last_part_cut]
            else:
                yield chunk

            current_part += 1

            if current_part > part_count:
                break

    return Response(file_generator(), headers=headers, status=206 if range_header else 200)

@bp.route('/stream/<int:chat_id>/<int:file_id>')
async def stream_file(chat_id, file_id):
    # Recupera il file da Telegram
    file = await get_message(chat_id, message_id=int(file_id)) or abort(404)
    # Restituisci il file come stream
    return await send_file(file, as_attachment=True)

@bp.route('/file/<int:chat_id>/<int:file_id>')
async def file_deeplink(chat_id, file_id):
    code = request.args.get('code') or abort(401)

    return redirect(f'https://t.me/{Telegram.BOT_USERNAME}?start=file_{chat_id}_{file_id}_{code}')
    
@bp.route('/get_code/<int:chat_id>/<int:file_id>')
async def get_code(chat_id, file_id):
    # Recupera il messaggio dalla chat specificata
    message = await get_message(chat_id, message_id=file_id)
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
