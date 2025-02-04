import discord
from discord import app_commands
from discord.ext import commands
import json
import aiohttp
from datetime import datetime, timedelta
import os

from data.data import (
    load_bank_data, bank_data, save_bank_data, load_backup, update_backup,
    update_exchange_rate, wallets, invite_uses, YOUR_SERVER_ID, BANK_JSON_FILE,
    SEND7_WEBHOOK, Wallet_WEBHOOK, ID_casino
)

class C7Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def load_user_gambling_data(self):
        file_path = 'data/user_gambling_data.json'
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return {}

    def calculate_level(self, total_won):
        if total_won < 50:
            return 0
        elif total_won < 120:
            return 1
        elif total_won < 250:
            return 2
        elif total_won < 500:
            return 3
        elif total_won < 5000:
            return 4
        else:
            return 5 + int((total_won - 1000) / 5000)

    @app_commands.command(name="c7", description="📊 Check your 7YAS balance and stats, or interact with other wallets.")
    @app_commands.describe(member="Member to check their 7YAS balance and stats.", user_to="Member to send 7YAS to.", amount="Amount of 7YAS to send.")
    async def c7(self, interaction: discord.Interaction, member: discord.Member = None, user_to: discord.Member = None, amount: float = None):
        await load_backup()
        user_id = int(interaction.user.id)

        # If no subcommand is provided, show the user's own stats
        if member is None and user_to is None and amount is None:
            if user_id not in wallets:
                wallets[user_id] = {'balance': 1.0, 'username': interaction.user.name, 'last_daily': datetime.now().isoformat()}
                await update_backup()
                embed = discord.Embed(title="💼 Wallet Activated", color=discord.Color.green())
                embed.description = "**Your wallet has been activated with 1 7YAS!**"
            else:
                balance = wallets[user_id]['balance']
                embed = discord.Embed(title="💰 7YAS Wallet Stats", color=discord.Color.gold())
                embed.add_field(name="💵 Balance", value=f"**{balance:,}** 7YAS", inline=False)
                
                if 'username' in wallets[user_id]:
                    embed.add_field(name="👤 Username", value=wallets[user_id]['username'], inline=False)
                
                if 'last_daily' in wallets[user_id]:
                    last_daily = datetime.fromisoformat(wallets[user_id]['last_daily'])
                    time_since_daily = datetime.now() - last_daily
                    embed.add_field(name="🕒 Last Daily Claim", value=f"{time_since_daily.days} days {time_since_daily.seconds // 3600} hours ago", inline=False)
                
                invite_count = invite_uses.get(user_id, 0)
                embed.add_field(name="🎉 Invites", value=f"**{invite_count}** new members invited", inline=False)

                gambling_data = await self.load_user_gambling_data()
                if str(user_id) in gambling_data:
                    user_gambling = gambling_data[str(user_id)]
                    total_won = user_gambling['total_won']
                    level = self.calculate_level(total_won)
                    embed.add_field(name="🎰 Gambling Stats", value=f"Games Played: **{user_gambling['games_played']}**\nTotal Won: **{total_won:,.2f}** 7YAS\n", inline=False)
                    embed.add_field(name="🏆 Gambling Level", value=f"Level **{level}**", inline=False)
                else:
                    embed.add_field(name="🎰 Gambling Stats", value="No gambling activity yet", inline=False)

            embed.set_footer(text="💡 Use /daily to claim your daily reward!")
            embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else None)
            await interaction.response.send_message(embed=embed)

        # If 'member' is provided, show the member's stats
        elif member is not None:
            member_id = member.id
            if member_id not in wallets:
                wallets[member_id] = {'balance': 1.0, 'username': member.name, 'last_daily': datetime.now().isoformat()}
                await update_backup()
                embed = discord.Embed(title="❌ No Wallet Found", color=discord.Color.red())
                embed.description = f"**{member.name} didn't have a wallet, so one has been created for them with 1 7YAS.**"
            else:
                balance = wallets[member_id]['balance']
                embed = discord.Embed(title=f"💰 {member.name}'s 7YAS Stats", color=discord.Color.blue())
                embed.add_field(name="💵 Balance", value=f"**{balance:,}** 7YAS", inline=False)
                
                if 'last_daily' in wallets[member_id]:
                    
                    last_daily = wallets[user_id].get('last_daily')
                    last_daily_dt = datetime.fromisoformat(last_daily)
                    time_since_daily = datetime.now() - last_daily_dt
                    embed.add_field(name="🕒 Last Daily Claim", value=f"{time_since_daily.days} days {time_since_daily.seconds // 3600} hours ago", inline=False)
                
                invite_count = invite_uses.get(member_id, 0)
                embed.add_field(name="🎉 Invites", value=f"**{invite_count}** new members invited", inline=False)

                gambling_data = await self.load_user_gambling_data()
                if str(member_id) in gambling_data:
                    user_gambling = gambling_data[str(member_id)]
                    total_won = user_gambling['total_won']
                    level = self.calculate_level(total_won)
                    embed.add_field(name="🎰 Gambling Stats", value=f"Games Played: **{user_gambling['games_played']}**\nTotal Won: **{total_won:,.2f}** 7YAS\n", inline=False)
                    embed.add_field(name="🏆 Gambling Level", value=f"Level **{level}**", inline=False)
                else:
                    embed.add_field(name="🎰 Gambling Stats", value="No gambling activity yet", inline=False)

            embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
            await interaction.response.send_message(embed=embed, ephemeral=True)

        # If 'user_to' and 'amount' are provided, handle the transfer
        elif user_to is not None and amount is not None:
            user_to_id = user_to.id
            
            # Check if users have wallets
            for check_id in [user_id, user_to_id]:
                if check_id not in wallets:
                    wallets[check_id] = {'balance': 1, 'username': interaction.guild.get_member(int(check_id)).name, 'last_daily': datetime.now().isoformat()}
                    await update_backup()
            
            if amount <= 0:
                await interaction.response.send_message("❌ The amount must be positive!", ephemeral=True)
                return
            
            if wallets[user_id]['balance'] < amount:
                needed = amount - wallets[user_id]['balance']
                await interaction.response.send_message(f"❌ You need **{needed:,}** more 7YAS to complete the transfer.", ephemeral=True)
                return
            
            tax = float(amount / 15)
            actual_amount = amount - tax
            
            wallets[user_id]['balance'] -= amount
            wallets[user_to_id]['balance'] += actual_amount
            wallets[ID_casino]['balance'] += tax
            await update_backup()
            
            embed = discord.Embed(title="💸 7YAS Transfer", color=discord.Color.green())
            embed.add_field(name="From", value=interaction.user.mention, inline=True)
            embed.add_field(name="To", value=user_to.mention, inline=True)
            embed.add_field(name="Amount Sent", value=f"**{actual_amount:,}** 7YAS", inline=False)
            embed.add_field(name="Tax", value=f"**{tax:,}** 7YAS", inline=False)
            embed.set_footer(text=f"Transaction Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
            
            await interaction.response.send_message(embed=embed)
            await interaction.user.send(f"💸 You sent **{actual_amount:,}** 7YAS to **{user_to}** (Tax: **{tax:,}** 7YAS)")
            await user_to.send(f"💰 You have received **{actual_amount:,}** 7YAS from **{interaction.user}**")

        else:
            await interaction.response.send_message("❌ Invalid command usage. Please check the parameters and try again.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(C7Commands(bot))