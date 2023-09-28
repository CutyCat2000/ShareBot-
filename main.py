import config
import discord
from discord import ui, app_commands
import sqlite3
import datetime
import asyncio
import logging

log = logging.getLogger()
log.setLevel(logging.DEBUG)

db = sqlite3.connect(config.DATABASE)

cursor = db.execute('''
    CREATE TABLE IF NOT EXISTS servers (
        server_id INTEGER PRIMARY KEY,
        description TEXT,
        language TEXT,
        invite TEXT,
        slogan TEXT,
        premium BOOLEAN,
        bump_count INTEGER,
        last_bump DATETIME,
        channel INTEGER
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
        cursor.execute('SELECT * FROM servers WHERE server_id = ?', (server_id, ))
        server_data = cursor.fetchone()
        if server_data:
            server_info = {
                'server_id': server_data[0],
                'description': server_data[1],
                'language': server_data[2],
                'invite': server_data[3],
                'slogan': server_data[4],
                'premium': server_data[5],
                'bump_count': server_data[6],
                'last_bump': server_data[7],
                'channel': server_data[8]
            }
            return server_info
        else:
            return None
    finally:
        db.close()

def set_server(server_id, description, language, invite, slogan, premium, bump_count, last_bump, channel):
    try:
        db = sqlite3.connect(config.DATABASE)
        cursor = db.cursor()
        cursor.execute('SELECT server_id from servers WHERE server_id = ?', (server_id, ))
        existing_server = cursor.fetchone()
        if existing_server:
            cursor.execute('''
                UPDATE servers
                SET description = ?, language = ?, invite = ?, slogan = ?, premium = ?, bump_count = ?, last_bump = ?, channel = ?
                WHERE server_id = ?
            ''', (description, language, invite, slogan, premium, bump_count, last_bump, channel, server_id))
        else:
            cursor.execute('''
                INSERT INTO servers (server_id, description, language, invite, slogan, premium, bump_count, last_bump, channel)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (server_id, description, language, invite, slogan, premium, bump_count, last_bump, channel))
        db.commit()
        return True
    except Exception as es:
        print(es)
        return False
    finally:
        db.close()

class Client(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(intents = intents, activity = discord.CustomActivity(name = text_replace(config.STATUS_MESSAGES[0])))
        self.tree = app_commands.CommandTree(self)
    async def setup_hook(self):
        await self.tree.sync()
    async def on_ready(self):
        print("Bot is running")
        while True:
            for current_message in config.STATUS_MESSAGES:
                await self.change_presence(activity = discord.CustomActivity(name = text_replace(current_message)))
                await asyncio.sleep(config.STATUS_CHANGE_DELAY)

client = Client()

async def sendNotYourButtonEmbed(interaction, userId):
    if interaction.user.id != userId:
        embed = discord.Embed(title="Not your button", description="This is not your button, please type the command yourself in this or another server to use the buttons.", color = EMBED_COLOR_ERROR)
        if client.user.avatar:
            embed.set_footer(icon_url = client.user.avatar.url, text = config.NAME + " Support: " + config.SUPPORT_SERVER)
        else:
            embed.set_footer(text = config.NAME + " Support: " + config.SUPPORT_SERVER)
        if config.EPHEMERAL_MESSAGES:
            await interaction.followup.send(embed=embed, ephemeral = True)
        else:
            await interaction.followup.send(embed=embed)
        return True
    return False

async def sendNeedWaitEmbed(interaction, seconds_left):
    hours, remainder = divmod(seconds_left, 3600)
    minutes, seconds = divmod(remainder, 60)
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)
    embed=discord.Embed(title="Wait for bump", description=f"""You need to wait until this server can be bumped again.
> Time left: `{hours}:{minutes}:{seconds}`""", color =EMBED_COLOR_ERROR)
    if client.user.avatar:
        embed.set_footer(icon_url = client.user.avatar.url, text = config.NAME + " Support: " + config.SUPPORT_SERVER)
    else:
        embed.set_footer(text = config.NAME + " Support: " + config.SUPPORT_SERVER)
    if config.EPHEMERAL_MESSAGES:
        await interaction.followup.send(embed=embed,ephemeral=True)
    else:
        await interaction.followup.send(embed = embed)

