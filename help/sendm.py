import discord
from discord import app_commands
from discord.ext import commands
from discord import Embed, Color
import asyncio

class Messaging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="sendm", description="Send a DM to all server members.")
    @app_commands.describe(title="Title of the message", message="The message to send")
    async def sendm(self, interaction: discord.Interaction, title: str, message: str):
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return

        members = [member for member in interaction.guild.members if not member.bot]

        total_members = len(members)
        sent_count = 0
        failed_count = 0

        await interaction.response.send_message(f"Sending messages to {total_members} members...")

        progress_message = await interaction.followup.send(f"Progress: 0/{total_members} members sent.")

        async def send_message(member):
            nonlocal sent_count, failed_count
            try:
                embed = discord.Embed(title=title, description=message, color=discord.Color.blue())
                embed.set_footer(text=f"Sent by {interaction.guild.name}")
                await member.send(embed=embed)
                sent_count += 1
            except Exception:
                failed_count += 1

        batch_size = 10  # Adjust batch size based on your needs
        for i in range(0, total_members, batch_size):
            tasks = [send_message(member) for member in members[i:i+batch_size]]
            await asyncio.gather(*tasks)
            await progress_message.edit(content=f"Progress: {sent_count}/{total_members} members sent. {failed_count} failed.")
            await asyncio.sleep(1)

        # Final summary
        final_embed = discord.Embed(title="Message Sending Complete", color=discord.Color.green())
        final_embed.add_field(name="Total Members", value=str(total_members))
        final_embed.add_field(name="Messages Sent", value=str(sent_count))
        final_embed.add_field(name="Failed", value=str(failed_count))
        await progress_message.edit(content=None, embed=final_embed)

async def setup(bot):
    await bot.add_cog(Messaging(bot))
