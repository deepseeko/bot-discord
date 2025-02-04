import discord
from discord import app_commands
from discord.ext import commands
from discord import Embed, Color
from datetime import datetime
from data.data import wallets, update_backup, ID_casino, LOG_CHANNEL_ID, load_backup, async_json_load, async_json_dump

class EnhancedBuyCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.products = {}
        self.ID_sellers = [1154486861113327710, 317826037050376205]
        self.CHANNELS_sell = [1279470256410071080, 1279470281009660007]
        self.BUY_CHANNEL = 1279470675337412619
        self.next_product_id = 1
        bot.loop.create_task(self.load_products())

    async def load_products(self):
        self.products = await async_json_load('data/products.json')
        if not self.products:
            self.products = {}
        self.next_product_id = max([int(id) for id in self.products.keys()], default=0) + 1

    async def save_products(self):
        await async_json_dump(self.products, 'data/products.json')

    @app_commands.command(name="add_product", description="Add a new product or restock an existing one.")
    @app_commands.describe(
        name="The product name",
        price="The price of the product",
        quantity="The quantity available",
        channel_id="The channel ID to display the product",
        thumbnail_url="The URL of the product thumbnail image",
        description="A brief description of the product",
        product_data="The product data (e.g., email:password)"
    )
    async def add_product(self, interaction: discord.Interaction, name: str, price: float, quantity: int, channel_id: str, thumbnail_url: str, description: str, product_data: str):
        if interaction.user.id not in self.ID_sellers or interaction.channel.id not in self.CHANNELS_sell:
            await interaction.response.send_message("You don't have permission to use this command here.", ephemeral=True)
            return

        product_id = str(self.next_product_id)
        self.next_product_id += 1

        self.products[product_id] = {
            "name": name,
            "price": price,
            "available": quantity,
            "items": [product_data],  # Store the product data in the first index of items
            "channel_id": int(channel_id),
            "thumbnail_url": thumbnail_url,
            "description": description
        }

        await self.save_products()

        channel = self.bot.get_channel(int(channel_id))
        if channel:
            embed = Embed(title=f"New Product: {name}", description=description, color=Color.green())
            embed.add_field(name="Price", value=f"{price} 7YAS", inline=True)
            embed.add_field(name="Available", value=str(quantity), inline=True)
            embed.add_field(name="Product ID", value=product_id, inline=False)
            embed.set_thumbnail(url=thumbnail_url)
            embed.set_footer(text=f"Use /buy {product_id} to purchase this product!")
            await channel.send(embed=embed)

        await interaction.response.send_message(f"Product {name} (ID: {product_id}) added successfully!", ephemeral=True)

    @app_commands.command(name="buy", description="Buy a product using your 7YAS balance.")
    @app_commands.describe(product_id="The ID of the product you want to buy", quantity="The quantity you want to buy (default: 1)")
    async def buy(self, interaction: discord.Interaction, product_id: str, quantity: int = 1):
        if interaction.channel.id != self.BUY_CHANNEL:
            await interaction.response.send_message("This command can only be used in the designated buy channel.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        user_id = int(interaction.user.id)
        
        if product_id not in self.products:
            await interaction.followup.send("Invalid product ID. Please check the available products and try again.", ephemeral=True)
            return

        product_info = self.products[product_id]
        required_balance = product_info['price'] * quantity

        if product_info['available'] < quantity:
            await interaction.followup.send(f"Sorry, only {product_info['available']} {product_info['name']} are available.", ephemeral=True)
            return
        await load_backup()
        if user_id not in wallets or wallets[user_id]['balance'] < required_balance:
            await interaction.followup.send(f"Insufficient balance. You need {required_balance} 7YAS for this purchase.", ephemeral=True)
            return

        wallets[user_id]['balance'] -= required_balance
        wallets[ID_casino]['balance'] += required_balance
        product_info['available'] -= quantity
        await update_backup()

        try:
            dm_embed = Embed(title=f"🎉 Your {product_info['name']} Purchase", color=Color.gold())
            dm_embed.add_field(name="🛍️ Quantity", value=f"```{quantity}```", inline=True)
            dm_embed.add_field(name="💰 Total Price", value=f"```{required_balance} 7YAS```", inline=True)
            dm_embed.add_field(name="🔑 Your Product Info", value=f"```{product_info['items'][0]}```", inline=False)
            dm_embed.add_field(name="📝 Description", value=f"```{product_info['description']}```", inline=False)
            dm_embed.set_thumbnail(url=product_info['thumbnail_url'])
            dm_embed.set_footer(text="🙏 Thank you for your purchase! Enjoy your product!")
            
            await interaction.user.send(embed=dm_embed)
        except discord.Forbidden:
            await interaction.followup.send("Unable to send you a DM. Please check your privacy settings.", ephemeral=True)
            return

        await self.save_products()
        await update_backup()

        success_embed = Embed(title="🎊 Purchase Successful", color=Color.green())
        success_embed.description = f"You have successfully purchased {quantity}x {product_info['name']}.\n{required_balance} 7YAS has been deducted from your wallet."
        success_embed.set_thumbnail(url=product_info['thumbnail_url'])
        await interaction.followup.send(embed=success_embed, ephemeral=True)

        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = Embed(title="📊 Product Purchase Log", color=Color.blue())
            log_embed.add_field(name="👤 Buyer", value=f"{interaction.user} (ID: {user_id})", inline=False)
            log_embed.add_field(name="🏷️ Product", value=f"{product_info['name']} (ID: {product_id})", inline=True)
            log_embed.add_field(name="🔢 Quantity", value=str(quantity), inline=True)
            log_embed.add_field(name="💸 Total Price", value=f"{required_balance} 7YAS", inline=True)
            log_embed.set_footer(text=f"🕒 Purchase Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
            await log_channel.send(embed=log_embed)

    @app_commands.command(name="list_products", description="List all available products.")
    async def list_products(self, interaction: discord.Interaction):
        embed = Embed(title="Available Products", color=Color.blue())
        for product_id, info in self.products.items():
            embed.add_field(
                name=f"{info['name']} (ID: {product_id})",
                value=f"Price: {info['price']} 7YAS\nAvailable: {info['available']}\nDescription: {info['description']}",
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(EnhancedBuyCommand(bot))