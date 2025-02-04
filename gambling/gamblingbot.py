import discord
from discord.ext import commands
from discord.ui import Button, View, Select, Modal, TextInput
import logging
from gambling.gambling import VSGame, EnhancedSoloGamblingGame

logging.basicConfig(level=logging.INFO)

class GamblingBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vs_game = VSGame(bot)
        self.solo_game = EnhancedSoloGamblingGame(bot)

    async def send_gambling_message(self):
        channel = self.bot.get_channel(1280629762238316589) 
        if channel:
            try:
                embed = discord.Embed(
                    title="🎲 Choose Your Game",
                    description="Select the game type and enter your bet amount.",
                    color=discord.Color.blue()
                )

                embed.add_field(name="Game Options", value="1. VS Game 🆚\n2. Solo Game 🎰", inline=False)
                embed.set_footer(text="Place your bet wisely!")

                view = GamblingView(self)
                await channel.send(embed=embed, view=view)
                logging.info(f"Embed message sent successfully in channel {channel.name}")
            except Exception as e:
                logging.error(f"Failed to send embed message: {e}")
        else:
            logging.error(f"Channel with ID {1280629762238316589} not found.")

class GamblingView(View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        self.game_choice = None
        self.bet_amount = None

        self.add_item(GameSelect(self))
        self.add_item(BidButton(self))

class GameSelect(Select):
    def __init__(self, view):
        options = [
            discord.SelectOption(label="VS Game", description="Compete against another player", emoji="🆚"),
            discord.SelectOption(label="Solo Game", description="Test your luck alone", emoji="🎰"),
        ]
        super().__init__(placeholder="Choose a game...", min_values=1, max_values=1, options=options)
        self.view = view

    async def callback(self, interaction: discord.Interaction):
        self.view.game_choice = self.values[0]
        await interaction.response.send_message(f"Selected game: {self.values[0]}", ephemeral=True)
        await interaction.response.send_modal(BetAmountModal(self.view))

class BetAmountModal(Modal):
    def __init__(self, view):
        super().__init__(title="Enter Bet Amount")
        self.view = view
        self.bet_amount_input = TextInput(label="Bet Amount", placeholder="Enter your bet amount in 7YAS", required=True)
        self.add_item(self.bet_amount_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            self.view.bet_amount = float(self.bet_amount_input.value)
            await interaction.response.send_message(f"You entered: {self.view.bet_amount} 7YAS", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Please enter a valid number.", ephemeral=True)

class BidButton(Button):
    def __init__(self, view):
        super().__init__(label="Bid", style=discord.ButtonStyle.green, emoji="💸")
        self.view = view

    async def callback(self, interaction: discord.Interaction):
        if not self.view.game_choice or not self.view.bet_amount:
            await interaction.response.send_message("Please select a game and enter a bet amount first.", ephemeral=True)
            return

        if self.view.game_choice == "VS Game":
            await self.view.cog.vs_game.start_game(interaction.channel, interaction.user, self.view.bet_amount)
        elif self.view.game_choice == "Solo Game":
            await self.view.cog.solo_game.start_game(interaction.channel, interaction.user, self.view.bet_amount)

        await interaction.response.send_message("Your game has started!", ephemeral=True)
