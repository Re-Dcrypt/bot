import interactions
import requests
import re
from interactions.ext.fastapi import setup
from os import getenv
from dotenv import load_dotenv
from fastapi import Request
load_dotenv()


intents = interactions.Intents.ALL
bot = interactions.Client(getenv("TOKEN"), intents=intents)
api = setup(bot)
GUILD_ID = getenv("GUILD_ID")
base_url = getenv("HOST")
AuthenticationKey = getenv("AUTHENTICATION_KEY")
headers = {"Authorization": AuthenticationKey}


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
        username = member.user.username
        new_nickname = f"✔️{username} - {username_site}"
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
    url = base_url+"/verify_discord_id/"+str(ctx.author.id)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        new_nickname = f"✔️{ctx.author.user.username} - {response.json()['Username']}"
        await ctx.author.modify(guild_id=int(GUILD_ID), nick=new_nickname[:32])
        await ctx.send(
            "You are verified. Your username on site is: " + str(response.json()["Username"]),
            ephemeral=True)
    elif response.status_code == 404:
        await ctx.send(
            "Could not find your account. Please connect your discord account to verify",
            ephemeral=True)
    else:
        await ctx.send(
            "Something went wrong. Please try again later",
            ephemeral=True)


@bot.command(
    name="profile",
    description="Your Profile",
    scope=int(GUILD_ID),
    options=[
        interactions.Option(
            name="user",
            description="User",
            type=interactions.OptionType.USER,
            required=False,
        ),
    ],
)
async def profile(
        ctx: interactions.CommandContext,
        user: interactions.User = None):
    if user is None:
        id = ctx.author.id
    else:
        id = user.id
    url = base_url + "/profile/" + str(id)
    headers = {"Authorization": AuthenticationKey}
    response = requests.get(url, headers=headers)
    button = interactions.Button(
        text="Profile",
        style=interactions.ButtonStyle.LINK,
        label="Profile",
        url=f"{base_url}/profile/{response.json()['username']}")

    if response.status_code != 200:
        embed_error = interactions.Embed(
            title="Error",
            description=f"Could not find profile of <@{id}>",
            color=0xFF0000)
        await ctx.send(embeds=[embed_error])
    else:
        embed = interactions.Embed(title="Profile", color=0x00d2d2)
        embed.add_field(
            "Username",
            f"[{response.json()['username']}]({base_url[:-3]}profile/{response.json()['username']})", inline=False)
        try:
            embed.add_field("Name", response.json()["name"], inline=False)
        except KeyError:
            pass
        except Exception as e:
            print(e)
        try:
            embed.add_field(
                "Organization",
                response.json()["organization"],
                inline=False)
        except KeyError:
            pass
        except Exception as e:
            print(e)
        embed.add_field("Score", response.json()["score"], inline=True)
        embed.add_field("Level", response.json()["current_level"], inline=True)
        embed.add_field("Rank", response.json()["rank"], inline=True)
        embed.set_thumbnail(url=response.json()["avatar_url"])
        if user is None:
            pass
        else:
            embed.set_footer(
                text=f"Requested by: {ctx.author}",
                icon_url=ctx.author.user.avatar_url)
        embed.set_author(
            name="Re-Dcrypt",
            icon_url="https://i.imgur.com/LvqKPO7.png")
        await ctx.send(embeds=embed, components=button)


@bot.command(
    name="leaderboard",
    description="Leaderboard",
    scope=int(GUILD_ID))
