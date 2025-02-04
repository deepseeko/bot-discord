import os
import json
from collections import defaultdict
from typing import Dict, Any
import asyncio
import logging
import aiofiles
from dotenv import load_dotenv



############################################# Your server ID and  DATA #################################


load_dotenv()

BANK_JSON_FILE = os.getenv('BANK_JSON_FILE')
bank_wallet_id = int(os.getenv('BANK_WALLET_ID'))
YOUR_SERVER_ID = int(os.getenv('YOUR_SERVER_ID'))
LOG_WIN_WEBHOOK = os.getenv('LOG_WIN_WEBHOOK')
SEND7_WEBHOOK = os.getenv('SEND7_WEBHOOK')
BUY_WEBHOOK = os.getenv('BUY_WEBHOOK')
AUCTION_WEBHOOK = os.getenv('AUCTION_WEBHOOK')
WALLET_WEBHOOK = os.getenv('WALLET_WEBHOOK')
ID_casino = int(os.getenv('ID_CASINO'))
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('7YASBot')

def load_bank_data() -> Dict[str, Any]:
    try:
        with open('data/bank_data.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "credits": 20000000,
            "total_7yas": 20000000,
            "max_7yas_supply": 20000000,
            "exchange_rate": 1
        }

def save_bank_data(data: Dict[str, Any]) -> None:
    with open('data/bank_data.json', 'w') as f:
        json.dump(data, f, indent=2)

bank_data = load_bank_data()


async def load_bank_data():
    global bank_data
    try:
        async with aiofiles.open(BANK_JSON_FILE, 'r') as f:
            content = await f.read()
            bank_data = json.loads(content)
    except FileNotFoundError:
        bank_data = {
            "credits": 20000000,
            "total_7yas": 0,
            "max_7yas_supply": 2000000000,
            "exchange_rate": 1
        }
        await save_bank_data()
    except json.JSONDecodeError:
        # Handle JSON decoding errors
        print("Error: The bank data file is corrupted or contains invalid JSON.")
        # Initialize with default values
        bank_data = {
            "credits": 20000000,
            "total_7yas": 0,
            "max_7yas_supply": 2000000000,
            "exchange_rate": 1
        }
        await save_bank_data()

async def save_bank_data():
    async with aiofiles.open(BANK_JSON_FILE, 'w') as f:
        await f.write(json.dumps(bank_data, indent=4))


# Load bank data
async def calculate_total_7yas(wallets):
    await load_backup()
    await load_bank_data()
    total_7yas = 0
    for user_id, data in wallets.items():
        if user_id != 1241716928561680397:
            total_7yas += data['balance']
    return total_7yas







async def update_backup():
    backup_data = {str(user_id): data for user_id, data in wallets.items()}
    await async_json_dump(backup_data, 'data/BackUp.json')
    logger.info("Backup updated successfully")

async def load_backup():
    if os.path.exists('data/BackUp.json'):
        backup_data = await async_json_load('data/BackUp.json')
        wallets.update({int(user_id): data for user_id, data in backup_data.items()})
        logger.info("Backup loaded successfully")














async def update_exchange_rate():
    await load_backup()
    await load_bank_data()

    bank_data['total_7yas'] = await calculate_total_7yas(wallets)

    remaining_7yas = max(0, bank_data['max_7yas_supply'] - bank_data['total_7yas'])
    print(f"max_7yas_supply = {bank_data['max_7yas_supply']} and total_7yas = {bank_data['total_7yas']}")

    if remaining_7yas == 0:
        bank_data['exchange_rate'] = float('inf')
    else:
        base_rate = 50
        scarcity_factor = (bank_data['max_7yas_supply'] / remaining_7yas) ** 0.1
        bank_data['exchange_rate'] = base_rate * scarcity_factor


    bank_data['exchange_rate'] = max(50, bank_data['exchange_rate'])
    await save_bank_data()






class WalletData(defaultdict):
    def __init__(self):
        super().__init__(lambda: {'balance': 0.0, 'username': '', 'last_daily': None})
wallets = WalletData()
invite_uses: Dict[float, Dict[str, float]] = {}


# Asynchronous file operations
async def async_json_dump(data: Dict[Any, Any], filename: str) -> None:
    def _dump():
        with open(filename, 'w') as f:
            json.dump(data, f)
    await asyncio.get_event_loop().run_in_executor(None, _dump)

async def async_json_load(filename: str) -> Dict[Any, Any]:
    def _load():
        with open(filename, 'r') as f:
            return json.load(f)
    return await asyncio.get_event_loop().run_in_executor(None, _load)









invite_uses = {}
suggestions = []
