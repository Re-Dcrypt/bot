import interactions
import requests
import re
from interactions.ext.fastapi import setup
from os import getenv
from dotenv import load_dotenv
from fastapi import Request
from discord_webhook import DiscordWebhook, DiscordEmbed

load_dotenv()

intents = interactions.Intents.ALL
bot = interactions.Client(
    getenv("TOKEN"),
    intents=intents,
    presence=interactions.ClientPresence(activities=[
        interactions.PresenceActivity(
            name="Re-Dcrypt Cryptic Hunt",
            type=interactions.PresenceActivityType.WATCHING)
    ]))
api = setup(bot, host="0.0.0.0", port=3000)
GUILD_ID = getenv("GUILD_ID")
base_url = getenv("HOST")
AuthenticationKey = getenv("AUTHENTICATION_KEY")
API_Cron = getenv("API_Cron")
headers = {"Authorization": AuthenticationKey}


@api.get("/")
async def index():
    return {"Hello World"}


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
    description=
    "If you have connected ur discord account but still aren't verified here, use this command to verify",
    scope=int(GUILD_ID),
)
async def verify(ctx: interactions.CommandContext):
    url = base_url + "/verify_discord_id/" + str(ctx.author.id)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        new_nickname = f"✔️{ctx.author.user.username} - {response.json()['Username']}"
        for guild in bot.guilds:
            if guild.id == int(GUILD_ID):
                break
        roles = interactions.search_iterable(await guild.get_all_roles(),
                                             name="Verified")
        await ctx.author.modify(guild_id=int(GUILD_ID), nick=new_nickname[:32])
        await ctx.author.add_role(roles[0], guild_id=int(GUILD_ID))
        await ctx.send("You are verified. Your username on site is: " +
                       str(response.json()["Username"]),
                       ephemeral=True)
    elif response.status_code == 404:
        await ctx.send(
            "Could not find your account. Please connect your discord account to verify",
            ephemeral=True)
    else:
        await ctx.send("Something went wrong. Please try again later",
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
async def profile(ctx: interactions.CommandContext,
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
            f"[{response.json()['username']}]({base_url[:-3]}profile/{response.json()['username']})",
            inline=False)
        try:
            embed.add_field("Name", response.json()["name"], inline=False)
        except KeyError:
            pass
        except Exception as e:
            print(e)
        try:
            embed.add_field("Organization",
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
            embed.set_footer(text=f"Requested by: {ctx.author}",
                             icon_url=ctx.author.user.avatar_url)
        embed.set_author(name="Re-Dcrypt",
                         icon_url="https://i.imgur.com/LvqKPO7.png")
        await ctx.send(embeds=embed, components=button)


@bot.command(name="leaderboard",
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
        button = interactions.Button(text="Leaderboard",
                                     style=interactions.ButtonStyle.LINK,
                                     label="Leaderboard",
                                     url=f"{base_url[:-3]}leaderboard")
        embed = interactions.Embed(title="Leaderboard",
                                   url=f"{base_url[:-3]}leaderboard",
                                   description=content,
                                   color=0x00d2d2)
        embed.set_footer(text=f"Requested by: {ctx.author}",
                         icon_url=ctx.author.user.avatar_url)
        embed.set_author(name="Re-Dcrypt",
                         icon_url="https://i.imgur.com/LvqKPO7.png")
        await ctx.send(embeds=embed, components=button)


@bot.command(name="stats", description="Your Stats", scope=int(GUILD_ID))
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
            f"[{response.json()['username']}]({base_url[:-3]}profile/{response.json()['username']})",
            inline=False)
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
        embed.set_footer(text=f"Requested by: {ctx.author}",
                         icon_url=ctx.author.user.avatar_url)
        embed.set_author(name="Re-Dcrypt",
                         icon_url="https://i.imgur.com/LvqKPO7.png")
        await ctx.send(embeds=embed, ephemeral=True)


@bot.command(name="ban",
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
                 interactions.Option(name="reason",
                                     description="Reason",
                                     type=interactions.OptionType.STRING,
                                     required=True)
             ])
async def ban(ctx: interactions.CommandContext, user: interactions.Member,
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
        embed = interactions.Embed(title="Success",
                                   description=f"<@{user.id}> has been banned",
                                   color=0x00d2d2)
        embed.set_footer(text=f"Requested by: {ctx.author}",
                         icon_url=ctx.author.user.avatar_url)
        embed.set_author(name="Re-Dcrypt",
                         icon_url="https://i.imgur.com/LvqKPO7.png")
        await ctx.send(embeds=embed)


@bot.command(name="unban",
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
        embed.set_footer(text=f"Requested by: {ctx.author}",
                         icon_url=ctx.author.user.avatar_url)
        embed.set_author(name="Re-Dcrypt",
                         icon_url="https://i.imgur.com/LvqKPO7.png")
        await ctx.send(embeds=embed)


@bot.command(name="easteregg", description="Easter Egg", scope=int(GUILD_ID))
async def easteregg(ctx):
    modal = interactions.Modal(
        title="Easter Egg",
        custom_id="easter_egg",
        components=[
            interactions.TextInput(style=interactions.TextStyleType.SHORT,
                                   label="Enter the easter egg...",
                                   placeholder="Easter Egg",
                                   custom_id="easter_egg_input",
                                   required=True)
        ],
    )
    await ctx.popup(modal)


@bot.modal("easter_egg")
async def modal_response(ctx, easter_egg_input: str):
    easter_egg_input_filtered = re.sub(
        '[\W_]+', '',
        easter_egg_input.lower().replace(' ', '').strip())
    url = base_url + "/easteregg/" + str(
        ctx.author.id) + "/" + easter_egg_input_filtered
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
            embed.set_footer(text=f"{ctx.author}",
                             icon_url=ctx.author.user.avatar_url)
            embed.set_author(name="Re-Dcrypt",
                             icon_url="https://i.imgur.com/LvqKPO7.png")
            await ctx.send(embeds=embed, ephemeral=True)
        elif response.json()['code'] == "not_found":
            embed = interactions.Embed(
                title="Wrong!",
                description=f"{response.json()['response']}",
                color=0xFF0000)
            embed.set_footer(text=f"{ctx.author}",
                             icon_url=ctx.author.user.avatar_url)
            embed.set_author(name="Re-Dcrypt",
                             icon_url="https://i.imgur.com/LvqKPO7.png")
            await ctx.send(embeds=embed, ephemeral=True)
        elif response.json()['code'] == "claimed":
            embed = interactions.Embed(
                title="Already Claimed!",
                description=f"{response.json()['response']}",
                color=0xFF0000)
            embed.set_footer(text=f"{ctx.author}",
                             icon_url=ctx.author.user.avatar_url)
            embed.set_author(name="Re-Dcrypt",
                             icon_url="https://i.imgur.com/LvqKPO7.png")
            await ctx.send(embeds=embed, ephemeral=True)
        else:
            embed = interactions.Embed(
                title="Error",
                description=f"Some error occured, try again later.",
                color=0xFF0000)
            embed.set_footer(text=f"{ctx.author}",
                             icon_url=ctx.author.user.avatar_url)
            embed.set_author(name="Re-Dcrypt",
                             icon_url="https://i.imgur.com/LvqKPO7.png")
            await ctx.send(embeds=embed, ephemeral=True)




@bot.command(name="verify_button",
             description="Verify yourself",
             scope=int(GUILD_ID),
             default_member_permissions=interactions.Permissions.ADMINISTRATOR)
async def verify_button(ctx: interactions.CommandContext):
    button = interactions.Button(style=interactions.ButtonStyle.PRIMARY,
                                 label="Verify",
                                 custom_id="verify")
    embed = interactions.Embed(title="Verify",
                               description="Please verify yourself",
                               color=0x00d2d2)
    embed.set_author(name="Re-Dcrypt",
                     icon_url="https://i.imgur.com/LvqKPO7.png")
    await ctx.send(embeds=[embed], components=[button])


@bot.component("verify")
async def button_verify(ctx: interactions.CommandContext):
    url = base_url + "/verify_discord_id/" + str(ctx.author.id)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        new_nickname = f"✔️{ctx.author.user.username} - {response.json()['Username']}"
        for guild in bot.guilds:
            if guild.id == int(GUILD_ID):
                break
        roles = interactions.search_iterable(await guild.get_all_roles(),
                                             name="Verified")
        await ctx.author.modify(guild_id=int(GUILD_ID), nick=new_nickname[:32])
        await ctx.author.add_role(roles[0], guild_id=int(GUILD_ID))
        await ctx.send("You are verified. Your username on site is: " +
                       str(response.json()["Username"]),
                       ephemeral=True)
    elif response.status_code == 404:
        await ctx.send(
            "Could not find your account. Please connect your discord account to verify",
            ephemeral=True)
    else:
        await ctx.send("Something went wrong. Please try again later",
                       ephemeral=True)


@bot.event(name="on_guild_member_add")
async def on_guild_member_add(member: interactions.Member):
    url = base_url + "/verify_discord_id/" + str(member.id)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        new_nickname = f"✔️{member.user.username} - {response.json()['Username']}"
        for guild in bot.guilds:
            if guild.id == int(GUILD_ID):
                break
        roles = interactions.search_iterable(await guild.get_all_roles(),
                                             name="Verified")
        await member.modify(nick=new_nickname[:32])
        await member.add_role(roles[0], )
        embed = interactions.Embed(
            title="Verifed",
            description="You have been verified through the Re-Dcrypt Website",
            color=0x00d2d2)
        embed.add_field(
            name="Your Username on the website:",
            value=str(response.json()["Username"]),
        )
        embed.set_author(name="Re-Dcrypt",
                         icon_url="https://i.imgur.com/LvqKPO7.png")
        await member.send(embeds=embed)
    else:
        pass


@bot.command(name="create_invite",
             description="Create an invite",
             scope=int(GUILD_ID),
             options=[
                 interactions.Option(
                     name="channel",
                     description="Channel to create invite in",
                     type=interactions.OptionType.CHANNEL,
                     required=True,
                 )
             ],
             default_member_permissions=interactions.Permissions.ADMINISTRATOR)
async def create_invite(ctx: interactions.CommandContext, channel):
    code = await channel.create_invite(max_age=0, max_uses=0)
    await ctx.send(
        f"Invite created in {channel.mention}: https://discord.com/invite/{code.code}",
        ephemeral=True)


@bot.command(name="verify_someone",
             description="verify a user",
             scope=int(GUILD_ID),
             default_member_permissions=interactions.Permissions.ADMINISTRATOR,
             options=[
                 interactions.Option(name="member",
                                     description="user to verify",
                                     type=interactions.OptionType.USER,
                                     required=True)
             ])
async def verify_someone(ctx: interactions.CommandContext,
                         member: interactions.Member):

    url = base_url + "/verify_discord_id/" + str(member.id)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        new_nickname = f"✔️{member.user.username} - {response.json()['Username']}"
        for guild in bot.guilds:
            if guild.id == int(GUILD_ID):
                break
        roles = interactions.search_iterable(await guild.get_all_roles(),
                                             name="Verified")
        await member.modify(guild_id=int(GUILD_ID), nick=new_nickname[:32])
        await member.add_role(
            guild_id=int(GUILD_ID),
            role=roles[0],
        )
        embed = interactions.Embed(
            title="Verifed",
            description="You have been verified through the Re-Dcrypt Website",
            color=0x00d2d2)
        embed.add_field(
            name="Your Username on the website:",
            value=str(response.json()["Username"]),
        )
        embed.set_author(name="Re-Dcrypt",
                         icon_url="https://i.imgur.com/LvqKPO7.png")
        await ctx.send(embeds=embed)
    else:
        await ctx.send("Error")


@bot.command(name="update_ranks",
             description="Update the ranks of the members",
             scope=int(GUILD_ID),
             default_member_permissions=interactions.Permissions.ADMINISTRATOR)
async def update_ranks(ctx: interactions.CommandContext):
    url = base_url + "/update_rank_all"
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        await ctx.send("Updating Ranks", ephemeral=True)
    else:
        await ctx.send(f"Update Ranks failed\nError:\n{response.json}",
                       ephemeral=True)


@bot.command(name="backup",
             description="Backup the database",
             scope=int(GUILD_ID),
             default_member_permissions=interactions.Permissions.ADMINISTRATOR)
async def backup(ctx: interactions.CommandContext):
    url = base_url + "/backup"
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        await ctx.send("Backing Up", ephemeral=True)
    else:
        await ctx.send(f"Backup failed\nError:\n{response.json}",
                       ephemeral=True)


@bot.command(name="start_hunt",
             description="Start Re-Dcrypt Hunt",
             scope=int(GUILD_ID),
             default_member_permissions=interactions.Permissions.ADMINISTRATOR)
async def start_hunt(ctx: interactions.CommandContext, status):
    url = base_url + '/start_hunt'
    response = requests.post(url, headers={"Authorization": API_Cron})
    if response.status_code == 200:
        await ctx.send("Hunt started", ephemeral=True)
    else:
        await ctx.send("Error", ephemeral=True)


@bot.command(name="end_hunt",
             description="End Re-Dcrypt Hunt",
             scope=int(GUILD_ID),
             default_member_permissions=interactions.Permissions.ADMINISTRATOR)
async def end_hunt(ctx: interactions.CommandContext):
    url = base_url + '/end_hunt'
    response = requests.post(url, headers={"Authorization": API_Cron})
    if response.status_code == 200:
        await ctx.send("Hunt ended", ephemeral=True)
    else:
        await ctx.send("Error", ephemeral=True)


@bot.command(name="feedback", description="Feedback")
async def feedback(ctx: interactions.CommandContext):
    modal = interactions.Modal(
        title="Feedback",
        custom_id="feedback_form",
        components=[
            interactions.TextInput(style=interactions.TextStyleType.SHORT,
                                   label="Your username on site",
                                   placeholder="Username",
                                   custom_id="username_site",
                                   required=True),
            interactions.TextInput(style=interactions.TextStyleType.SHORT,
                                      label="Till which level did you complete the hunt",
                                        placeholder="Level",
                                        custom_id="level",
                                        required=True),
            interactions.TextInput(style=interactions.TextStyleType.PARAGRAPH,
                                        label="Favourite Level",
                                        placeholder="Favourite Level",
                                        custom_id="fav_level",
                                        required=True),
            interactions.TextInput(style=interactions.TextStyleType.PARAGRAPH,
                                        label="Least Favourite Level",
                                        placeholder="Least Favourite Level",
                                        custom_id="least_fav_level",
                                        required=True),
            interactions.TextInput(style=interactions.TextStyleType.PARAGRAPH,
                                        label="Suggestions/Feedback",   
                                        placeholder="Suggestions/feedback",
                                        custom_id="suggestions",
                                        required=True),

        ],
    )
    await ctx.popup(modal)


@bot.modal("feedback_form")
async def modal_response_feedback(ctx: interactions.CommandContext, username_site: str, level: str, fav_level: str, least_fav_level: str, suggestions: str):
    webhook_url=getenv("WEBHOOK_FEEDBACK_URL")
    webhookt = DiscordWebhook(url=webhook_url)
    embed = DiscordEmbed(title="Feedback", description="Feedback from the Re-Dcrypt Hunt",color="00d2d2")
    embed.add_embed_field(name="User", value=f"{ctx.user.mention}\n{ctx.user.username}#{ctx.user.discriminator},\n{ctx.user.id}")
    embed.add_embed_field(name="Username on site", value=username_site, inline=False)
    embed.add_embed_field(name="Till which level did you complete the hunt", value=level, inline=False)
    embed.add_embed_field(name="Favourite Level", value=fav_level, inline=False)
    embed.add_embed_field(name="Least Favourite Level", value=least_fav_level, inline=False)
    embed.add_embed_field(name="Suggestions/Feedback", value=suggestions, inline=False)
    embed.set_author(name="Re-Dcrypt", icon_url="https://i.imgur.com/LvqKPO7.png")
    webhookt.add_embed(embed)
    response = webhookt.execute()
    if str(response)=="<Response [200]>":
        await ctx.send("Feedback Submitted",ephemeral=True)
    else:
        await ctx.send("Some error occured",ephemeral=True)


bot.start()