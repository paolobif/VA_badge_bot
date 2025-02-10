# bot.py
import os
import random
import datetime
import asyncio
import json

import discord
from discord.ext import commands
from dotenv import load_dotenv
from urllib.parse import urljoin
from dateutil import parser

from mongo.database import DataBase





load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
PASS = os.getenv('MONGO_PASS')

WEB_URL = "https://vabot-g6b3cfafa8fybfdj.westus2-01.azurewebsites.net"

locked_channels = {}

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

# Command check to ensure the user is registered
def is_registered():
    """A command check that ensures the user is in the database."""
    async def predicate(ctx):
        # Replace 'db.check_discord' with whatever logic checks if the user is registered
        if db.check_discord(ctx.author.id):
            return True
        else:
            return False
    return commands.check(predicate)

# Manages to saved locked channels for the bot...
SAVE_FILE = "locked_channels.json"

def load_locked_channels():
    global locked_channels
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            locked_channels = json.load(f)  # e.g., {guild_id_str: channel_id_str}

def save_locked_channels():
    with open(SAVE_FILE, "w") as f:
        json.dump(locked_channels, f)

# On load what it runs.
@bot.event
async def on_ready():
    load_locked_channels()  # load once bot is ready
    print("Locked channels loaded:", locked_channels)

# Command to set the locked channel
@bot.command(name="setchannel", help="Sets the locked channel for this server.")
@commands.has_permissions(manage_guild=True)
async def set_channel(ctx, channel: discord.TextChannel):
    locked_channels[str(ctx.guild.id)] = str(channel.id)
    save_locked_channels()
    await ctx.send(f"Locked channel set to {channel.mention}")