async def sendMissingPermsEmbed(interaction, permission_name):
    embed = discord.Embed(title="Missing Perms", description=config.NAME+" is missing the permission "+permission_name, color=EMBED_COLOR_ERROR)
    if client.user.avatar:
        embed.set_footer(icon_url = client.user.avatar.url, text = config.NAME + " Support: " + config.SUPPORT_SERVER)
    else:
        embed.set_footer(text = config.NAME + " Support: " + config.SUPPORT_SERVER)
    if config.EPHEMERAL_MESSAGES:
        await interaction.followup.send(embed = embed, ephemeral = True)
    else:
        await interaction.followup.send(embed = embed)

async def sendGuildNotFoundEmbed(interaction, guild_id):
    embed = discord.Embed(title="Guild not found", description=config.NAME+" was unable to locate the server with the ID: "+str(guild_id), color=EMBED_COLOR_ERROR)
    if client.user.avatar:
        embed.set_footer(icon_url = client.user.avatar.url, text=config.NAME+" Support: " + config.SUPPORT_SERVER)
    else:
        embed.set_footer(text=config.NAME + " Support: " + config.SUPPORT_SERVER)
    if config.EPHEMERAL_MESSAGES:
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.followup.send(embed=embed)

async def sendNoAdminEmbed(interaction, permission_name):
    embed = discord.Embed(title="Missing Perms", description="You are missing the permission "+permission_name, color=EMBED_COLOR_ERROR)
    if client.user.avatar:
        embed.set_footer(icon_url = client.user.avatar.url, text = config.NAME + " Support: " + config.SUPPORT_SERVER)
    else:
        embed.set_footer(text = config.NAME + " Support: " + config.SUPPORT_SERVER)
    if config.EPHEMERAL_MESSAGES:
        await interaction.followup.send(embed = embed, ephemeral = True)
    else:
        await interaction.followup.send(embed = embed)

async def sendNotSetupEmbed(interaction):
    embed = discord.Embed(title="Not Setup", description="This server has not been setup yet. (/setup)", color=EMBED_COLOR_ERROR)
    if client.user.avatar:
        embed.set_footer(icon_url = client.user.avatar.url, text = config.NAME + " Support: " + config.SUPPORT_SERVER)
    else:
        embed.set_footer(text = config.NAME + " Support: " + config.SUPPORT_SERVER)
    if config.EPHEMERAL_MESSAGES:
        await interaction.followup.send(embed = embed, ephemeral = True)
    else:
        await interaction.followup.send(embed = embed)

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

class InfoCommandButton(ui.Button):
    def __init__(self, userId):
        super().__init__(label = "Commands", emoji = "🤖")
        self.userId = userId
    async def callback(self, interaction):
        await interaction.response.defer(ephemeral = True)
        if await sendNotYourButtonEmbed(interaction, self.userId):
            return
        embed = interaction.message.embeds[0]
        embed.description="**__"+config.NAME+""" commands__**:
/info -> Show the information menu.
/setup -> Start the interaction setup.
/show -> Show the settings from setup.
"""
        await interaction.message.edit(embed = embed)

class InfoPremiumButton(ui.Button):
    def __init__(self, userId):
        super().__init__(label = "Premium", emoji = "🌟")
        self.userId = userId
    async def callback(self, interaction):
        await interaction.response.defer(ephemeral = True)
        if await sendNotYourButtonEmbed(interaction, self.userId):
            return
        embed = interaction.message.embeds[0]
        embed.description="""[Join to get premium]("""+config.SUPPORT_SERVER+""")
* Premium Perks: *
> Faster Bumps
> More powerful Bumps"""
        await interaction.message.edit(embed = embed)

