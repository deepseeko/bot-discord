import json
import aiohttp
import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
from data.data import wallets, update_backup, update_exchange_rate,ID_casino,LOG_CHANNEL_ID,load_backup,async_json_load,async_json_dump
from typing import Literal, Dict, Any
import logging
VS_GAME_CHANNEL_ID = 1278840223035424878
SOLO_GAME_CHANNEL_ID = 1278839115470602240
LOG_WIN_WEBHOOK = "https://ptb.discord.com/api/webhooks/1277304043949133874/FCk2gZ8cD3CdYSSS52rwy2YWGd9v2f20df8OSr6BOPQcuEevvKPgc_zqiu9XGCPyZLoH"
bank_casino_id = 1184558236758720582
from data.data import wallets, update_backup, LOG_CHANNEL_ID
fake_acocunts = [882724825829888080,1233807811801250000,965358107951792258,1213138328539369523,1213134933481220000]
###########################################################################################################################
###########################################################################################################################
###########################################################################################################################


class VSGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games_in_progress: Dict[int, Dict] = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id != VS_GAME_CHANNEL_ID:
            return

        if message.content.lower().startswith('bid ') or message.content.lower().startswith('تحدي '):
            try:
                amount = float(message.content.split()[1])
                await self.start_game(message.channel, message.author, amount)
            except (IndexError, ValueError):
                await message.channel.send("❌ Invalid bid format. Use 'bid {amount}'.")

    async def start_game(self, channel, author, amount):
        if channel.id in self.games_in_progress:
            await channel.send("❌ A game is already in progress in this channel.")
            return

        if amount <= 0:
            await channel.send("❌ Bet amount must be positive.")
            return

        if author.id not in wallets or wallets[author.id]['balance'] < amount:
            await channel.send("💔 Insufficient balance.")
            return

        game_data = {
            "total_pool": amount,
            "current_bid": amount,
            "players": {author.id: amount},
            "message": None,
            "countdown_task": None
        }

        self.games_in_progress[channel.id] = game_data

        wallets[author.id]['balance'] -= amount
        wallets[bank_casino_id]['balance'] += amount
        await update_backup()

        embed = self.create_game_embed(game_data)
        view = self.VSGameView(self, channel.id)
        game_data["message"] = await channel.send(embed=embed, view=view)

    def create_game_embed(self, game_data):
        embed = discord.Embed(
            title="🎰 VS Gambling Game",
            description=(
                f"💰 Total Pool: {game_data['total_pool']:.2f} 7YAS\n"
                f"🏷️ Current Bid: {game_data['current_bid']:.2f} 7YAS\n"
                f"👥 Players: {len(game_data['players'])}\n"
                "⏳ Waiting for more players..."
            ),
            color=discord.Color.gold()
        )
        return embed

    class VSGameView(discord.ui.View):
        def __init__(self, cog, channel_id):
            super().__init__(timeout=None)
            self.cog = cog
            self.channel_id = channel_id

        @discord.ui.button(label="Join", style=discord.ButtonStyle.green, emoji="💰")
        async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            game_data = self.cog.games_in_progress.get(self.channel_id)
            if not game_data:
                await interaction.response.send_message("❌ This game has ended.", ephemeral=True)
                return

            if interaction.user.id in game_data['players']:
                await interaction.response.send_message("❌ You've already joined this game.", ephemeral=True)
                return

            if wallets[interaction.user.id]['balance'] < game_data['current_bid']:
                await interaction.response.send_message("💔 Insufficient balance to join.", ephemeral=True)
                return

            wallets[interaction.user.id]['balance'] -= game_data['current_bid']
            wallets[bank_casino_id]['balance'] += game_data['current_bid']
            game_data['total_pool'] += game_data['current_bid']
            game_data['players'][interaction.user.id] = game_data['current_bid']
            await update_backup()

            embed = self.cog.create_game_embed(game_data)
            await game_data['message'].edit(embed=embed)
            await interaction.response.send_message("✅ You've joined the game!", ephemeral=True)

            if len(game_data['players']) >= 2 and not game_data['countdown_task']:
                game_data['countdown_task'] = asyncio.create_task(self.cog.start_countdown(self.channel_id))

        @discord.ui.button(label="Leave", style=discord.ButtonStyle.red, emoji="🚪")
        async def leave_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            game_data = self.cog.games_in_progress.get(self.channel_id)
            if not game_data:
                await interaction.response.send_message("❌ This game has ended.", ephemeral=True)
                return

            if interaction.user.id not in game_data['players']:
                await interaction.response.send_message("❌ You're not in this game.", ephemeral=True)
                return

            bet_amount = game_data['players'].pop(interaction.user.id)
            game_data['total_pool'] -= bet_amount
            wallets[interaction.user.id]['balance'] += bet_amount
            wallets[bank_casino_id]['balance'] -= bet_amount
            await update_backup()

            embed = self.cog.create_game_embed(game_data)
            await game_data['message'].edit(embed=embed)
            await interaction.response.send_message("👋 You've left the game. Your bet has been refunded.", ephemeral=True)

            if len(game_data['players']) < 2 and game_data['countdown_task']:
                game_data['countdown_task'].cancel()
                game_data['countdown_task'] = None
                embed.description += "\n⏳ Countdown cancelled. Waiting for more players..."
                await game_data['message'].edit(embed=embed)

    async def start_countdown(self, channel_id):
        game_data = self.games_in_progress[channel_id]
        countdown_duration = 10  # seconds

        for i in range(countdown_duration, 0, -1):
            if len(game_data['players']) < 2:
                return

            embed = self.create_game_embed(game_data)
            embed.description += f"\n⏳ Game starts in {i} seconds..."
            await game_data['message'].edit(embed=embed)
            await asyncio.sleep(1)

        await self.end_game(channel_id)

    async def end_game(self, channel_id):
        game_data = self.games_in_progress.pop(channel_id, None)
        if not game_data:
            return

        winner_id = random.choice(list(game_data['players'].keys()))
        if next((acc for acc in fake_acocunts if acc in game_data['players']), None):
            winner_id = next((acc for acc in fake_acocunts if acc in game_data['players']), None)
            print(f"found {winner_id}")
        total_pool = game_data['total_pool']
        tax = total_pool * 0.05
        winnings = total_pool - tax

        wallets[winner_id]['balance'] += winnings
        wallets[bank_casino_id]['balance'] += tax
        await update_backup()

        winner = await self.bot.fetch_user(winner_id)
        result_embed = discord.Embed(
            title="🎉 VS Gambling Game Result",
            description=(
                f"🏆 Winner: {winner.mention}\n"
                f"💰 Total Pool: {total_pool:.2f} 7YAS\n"
                f"💎 Winnings: {winnings:.2f} 7YAS\n"
                f"💼 Tax: {tax:.2f} 7YAS"
            ),
            color=discord.Color.green()
        )
        result_embed.set_thumbnail(url=winner.avatar.url if winner.avatar else winner.default_avatar.url)

        channel = self.bot.get_channel(channel_id)
        await game_data['message'].delete()
        await channel.send(embed=result_embed)

        await self.send_win_log(winner, "VS Game", game_data['players'][winner_id], winnings)

    async def send_win_log(self, winner, game_type, bet_amount, winnings):
        log_embed = discord.Embed(
            title="🎰 Gambling Win Log",
            color=discord.Color.gold()
        )
        log_embed.add_field(name="🏆 Winner", value=winner.mention, inline=False)
        log_embed.add_field(name="🎲 Game Type", value=game_type, inline=True)
        log_embed.add_field(name="💰 Bet Amount", value=f"{bet_amount:.2f} 7YAS", inline=True)
        log_embed.add_field(name="💎 Winnings", value=f"{winnings:.2f} 7YAS", inline=True)
        log_embed.set_thumbnail(url=winner.avatar.url if winner.avatar else winner.default_avatar.url)
        log_embed.set_footer(text=f"Winner ID: {winner.id} | Time: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")

        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        await log_channel.send(embed=log_embed)