@bot.command(name="clearchannel", help="Clears the locked channel setting for this server.")
@commands.has_permissions(manage_guild=True)  # Optional: require Manage Server permission
async def clear_channel(ctx):
    guild_id_str = str(ctx.guild.id)
    if guild_id_str in locked_channels:
        locked_channels.pop(guild_id_str)
        save_locked_channels()
        await ctx.send("The locked channel setting has been cleared for this server. The bot will now respond in any channel.")
    else:
        await ctx.send("No locked channel is currently set for this server.")

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
            "Enter the date in **MM-DD-YYYY format**. For example, `01-02-24`. \n\n"
            "Really, any format will work! We'll let you know if we don't understand."
        )

        # Wait for a date response
        date_message = await bot.wait_for(
            'message',
            check=lambda m: m.author == ctx.author and m.channel == dm_channel,
            timeout=120.0  # 2 minutes timeout
        )
        date_input = date_message.content

        last_login_date = convert_to_iso(date_input)

        if last_login_date is None:
            await dm_channel.send(
                "Uh-oh! That doesn't look like a valid date. Please use a different format like DD-MM-YYYY `!join` again."
            )
            return

        # # Validate the date format
        # try:
        #     last_login_date = datetime.datetime.strptime(date_input, '%Y-%m-%d')
        # except ValueError:
        #     await dm_channel.send(
        #         "Uh-oh! That doesn't look like a valid date. Please use the format **YYYY-MM-DD** and run `!join` again."
        #     )
        #     return

        # Confirmation message
        web_url = f"{WEB_URL}/download_calendar/{ctx.author.id}"

        await dm_channel.send(
            f"Thank you! 🎉\n\nHere’s what I’ve recorded:\n"
            f"- **Preferred Email**: {email}\n"
            f"- **Last Login Date**: {last_login_date.strftime('%Y-%m-%d')}\n\n"
            "You’re all set! I’ll send reminders to log in and check your VA medical account. 🗓️\n\n"
            "Additionally, you can subscribe to your calendar to receive automatic updates. \n\n"
            "• **Others**: Copy and paste the URL below into your preferred calendar app’s “Subscribe by URL” or “Add Calendar” feature.\n\n"
            f"```\n{web_url}\n```\n"
            "or type `!instructions` for more detailed instructions."
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
@is_registered()
async def record_login(ctx):
    if ctx.guild is not None:
        await ctx.send(f"👋 {ctx.author} - Please check your DMs to record your login date!")

    # Open a DM channel with the user
    dm_channel = await ctx.author.create_dm()

    # Send initial prompt message
    message = await dm_channel.send(
        "Let's record your latest login date to your VA medical account. 🏥\n"
        "Please enter the date in **MM-DD-YYYY format**. For example, `02-02-24` or `Feb 2, 24`, or react with 👍 to log today's date."
    )

    # Add a thumbs up reaction to the message
    await message.add_reaction('👍')

    def check_message(m):
        return m.author == ctx.author and m.channel == dm_channel

    def check_reaction(reaction, user):
        return user == ctx.author and str(reaction.emoji) == '👍' and reaction.message.id == message.id

    try:
        # Wait for a message or reaction
        task_message = asyncio.create_task(
            bot.wait_for('message', check=check_message, timeout=120.0)
        )
        task_reaction = asyncio.create_task(
            bot.wait_for('reaction_add', check=check_reaction, timeout=120.0)
        )

        done, pending = await asyncio.wait(
            [task_message, task_reaction],
            return_when=asyncio.FIRST_COMPLETED
        )

        for task in pending:
            task.cancel()  # Cancel all pending tasks

        if done:
            res = done.pop().result()
            if isinstance(res, discord.Message):
                # User sent a message with the date
                date_input = res.content

                login_date = convert_to_iso(date_input)

                if login_date is None:
                    await dm_channel.send(
                        "Uh-oh! That doesn't look like a valid date. Please use a different format like MM-DD-YYYY `!join` again."
                    )
                    return

                response = f"Today's date **{login_date.strftime('%Y-%m-%d')}** has been recorded as your login date. 🗓️"
                await dm_channel.send(response)

            elif isinstance(res, tuple):
                # User reacted with thumbs up, log today's date
                login_date = datetime.datetime.today()
                response = f"Today's date **{login_date.strftime('%Y-%m-%d')}** has been recorded as your login date. 🗓️"
                await dm_channel.send(response)

            # Update the user's data in the database
            try:
                db.update_last_login(ctx.author.id, login_date.isoformat())
            except Exception as e:
                print("Error updating last login date:", e)


    except asyncio.TimeoutError:
        await dm_channel.send(
            "It seems like you didn't respond in time. ⌛\n"
            "If you'd like to record your login date, just use the `!record_login` command again."
        )

# Unsubscribe
@bot.command(name="unsubscribe", help="Unsubscribe from the VA Calendar Reminder Bot.")
@is_registered()
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
@is_registered()
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
        web_url = f"{WEB_URL}/download_calendar/{ctx.author.id}"

        await dm_channel.send(
            f"**Your next VA medical account login date:** {readable_date_time} 🗓️\n\n"
            "Stay on top of your reminders by subscribing to your personal calendar! 🎉\n\n"

            "Here’s the calendar link (easy to copy):\n"
            f"```bash\n{web_url}\n\n``` \n\n"
            "**For help subscribing** to your calendar in Outlook, Google Calendar, etc... -\n"
            "type `!instructions`"
        )
    else:
        await dm_channel.send(
            "It seems like you haven't subscribed to VA Calendar Reminder Bot yet. 😅\n"
            "Use the `!join` command to get started!"
        )

# Instructions for linking the calendar
@bot.command(name="instructions", help="Provides instructions on how to add the calendar feed to your calendar app.")
async def instructions(ctx):
    """
    Explains how to add the user's ICS link to different calendar apps or platforms.
    """
    # Decide whether to send instructions in the current channel or via DM
    # Here, we'll DM the user for cleanliness, but you could just use `await ctx.send(...)` for a channel message.
    dm_channel = await ctx.author.create_dm()

    # Generate the user's calendar link, e.g., an HTTPS link to download the ICS file
    # If your route ends with .ics, consider including that in the URL.
    user_calendar_url = f"{WEB_URL}download_calendar/{ctx.author.id}.ics"

    instructions_text = (
        "**How to Add the VA Badge Reminder Calendar**\n\n"
        "Below are instructions for adding the calendar to some common calendar apps. "
        "Your personal link is included at the bottom.\n\n"
        "**1. Apple Calendar (iOS/macOS)** 🏠\n"
        "• On **iPhone/iPad**: Open Safari and enter a link that starts with `webcal://` (if supported). "
        "  Since Discord doesn't make `webcal://` clickable, you might need to copy/paste it into Safari.\n"
        "• Alternatively, open Safari at the regular HTTPS link and if prompted, allow subscription.\n"
        "• Follow the on-screen prompts to confirm you want to add this subscription.\n\n"
        "**2. Google Calendar (Web/Desktop)** 🌐\n"
        "• Go to [Google Calendar](https://calendar.google.com) in a web browser.\n"
        "• On the left sidebar, find **Other calendars** → **Add by URL**.\n"
        f"• Paste the link below (`{user_calendar_url}`) into the **URL** field.\n"
        "• Click **Add Calendar** and wait for it to import.\n\n"
        "**3. Outlook (Desktop)** 📧\n"
        "• In Outlook, go to **File** → **Account Settings** → **Account Settings**.\n"
        "• Select the **Internet Calendars** tab, then **New**.\n"
        f"• Paste the link: `{user_calendar_url}`\n"
        "• Click **Add**, then **Close**. The calendar should appear under **Other Calendars**.\n\n"
        "**4. Other Devices/Apps**\n"
        "• Most calendar apps have an option like 'Subscribe by URL' or 'Add Calendar via URL'.\n"
        "• Copy the link below and paste it where your app instructs.\n\n"
        "**Your Personal Calendar Link**:\n"
        "```\n"
        f"{user_calendar_url}\n"
        "```\n"
        "Depending on the app, you can either click it (if supported) or copy/paste it. "
        "If you're on iOS/macOS and want to try a `webcal://` link, replace the prefix `https://` with `webcal://` "
        "when entering it in Safari.\n\n"
        "If you run into any trouble, just let me know!"
    )

    await dm_channel.send(instructions_text)

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
        await ctx.send("It looks like that command doesn't exist. Try using `!help` to see the list of available commands. To log a date use `!log`")
    elif isinstance(error, commands.CheckFailure):
        # The user failed a custom check (e.g., not registered).
        # Does nothing....
        await ctx.send("You must run `!join` first to register before using this command.")
        # pass
    else:
        # If you want, handle other types of errors here
        raise error  # Reraises the error if it's not a CommandNotFound to avoid suppressing unintended errors

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.guild:
        locked_id = locked_channels.get(str(message.guild.id))
        if locked_id is None:
            # If no lock permsions have been set yet.
            pass
        elif locked_id and locked_id == str(message.channel.id):
            # If the user message is not "join"
            pass
        else:
            return

    await bot.process_commands(message)

def run_bot():
    bot.run(TOKEN)


# Converts any date string to a datetime object
def convert_to_iso(date_string):
    """
    Attempts to parse a date/time string in various common formats
    and returns a standard ISO 8601 string (e.g., '2025-02-09T14:30:00').

    :param date_string: A string representing a date/time in any of many possible formats.
    :return: ISO-formatted date/time string if parsing succeeds, otherwise None.
    """
    try:
        # Use dateutil.parser to parse the input string
        dt = parser.parse(date_string)
        return dt
    except (ValueError, TypeError):
        # If parsing fails, handle or return None
        return None


if __name__ == '__main__':
    print("Launching bot!")
    run_bot()