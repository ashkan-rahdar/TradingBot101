import requests
from datetime import datetime
import sys
import os
import time
import typing

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import parameters
from functions.logger import print_and_logging_Function

class Telegrambot_Class():
    PASSWORD = '09120058456'
    authenticated_users = set()
    last_message_responded = None
    
    def __init__(self) -> None:
        print_and_logging_Function("info", 'Secure Telegram Bot is running...', "title")
        
        TELEGRAM_BOT_TOKEN = '8061847946:AAHdA8TJr7MpMUtnrbMLKs3NoLpJTxysxLY'
        self.API_URL = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}'
        
    def get_updates(self):
        params = {'timeout': 10, 'offset': self.last_message_responded}
        response = requests.get(f'{self.API_URL}/getUpdates', params=params)
        result = response.json()

        if result['ok']:
            for update in result['result']:
                self.last_message_responded = update['update_id'] + 1
                self.handle_message(update)
                
    def send_message(self, chat_id, text):
        payload = {'chat_id': chat_id, 'text': text}
        requests.post(f'{self.API_URL}/sendMessage', json=payload)
        
    def notify_placed_position(self, direction: typing.Literal["Buy Limit", "Sell Limit"], price: int, sl: int, tp: int, vol: int, chance: int,  chat_id: str = '645769674'):
        text = (
            "*`{}` Position Placed*\n"
            " `{}` % chance \n\n"
            "*Price:*   `{}`\n"
            "*SL:*   `{}`\n"
            "*TP:*   `{}`\n"
            "*Volume:*   `{}`"
        ).format(
            "🟢" + direction if direction == "Buy Limit" else "🔴" + direction,
            chance,
            self.escape_md(str(price)),
            self.escape_md(str(sl)),
            self.escape_md(str(tp)),
            self.escape_md(str(vol))
        )

        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'MarkdownV2'
        }

        res = requests.post(f'{self.API_URL}/sendMessage', json=payload)
        res_json = res.json()
        if not res_json.get('ok'):
            raise Exception(f"An error occurred: {res_json}")



    def handle_message(self, update):
        message = update.get('message')
        if not message:
            return

        chat_id = message['chat']['id']
        text = message.get('text', '').strip()

        # Step 1: Check if user is already authenticated
        if chat_id not in self.authenticated_users:
            if text == self.PASSWORD:
                self.authenticated_users.add(chat_id)
                self.send_message(chat_id, '✅ Authenticated successfully.')
            else:
                self.send_message(chat_id, '🔒 Access denied. Please enter the correct password.')
            return

        # Step 2: Handle authenticated commands
        command = text.lower()
        print_and_logging_Function("info", f"Telegram command: {command}")
        if command == 'time':
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.send_message(chat_id, f'🕒 Current time is: {now}')
        elif command == 'start bot':
            self.send_message(chat_id, '🤖 Bot is starting...')
            # insert your bot startup logic here
        elif command == 'stop bot':
            self.send_message(chat_id, '🛑 Bot is stopping...')
            parameters.shutdown_flag = True
            # insert your bot shutdown logic here
        else:
            self.send_message(chat_id, '❓ Unknown command.')
            
    def escape_md(self, text: str) -> str:
        escape_chars = r"_*[]()~`>#+-=|{}.!"
        for char in escape_chars:
            text = text.replace(char, f"\\{char}")
        return text
            
CTelegramBot = Telegrambot_Class()

def TelegramBot_loop_Funciton():
    while not parameters.shutdown_flag:
        try:
            CTelegramBot.get_updates()
        except Exception as e:
            print_and_logging_Function('error', f'Error in Telegram Bot: {e}')
        time.sleep(10)  # Avoid polling too fast