class JoinServerButton(ui.Button):
    def __init__(self, invite, serverName):
        if not "discord.gg/" in invite:
            invite = "discord.gg/"+invite
        if not invite.startswith("https://") and not invite.startswith("http://"):
            invite = "https://" + invite
        super().__init__(label="Join " + serverName, emoji = "🔗", style=discord.ButtonStyle.link, url=invite)

class JoinSupportServerButton(ui.Button):
    def __init__(self):
        super().__init__(label="Join "+config.NAME+" support", emoji = "👤", style=discord.ButtonStyle.link, url=config.SUPPORT_SERVER)

class InfoView(ui.View):
    timeout = None
    def __init__(self, userId):
        super().__init__()
        self.add_item(InfoMainButton(userId))
        self.add_item(InfoAboutButton(userId))
        self.add_item(InfoPermissionButton(userId))
        self.add_item(InfoCommandButton(userId))
        if config.ENABLE_PREMIUM:
            self.add_item(InfoPremiumButton(userId))
        self.add_item(JoinSupportServerButton())

class ServerView(ui.View):
    timeout = None
    def __init__(self, invite, serverName):
        super().__init__()
        self.add_item(JoinServerButton(invite, serverName))
        self.add_item(JoinSupportServerButton())

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

class SetupModal(ui.Modal, title=config.NAME+" setup"):
    description = ui.TextInput(label="Description", placeholder="This server is for advertising using "+config.NAME, style=discord.TextStyle.long, required=True, max_length=512)
    invite = ui.TextInput(label="Invite", placeholder="If not given, "+config.NAME+" will make an invite itself.", style=discord.TextStyle.short, required=False)
    language = ui.TextInput(label="Language", placeholder="English / German", required=False)
    slogan = ui.TextInput(label="Slogan", placeholder="Free Ads, everywhere", required=False)
    def __init__(self, channel):
        self.channel = channel
        super().__init__(title=config.NAME+" setup")
    async def on_submit(self, interaction):
        await interaction.response.defer(ephemeral=True)
        if not self.language.value or self.language.value=="":
            language = "English"
        else:
            language = self.language.value
        if not self.invite.value or self.invite.value=="":
            try:
                invite = await self.channel.create_invite(max_age = 300)
            except Exception as es:
                print(es)
                return await sendMissingPermsEmbed(interaction, "CREATE_INSTANT_INVITE")
        else:
            invite = self.invite.value
        if not self.slogan or self.slogan.value=="":
            slogan="N/A"
        else:
            slogan = self.slogan.value
        set_server(str(self.channel.guild.id), self.description.value, language, str(invite), slogan, "false", "0", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), str(self.channel.id))
        embed = discord.Embed(title="Setup successful", color=EMBED_COLOR)
        embed.description = """The setup has been successful.
- NAME: """+str(self.channel.guild.name)+"""
- INVITE: """+str(invite)+"""
- CHANNEL: """+str(self.channel.mention)+"""
- LANGUAGE: """+str(language)+"""
- SLOGAN: """+str(slogan)+"""
- DESCRIPTION: """+str(self.description.value)
        if self.channel.guild.icon:
            embed.set_thumbnail(url = self.channel.guild.icon.url)
        if client.user.avatar:
            embed.set_footer(icon_url = client.user.avatar.url, text = config.NAME + " Support: " + config.SUPPORT_SERVER)
        else:
            embed.set_footer(text = config.NAME + " Support: " + config.SUPPORT_SERVER)
        await interaction.followup.send(embed = embed)


@client.tree.command(name="setup", description="Setup "+config.NAME+" on this server")
async def setup_command(interaction, channel:discord.TextChannel):
    """

    Parameters
    ----------
    channel : discord.TextChannel
        The channel where the ads shall be sent in
    """
    member = await interaction.guild.fetch_member(interaction.user.id)
    if not member.guild_permissions.administrator:
        await interaction.response.defer(ephemeral=True)
        return await sendNoAdminEmbed(interaction, "administrator")
    await interaction.response.send_modal(SetupModal(channel))
    
