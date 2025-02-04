import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
import json
import aiohttp
YOUR_SERVER_ID = 1276474212424482856
AUCTION_WEBHOOK = "https://ptb.discord.com/api/webhooks/1277311619789099099/KPojk8q-OUJkgPpFmTywnZ7u5rf4uKBCVfs-JVmrsqCCVTU0jpbd8hB_EJKDFHj3tYWU"
ID_CASINO = 1184558236758720582
Auction_chanel = [1279548108728172625,1279548103170592968]

# Import necessary functions and variables from other filesclientclient
from data.data import wallets ,update_backup, load_backup, update_exchange_rate, save_bank_data, load_bank_data






class AuctionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="auction", description="🏷️ Start an auction for a product")
    @app_commands.describe(
        product_name="Name of the product",
        product="Digital product information (e.g., email:password)",
        duration_minutes="Duration of the auction in minutes",
        max_price="Maximum price for instant purchase",
        starting_price="Starting bid price",
        bid_increment="Minimum bid increment",
        channel_id="ID of the channel to host the auction"
    )
    async def auction(self, interaction: discord.Interaction, product_name: str, product: str,
                      duration_minutes: int, max_price: float, starting_price: float,
                      bid_increment: float, channel_id: str):
        if interaction.guild.id != YOUR_SERVER_ID or interaction.channel.id not in Auction_chanel:
            await interaction.response.send_message("🚫 **This command can only be used in the designated channel by the server owner.**", ephemeral=True)
            return
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("🚫 **Only the server owner can use this command.**", ephemeral=True)
            return

        await interaction.response.send_message("🎉 **Starting the auction process...**", ephemeral=True)

        try:
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                await interaction.followup.send("❌ **Invalid channel ID provided.**", ephemeral=True)
                return
        except ValueError:
            await interaction.followup.send("❌ **Invalid channel ID format.**", ephemeral=True)
            return

        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        current_bid = starting_price
        current_winner = None
        bid_history = []
        auction_ended = False
        last_bidder = None

        async def update_embed():
            remaining_time = max(int((end_time - datetime.now()).total_seconds()), 0)
            embed = discord.Embed(title=f"🎉 Auction: {product_name}", description="Digital Product: [HIDDEN]", color=0x00ff00)
            embed.add_field(name="💰 Max Price", value=f"{max_price} 7YAS", inline=True)
            embed.add_field(name="🏷️ Current Bid", value=f"{current_bid} 7YAS", inline=True)
            embed.add_field(name="🏆 Current Winner", value=current_winner.name if current_winner else "No bids yet", inline=True)
            embed.add_field(name="⏳ Time Remaining", value=f"{remaining_time // 60}m {remaining_time % 60}s", inline=False)
            embed.add_field(name="📊 Bid History", value="\n".join(bid_history[-5:]) or "No bids yet", inline=False)
            embed.set_footer(text=f"Minimum Bid Increment: {bid_increment} 7YAS")
            return embed

        async def log_auction_event(event_type, details):
            log_embed = discord.Embed(title=f"🏷️ Auction Event: {event_type}", color=discord.Color.gold())
            log_embed.add_field(name="Product", value=product_name, inline=False)
            log_embed.add_field(name="Digital Product", value=f"||{product}||", inline=False)
            for key, value in details.items():
                log_embed.add_field(name=key, value=value, inline=True)
            log_embed.set_footer(text=f"Event Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")

            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(AUCTION_WEBHOOK, session=session)
                await webhook.send(embed=log_embed)

        class AuctionView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)

            @discord.ui.button(style=discord.ButtonStyle.green, label="Buy Now!", emoji="💎", custom_id="buy_now")
            async def buy_now(self, interaction: discord.Interaction, button: discord.ui.Button):
                nonlocal current_winner, current_bid, auction_ended, last_bidder
                if auction_ended:
                    await interaction.response.send_message("🚫 **This auction has already ended.**", ephemeral=True)
                    return
                if wallets.get(interaction.user.id, {}).get('balance', 0) >= max_price:
                    await load_bank_data()
                    await load_backup()
                    wallets[interaction.user.id]['balance'] -= max_price
                    wallets[ID_CASINO]['balance'] += max_price
                    if last_bidder:
                        wallets[last_bidder.id]['balance'] += current_bid
                        wallets[ID_CASINO]['balance'] -= current_bid
                    await update_backup()
                    await save_bank_data()
                    await update_exchange_rate()
                    current_bid = max_price
                    current_winner = interaction.user
                    bid_history.append(f"💎 {interaction.user.name} bought now for {max_price} 7YAS!")
                    await interaction.response.send_message(embed=discord.Embed(
                        title="🎊 Item Bought!",
                        description=f"**`{interaction.user.name}` has bought the item for `{max_price}` 7YAS!**",
                        color=0xFFD700
                    ), ephemeral=False)
                    auction_ended = True
                    await end_auction()
                else:
                    await interaction.response.send_message("💔 **You don't have enough balance to buy now. Use '/convert7' To Get 7YAS coins**", ephemeral=True)
                await log_auction_event("Buy Now", {
                    "Buyer": f"{interaction.user} (ID: {interaction.user.id})",
                    "Price": f"{max_price} 7YAS"
                })

            @discord.ui.button(style=discord.ButtonStyle.primary, label="Bid Now!", emoji="🔨", custom_id="bid_now")
            async def bid_now(self, interaction: discord.Interaction, button: discord.ui.Button):
                nonlocal current_bid, current_winner, auction_ended, end_time, last_bidder
                if auction_ended:
                    await interaction.response.send_message("🚫 **This auction has already ended.**", ephemeral=True)
                    return
                bid_amount = current_bid + bid_increment
                if wallets.get(interaction.user.id, {}).get('balance', 0) >= bid_amount:
                    await load_bank_data()
                    await load_backup()
                    if last_bidder:
                        wallets[last_bidder.id]['balance'] += current_bid
                        wallets[ID_CASINO]['balance'] -= current_bid
                        await last_bidder.send(embed=discord.Embed(
                            title="😱 You've Been Outbid!",
                            description=f"**`{interaction.user.name}` has outbid you with a bid of `{bid_amount}` 7YAS!**",
                            color=0xFF0000
                        ))
                    wallets[interaction.user.id]['balance'] -= bid_amount
                    wallets[ID_CASINO]['balance'] += bid_amount
                    await update_backup()
                    await save_bank_data()
                    await update_exchange_rate()
                    current_bid = bid_amount
                    current_winner = interaction.user
                    last_bidder = interaction.user
                    bid_history.append(f"🔨 {interaction.user.name} bid {bid_amount} 7YAS")
                    end_time = datetime.now() + timedelta(minutes=duration_minutes)
                    await interaction.response.send_message(f"🎉 **You are now the highest bidder at `{current_bid}` 7YAS!**", ephemeral=True)
                    await message.edit(embed=await update_embed())
                else:
                    await interaction.response.send_message("💔 **You don't have enough balance to place this bid.**", ephemeral=True)
                await log_auction_event("New Bid", {
                    "Bidder": f"{interaction.user} (ID: {interaction.user.id})",
                    "Bid Amount": f"{bid_amount} 7YAS"
                })

        view = AuctionView()
        message = await channel.send(embed=await update_embed(), view=view)

        async def end_auction():
            nonlocal auction_ended
            auction_ended = True
            for child in view.children:
                child.disabled = True
            await message.edit(view=view)

            if current_winner:
                await log_auction_event("Auction Ended", {
                    "Winner": f"{current_winner} (ID: {current_winner.id})",
                    "Final Bid": f"{current_bid} 7YAS"
                })
                win_embed = discord.Embed(
                    title="🎉 Your stream Purchase",
                    color=0x2b2d31
                )
                win_embed.add_field(name="Quantity 💰 Total Price", value=f"1        {current_bid} 7YAS", inline=False)
                win_embed.add_field(name="🔑 Your Product Info", value=f"||{product}||", inline=False)
                win_embed.add_field(name="📝 Description", value=product_name, inline=False)
                win_embed.add_field(name="🎊 Thank you for your purchase! Enjoy your product!", value="", inline=False)
                win_embed.set_thumbnail(url="https://i.top4top.io/p_3159x90111.jpg")
                await current_winner.send(embed=win_embed)

                end_embed = discord.Embed(
                    title="🏁 Auction Ended",
                    description=f"**The auction has ended. `{current_winner.name}` won with a bid of `{current_bid}` 7YAS!**",
                    color=0xFFD700
                )
                end_embed.set_thumbnail(url="https://i.top4top.io/p_3159x90111.jpg")
                await channel.send(embed=end_embed)
            else:
                await channel.send(embed=discord.Embed(
                    title="🏁 Auction Ended",
                    description="**The auction has ended with no winners.**",
                    color=0xFF0000
                ))

        await interaction.followup.send(f"🎉 **Auction started in {channel.mention}!**", ephemeral=True)

        while datetime.now() < end_time and not auction_ended:
            await asyncio.sleep(1)
            try:
                await message.edit(embed=await update_embed())
            except discord.errors.NotFound:
                print("The message was not found during the auction.")
                break

        if not auction_ended:
            await end_auction()

        await update_backup()
        #await update_leaderboard()
        await save_bank_data()

async def setup(bot):
    await bot.add_cog(AuctionCog(bot))