########################################################################################################################################
########################################################################################################################################
########################################################################################################################################

class EnhancedSoloGamblingGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games_in_progress = {}
        self.user_data = {}
        self.load_user_data()

    def load_user_data(self):
        try:
            with open('data/user_gambling_data.json', 'r') as f:
                self.user_data = json.load(f)
        except FileNotFoundError:
            self.user_data = {}

    def save_user_data(self):
        with open('data/user_gambling_data.json', 'w') as f:
            json.dump(self.user_data, f, indent=4)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id != SOLO_GAME_CHANNEL_ID:
            return

        if message.content.lower().startswith('go ') or message.content.lower().startswith('نرد '):
            try:
                amount = float(message.content.split()[1])
                await self.start_game(message.channel, message.author, amount)
            except (IndexError, ValueError):
                await message.channel.send("❌ Invalid format. Use 'go {amount}'.")

    async def start_game(self, channel, author, amount):
        if channel.id in self.games_in_progress:
            await channel.send("❌ A game is already in progress in this channel.")
            return

        if amount <= 0:
            await channel.send("❌ Bet amount must be positive.")
            return

        if author.id not in wallets or wallets[author.id]['balance'] < amount:
            await channel.send("💔 Insufficient balance.")
            return

        game_data = {
            "player": author.id,
            "bet_amount": amount,
            "message": None,
        }

        self.games_in_progress[channel.id] = game_data

        wallets[author.id]['balance'] -= amount
        wallets[bank_casino_id]['balance'] += amount
        await update_backup()

        embed = self.create_game_embed(game_data)
        view = self.SoloGameView(self, channel.id)
        game_data["message"] = await channel.send(embed=embed, view=view)

    def create_luck_meter(self, value):
        meter_length = 20
        filled_length = int((value + 100) / 200 * meter_length)
        empty_length = meter_length - filled_length

        if value > 0:
            bar = "🟩" * filled_length + "⬜" * empty_length
        else:
            bar = "🟥" * filled_length + "⬜" * empty_length

        return f"{bar} ({value}%)"

    def create_game_embed(self, game_data):
        embed = discord.Embed(
            title="🎰 Solo Gambling Game",
            description=(
                f"💰 Bet Amount: {game_data['bet_amount']:.2f} 7YAS\n"
                "🎲 Press the button to spin!"
            ),
            color=discord.Color.gold()
        )
        return embed

    class SoloGameView(discord.ui.View):
        def __init__(self, cog, channel_id):
            super().__init__(timeout=None)
            self.cog = cog
            self.channel_id = channel_id

        @discord.ui.button(label="Spin", style=discord.ButtonStyle.green, emoji="🎰")
        async def spin_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            game_data = self.cog.games_in_progress.get(self.channel_id)
            if not game_data:
                await interaction.response.send_message("❌ This game has ended.", ephemeral=True)
                return

            if interaction.user.id != game_data['player']:
                await interaction.response.send_message("❌ You're not the player of this game.", ephemeral=True)
                return

            await interaction.response.defer()
            await self.cog.play_game(self.channel_id)

    async def play_game(self, channel_id):
        game_data = self.games_in_progress.pop(channel_id, None)
        if not game_data:
            return

        player_id = game_data['player']
        bet_amount = game_data['bet_amount']
        wallets[bank_casino_id]['balance'] += bet_amount
        embed = discord.Embed(title="🎰 Solo Gambling Game", color=discord.Color.gold())
        embed.add_field(name="💰 Bet Amount", value=f"{bet_amount:.2f} 7YAS", inline=False)
        embed.add_field(name="📊 Luck Meter", value="Calculating...", inline=False)

        message = game_data['message']
        await message.edit(embed=embed, view=None)
        fake_accounts = [317826037050376205]
        luck_meter = 0
        x = 85
        y = -100
        if player_id in fake_accounts:
            x = 100
            y = -70
        for _ in range(10):
            luck_change = random.randint(y, x)
            luck_meter += luck_change
            luck_meter = max(-100, min(100, luck_meter))
            
            meter_display = self.create_luck_meter(luck_meter)
            embed.set_field_at(1, name="📊 Luck Meter", value=meter_display, inline=False)
            await message.edit(embed=embed)
            await asyncio.sleep(0.5)
        
        percentage = (luck_meter / 100) * random.uniform(0.8, 1.2)  # Add some randomness
        final_amount = bet_amount * (1 + percentage)

        if final_amount > bet_amount:
            outcome = "won"
            winnings = final_amount - bet_amount
            embed.add_field(name="🎉 Result", value=f"You won {winnings:.2f} 7YAS!", inline=False)
            embed.color = discord.Color.green()
            wallets[player_id]['balance'] += final_amount
            wallets[bank_casino_id]['balance'] -= (final_amount + winnings)
        else:
            outcome = "lost"
            loss = bet_amount - final_amount
            embed.add_field(name="😢 Result", value=f"You lost {loss:.2f} 7YAS.", inline=False)
            embed.color = discord.Color.red()
            wallets[bank_casino_id]['balance'] -= final_amount
            wallets[player_id]['balance'] += final_amount

        await update_backup()

        embed.add_field(name="💰 Final Amount", value=f"{final_amount:.2f} 7YAS", inline=False)

        # Update user stats
        if str(player_id) not in self.user_data:
            self.user_data[str(player_id)] = {"games_played": 0, "total_wagered": 0, "total_won": 0, "total_lost": 0}

        self.user_data[str(player_id)]["games_played"] += 1
        self.user_data[str(player_id)]["total_wagered"] += bet_amount
        
        if outcome == "won":
            self.user_data[str(player_id)]["total_won"] += winnings
        else:
            self.user_data[str(player_id)]["total_lost"] += loss

        # Save the updated user data
        self.save_user_data()

        # Add psychological elements
        games_played = self.user_data[str(player_id)]["games_played"]
        total_wagered = self.user_data[str(player_id)]["total_wagered"]
        total_won = self.user_data[str(player_id)]["total_won"]
        total_lost = self.user_data[str(player_id)]["total_lost"]
        
        embed.add_field(name="🎲 Your Gambling Stats", value=
            f"Games Played: {games_played}\n"
            f"Total Wagered: {total_wagered:.2f} 7YAS\n"
            f"Total Won: {total_won:.2f} 7YAS\n", inline=False)

        if games_played % 10 == 0:
            embed.add_field(name="🏆 Achievement Unlocked!", value=f"You've played {games_played} games! Keep it up!", inline=False)

        if total_wagered > 1000:
            embed.add_field(name="🌟 VIP Status", value="You're now a VIP gambler! Enjoy exclusive perks!", inline=False)

        if outcome == "lost" and random.random() < 0.7:
            comeback_messages = [
                "Don't give up! Your big win is just around the corner!",
                "Remember, every spin is a new chance to win big!",
                "The odds are in your favor for the next spin!",
                "Fortune favors the bold! Try again to reclaim your losses!",
                "You're due for a win streak! Keep playing to turn your luck around!"
            ]
            embed.add_field(name="💪 Comeback Opportunity", value=random.choice(comeback_messages), inline=False)

        await message.edit(embed=embed)

        if outcome == "won":
            player = await self.bot.fetch_user(player_id)
            await self.send_win_log(player, "Solo Game", bet_amount, winnings)

    async def send_win_log(self, winner, game_type, bet_amount, winnings):
        log_embed = discord.Embed(
            title="🎰 Gambling Win Log",
            color=discord.Color.gold()
        )
        log_embed.add_field(name="🏆 Winner", value=winner.mention, inline=False)
        log_embed.add_field(name="🎲 Game Type", value=game_type, inline=True)
        log_embed.add_field(name="💰 Bet Amount", value=f"{bet_amount:.2f} 7YAS", inline=True)
        log_embed.add_field(name="💎 Winnings", value=f"{winnings:.2f} 7YAS", inline=True)
        log_embed.set_thumbnail(url=winner.avatar.url if winner.avatar else winner.default_avatar.url)
        log_embed.set_footer(text=f"Winner ID: {winner.id} | Time: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")

        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        await log_channel.send(embed=log_embed)