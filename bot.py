import discord
from discord.ext import commands
from discord.ext.commands import Bot
import os
from collections.abc import Sequence
import json

f = open('config.json',)
config = json.load(f)
 
for i in config['data']:
    print(i)

token = config['data']['token']

#Chat channels
whitelist_response_channel = config['data']['whitelist_response_channel']
report_channel = config['data']['report_channel']

f.close()


client = discord.Client()

whitelist_reactions = {
    "✅": "Accept",
    "⭕": "Deny",
}


bot = Bot(command_prefix='!')

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

@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user}')

@bot.event   
async def on_message(message):
    if message.author == bot.user:
        return
    else:
        await bot.process_commands(message)

@bot.command(name="whitelist")
async def whitelist(ctx):
    answer_list = await send_questions(ctx, load_questions())
    await submit_answers(generate_answers_embed(answer_list))
    await ctx.message.delete()
    
#UNDO TO HERE

@bot.command(name="addquestion")
@commands.has_role("Owner")
async def add_question_command(ctx):
    await add_question(ctx)
    channel = bot.get_channel(whitelist_response_channel)
    questions_list = load_questions()
    embed = generate_questions_embed(questions_list)
    await ctx.author.send(embed=embed)
    await channel.send("A new question has been added to the whitelist application.. Please see below.")
    await channel.send(embed=embed)
    await ctx.message.delete()

@bot.command(name="removequestion")
@commands.has_role("Owner")
async def remove_question_command(ctx):
    await remove_question(ctx)
    channel = bot.get_channel(whitelist_response_channel)
    questions_list = load_questions()
    embed = generate_questions_embed(questions_list)
    await channel.send("A question has been removed from the whitelist application. Please see below.")
    await channel.send(embed=embed)
    await ctx.message.delete()

@bot.command(name="report")
async def report_player(ctx):
    report = []
    preface = "Thank you for submitting a report to get assistance. Please answer all questions. If the question isn't relevant to your issue, please put 'none' as your answer."
    await ctx.author.send(preface)

    await ctx.author.send("What is your minecraft username?")
    response = await bot.wait_for('message', check=message_check(channel=ctx.author.dm_channel))
    report.append(response.content)

    await ctx.author.send("What issue are your reporting?")
    response = await bot.wait_for('message', check=message_check(channel=ctx.author.dm_channel))
    report.append(response.content)

    await ctx.author.send("If another player was involved please provide their username, or put 'none' if no one else was involved.")
    response = await bot.wait_for('message', check=message_check(channel=ctx.author.dm_channel))
    report.append(response.content)

    await ctx.author.send("Please provide any additional details you may think are necessary. (One message)")
    response = await bot.wait_for('message', check=message_check(channel=ctx.author.dm_channel))
    report.append(response.content)

    channel = bot.get_channel(report_channel)

    embed = generate_report_embed(report)
    await channel.send(embed=embed)

def generate_report_embed(report):
    embed=discord.Embed(title="A player has been reported!", description="Please review the report and respond appropriately.")
    embed.set_author(name="Nuggies Bot")
    embed.set_thumbnail(url="https://i.imgur.com/ERXfuE5.png")
    embed.add_field(name="Username:", value=report[0], inline=False)
    embed.add_field(name="Issue:", value=report[1], inline=False)
    embed.add_field(name="Player Reported:", value=report[2], inline=False)
    embed.add_field(name="Details:", value=report[3], inline=False)
    return embed


#Generate discord embed using the dictionary of responses from the whitelist application.
def generate_answers_embed(answers: dict):
    embed=discord.Embed(title="Whitelist Application", description="Please review the application for approval.")
    embed.set_author(name="Nuggies Bot")
    embed.set_thumbnail(url="https://i.imgur.com/ERXfuE5.png")
    for answer in answers:
        embed.add_field(name=answer, value=answers[answer], inline=False)    
    embed.set_footer(text="Use the appropriate emoji to approve or deny the application.")
    return embed    

#Generate a discord embed from provided list of questions.
def generate_questions_embed(questions_list: list):
    embed=discord.Embed(title="Whitelist Application Questions", description="The current list of application questions that new applicants receive.")
    embed.set_author(name="Nuggies Bot")
    embed.set_thumbnail(url="https://i.imgur.com/ERXfuE5.png")
    for i, question in enumerate(questions_list):
        embed.add_field(name=str(i) + ":", value=question, inline=False)
    return embed    

#Sends current whitelist application questions to author and returns a dictionary of responses.
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

#Add a question to the whitelist application question list.
async def add_question(message):
    preface = "Please type your full question below. Be sure to include proper punctionation and include a : at the end."
    preface2 = "Example: What is your favorite dipping sauce for chicken nuggets?:"
    preface3 = "What question would you like to add?"
    await message.author.send(preface)
    await message.author.send(preface2)
    await message.author.send(preface3)

    #Wait for response and write question to the file.
    response = await bot.wait_for('message', check=message_check(channel=message.author.dm_channel))
    question_file = open("questions.txt", 'a')
    question_file.write(str(response.content) + "\n")
    question_file.close()

#Remove a question from the whitelist application question list.
async def remove_question(message):

    #Load current set of questions and send them to the author.
    questions_list = load_questions()
    embed = generate_questions_embed(questions_list)
    await message.author.send(embed=embed)
    await message.author.send("Please respond with the number of the question you wish to delete.")
    await message.author.send("Example: 3")

    #Wait for selection and pop that index from the list.
    response = await bot.wait_for('message', check=message_check(channel=message.author.dm_channel))
    questions_list.pop(int(response.content))

    #Write new list of questions back to the file.
    question_file = open("questions.txt", 'w')
    for question in questions_list:
        question_file.write(str(question) + "\n")
    question_file.close()

#Update the status of an application based on the given reaction.
def update_status():
    pass

bot.run(token)