@client.tree.command(name="show", description="Show current server setup")
async def show_command(interaction):
    server_dict = get_server(interaction.guild.id)
    if not server_dict:
        await interaction.response.defer(ephemeral=True)
        return await sendNotSetupEmbed(interaction)
    await interaction.response.defer()
    channel = await interaction.guild.fetch_channel(server_dict["channel"])
    embed = discord.Embed(title="Current setup", color=EMBED_COLOR)
    embed.description="""Settings for """+interaction.guild.name+"""
- NAME: """+str(interaction.guild.name)+"""
- INVITE: """+str(server_dict["invite"])+"""
- CHANNEL: """+str(channel.mention)+"""
- LANGUAGE: """+str(server_dict["language"])+"""
- SLOGAN: """+str(server_dict["slogan"])+"""
- DESCRIPTION: """+str(server_dict["description"])
    if interaction.guild.icon:
        embed.set_thumbnail(url = interaction.guild.icon.url)
    if client.user.avatar:
        embed.set_footer(icon_url = client.user.avatar.url, text = config.NAME + " Support: " + config.SUPPORT_SERVER)
    else:
        embed.set_footer(text = config.NAME + " Support: " + config.SUPPORT_SERVER)
    await interaction.followup.send(embed = embed, ephemeral=False)

@client.tree.command(name="bump", description="Bump the current server")
async def bump_command(interaction):
    server_dict = get_server(interaction.guild.id)
    if not server_dict:
        await interaction.response.defer(ephemeral=True)
        return await sendNotSetupEmbed(interaction)
    channel = await interaction.guild.fetch_channel(server_dict["channel"])
    try:
        await client.fetch_invite(server_dict["invite"])
    except:
        try:
            server_dict["invite"] = str(await channel.create_invite(max_age = 300))
        except:
            await interaction.response.defer(ephemeral=True)
            return await sendMissingPermsEmbed(interaction, "create_instant_invite")
    permissions = channel.permissions_for(interaction.guild.default_role)
    if not permissions.read_messages:
        await interaction.response.defer(ephemeral=True)
        return await sendMissingPermsEmbed(interaction, "send_messages in "+str(channel.mention))
    oldbumptime = datetime.datetime.strptime(server_dict["last_bump"], "%Y-%m-%d %H:%M:%S")
    newbumptime = datetime.datetime.now()
    seconds_passed = (newbumptime - oldbumptime).total_seconds()
    print(server_dict["premium"])
    if config.ENABLE_PREMIUM and server_dict["premium"] != "false" and server_dict["premium"] != False:
        BUMP_RATE_LIMIT = config.PREMIUM_BUMP_RATE_LIMIT
    else:
        BUMP_RATE_LIMIT = config.BUMP_RATE_LIMIT
    if seconds_passed < BUMP_RATE_LIMIT:
        await interaction.response.defer(ephemeral=True)
        return await sendNeedWaitEmbed(interaction, BUMP_RATE_LIMIT - seconds_passed)
    else:
        newbumptime = newbumptime.strftime("%Y-%m-%d %H:%M:%S")
    await interaction.response.defer()
    embed = discord.Embed(title=interaction.guild.name, color=EMBED_COLOR)
    if interaction.guild.icon:
        embed.set_thumbnail(url = interaction.guild.icon.url)
        if server_dict["slogan"] != "N/A":
            embed.set_footer(text=server_dict["slogan"], icon_url = interaction.guild.icon.url)
    else:
        if server_dict["slogan"] != "N/A":
            embed.set_footer(text=server_dict["slogan"])
    owner = interaction.guild.owner.name
    if int(interaction.guild.owner.discriminator) != 0:
        owner += "#"+str(interaction.guild.owner.discriminator)
    username = interaction.user.name
    if int(interaction.user.discriminator) != 0:
        username += "#"+str(interaction.user.discriminator)
    server_dict["bump_count"] = int(server_dict["bump_count"]) + 1
    if config.ENABLE_PREMIUM:
        if server_dict["premium"] != "false" and server_dict["premium"] != False:
            embed.add_field(name="Server Information", value="""> Language: `"""+server_dict["language"]+"""`
> Members: `"""+str(interaction.guild.member_count)+"""`
> Owner: `"""+owner+"""`
> Premium: `activated`""", inline=False)
        else:
            embed.add_field(name="Server Information", value="""> Language: `"""+server_dict["language"]+"""`
> Members: `"""+str(interaction.guild.member_count)+"""`
> Owner: `"""+owner+"""`
> Premium: `disabled`""", inline=False)
    else:
        embed.add_field(name="Server Information", value="""> Language: `"""+server_dict["language"]+"""`
> Members: `"""+str(interaction.guild.member_count)+"""`
> Owner: `"""+owner+"`", inline=False)
    embed.add_field(name="Description", value=server_dict["description"], inline = False)
    embed.add_field(name="Bump Information", value="""> Bumped by `"""+username+"""`
> Bumped at `"""+str(datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))+"""`
> Bump count: `"""+str(server_dict["bump_count"])+"""`""", inline = False)
    set_server(str(interaction.guild.id), str(server_dict["description"]), str(server_dict["language"]), str(server_dict["invite"]), str(server_dict["slogan"]), str(server_dict["premium"]), str(server_dict["bump_count"]), newbumptime, str(server_dict["channel"]))
    bumpingNowEmbed = discord.Embed(title="Bump started", description="This server is now being shared in other servers.", color=EMBED_COLOR)
    if client.user.avatar:
        bumpingNowEmbed.set_footer(icon_url = client.user.avatar.url, text = config.NAME + " Support: " + config.SUPPORT_SERVER)
    else:
        bumpingNowEmbed.set_footer(text = config.NAME + " Support: " + config.SUPPORT_SERVER)
    await interaction.followup.send(embed=bumpingNowEmbed)
    if config.ENABLE_PREMIUM and server_dict["premium"] != "false" and server_dict["premium"] != False:
        iterations = int(len(client.guilds) /50) + 1
    else:
        iterations = 1
    for n in range(iterations):
        for guild in client.guilds:
            guild_server_dict = get_server(guild.id)
            if guild_server_dict:
                guild_channel = await guild.fetch_channel(guild_server_dict["channel"])
                try:
                    await guild_channel.send(embed = embed, view = ServerView(server_dict["invite"], interaction.guild.name))
                except:
                    pass