async def leaderboard(ctx: interactions.CommandContext):
    url = base_url + "/leaderboard"
    headers = {"Authorization": AuthenticationKey}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        embed_error = interactions.Embed(
            title="Error",
            description="Could not find leaderboard",
            color=0xFF0000)
        await ctx.send(embeds=[embed_error])
    else:
        content = ""
        for i in range(10):
            try:
                content = content + f"**{i+1}. <@{response.json()[i]['discord_id']}>** \nScore: {response.json()[i]['score']} - Level: {response.json()[i]['current_level']}" + "\n"
            except KeyError:
                content = content + f"**{i+1}. {response.json()[i]['username']}** \nScore:{response.json()[i]['score']} - Level: {response.json()[i]['current_level']}" + "\n"
            except IndexError:
                break
            except Exception as e:
                print(e)
        button = interactions.Button(
            text="Leaderboard",
            style=interactions.ButtonStyle.LINK,
            label="Leaderboard",
            url=f"{base_url[:-3]}leaderboard")
        embed = interactions.Embed(
            title="Leaderboard",
            url=f"{base_url[:-3]}leaderboard",
            description=content,
            color=0x00d2d2)
        embed.set_footer(
            text=f"Requested by: {ctx.author}",
            icon_url=ctx.author.user.avatar_url)
        embed.set_author(
            name="Re-Dcrypt",
            icon_url="https://i.imgur.com/LvqKPO7.png")
        await ctx.send(embeds=embed, components=button)


@bot.command(
    name="stats",
    description="Your Stats",
    scope=int(GUILD_ID))
async def stats(ctx: interactions.CommandContext):
    url = base_url + "/stats/" + str(ctx.author.id)
    headers = {"Authorization": AuthenticationKey}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        embed_error = interactions.Embed(
            title="Error",
            description=f"Could not find stats of <@{ctx.author.id}>",
            color=0xFF0000)
        await ctx.send(embeds=[embed_error])
    else:
        embed = interactions.Embed(title="Stats", color=0x00d2d2)
        embed.add_field(
            "Username",
            f"[{response.json()['username']}]({base_url[:-3]}profile/{response.json()['username']})", inline=False)
        content = ""
        total_count = 0
        for i in response.json()['stats']:
            content = content + f"Level {i}: {response.json()['stats'][i]}"
            total_count += int(response.json()['stats'][i])
            content = content + "\n"
        embed.add_field("Score", response.json()['score'], inline=True)
        embed.add_field("Level", response.json()['current_level'], inline=True)
        embed.add_field("Stats", content, inline=False)
        embed.add_field("Total Number of Attempts", total_count, inline=True)
        embed.set_thumbnail(url=response.json()["avatar_url"])
        embed.set_footer(
            text=f"Requested by: {ctx.author}",
            icon_url=ctx.author.user.avatar_url)
        embed.set_author(
            name="Re-Dcrypt",
            icon_url="https://i.imgur.com/LvqKPO7.png")
        await ctx.send(embeds=embed, ephemeral=True)


@bot.command(
    name="ban",
    description="Ban a user",
    scope=int(GUILD_ID),
    default_member_permissions=interactions.Permissions.ADMINISTRATOR,
    options=[
        interactions.Option(
            name="user",
            description="User",
            type=interactions.OptionType.USER,
            required=True,
        ),
        interactions.Option(
            name="reason",
            description="Reason",
            type=interactions.OptionType.STRING,
            required=True)
    ])
async def ban(
        ctx: interactions.CommandContext,
        user: interactions.Member,
        reason: str):
    url = base_url + "/ban/" + str(user.id) + "/" + str(reason)
    headers = {"Authorization": AuthenticationKey}
    response = requests.post(url, headers=headers)
    if response.status_code != 200:
        embed_error = interactions.Embed(
            title="Error",
            description=f"Could not ban <@{user.id}>",
            color=0xFF0000)
        await ctx.send(embeds=[embed_error])
    else:
        embed = interactions.Embed(
            title="Success",
            description=f"<@{user.id}> has been banned",
            color=0x00d2d2)
        embed.set_footer(
            text=f"Requested by: {ctx.author}",
            icon_url=ctx.author.user.avatar_url)
        embed.set_author(
            name="Re-Dcrypt",
            icon_url="https://i.imgur.com/LvqKPO7.png")
        await ctx.send(embeds=embed)


