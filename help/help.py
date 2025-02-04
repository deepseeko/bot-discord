import discord
from discord import app_commands
from discord.ext import commands
from decimal import Decimal
from data.data import wallets, update_exchange_rate, bank_data
CHANNEL_ID = 1280295543809249421
class HelpCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help7", description="Get a list of available commands")
    async def help7(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Language Selection | اختيار اللغة",
            description="Please choose your preferred language | من فضلك اختر لغتك المفضلة",
            color=discord.Color.blue()
        )
        embed.add_field(name="**English**", value="🇬🇧 Click the button below to see the commands in English", inline=False)
        embed.add_field(name="**العربية**", value="🇸🇦 اضغط على الزر أدناه لرؤية الأوامر بالعربية", inline=False)
        
        view = discord.ui.View()

        english_button = discord.ui.Button(label="English", style=discord.ButtonStyle.primary, emoji="🇬🇧")
        arabic_button = discord.ui.Button(label="العربية", style=discord.ButtonStyle.primary, emoji="🇸🇦")

        async def english_button_callback(interaction: discord.Interaction):
            command_list = [
                ("**/c7**", "Check your 7YAS balance and stats"),
                ("**/c7 {member}**", "Check balance and stats for another user"),
                ("**/c7 {user_to} {amount}**", "Send 7YAS coin to another user"),
                ("**/convertc**", "Convert 7YAS to ProBot credits"),
                ("**/convert7**", "View conversion instructions"),
                ("**/add_product**", "Add a new product or restock an existing one (Seller role required)"),
                ("**/buy**", "Buy a product using your 7YAS balance"),
                ("**/auction**", "Start an auction for a product (VIP Seller role required)"),
                ("**/list_products**", "View all available products"),
                ("**Gambling Commands**", "Play against others: type `bid {amount}` or `تحدي {amount}` in the specified channel"),
                ("**Highroller Game**", "Type `go {amount}` or `نرد {amount}` in the specified channel")
            ]
            
            embed_en = discord.Embed(title="7YAS Bot Commands", color=discord.Color.green())
            for cmd, desc in command_list:
                embed_en.add_field(name=cmd, value=desc, inline=False)
            
            await interaction.user.send(embed=embed_en)
            await interaction.response.send_message("I've sent you a DM with the command list in English.", ephemeral=True)
        
        async def arabic_button_callback(interaction: discord.Interaction):
            command_list_ar = [
                ("**/c7**", "تحقق من رصيد 7YAS والإحصائيات الخاصة بك"),
                ("**/c7 {member}**", "تحقق من رصيد وإحصائيات مستخدم آخر"),
                ("**/c7 {user_to} {amount}**", "أرسل عملة 7YAS إلى مستخدم آخر"),
                ("**/convertc**", "تحويل 7YAS إلى أرصدة ProBot"),
                ("**/convert7**", "عرض تعليمات التحويل"),
                ("**/add_product**", "إضافة منتج جديد أو إعادة تخزين منتج موجود (تحتاج إلى دور البائع)"),
                ("**/buy**", "شراء منتج باستخدام رصيد 7YAS الخاص بك"),
                ("**/auction**", "بدء مزاد لمنتج (تحتاج إلى دور بائع VIP)"),
                ("**/list_products**", "عرض جميع المنتجات المتاحة"),
                ("**أوامر القمار**", "العب ضد الآخرين: اكتب `تحدي {amount}` أو `bid {amount}` في القناة المحددة"),
                ("**لعبة الرولر العالي**", "اكتب `نرد {amount}` أو `go {amount}` في القناة المحددة")
            ]
            
            embed_ar = discord.Embed(title="أوامر بوت 7YAS", color=discord.Color.green())
            for cmd, desc in command_list_ar:
                embed_ar.add_field(name=cmd, value=desc, inline=False)
            
            await interaction.user.send(embed=embed_ar)
            await interaction.response.send_message("لقد أرسلت لك قائمة الأوامر عبر الرسائل الخاصة باللغة العربية.", ephemeral=True)

        english_button.callback = english_button_callback
        arabic_button.callback = arabic_button_callback

        view.add_item(english_button)
        view.add_item(arabic_button)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="convert7", description="View conversion instructions")
    async def convert7(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        
        if user_id not in wallets:
            await interaction.response.send_message(
                f"**:warning: {interaction.user.name}, you don't have an active wallet!**\n"
                f"Please activate your wallet by using the `/activewallet` command in <#1277582775180066899>.",
                ephemeral=True
            )
            return
        
        await update_exchange_rate()
        convert_rate = Decimal(str(bank_data['exchange_rate']))

        embed = discord.Embed(
            title="Language Selection | اختيار اللغة",
            description="Please choose your preferred language | من فضلك اختر لغتك المفضلة",
            color=discord.Color.blue()
        )
        embed.add_field(name="**English**", value="🇬🇧 Click the button below to see the conversion instructions in English", inline=False)
        embed.add_field(name="**العربية**", value="🇸🇦 اضغط على الزر أدناه لرؤية تعليمات التحويل بالعربية", inline=False)
        
        view = discord.ui.View()

        english_button = discord.ui.Button(label="English", style=discord.ButtonStyle.primary, emoji="🇬🇧")
        arabic_button = discord.ui.Button(label="العربية", style=discord.ButtonStyle.primary, emoji="🇸🇦")

        async def english_button_callback(interaction: discord.Interaction):
            embed_en = discord.Embed(
                title="7YAS Wallet - Convert Credits to 7YAS",
                description="**Here's how you can convert your ProBot Credits to 7YAS and vice versa:**",
                color=0x3498db
            )
            embed_en.add_field(name=":currency_exchange:", value=f"**Transfer your desired amount of ProBot Credits to the bank account <@1241716928561680397> in <#{CHANNEL_ID}>.**", inline=False)
            embed_en.add_field(name=":currency_exchange:", value=f"**For every `1 7YAS`:dollar:,\nyou will receive `{convert_rate:.0f}` credit...ect:yen:**.", inline=False)
            embed_en.add_field(name=":robot:", value="**After the transfer, the converted 7YAS will be added to your wallet automatically.**", inline=False)
            embed_en.add_field(name=":white_check_mark: Conversion Stats", value=f"**> BANK7Y has successfully converted `{conversion_count}` times!**", inline=False)
            embed_en.add_field(name="Current Wallet Balance", value=f"`{wallets[user_id]['balance']} 7YAS`", inline=False)
            embed_en.set_thumbnail(url="https://i.top4top.io/p_3159x90111.jpg")
            embed_en.set_footer(text="Thank you for using 7YAS Wallet!")
            
            await interaction.user.send(embed=embed_en)
            await interaction.user.send("Here is a video tutorial on how to convert: https://youtu.be/MA_GnZFJxWU")
            await interaction.user.send("Watch this video to learn how to convert 7YAS to credits: https://youtu.be/FesTS_gQxC4")
            await interaction.response.send_message("I've sent you the conversion instructions in English via DM.", ephemeral=True)
        with open("data/log_convert.txt", "r") as log_file:
            conversion_count = len(log_file.readlines())
        async def arabic_button_callback(interaction: discord.Interaction):
            embed_ar = discord.Embed(
                title="محفظة 7YAS - تحويل الأرصدة إلى 7YAS",
                description="**إليك كيفية تحويل أرصدة ProBot إلى 7YAS والعكس:**",
                color=0x3498db
            )
            embed_ar.add_field(name=":currency_exchange:", value=f"**قم بتحويل المبلغ الذي تريده من أرصدة ProBot إلى حساب البنك <@1241716928561680397> في <#{CHANNEL_ID}>.**", inline=False)
            embed_ar.add_field(name=":currency_exchange:", value=f"**مقابل كل `1 7YAS`:dollar:، ستحصل على `{convert_rate:.0f}` رصيد...الخ:yen:**.", inline=False)
            embed_ar.add_field(name=":robot:", value="**بعد التحويل، سيتم إضافة 7YAS المحولة إلى محفظتك تلقائيًا.**", inline=False)
            embed_ar.add_field(name=":white_check_mark: إحصائيات التحويل", value=f"**> BANK7Y ، لقد تم التحويل بنجاح `{conversion_count}` مرة!**", inline=False)
            embed_ar.add_field(name="الرصيد الحالي للمحفظة", value=f"`{wallets[user_id]['balance']} 7YAS`", inline=False)
            embed_ar.set_thumbnail(url="https://i.top4top.io/p_3159x90111.jpg")
            embed_ar.set_footer(text="شكرًا لاستخدامك محفظة 7YAS!")
            
            await interaction.user.send(embed=embed_ar)
            await interaction.user.send("إليك فيديو تعليمي حول كيفية التحويل: https://youtu.be/uMpCxvgjV0s")
            await interaction.user.send("شاهد هذا الفيديو لتعلم كيفية صرف عملات 7YAS إلى كريديت: https://youtu.be/FesTS_gQxC4")
            await interaction.response.send_message("لقد أرسلت لك تعليمات التحويل بالعربية عبر الرسائل الخاصة.", ephemeral=True)
        
        english_button.callback = english_button_callback
        arabic_button.callback = arabic_button_callback

        view.add_item(english_button)
        view.add_item(arabic_button)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# Function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(HelpCommands(bot))
