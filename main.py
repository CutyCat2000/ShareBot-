import config
import discord
from discord import ui, app_commands
import sqlite3
import datetime

db = sqlite3.connect(config.DATABASE)

cursor = db.execute('''
    CREATE TABLE IF NOT EXISTS servers (
        server_id INTEGER PRIMARY KEY,
        description TEXT,
        premium BOOLEAN,
        last_bump DATETIME,
        cooldown DATETIME
        bump_count INTEGER
    )
''')

db.close()

def text_replace(text):
    text = text.upper()
    letter_mapping = {
        'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘',
        'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 'I': '𝗜', 'J': '𝗝',
        'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢',
        'P': '𝗣', 'Q': '𝗤', 'R': '𝗥', 'S': '𝗦', 'T': '𝗧',
        'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬', 'Z': '𝗭'
    }
    replaced_text = ''.join(letter_mapping.get(char, char) for char in text)
    return replaced_text


def get_server(server_id):
    try:
        db = sqlite3.connect(config.DATABASE)
        cursor = db.cursor()
        cursor.execute('SELECT * FROM servers WHERE server_id = ?', (server_id))
        server_data = cursor.fetchone()
        if server_data:
            server_info = {
                'server_id': server_data[0],
                'description': server_data[1],
                'premium': bool(server_data[2]),
                'last_bump': server_data[3],
                'cooldown': server_data[4],
                'bump_count': server_data[5]
            }
            return server_info
        else:
            return None
    finally:
        db.close()

def set_server(server_id, description, premium, last_bump, cooldown, bump_count):
    try:
        db = sqlite3.connect(config.DATABASE)
        cursor = db.cursor()
        cursor.execute('SELECT id from servers WHERE id = ?', (server_id))
        existing_server = cursor.fetchone()
        if existing_server:
            cursor.execute('''
                UPDATE servers
                SET description = ?, premium = ?, bump = ?, cooldown = ?, bump_count = ?
                WHERE id = ?
            ''', (description, premium, last_bump, cooldown, bump_count, server_id))
        else:
            cursor.execute('''
                INSERT INTO servers (server_id, description, premium, last_bump, cooldown, bump_count)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (server_id, description, premium, last_bump, cooldown, bump_count))
        db.commit()
        return True
    except:
        return False
    finally:
        db.close()

class Client(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(intents = intents, activity = discord.CustomActivity(name = text_replace(config.STATUS_MESSAGE)))
        self.tree = app_commands.CommandTree(self)
    async def setup_hook(self):
        await self.tree.sync()
    async def on_ready(self):
        print("Bot is running")

client = Client()

@client.tree.command(name="info")
async def info_command(interaction):
    await interaction.response.defer()
    user_count = len(client.users)
    server_count = len(client.servers)
    embed = discord.Embed(title = config.NAME, color = 0xFFFFFF)
    embed.description = config.NAME + " is a powerful server promotion assistant for Discord communities."
    # add fields + buttons
    await interaction.followup.send(embed = embed)


client.run(config.TOKEN)