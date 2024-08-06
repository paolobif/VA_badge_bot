# bot.py
import os
import random

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Define the intents object with specific intents enabled
intents = discord.Intents.default()  # This enables the default intents like guilds and messages
intents.members = True  # Enable the member intent if you need access to members information
intents.message_content = True
intents.reactions = True
intents.messages = True
# Initialize the client with the defined intents
client = discord.Client(intents=intents)

bot = commands.Bot(command_prefix='!', intents=intents)


# @bot.command(name="s")
# async def startsurvey(ctx):
#     """Sends a survey question and adds reactions for the user to respond."""
#     message = await ctx.send("Do you enjoy using this Discord server? React with 👍 or 👎.")
#     # Add reactions
#     await message.add_reaction('👍')

#     await message.add_reaction('👎')

#     def check(reaction, user):
#         # Make sure the reaction is on the correct message and the reactor is not the bot
#         return user != bot.user and reaction.message.id == message.id and str(reaction.emoji) in ['👍', '👎']

#     try:
#         # Wait for a reaction
#         reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
#         if str(reaction.emoji) == '👍':
#             await ctx.send(f"{user.display_name} reacted with 👍. Thanks for your positive feedback!")
#         else:
#             await ctx.send(f"{user.display_name} reacted with 👎. Thanks for your feedback!")
#     except discord.TimeoutError:
#         await ctx.send("No response received. Survey closed.")


@bot.command(name="s")
async def startsurvey(ctx):
    """Sends a survey question and adds reactions for the user to respond."""
    count = 0  # Initialize count
    update_message = f"Test count = {count}"

    message = await ctx.send(update_message)
    # Add reactions
    await message.add_reaction('👍')
    await message.add_reaction('👎')

    def check(reaction, user):
        # Make sure the reaction is on the correct message and the reactor is not the bot
        return user == ctx.author and reaction.message.id == message.id and str(reaction.emoji) in ['👍', '👎']

    while True:
        try:
            # Wait for a reaction (with a timeout for ending the survey)
            reaction, user = await bot.wait_for('reaction_add', timeout=300.0, check=check)  # 5 minutes timeout
            if str(reaction.emoji) == '👍':
                count += 1
            elif str(reaction.emoji) == '👎':
                count -= 1

            update_message = f"Test count = {count}"
            await message.edit(content=update_message)

            # Optionally remove the user's reaction to allow them to react again
            await reaction.remove(user)

        except:
            break


@bot.command(name="join")
async def join(ctx):

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel and msg.content.lower().strip()

    await ctx.send("Please enter your email:")

    try:
        msg = await bot.wait_for('message', check=check, timeout=90.0)  # 60 seconds to reply
        email = msg.content
        if "@" in email and "." in email:  # Basic check for email format
            await ctx.send("Thank you! Your email has been recorded.")
        else:
            await ctx.send("This doesn't seem like a valid email. Please try again.")
    except discord.TimeoutError:
        await ctx.send("Sorry, you didn't reply in time!")

# client.run(TOKEN)
bot.run(TOKEN)