from dotenv import load_dotenv
import discord, asyncio, json, os
import requests as r

ctx = discord.Client()
load_dotenv(verbose=True)

@ctx.event
async def on_message(message):
    if message.content.startswith("~config"):
        if message.channel.server.owner.id == message.author.id:
            with open("servers.json", "r") as f:
                servers = json.load(f)
            if message.channel.server.id in servers:
                await ctx.send_message(message.channel, 'Overwriting your previous configuration')
            if len(message.content.split(" ")) < 3:
                await ctx.send_message(message.channel, 'Invalid syntax, expected ``~config [channel_id] [alert_role_id]``, you can also use ``-1`` for the alerts role to alert no role.')
            else:
                channel = message.content.split(" ")[1]
                role = message.content.split(" ")[2]
                await ctx.send_message(message.channel, f"Your config for the server ``{message.channel.server.name}`` is to ping <@&{role}> in <#{channel}>! Don't forget I need ``Manage Roles`` permissions to do my job!")
                servers.update({message.channel.server.id: {
                    "channel": channel,
                    "role": role
                }})
                #await ctx.send_message(discord.Object(id=channel), "Configuration set! Anyone with the correct role will get pinged with new **Canary** builds.")
                with open("servers.json", "w") as f:
                    json.dump(servers, f, indent=1)
        else: 
            await ctx.send_message(message.channel, "🔒 You do not have permission to do that!")
    if message.content.startswith("~stable"):
        req = r.get("http://localhost:1337/discord/stable/builds/latest").json()
        embed = discord.Embed(type="rich", color=0x7289DA)
        embed.add_field(name="Build Number", value=req['build_num'])
        embed.add_field(name="Build ID", value=req['build_id'])
        embed.set_author(name="Latest Stable Build",
                         icon_url="https://img.adityadiwakar.me/8x4R.jpg")
        await ctx.send_message(message.channel, embed=embed)
    if message.content.startswith("~canary"):
        req = r.get("http://localhost:1337/discord/canary/builds/latest").json()
        embed = discord.Embed(type="rich", color=0x7289DA)
        embed.add_field(name="Build Number", value=req['build_num'])
        embed.add_field(name="Build ID", value=req['build_id'])
        embed.set_author(name="Latest Canary Build",
                         icon_url="https://img.adityadiwakar.me/8x4R.jpg")
        await ctx.send_message(message.channel, embed=embed)
    if message.content.startswith("~ptb"):
        req = r.get("http://localhost:1337/discord/ptb/builds/latest").json()
        embed = discord.Embed(type="rich", color=0x7289DA)
        embed.add_field(name="Build Number", value=req['build_num'])
        embed.add_field(name="Build ID", value=req['build_id'])
        embed.set_author(name="Latest PTB Build",
                         icon_url="https://img.adityadiwakar.me/8x4R.jpg")
        await ctx.send_message(message.channel, embed=embed)


@ctx.event
async def on_ready():
    print('Logged in')


def check_diff(req):
    with open("hash.txt", "r") as f:
        hash = f.read()
    if req['build_hash'] == hash:
        return False
    hash = req['build_hash']
    with open("hash.txt", "w") as f:
        f.write(hash)
    return True

def get_server_config():
    with open("servers.json", "r") as f:
        servers = json.load(f)
    return servers

def create_new_embed(build_num, build_id):
    embed = discord.Embed(type="rich", color=0x7289DA)
    embed.add_field(name="Build Number", value=build_num)
    embed.add_field(name="Build ID", value=build_id)
    embed.set_author(name="New Canary Build", url="https://img.adi.wtf/8x4R.jpg", icon_url="https://img.adi.wtf/8x4R.jpg")
    return embed

async def new_update_alert(role, server, channel, embed):
    if channel == None or server == None:
        return
    if role == None:
        await ctx.send_message(channel, embed=embed)
        return
    else:
        await ctx.edit_role(server, role, mentionable=True)
        await ctx.send_message(channel, f"<@&{role.id}>", embed=embed)
        await ctx.edit_role(server, role, mentionable=False)

async def push_canary_update():
    await ctx.wait_until_ready()
    while True:
        req = r.get("http://localhost:1337/discord/canary/builds/latest").json()
        if check_diff(req) == True:
            
            update_embed = create_new_embed(req['build_num'], req['build_id'])       
            servers_to_ping = get_server_config()

            for client_server in ctx.servers:
                if client_server.id in servers_to_ping:
                    config = servers_to_ping[client_server.id]

                    role = None
                    for server_role in client_server.roles:
                        if server_role.id == config['role']:
                            role = server_role
                            break

                    channel = None
                    for server_channel in client_server.channels:
                        if server_channel.id == config['channel']:
                            channel = server_channel
                            break

                    try:
                        await new_update_alert(role, client_server, channel, update_embed)
                    except:
                        pass

        await asyncio.sleep(4)


def run_bot():
    ctx.loop.create_task(push_canary_update())
    ctx.run(os.getenv('BOT_TOKEN'))


run_bot()

