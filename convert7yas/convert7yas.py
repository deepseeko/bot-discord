import discord
import requests
from discord.ext import commands
from decimal import Decimal, ROUND_DOWN
from datetime import datetime
import asyncio
from discord import Client, app_commands
from data.data import load_bank_data, update_exchange_rate, update_backup, save_bank_data, load_backup, wallets, bank_data
USER_TOKEN = 'TOKEB BANK account '
# Channel ID for conversion (to be checked before executing the command)
CONVERSION_CHANNEL_ID = 1280304070753517752
active_conversions = set()  # Track active conversions to prevent multiple conversions at once
CHANEL_CONVERT = 1278733342690250833
API_ENDPOINT = f'https://discord.com/api/v9/channels/{CHANEL_CONVERT}/messages'
CHANNEL_ID = 1280304070753517752

active_conversions = {}


class BankCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="convertc", description="Convert 7YAS to ProBot Credits")
    @app_commands.describe(amount="Amount of 7YAS to convert")
    async def convertc(self, interaction: discord.Interaction, amount: float):
        channel_id = interaction.channel_id

        if channel_id != CONVERSION_CHANNEL_ID:
            await interaction.response.send_message("This command can only be used in the designated conversion channel.", ephemeral=True)
            return

        if channel_id in active_conversions:
            await interaction.response.send_message("A conversion is already in progress in this channel. Please wait for it to complete.", ephemeral=True)
            return

        # Mark this channel as having an active conversion
        active_conversions[channel_id] = True

        try:
            await load_backup()
            await update_exchange_rate()

            user_id = interaction.user.id

            if amount <= 0:
                await interaction.response.send_message("Please enter a positive amount to convert.", ephemeral=True)
                return

            if wallets[user_id]['balance'] < amount:
                await interaction.response.send_message("You don't have enough 7YAS to convert.", ephemeral=True)
                return

            amount_decimal = Decimal(str(amount))
            original_balance = wallets[user_id]['balance']

            wallets[user_id]['balance'] -= amount
            await update_backup()
            await update_exchange_rate()

            value_in_credits = (amount_decimal * Decimal(float(bank_data['exchange_rate']))).quantize(Decimal('0.01'), rounding=ROUND_DOWN)

            embed = discord.Embed(title="7YAS to ProBot Credits Conversion", color=discord.Color.green())
            embed.add_field(name="Amount to Convert", value=f"{amount} 7YAS")
            embed.add_field(name="Estimated Credits", value=f"{value_in_credits} Credits")
            await interaction.response.send_message(embed=embed)

            headers = {
                'Authorization': USER_TOKEN,
                'Content-Type': 'application/json'
            }
            data = {
                'content': f"c <@{user_id}> {int(value_in_credits)}",
            }
            response = requests.post(API_ENDPOINT, headers=headers, json=data)

            if response.status_code != 200:
                wallets[user_id]['balance'] = original_balance
                await interaction.followup.send("Failed to send conversion request. Please try again later.", ephemeral=True)
                return

            def probot_captcha_check(m):
                return m.author.id == 282859044593598464 and m.channel.id == int(CHANEL_CONVERT) and len(m.attachments) > 0

            try:
                captcha_msg = await self.bot.wait_for('message', check=probot_captcha_check, timeout=30.0)
                captcha_image_url = captcha_msg.attachments[0].url
                #print(f"{captcha_image_url}")

                captcha_embed = discord.Embed(title="CAPTCHA Verification", color=discord.Color.blue())
                captcha_embed.add_field(name="Instructions", value="Please enter the numbers shown in the CAPTCHA image below.", inline=False)
                captcha_embed.set_image(url=captcha_image_url)
                await interaction.followup.send(embed=captcha_embed)

                def user_captcha_response_check(m):
                    return m.author.id == user_id and m.channel.id == int(CHANNEL_ID)
                #print("wait fot respone ")
                user_captcha_response = await self.bot.wait_for('message', check=user_captcha_response_check, timeout=10.0)
                #print ("respone from user is done ")
                data = {
                    'content': user_captcha_response.content,
                }
                response = requests.post(API_ENDPOINT, headers=headers, json=data)

                if response.status_code != 200:
                    wallets[user_id]['balance'] = original_balance
                    await interaction.followup.send("Failed to send CAPTCHA response. Please try again later.", ephemeral=True)
                    return

            except asyncio.TimeoutError:
                wallets[user_id]['balance'] = original_balance
                await interaction.followup.send("CAPTCHA verification timed out. Please try again.", ephemeral=True)
                return

            def probot_confirmation_check(m):
                return m.author.id == 282859044593598464 and m.channel.id == CHANEL_CONVERT and '|' in m.content

            try:
                confirmation_msg = await self.bot.wait_for('message', check=probot_confirmation_check, timeout=30.0)

                content = confirmation_msg.content
                start_idx = content.index('|') + 2
                end_idx = content.index(',', start_idx)
                sender = content[start_idx:end_idx]

                amount_start = content.index('$') + 1
                amount_end = content.index(' ', amount_start)
                amount_send = int(''.join(filter(str.isdigit, content[amount_start:amount_end])))

                id_start = content.index('!') + 1
                id_end = content.index('>', id_start)
                ID_Send_To = int(content[id_start:id_end])
                value_after_tax = int(int(value_in_credits) - (int(value_in_credits) * 0.05))

                if ID_Send_To == user_id and value_after_tax == amount_send:
                    await update_backup()
                    success_embed = discord.Embed(title="Conversion Successful!", color=discord.Color.green())
                    success_embed.add_field(name="Converted", value=f"{amount} 7YAS", inline=True)
                    success_embed.add_field(name="Received", value=f"{value_in_credits} Credits", inline=True)
                    success_embed.add_field(name="Exchange Rate", value=f"{bank_data['exchange_rate']}", inline=False)
                    success_embed.set_footer(text="Thank you for using our service! 🎉")
                    await interaction.followup.send(embed=success_embed)
                else:
                    wallets[user_id]['balance'] = original_balance
                    await update_backup()
                    await interaction.followup.send(f"There was an error in processing your conversion. Please try again.", ephemeral=True)

            except asyncio.TimeoutError:
                wallets[user_id]['balance'] = original_balance
                await update_backup()
                await interaction.followup.send("Did not receive confirmation from ProBot. Please check if the conversion was successful.", ephemeral=True)

        finally:
            del active_conversions[channel_id]
