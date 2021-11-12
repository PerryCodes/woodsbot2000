import discord
from discord_slash import SlashCommand # Importing the newly installed library.
from collections.abc import Sequence
from discord.ext import commands
from discord.ext.commands import Bot
import os
import config

client = discord.Client(intents=discord.Intents.all())
slash = SlashCommand(client, sync_commands=True) # Declares slash commands through the client.

whitelist_response_channel = 801285148691791902
report_channel = 891116195670016070
bot = Bot(command_prefix='/')

def make_sequence(seq):
    if seq is None:
        return ()
    if isinstance(seq, Sequence) and not isinstance(seq, str):
        return seq
    else:
        return (seq,)
def message_check(channel=None, author=None, content=None, ignore_bot=True, lower=True):
    channel = make_sequence(channel)
    author = make_sequence(author)
    content = make_sequence(content)
    if lower:
        content = tuple(c.lower() for c in content)
    def check(message):
        if ignore_bot and message.author.bot:
            return False
        if channel and message.channel not in channel:
            return False
        if author and message.author not in author:
            return False
        actual_content = message.content.lower() if lower else message.content
        if content and actual_content not in content:
            return False
        return True
    return check

@client.event
async def on_ready():
    print("Ready!")

guild_ids = [801253063934476359] # Put your server ID in this array.

@slash.slash(name="ping", guild_ids=guild_ids)
async def _ping(ctx): # Defines a new "context" (ctx) command called "ping."
    await ctx.send(f"Pong! ({client.latency*1000}ms)")

@slash.slash(name="whitelist", guild_ids=guild_ids)
async def _whitelist(ctx):
    await ctx.send(f"Whitelist Application Sent!")
    answer_list = await send_questions(ctx, load_questions())
    await submit_answers(generate_answers_embed(answer_list))
    

async def send_questions(message, question_list):
    preface = "Please answer all questions completely. For the best chances of getting approved please use full sentences and be as detailed as possible. You will be asked one question at a time. Reply to each question to get the next question."
    answers = {}
    await message.author.send(preface)
    for question in question_list:
        await message.author.send(question)
        response = await bot.wait_for('message', check=message_check(channel=message.author.dm_channel))
        answers[str(question)] = str(response.content)
    return answers

#Submits the answer embeded object to the whitelist responses channel. Adds reactions for approval/denial
async def submit_answers(answer_embed):
    channel = bot.get_channel(whitelist_response_channel)
    application = await channel.send(embed=answer_embed)
    await application.add_reaction('\N{White Heavy Check Mark}')
    await application.add_reaction('\N{Heavy Large Circle}')
 
#Returns list of current application questions.
def load_questions():
    question_file = open("questions.txt", "r")
    lines = question_file.read()
    question_list = lines.splitlines()
    question_file.close()
    return question_list

def generate_answers_embed(answers: dict):
    embed=discord.Embed(title="Whitelist Application", description="Please review the application for approval.")
    embed.set_author(name="Nuggies Bot")
    embed.set_thumbnail(url="https://i.imgur.com/ERXfuE5.png")
    for answer in answers:
        embed.add_field(name=answer, value=answers[answer], inline=False)    
    embed.set_footer(text="Use the appropriate emoji to approve or deny the application.")
    return embed

client.run(config.TOKEN)


# This is some new shit at the bottom...
#
# new shit
