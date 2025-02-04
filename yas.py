import discord
from discord.ext import commands
import random
from datetime import datetime, timedelta
import logging
from discord import app_commands
from decimal import Decimal, ROUND_DOWN
from gambling.gambling import VSGame,EnhancedSoloGamblingGame
from YASinfo.c7 import C7Commands
from convertcredit.convertcredit import ConvertCredit
from convert7yas.convert7yas import BankCommands
from data.data import load_bank_data , bank_data
from data.data import save_bank_data
from data.data import load_backup
from data.data import update_backup
from data.data import update_exchange_rate
from data.data import wallets
from data.data import invite_uses
from data.data import YOUR_SERVER_ID
from invites.invite_manager import handle_member_join
from gambling.gamblingbot import GamblingBot
from dotenv import load_dotenv
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('7YASBot')



intents = discord.Intents.default()
intents.members = True
intents.invites = True
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

###########################################convert data ##################################################
from dotenv import load_dotenv

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
TOKEN = os.getenv('TOKEN')

##########################################################################################################
@bot.event
async def on_ready():
    logger.info(f'{bot.user} is connected to Discord!')
    print("load data : loading")
    await load_backup()
    await load_bank_data()
    print("load data : DONE")
    print("load command files : loading...")
    await bot.add_cog(BankCommands(bot))
    await bot.add_cog(VSGame(bot))
    await bot.add_cog(EnhancedSoloGamblingGame(bot))
    await bot.add_cog(C7Commands(bot))
    await bot.add_cog(ConvertCredit(bot))
    await bot.load_extension("help.sendm")
    await bot.load_extension("help.help")
    await bot.load_extension('market.auction')
    await bot.load_extension('market.Buy_Sell')
    gambling_cog = GamblingBot(bot)
    await bot.add_cog(gambling_cog)
    await gambling_cog.send_gambling_message()
    print("load command files : DONE")
    for guild in bot.guilds:
        invites = await guild.invites()
        invite_uses[guild.id] = {invite.code: invite.uses for invite in invites}
    logger.info("Bot is ready!")
    # Sync commands
    await bot.tree.sync()
    logger.info("Commands synced successfully")
@bot.event
async def on_member_join(member):
    await handle_member_join(member, bot)
@bot.event
async def setup_hook():
    guild = discord.Object(id=YOUR_SERVER_ID)
    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)#update commands
########################################################### Liderboard 7yas########################################################

#need update

############################################## price 7yas ##########################################################

@bot.tree.command(name="price7", description="Check the current exchange rate of 7YAS to ProBot credits")
async def price7(interaction: discord.Interaction):

    await load_backup()
    await load_bank_data()
    await update_exchange_rate()
    exchange_rate = float(bank_data['exchange_rate'])

    embed = discord.Embed(title="💱 7YAS Exchange Rate", color=discord.Color.gold())
    embed.add_field(name="Current Rate", value=f"1 7YAS = {exchange_rate:.4f} ProBot Credits", inline=False)
    embed.add_field(name="Reverse Rate", value=f"{(1/exchange_rate):.4f} 7YAS = 1 ProBot Credit", inline=False)
    embed.set_footer(text="Exchange rates are subject to change based on market conditions.")

    await interaction.response.send_message(embed=embed)
############################################## value wallet ########################################################
@bot.tree.command(name="value7", description="Check the value of your 7YAS in ProBot credits")
async def value7(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id not in wallets:
        await interaction.response.send_message("You don't have a 7YAS wallet. Use `/activewallet` to create one.", ephemeral=True)
        return
    await load_backup()
    await load_bank_data()
    balance = Decimal(str(wallets[user_id]['balance']))
    exchange_rate = Decimal(str(bank_data['exchange_rate']))
    value_in_credits = balance * exchange_rate

    embed = discord.Embed(title="💰 Your 7YAS Value", color=discord.Color.green())
    embed.add_field(name="Your 7YAS Balance", value=f"{balance:.4f} 7YAS", inline=False)
    embed.add_field(name="Value in ProBot Credits", value=f"{value_in_credits:.2f} Credits", inline=False)
    embed.set_footer(text="Values are based on the current exchange rate.")

    await interaction.response.send_message(embed=embed)

#################################################SENDER MESAGES TO members##############################################################


##############################daily prize################################################

@bot.tree.command(name="daily7", description="Claim your daily reward")
async def daily7(interaction: discord.Interaction):
    user_id = interaction.user.id
    current_time = datetime.now()

    if user_id not in wallets:
        wallets[user_id] = {'balance': 0, 'username': interaction.user.name, 'last_daily': None}

    last_claim = wallets[user_id]['last_daily']
    if last_claim and (current_time - datetime.fromisoformat(last_claim)) < timedelta(days=1):
        time_left = timedelta(days=1) - (current_time - datetime.fromisoformat(last_claim))
        await interaction.response.send_message(f"You can claim again in {time_left.seconds // 3600} hours and {(time_left.seconds // 60) % 60} minutes.", ephemeral=True)
        return

    reward = random.uniform(1, 25)
    wallets[user_id]['balance'] += reward
    wallets[user_id]['last_daily'] = current_time.isoformat()

    await update_backup()
    await interaction.response.send_message(f"You've claimed your daily reward of {reward} 7YAS!", ephemeral=True)


#################################cmd Add balance To user##################################
@bot.tree.command(name="cico", description="Check all member's 7YAS balance. **OWNER**")
async def cico(interaction: discord.Interaction, check: float, user_to_check: discord.Member):
    if interaction.guild.id != YOUR_SERVER_ID:
        await interaction.response.send_message("🚫 **Only the server 7YAS owner can use this command.**", ephemeral=True)
        return
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("🚫 **Only the server owner can use this command.**", ephemeral=True)
        return
    await load_backup()
    user_to_id = user_to_check.id
    wallets[user_to_id]['balance'] += check
    print(f"DONE:{user_to_id} {wallets[user_to_id]['balance']}")
    await interaction.response.send_message(":white_check_mark:  **DONE!**", ephemeral=True)
    await update_backup()
    await update_exchange_rate()
    await save_bank_data()

bot.run('YOUR-BOT-TOKEN')
