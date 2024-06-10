import discord
from discord.ext import commands
import requests
import json
import datetime

# Substitua pelo seu token
DISCORD_BOT_TOKEN = ''

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guild_reactions = True

bot = commands.Bot(command_prefix='!', intents=intents)
bot.config = {}

# Função para carregar a configuração do arquivo JSON
def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Função para salvar a configuração no arquivo JSON
def save_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)

processed_reactions = set()

# Função para enviar dados para o SheetsDB
def send_data_to_sheetdb(api_url, reaction_data):
    try:
        response = requests.post(api_url, json=reaction_data)
        response.raise_for_status()
    except Exception as e:
        print(f'Erro ao enviar dados para o SheetsDB: {e}')

@bot.event
async def on_ready():
    print(f'Bot está online!')
    bot.config = load_config()

@bot.event
async def on_message_reaction_add(reaction, user):
    if user.bot:
        return

    reaction_key = (reaction.message.id, str(reaction.emoji))
    if reaction_key in processed_reactions:
        return

    processed_reactions.add(reaction_key)

    print(f'Reação adicionada: {user.name} na mensagem {reaction.message.id} com emoji {reaction.emoji}')

@bot.command(name='setallowedrole')
async def set_allowed_role(ctx, role_id: int):
    if str(ctx.guild.id) not in bot.config:
        bot.config[str(ctx.guild.id)] = {}
    bot.config[str(ctx.guild.id)]['allowed_role_id'] = role_id
    save_config(bot.config)
    await ctx.send(f'O cargo permitido foi definido como {role_id}')

@bot.command(name='logreactions')
async def log_reactions(ctx, message_id: int):
    # Verifica se o cargo permitido está definido no arquivo de configuração
    guild_id = str(ctx.guild.id)
    if guild_id not in bot.config or 'allowed_role_id' not in bot.config[guild_id]:
        await ctx.send('O cargo permitido ainda não foi definido. Verifique o arquivo de configuração.')
        return

    author = ctx.message.author
    # Verifica se o autor tem permissão para usar o comando
    if bot.config[guild_id]['allowed_role_id'] not in [role.id for role in author.roles]:
        await ctx.send('Você não tem permissão para usar este comando.')
        return

    message = await ctx.channel.fetch_message(message_id)
    if not message:
        await ctx.send('Mensagem não encontrada.')
        return

    reaction_data = []
    for reaction in message.reactions:
        async for user in reaction.users():
            if not user.bot:
                reaction_data.append({
                    "User": user.display_name,
                    "Reaction Time": datetime.datetime.now().isoformat()
                })

    # Envia os dados para o SheetsDB
    SHEETDB_API_URL = 'https://sheetdb.io/api/v1/a9yxc50o8g9gs'  # Substitua pela sua URL do SheetsDB
    send_data_to_sheetdb(SHEETDB_API_URL, reaction_data)
    print('Dados enviados para a planilha com sucesso!')

bot.run(DISCORD_BOT_TOKEN)