@bot.command(
    name="unban",
    description="Unban a user",
    scope=int(GUILD_ID),
    default_member_permissions=interactions.Permissions.ADMINISTRATOR,
    options=[
        interactions.Option(
            name="user",
            description="User",
            type=interactions.OptionType.USER,
            required=True,
        ),
    ])
async def unban(ctx: interactions.CommandContext, user: interactions.Member):
    url = base_url + "/unban/" + str(user.id)
    headers = {"Authorization": AuthenticationKey}
    response = requests.post(url, headers=headers)
    if response.status_code != 200:
        embed_error = interactions.Embed(
            title="Error",
            description=f"Could not unban <@{user.id}>",
            color=0xFF0000)
        await ctx.send(embeds=[embed_error])
    else:
        embed = interactions.Embed(
            title="Success",
            description=f"<@{user.id}> has been unbanned",
            color=0x00d2d2)
        embed.set_footer(
            text=f"Requested by: {ctx.author}",
            icon_url=ctx.author.user.avatar_url)
        embed.set_author(
            name="Re-Dcrypt",
            icon_url="https://i.imgur.com/LvqKPO7.png")
        await ctx.send(embeds=embed)


@bot.command(
    name="easteregg",
    description="Easter Egg",
    scope=int(GUILD_ID))
async def easteregg(ctx):
    modal = interactions.Modal(
        title="Easter Egg",
        custom_id="easter_egg",
        components=[interactions.TextInput(
            style=interactions.TextStyleType.SHORT,
            label="Enter the easter egg...",
            placeholder="Easter Egg",
            custom_id="easter_egg_input",
            required=True
        )],
    )
    await ctx.popup(modal)


@bot.modal("easter_egg")
async def modal_response(ctx, easter_egg_input: str):
    easter_egg_input_filtered = re.sub('[\W_]+', '', easter_egg_input.lower().replace(' ', '').strip())
    url =  base_url + "/easteregg/" + str(ctx.author.id) + "/" + easter_egg_input_filtered
    headers = {"Authorization": AuthenticationKey}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        embed_error = interactions.Embed(
            title="Error",
            description=f"Some Error Occured, Try again later.",
            color=0xFF0000)
        await ctx.send(embeds=[embed_error], ephemeral=True)
    else:
        if response.json()['code'] == "success":
            embed = interactions.Embed(
                title="Success",
                description=f"{response.json()['response']}",
                color=0x00d2d2)
            embed.set_footer(
                text=f"{ctx.author}",
                icon_url=ctx.author.user.avatar_url)
            embed.set_author(
                name="Re-Dcrypt",
                icon_url="https://i.imgur.com/LvqKPO7.png")
            await ctx.send(embeds=embed, ephemeral=True)
        elif response.json()['code'] == "not_found":
            embed = interactions.Embed(
                title="Wrong!",
                description=f"{response.json()['response']}",
                color=0xFF0000)
            embed.set_footer(
                text=f"{ctx.author}",
                icon_url=ctx.author.user.avatar_url)
            embed.set_author(
                name="Re-Dcrypt",
                icon_url="https://i.imgur.com/LvqKPO7.png")
            await ctx.send(embeds=embed, ephemeral=True)
        elif response.json()['code'] == "claimed":
            embed = interactions.Embed(
                title="Already Claimed!",
                description=f"{response.json()['response']}",
                color=0xFF0000)
            embed.set_footer(
                text=f"{ctx.author}",
                icon_url=ctx.author.user.avatar_url)
            embed.set_author(
                name="Re-Dcrypt",
                icon_url="https://i.imgur.com/LvqKPO7.png")
            await ctx.send(embeds=embed, ephemeral=True)
        else:
            embed = interactions.Embed(
                title="Error",
                description=f"Some error occured, try again later.",
                color=0xFF0000)
            embed.set_footer(
                text=f"{ctx.author}",
                icon_url=ctx.author.user.avatar_url)
            embed.set_author(
                name="Re-Dcrypt",
                icon_url="https://i.imgur.com/LvqKPO7.png")
            await ctx.send(embeds=embed, ephemeral=True)


bot.start()