@client.tree.command(name="setpremium", description="Set the premium status of a server.")
async def setpremium_command(interaction, server_id:str, is_premium:bool):
    """

    Parameters
    ----------
    server_id : str
        The ID of the server to set the premium status for
    is_premium : bool
        If the server has premium"""
    server_id = int(server_id)
    server_dict = get_server(str(server_id))
    if not interaction.user.id in config.ADMINS:
        await interaction.response.defer(ephemeral=True)
        return await sendNoAdminEmbed(interaction, "bot_admin")
    if not server_dict:
        await interaction.response.defer(ephemeral=True)
        return await sendGuildNotFoundEmbed(interaction, server_id)
    server = None
    for guild in client.guilds:
        if guild.id == server_id:
            server = guild
    if is_premium:
        if server_dict["premium"] == "true":
            return await interaction.response.send_message(server.name+" already has premium")
        server_dict["premium"] = "true"
        set_server(str(interaction.guild.id), str(server_dict["description"]), str(server_dict["language"]), str(server_dict["invite"]), str(server_dict["slogan"]), str(server_dict["premium"]), str(server_dict["bump_count"]), str(server_dict["last_bump"]), str(server_dict["channel"]))
        await interaction.response.send_message(server.name+" now has premium")
    else:
        if server_dict["premium"] == "false":
            return await interaction.response.send_message(server.name+" already has no premium")
        server_dict["premium"] = "false"
        set_server(str(interaction.guild.id), str(server_dict["description"]), str(server_dict["language"]), str(server_dict["invite"]), str(server_dict["slogan"]), str(server_dict["premium"]), str(server_dict["bump_count"]), str(server_dict["last_bump"]), str(server_dict["channel"]))
        await interaction.response.send_message(server.name+" now has no premium")





client.run(config.TOKEN)
