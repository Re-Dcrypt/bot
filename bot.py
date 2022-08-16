import interactions
from interactions.ext.fastapi import setup
from os import getenv
from dotenv import load_dotenv
load_dotenv()
intents = interactions.Intents.ALL
bot = interactions.Client(getenv("TOKEN"), intents=intents)
api = setup(bot)
GUILD_ID = getenv("GUILD_ID")
@api.get("/")
async def index():
    return {"status": "success"}

@api.post("/connect/discord/{username_site}/{id}")
async def connect(username_site, id):
    for guild in bot.guilds:
        if guild.id == GUILD_ID:
            break
    member = await guild.get_member(int(id))
    username=member.user.username
    new_nickname=f"✔️{username} - {username_site}"
    await member.modify(guild_id=GUILD_ID, nick=new_nickname[:32])
    return {"status": "changing"}


@bot.command(
    name="verify",
    description="If you have connected ur discord account but still aren't verified here, use this command to verify",
    scope=GUILD_ID,
)
async def verify(ctx: interactions.CommandContext):
    await ctx.send("Verifying your account...")

bot.start()