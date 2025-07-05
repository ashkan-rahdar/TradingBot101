import requests
from requests.exceptions import RequestException
from datetime import datetime
import sys
import os
import typing
import json
from pathlib import Path
from colorama import Fore, Style

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import parameters

with open("./TelegramBot_Token.json", "r") as file:
    config = json.load(file)
    
class Telegrambot_Class():
    PASSWORD = config["password"]
    authenticated_users = set()
    last_message_responded = None
    
    def __init__(self) -> None:        
        TELEGRAM_BOT_TOKEN = config['token']
        self.API_URL = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}'
        self.queue_file = "unsent_telegram_messages.json"
        
    def get_updates(self):
        params = {'timeout': 10, 'offset': self.last_message_responded}
        try:
            response = requests.get(f'{self.API_URL}/getUpdates', params=params)
            # response.raise_for_status()  # Raises HTTPError for bad HTTP status (e.g., 500)
            result = response.json()

            if result['ok']:
                for update in result['result']:
                    self.last_message_responded = update['update_id'] + 1
                    self.handle_message(update)
        # except RequestException as e:
            # print(Fore.YELLOW + f"[TelegramBot warning]-> Network error while getting new messages from Telegram: {e}." + Style.RESET_ALL)
        except Exception as e:
            raise e
                
    def send_message(self, chat_id: str = config['chat_id'], text: str= ''):
        payload = {'chat_id': chat_id, 'text': text}
        try:
            response = requests.post(f'{self.API_URL}/sendMessage', json=payload)
            response.raise_for_status()  # Raises HTTPError for bad HTTP status (e.g., 500)
            result = response.json()
            if not result.get("ok", False):
                # This is an API-level failure (bad formatting, bad token, etc.)
                raise Exception(f"Telegram API error: {result}")
        except RequestException as e:
            # ✅ Only catches real HTTP issues like timeouts, connection errors, etc.
            print(Fore.YELLOW + f"[TelegramBot warning]-> Network error while sending to Telegram: {e}. Queuing message." + Style.RESET_ALL)
            self._save_unsent_message(text)
        except Exception as e:
            # ❌ For all other logic/config errors
            raise e
        
    def _save_unsent_message(self, text: str):
        path = Path(self.queue_file)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                messages = json.load(f)
        else:
            messages = []

        messages.append(text)
    
        with open(path, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=4)

    def flush_unsent_messages(self):
        path = Path(self.queue_file)
        if not path.exists():
            return

        with open(path, "r", encoding="utf-8") as f:
            messages = json.load(f)

        failed = []
        for msg in messages:
            try:
                self.send_message(msg)
            except RequestException:
                failed.append(msg)
                continue  # still a network problem
            except Exception as e:
                print(Fore.RED + f"Unhandled error sending queued message: {e}" + Style.RESET_ALL)

        if failed:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(failed, f, indent=4)
        else:
            path.unlink()  # all sent successfully
        
    def notify_placed_position(self, timeframe: str, direction: typing.Literal["Buy Limit", "Sell Limit"], price: int, sl: int, tp: int, vol: int, chance: int, order_Id: int, chat_id: str = config['chat_id']):
        text = (
            "*`{}` `{}` Position Placed*\n"
            " `{}` % chance \n\n"
            "*Price:*   `{}`\n"
            "*SL:*   `{}`\n"
            "*TP:*   `{}`\n"
            "*Volume:*   `{}`\n"
            "*Order ID:*   `{}`"
        ).format(
            timeframe,
            "🟢" + direction if direction == "Buy Limit" else "🔴" + direction,
            chance,
            self.escape_md(str(price)),
            self.escape_md(str(sl)),
            self.escape_md(str(tp)),
            self.escape_md(str(vol)),
            self.escape_md(str(order_Id))
        )

        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'MarkdownV2'
        }

        try:
            res = requests.post(f'{self.API_URL}/sendMessage', json=payload)
            res.raise_for_status()
            res_json = res.json()
            if not res_json.get('ok'):
                raise Exception(f"An error occurred: {res_json}")
        except RequestException as e:
            print(Fore.YELLOW + f"[TelegramBot warning]-> Network error while notifying new orders: {e}. Queuing message." + Style.RESET_ALL)
            self._save_unsent_message(text)
        except Exception as e:
            raise e

    def handle_message(self, update):
        message = update.get('message')
        if not message:
            return

        chat_id = message['chat']['id']
        text = message.get('text', '').strip()

        # Normalize command
        command = text.lower()

        # --- Step 1: Login Handling ---
        if command.startswith('/login'):
            try:
                _, password = text.split(maxsplit=1)
            except ValueError:
                self.send_message(chat_id, '❌ Usage: /login <password>')
                return

            if password == self.PASSWORD:
                self.authenticated_users.add(chat_id)
                self.send_message(chat_id, '✅ Authentication successful.')
            else:
                self.send_message(chat_id, '🔒 Incorrect password. Try again.')
            return

        # --- Step 2: Logout Handling ---
        if command in ['/logout', 'logout']:
            self.authenticated_users.discard(chat_id)
            self.send_message(chat_id, '🚪 You have been logged out.\n🔒 Use /login <password> to log in again.')
            return

        # --- Step 3: Require Authentication ---
        if chat_id not in self.authenticated_users:
            self.send_message(chat_id, '🔒 You are not authenticated.\nPlease use /login <password> to access commands.')
            return

        # --- Step 4: Handle Authenticated Commands ---
        if command in ['/time', 'time']:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.send_message(chat_id, f'🕒 Current time is: {now}')

        elif command in ['/startbot', 'start bot']:
            self.send_message(chat_id, '🤖 Bot is starting...')
            # Insert your bot startup logic here

        elif command in ['/stopbot', 'stop bot']:
            self.send_message(chat_id, '🛑 Bot is stopping...')
            # Insert your bot shutdown logic here

        elif command in ['/shutdown']:
            self.send_message(chat_id, '⚠️ Emergency shutdown requested. Closing positions...')
            parameters.shutdown_flag = True
            # Insert emergency shutdown logic here

        elif command in ['/status']:
            # Example response – customize this to your needs
            self.send_message(chat_id, '📊 Bot is currently running and monitoring markets.')

        elif command in ['/help']:
            self.send_message(chat_id, (
                "📖 *Available Commands:*\n"
                "/login <password> – Authenticate to use the bot\n"
                "/logout – Log out of your session\n"
                "/startbot – Start the trading bot\n"
                "/stopbot – Stop the bot\n"
                "/shutdown – Emergency shutdown\n"
                "/status – Show current bot status\n"
                "/time – Get current server time\n"
                "/help – Show this help message"
            ))

        else:
            self.send_message(chat_id, '❓ Unknown command. Use /help to see available options.')
            
    def escape_md(self, text: str) -> str:
        escape_chars = r"_*[]()~`>#+-=|{}.!"
        for char in escape_chars:
            text = text.replace(char, f"\\{char}")
        return text
            
CTelegramBot = Telegrambot_Class()