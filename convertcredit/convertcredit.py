from discord.ext import commands
import discord
import requests
from decimal import Decimal, ROUND_DOWN
from datetime import datetime
from data.data import load_bank_data, update_exchange_rate, update_backup, save_bank_data, load_backup, wallets, bank_data

CHANNEL_ID = CHANNEL_ID_for_convert = [1280295399198036031, 1280295543809249421]
WEBHOOK_URL = PROBOT_ID = 282859044593598464
LOG_WEBHOOK_URL = "https://ptb.discord.com/api/webhooks/1277345648471179315/PKSIwjMpY0aCPqs_pXV8o12o8Oun_T6fGvJ7rhKEUNNFz8NyMRRvIuWqdaz43i1OSaqW"
ID_BANK = 1241716928561680397

class ConvertCredit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def convert_to_7yas(self, SenderUser_ID, amount_send):
        if SenderUser_ID not in wallets:
            return 0, "No wallet found"
        if amount_send < 10:
            return 0, f"mini = {bank_data['exchange_rate']}"
        
        await load_bank_data()
        await update_exchange_rate()

        exchange_rate = Decimal(str(bank_data['exchange_rate']))
        amount_send_decimal = Decimal(str(amount_send))
        
        value_in_7yas = (amount_send_decimal / exchange_rate).quantize(Decimal('0.00000001'), rounding=ROUND_DOWN)
        
        if value_in_7yas <= 0:
            return 0, "Amount too small to convert"
        
        old_balance = wallets[SenderUser_ID]['balance']
        wallets[SenderUser_ID]['balance'] += float(value_in_7yas)
        wallets[ID_BANK]['balance'] -= float(value_in_7yas)
        bank_data['credits'] += amount_send
        bank_data['total_7yas'] -= float(value_in_7yas)
        
        await update_backup()
        await save_bank_data()
        await update_exchange_rate()
        
        new_balance = wallets[SenderUser_ID]['balance']
        
        return float(value_in_7yas), old_balance, new_balance

    def log_conversion(self, user_name, user_id, amount_send, value_in_7yas):
        with open("data/log_convert.txt", "a") as log_file:
            log_file.write(f"User: {user_name} | UserID: {user_id} | Sent: {amount_send} Credits | Received: {value_in_7yas} 7YAS | Time: {datetime.now().isoformat()}\n")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id == PROBOT_ID and message.channel.id in CHANNEL_ID:
            if len(message.content) > 13 and message.content[13] == '|':
                try:
                    start_idx = 15
                    end_idx = message.content.index(',', start_idx)
                    sender = message.content[start_idx:end_idx]
                    
                    amount_start = message.content.index('$') + 1
                    amount_end = message.content.index(' ', amount_start)
                    amount_send = int(''.join(filter(str.isdigit, message.content[amount_start:amount_end])))
                    
                    id_start = message.content.index('!') + 1
                    id_end = message.content.index('>', id_start)
                    ID_Send_To = int(message.content[id_start:id_end])
                    
                    SenderUser_ID = None
                    await load_backup()
                    for user_id, data in wallets.items():
                        if data['username'] == sender:
                            SenderUser_ID = int(user_id)
                            break
                    
                    if data['username'] == "bank7y":
                        print("fixed")
                        return

                    if ID_Send_To == ID_BANK:
                        value_in_7yas, old_balance, new_balance = await self.convert_to_7yas(SenderUser_ID, amount_send)
                        self.log_conversion(sender, SenderUser_ID, amount_send, value_in_7yas)
                    else:
                        raise ValueError(f"Sender username sent to a user test if on message in use other than Bank {ID_BANK} is not {SenderUser_ID}")

                    sender_embed = self.create_sender_embed(sender, amount_send, value_in_7yas, old_balance, new_balance)
                    
                    user = await self.bot.fetch_user(SenderUser_ID)
                    await user.send(embed=sender_embed)
                    
                    channel = self.bot.get_channel(message.channel.id)
                    await channel.send(embed=sender_embed)

                    log_embed = self.create_log_embed(sender, amount_send, value_in_7yas, ID_Send_To, old_balance, new_balance)
                    self.send_log_webhook(log_embed)

                except Exception as e:
                    bank_user = "bank7y"
                    if bank_user != sender:
                        self.send_error_webhook(str(e))

    def create_sender_embed(self, sender, amount_send, value_in_7yas, old_balance, new_balance):
        sender_embed = discord.Embed(
            title="7YAS Wallet - Transaction Complete 🎉",
            description=f"**Thank you for using 7YAS Wallet, {sender}!**",
            color=0x00ff00
        )
        sender_embed.set_thumbnail(url="https://i.top4top.io/p_3159x90111.jpg")
        sender_embed.add_field(name="Amount Sent", value=f"`{amount_send} ProBot Credits`", inline=False)
        sender_embed.add_field(name="Converted to 7YAS", value=f"`{value_in_7yas} 7YAS`", inline=False)
        sender_embed.add_field(name="Old Balance", value=f"`{old_balance} 7YAS`", inline=True)
        sender_embed.add_field(name="New Balance", value=f"`{new_balance} 7YAS`", inline=True)
        sender_embed.add_field(name="Current Exchange Rate", value=f"1 7YAS = {bank_data['exchange_rate']} credits", inline=False)
        sender_embed.set_footer(text="Transaction processed successfully.")
        return sender_embed

    def create_log_embed(self, sender, amount_send, value_in_7yas, ID_Send_To, old_balance, new_balance):
        log_embed = discord.Embed(
            title="7YAS Transaction Log",
            color=0x3498db
        )
        log_embed.add_field(name="Sender", value=sender, inline=True)
        log_embed.add_field(name="Amount Sent", value=f"{amount_send} ProBot Credits", inline=True)
        log_embed.add_field(name="Converted to 7YAS", value=f"{value_in_7yas} 7YAS", inline=True)
        log_embed.add_field(name="Recipient ID", value=f"{ID_Send_To}", inline=True)
        log_embed.add_field(name="Old Balance", value=f"{old_balance} 7YAS", inline=True)
        log_embed.add_field(name="New Balance", value=f"{new_balance} 7YAS", inline=True)
        log_embed.add_field(name="Current Exchange Rate", value=f"1 7YAS = {bank_data['exchange_rate']} credits", inline=True)
        log_embed.set_footer(text="Logged by 7YAS Wallet Bot")
        return log_embed

    def send_log_webhook(self, log_embed):
        log_response = requests.post(LOG_WEBHOOK_URL, json={"embeds": [log_embed.to_dict()]})
        if log_response.status_code == 204:
            print("Log embed message sent via webhook.")
        else:
            print(f"Failed to send log embed message via webhook. Status code: {log_response.status_code}")

    def send_error_webhook(self, error_message):
        data = {"content": f"An error occurred while processing: {error_message}"}
        response = requests.post(WEBHOOK_URL, json=data)
        if response.status_code == 204:
            print("Error message sent successfully via webhook.")
        else:
            print(f"Failed to send error message via webhook. Status code: {response.status_code}")

def setup(bot):
    bot.add_cog(ConvertCredit(bot))