# bot.py
import os
import random
import datetime

import bot
from discord.ext import commands
from dotenv import load_dotenv

# from mongo.query import query_all

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Define the intents object with specific intents enabled
intents = bot.Intents.default()  # This enables the default intents like guilds and messages
intents.members = True  # Enable the member intent if you need access to members information
intents.message_content = True
intents.reactions = True
intents.messages = True
# Initialize the client with the defined intents
client = bot.Client(intents=intents)

bot = commands.Bot(command_prefix='!', intents=intents)

# Onboarding
@bot.command(name="join", help='Starts a DM with VA Calendar Bot for onboarding.')
async def join(ctx):
    if ctx.guild is not None:
        await ctx.send(f"👋 {ctx.author} - Please check your DMs for further instructions!")

    # Open a DM channel with the user
    dm_channel = await ctx.author.create_dm()

    try:
        # Introduction message
        await dm_channel.send(
            "Welcome to the VA Calendar Reminder Bot! 🗓️\n"
            "I'll guide you through the onboarding process.\n\n"
            "Let's start with your preferred email address. 📧\n"
            "Please enter a valid email to receive reminders."
        )

        # Wait for an email response
        email_message = await bot.wait_for(
            'message',
            check=lambda m: m.author == ctx.author and m.channel == dm_channel,
            timeout=120.0  # 2 minutes timeout
        )
        email = email_message.content

        # Validate the email format
        if '@' not in email or '.' not in email.split('@')[-1]:
            await dm_channel.send(
                "Uh-oh! That doesn't look like a valid email address. Please run `!join` again to restart the process."
            )
            return

        await dm_channel.send(
            "Great! Now, could you please provide your last login date to your VA medical account? 🏥\n"
            "Enter the date in **YYYY-MM-DD format**. For example, `2024-08-07`."
        )

        # Wait for a date response
        date_message = await bot.wait_for(
            'message',
            check=lambda m: m.author == ctx.author and m.channel == dm_channel,
            timeout=120.0  # 2 minutes timeout
        )
        date_input = date_message.content

        # Validate the date format
        try:
            last_login_date = datetime.datetime.strptime(date_input, '%Y-%m-%d')
        except ValueError:
            await dm_channel.send(
                "Uh-oh! That doesn't look like a valid date. Please use the format **YYYY-MM-DD** and run `!join` again."
            )
            return

        # Confirmation message
        await dm_channel.send(
            f"Thank you! 🎉\n\nHere’s what I’ve recorded:\n"
            f"- **Preferred Email**: {email}\n"
            f"- **Last Login Date**: {last_login_date.strftime('%Y-%m-%d')}\n\n"
            "You’re all set! I’ll send reminders to log in and check your VA medical account. 🗓️"
        )

        # TODO: Save the user data (email and date) to your database or file.

    except bot.TimeoutError:
        await dm_channel.send(
            "Looks like you didn't respond in time! ⌛\n"
            "No worries, just use the `!join` command again whenever you're ready. 🔄"
        )

# Log a date
@bot.command(name="log", help="Record your latest VA medical account login date.")
async def record_login(ctx):
    if ctx.guild is not None:
        await ctx.send(f"👋 {ctx.author} - Please check your DMs to record your login date!")

    # Open a DM channel with the user
    dm_channel = await ctx.author.create_dm()

    try:
        # Prompt the user for their login date
        await dm_channel.send(
            "Let's record your latest login date to your VA medical account. 🏥\n"
            "Please enter the date in **YYYY-MM-DD format**. For example, `2024-08-07`."
        )

        # Wait for the user's response
        date_message = await bot.wait_for(
            'message',
            check=lambda m: m.author == ctx.author and m.channel == dm_channel,
            timeout=120.0  # 2 minutes timeout
        )
        date_input = date_message.content

        # Validate the date format
        try:
            login_date = datetime.datetime.strptime(date_input, '%Y-%m-%d')
            await dm_channel.send(
                f"Thank you! 🎉\n"
                f"Your login date **{login_date.strftime('%Y-%m-%d')}** has been recorded. 🗓️\n"
                "We’ll remind you to log in to your VA medical account periodically."
            )

            # TODO: Save the login date to your database or data storage
            # Example: save_to_database(ctx.author.id, login_date)

        except ValueError:
            await dm_channel.send(
                "Uh-oh! That doesn't look like a valid date. Please use the format **YYYY-MM-DD** and try again by using the `!record_login` command."
            )

    except bot.TimeoutError:
        await dm_channel.send(
            "It seems like you didn't respond in time. ⌛\n"
            "If you'd like to record your login date, just use the `!record_login` command again."
        )

# Unsubscribe
@bot.command(name="unsubscribe", help="Unsubscribe from the VA Calendar Reminder Bot.")
async def unsubscribe(ctx):
    if ctx.guild is not None:
        await ctx.send(f"👋 {ctx.author} - Please check your DMs for further instructions!")

    # Open a DM channel with the user
    dm_channel = await ctx.author.create_dm()

    try:
        # Ask for confirmation
        unsubscribe_message = await dm_channel.send(
            "We're sorry to see you go! 😔\n\n"
            "Are you sure you want to unsubscribe from VA Calendar Reminder Bot?\n"
            "React with 👍 to confirm or 👎 to cancel."
        )

        # Add reactions for confirmation
        await unsubscribe_message.add_reaction('👍')
        await unsubscribe_message.add_reaction('👎')

        # Wait for the user's reaction
        def check_reaction(reaction, user):
            return (
                user == ctx.author and
                str(reaction.emoji) in ['👍', '👎'] and
                reaction.message.id == unsubscribe_message.id
            )

        reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check_reaction)

        if str(reaction.emoji) == '👍':
            # If confirmed, unsubscribe the user
            await dm_channel.send(
                "You've been unsubscribed from VA Calendar Reminder Bot. 😢\n"
                "If you ever wish to rejoin, you can always use the `!join` command!"
            )

            # TODO: Remove the user's data from your database or data storage

        elif str(reaction.emoji) == '👎':
            # If canceled, inform the user
            await dm_channel.send("No worries! You're still subscribed to our reminders. 😊")

    except bot.TimeoutError:
        # Handle timeout
        await dm_channel.send(
            "It seems like you didn't respond in time. ⌛\n"
            "If you'd like to unsubscribe, just use the `!unsubscribe` command again."
        )

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)

def run_bot():
    bot.run(TOKEN)

if __name__ == '__main__':
    run_bot()
    print("Discord bot is running")