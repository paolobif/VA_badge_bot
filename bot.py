# bot.py
import os
import random
import datetime
import asyncio

import discord
from discord.ext import commands
from dotenv import load_dotenv
from urllib.parse import urljoin

from mongo.database import DataBase





load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
PASS = os.getenv('MONGO_PASS')

WEB_URL = "https://vabot-g6b3cfafa8fybfdj.westus2-01.azurewebsites.net/"

# Initialize the database
db = DataBase(PASS)
print("Database initialized")

# Define the intents object with specific intents enabled
intents = discord.Intents.default()  # This enables the default intents like guilds and messages
intents.members = True  # Enable the member intent if you need access to members information
intents.message_content = True
intents.reactions = True
intents.messages = True
# Initialize the client with the defined intents
client = discord.Client(intents=intents)

bot = commands.Bot(command_prefix='!', intents=intents)

# Onboarding
@bot.command(name="join", aliases=["j"], help='Starts a DM with VA Calendar Bot for onboarding.')
async def join(ctx):
    if ctx.guild is not None:
        await ctx.send(f"👋 {ctx.author} - Please check your DMs for further instructions!")

    # Open a DM channel with the user
    dm_channel = await ctx.author.create_dm()

    if db.check_discord(ctx.author.id):
        print("User already exists")
        await dm_channel.send(
            "You're already subscribed to VA Calendar Reminder Bot! 📅\n"
            "If you need any assistance, feel free to use the `!help` command."
        )
        return

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
        calendar_url = urljoin(WEB_URL, f"download_calendar/{ctx.author.id}")

        await dm_channel.send(
            f"Thank you! 🎉\n\nHere’s what I’ve recorded:\n"
            f"- **Preferred Email**: {email}\n"
            f"- **Last Login Date**: {last_login_date.strftime('%Y-%m-%d')}\n\n"
            "You’re all set! I’ll send reminders to log in and check your VA medical account. 🗓️\n\n"
            "Additionally, you can add these dates automatically to your calendar. "
            "Just click the following link to download and add the event to your personal calendar: "
            f"[Add to Calendar]({calendar_url})"
        )

        # Insert the user's data into the database
        print(last_login_date.isoformat())
        insert_item = {
            "discord": str(ctx.author.name),
            "discord_id": ctx.author.id,
            "email": email,
            "last_login": last_login_date.isoformat(),
            "next_login": db.calc_next_login(last_login_date.isoformat()),
            "count": 0
        }

        try:
            db.insert(insert_item)
        except Exception as e:
            print("Error inserting item:", e)

    # Handle timeout
    except asyncio.TimeoutError:
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

    # Send initial prompt message
    message = await dm_channel.send(
        "Let's record your latest login date to your VA medical account. 🏥\n"
        "Please enter the date in **YYYY-MM-DD format**. For example, `2024-08-07`, or react with 👍 to log today's date."
    )

    # Add a thumbs up reaction to the message
    await message.add_reaction('👍')

    def check_message(m):
        return m.author == ctx.author and m.channel == dm_channel

    def check_reaction(reaction, user):
        return user == ctx.author and str(reaction.emoji) == '👍' and reaction.message.id == message.id

    try:
        # Wait for a message or reaction
        done, pending = await asyncio.wait([
            bot.wait_for('message', check=check_message, timeout=120.0),
            bot.wait_for('reaction_add', check=check_reaction, timeout=120.0)
        ], return_when=asyncio.FIRST_COMPLETED)

        for task in pending:
            task.cancel()  # Cancel all pending tasks

        if done:
            res = done.pop().result()
            if isinstance(res, discord.Message):
                # User sent a message with the date
                date_input = res.content
                try:
                    login_date = datetime.datetime.strptime(date_input, '%Y-%m-%d')
                    response = f"Your login date **{login_date.strftime('%Y-%m-%d')}** has been recorded. 🗓️"
                except ValueError:
                    await dm_channel.send(
                        "Uh-oh! That doesn't look like a valid date. Please use the format **YYYY-MM-DD** and try again by using the `!record_login` command."
                    )
                    return
            elif isinstance(res, tuple):
                # User reacted with thumbs up, log today's date
                login_date = datetime.datetime.today()
                response = f"Today's date **{login_date.strftime('%Y-%m-%d')}** has been recorded as your login date. 🗓️"

            await dm_channel.send(response)

            # Update the user's data in the database
            try:
                db.update_last_login(ctx.author.id, login_date)
            except Exception as e:
                print("Error updating last login date:", e)


    except asyncio.TimeoutError:
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

            # Remove the user from the database
            try:
                db.delete_from_discord_id(ctx.author.id)
            except Exception as e:
                print("Error deleting user:", e)

        elif str(reaction.emoji) == '👎':
            # If canceled, inform the user
            await dm_channel.send("No worries! You're still subscribed to our reminders. 😊")

    except asyncio.TimeoutError:
        # Handle timeout
        await dm_channel.send(
            "It seems like you didn't respond in time. ⌛\n"
            "If you'd like to unsubscribe, just use the `!unsubscribe` command again."
        )

# Check next login date
@bot.command(name="next", help="Check your next VA medical account login date.")
async def check_next_login(ctx):
    if ctx.guild is not None:
        await ctx.send(f"👋 {ctx.author} - Please check your DMs for your next login date!")

    # Open a DM channel with the user
    dm_channel = await ctx.author.create_dm()

    # Fetch the user's data from the database
    user_data = db.get_user(ctx.author.id)

    if user_data:
        next_login_date = user_data['next_login']
        # Parsing ISO 8601 string to datetime object
        next_login_datetime = datetime.datetime.fromisoformat(next_login_date)

        # Formatting datetime object to a more readable form
        readable_date_time = next_login_datetime.strftime("%A, %B %d, %Y")
        await dm_channel.send(
            f"Your next VA medical account login date is on **{readable_date_time}**. 🗓️"
        )
    else:
        await dm_channel.send(
            "It seems like you haven't subscribed to VA Calendar Reminder Bot yet. 😅\n"
            "Use the `!join` command to get started!"
        )

# Help command
@bot.command(name="commands", help="Displays all commands and their aliases.")
async def list_commands(ctx):
    embed = discord.Embed(title="Bot Commands List", description="Here are all the commands and their aliases:", color=0x00ff00)
    for command in bot.commands:
        # Add each command as a field in the embed
        aliases = ', '.join(command.aliases) if command.aliases else 'No aliases'
        embed.add_field(name=command.name, value=f"Aliases: {aliases}", inline=False)

    await ctx.send(embed=embed)

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        # Send a message to the user suggesting them to use the help command
        await ctx.send("It looks like that command doesn't exist. Try using `!help` to see the list of available commands.")
    else:
        # If you want, handle other types of errors here
        raise error  # Reraises the error if it's not a CommandNotFound to avoid suppressing unintended errors

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)

def run_bot():
    bot.run(TOKEN)

if __name__ == '__main__':
    print("Launching bot!")
    run_bot()