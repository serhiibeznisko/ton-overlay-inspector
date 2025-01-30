from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from .http_request import http_request


async def send_telegram_message(text, reply_to_message_id='', chat_id=TELEGRAM_CHAT_ID):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    return await http_request('GET', url, params={
        "chat_id": chat_id,
        "text": text,
        "reply_to_message_id": reply_to_message_id
    })
