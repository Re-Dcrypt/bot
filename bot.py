from multiprocessing import AuthenticationError
import interactions
from interactions.ext.fastapi import setup
from os import getenv
from dotenv import load_dotenv
from fastapi import Request
load_dotenv()
import requests
intents = interactions.Intents.ALL
bot = interactions.Client(getenv("TOKEN"), intents=intents)
api = setup(bot)
GUILD_ID = getenv("GUILD_ID")
base_url=getenv("HOST")
AuthenticationKey=getenv("AUTHENTICATION_KEY")
headers = {"Authorization":AuthenticationKey}

@api.get("/")
async def index():
    return {"Logged in as ": bot.user.name}

@api.post("/connect/discord/{username_site}/{id}")
async def connect(request: Request, username_site, id):
    header = request.headers.get('Authorization')
    if header != AuthenticationKey:
        return {"status": "unauthorized"}
    else:    
        for guild in bot.guilds:
            if guild.id == GUILD_ID:
                break
        member = await guild.get_member(int(id))
        username=member.user.username
        new_nickname=f"✔️{username} - {username_site}"
        await member.modify(guild_id=int(GUILD_ID), nick=new_nickname[:32])
        return {"status": "changing"}


@api.post('/level/complete/{id}/{completed_lvl}')
async def complete_level(request: Request, id, completed_lvl):
    header = request.headers.get('Authorization')
    if header != AuthenticationKey:
        return {"status": "unauthorized"}
    else:
        for guild in bot.guilds:
            if guild.id == int(GUILD_ID):
                break
        member = await guild.get_member(int(id))
        for roles in guild.roles:
            if roles.name == f"Lvl {completed_lvl}":
                try:
                    await member.remove_role(roles, guild_id=int(GUILD_ID))
                except Exception as e:
                    print(e)
                pass
            elif roles.name == f"Lvl {int(completed_lvl)+1}":
                try:
                    await member.add_role(roles, guild_id=int(GUILD_ID))
                except Exception as e:
                    print(e)
                break
        return {"status": "Done"}

@bot.command(
    name="verify",
    description="If you have connected ur discord account but still aren't verified here, use this command to verify",
    scope=int(GUILD_ID),
)
async def verify(ctx: interactions.CommandContext):
    url=base_url+"/verify_discord_id/"+str(ctx.author.id)
    response=requests.get(url, headers=headers)
    if response.status_code==200:
        new_nickname=f"✔️{ctx.author.user.username} - {response.json()['Username']}"
        await ctx.author.modify(guild_id=int(GUILD_ID), nick=new_nickname[:32])
        await ctx.send("You are verified. Your username on site is: " + str(response.json()["Username"]), ephemeral=True)
    elif response.status_code==404:
        await ctx.send("Could not find your account. Please connect your discord account to verify", ephemeral=True)
    else:
        await ctx.send("Something went wrong. Please try again later", ephemeral=True)

bot.start()