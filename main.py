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
EMBED_COLOR_ERROR = 0xE74C3C
embed_color_mapping = {
    'teal': 0x1ABC9C,
    'purple': 0x9B59B6,
    'yellow': 0xF1C40F,
    'blue': 0x3498DB,
    'green': 0x2ECC71,
    'pink': 0xFF6B81,
    'black': 0x34495E,
    'lavender': 0xAF7AC5,
    'crimson': 0xC0392B,
    'none': 0x2F3136
}
EMBED_COLOR = embed_color_mapping.get(config.EMBED_COLOR, 0xFFFFFF)

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

async def sendNotYourButtonEmbed(interaction, userId):
    if interaction.user.id != userId:
        embed = discord.Embed(title="Not your button", description="This is not your button, please type the command yourself in this or another server to use the buttons.", color = EMBED_COLOR_ERROR)
        if config.EPHEMERAL_MESSAGES:
            await interaction.followup.send(embed=embed, ephemeral = True)
        else:
            await interaction.followup.send(embed=embed)
        return True
    return False

class InfoMainButton(ui.Button):
    def __init__(self, userId):
        super().__init__(label = "Main", emoji = "🛖")
        self.userId = userId
    async def callback(self, interaction):
        await interaction.response.defer(ephemeral = True)
        if await sendNotYourButtonEmbed(interaction, self.userId):
            return
        embed = interaction.message.embeds[0]
        server_count = len(client.guilds)
        user_count = len(client.guilds)
        try:
            db = sqlite3.connect(config.DATABASE)
            running_server_count = db.execute('SELECT COUNT(*) FROM servers').fetchone()[0]
        finally:
            db.close()
        embed.description = config.NAME + f""" is a powerful server promotion assistant for Discord communities.
Navigate through the sections of the /info menu for more.

**Stats**:
- Servers: {server_count}
- Users: {user_count}
- Running Servers: {running_server_count}"""
        await interaction.message.edit(embed = embed)

class InfoAboutButton(ui.Button):
    def __init__(self, userId):
        super().__init__(label = "About", emoji = "ℹ️")
        self.userId = userId
    async def callback(self, interaction):
        await interaction.response.defer(ephemeral = True)
        if await sendNotYourButtonEmbed(interaction, self.userId):
            return
        embed = interaction.message.embeds[0]
        embed.description = """About """+config.NAME+""":
Bot Invite: [Click here](https://discord.com/api/oauth2/authorize?client_id="""+str(client.user.id)+"""&permissions=139586751553&scope=bot%20applications.commands)
Support Server: """+config.SUPPORT_SERVER+"""
Github: https://github.com/CutyCat2000/ShareBot-"""
        await interaction.message.edit(embed = embed)
        
class InfoPermissionButton(ui.Button):
    def __init__(self, userId):
        super().__init__(label = "Permissions", emoji = "🗝️")
        self.userId = userId
    async def callback(self, interaction):
        await interaction.response.defer(ephemeral = True)
        if await sendNotYourButtonEmbed(interaction, self.userId):
            return
        embed = interaction.message.embeds[0]
        embed.description = """The required permissions are:
- CREATE_INSTANT_INVITE
- VIEW_CHANNEL
- SEND_MESSAGES
- EMBED_LINKS
- ATTACH_FILES
- ADD_REACTIONS
- USE_EXTERNAL_EMOJIS
- USE_EXTERNAL_STICKERS
- USE_APPLICATION_COMMANDS"""
        await interaction.message.edit(embed = embed)

class InfoView(ui.View):
    timeout = None
    def __init__(self, userId):
        super().__init__()
        self.add_item(InfoMainButton(userId))
        self.add_item(InfoAboutButton(userId))
        self.add_item(InfoPermissionButton(userId))

@client.tree.command(name="info", description = "Show information about "+config.NAME)
async def info_command(interaction):
    await interaction.response.defer()
    user_count = len(client.users)
    server_count = len(client.guilds)
    embed = discord.Embed(title = config.NAME, color = EMBED_COLOR)
    server_count = len(client.guilds)
    user_count = len(client.guilds)
    try:
        db = sqlite3.connect(config.DATABASE)
        running_server_count = db.execute('SELECT COUNT(*) FROM servers').fetchone()[0]
    finally:
        db.close()
    embed.description = config.NAME + f""" is a powerful server promotion assistant for Discord communities.
Navigate through the sections of the /info menu for more.

**Stats**:
- Servers: {server_count}
- Users: {user_count}
- Running Servers: {running_server_count}"""
    if client.user.avatar:
        embed.set_footer(icon_url = client.user.avatar.url, text = config.NAME + " Support: " + config.SUPPORT_SERVER)
    else:
        embed.set_footer(text = config.NAME + " Support: " + config.SUPPORT_SERVER)
    embed.set_thumbnail(url = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/25/Info_icon-72a7cf.svg/2048px-Info_icon-72a7cf.svg.png")
    await interaction.followup.send(embed = embed, view = InfoView(interaction.user.id))




client.run(config.TOKEN)
