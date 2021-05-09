import asyncio
from asyncio import subprocess
import time
from collections import deque

import discord
from aiomcrcon import Client as MCClient, RCONConnectionError
from discord.ext import commands, tasks
from loguru import logger

from creds import ip, port, password, console_controller_role_id, server_folder_path, console_channel_outp_id, \
    log_file, d_bot_token

intents = discord.Intents(guild_messages=True, members=True, guilds=True)
d_bot = commands.Bot(command_prefix='%', help_command=commands.MinimalHelpCommand(),
                     case_insensitive=True, intents=intents)
d_bot.mc_output = deque()

mc_client = MCClient(ip, port, password)

setup = True


@tasks.loop(seconds=0.1)
async def add_output_to_deque():
    server = getattr(d_bot, 'process', None)

    if not server:
        return

    line = await server.stdout.readline()
    d_bot.mc_output.append(line)


@tasks.loop(seconds=1)
@logger.catch()
async def mc_console_output():
    server = getattr(d_bot, 'process', None)

    if server is None:
        return

    c = d_bot.get_channel(console_channel_outp_id)
    timeout_start = time.monotonic()

    to_send = ''
    n = 0
    timeout = 10

    while time.monotonic() < timeout_start + timeout:
        await asyncio.sleep(0.1)

        if not d_bot.mc_output:
            break
        line = d_bot.mc_output.popleft()

        if not line:
            print('no line?')
        to_send += line.decode(errors='ignore')

        n += 1

        if n == 13:
            break

    if to_send != '':
        to_send = discord.utils.escape_markdown(to_send)
        await c.send(to_send)


@d_bot.event
async def on_ready():
    global setup

    if setup:
        logger.add(
            log_file,
            level='DEBUG',
            filter='d_bot'
        )
        logger.info("bot on")
        setup = False
        d_bot.server_started = False
        add_output_to_deque.start()
        mc_console_output.start()


@d_bot.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.MissingRequiredArgument):
        return await ctx.send(f'{ctx.command.qualified_name} is missing a required argument\n\n'
                              f'%{ctx.command.qualified_name} {ctx.command.signature}')

    elif isinstance(error, commands.MissingRole):
        r = ctx.guild.get_role(console_controller_role_id)
        return await ctx.send(f'You need the {r.name} role')

    else:
        raise error


@d_bot.command()
@commands.guild_only()
@commands.has_role(console_controller_role_id)
@logger.catch()
async def start(ctx):
    """
    Starts the mc server and starts the connection with RCON
    *Only works if you have the minecraft server console controller role*
    """

    if d_bot.server_started:
        return await ctx.send("Server is already started")

    d_bot.server_started = True

    d_bot.process = await asyncio.create_subprocess_shell('java -Xmx4096M -Xms4096M -jar spigot-1.16.5.jar',
                                                          stdin=asyncio.subprocess.DEVNULL, stdout=subprocess.PIPE,
                                                          cwd=server_folder_path)
    # await d_bot.process.stdout
    await ctx.send('Server is starting, connecting RCON client')
    await asyncio.sleep(15)

    try:
        await mc_client.connect(25)

    except RCONConnectionError:
        return await ctx.send('RCON client was unable to connect')

    await ctx.send('RCON client is connected')


@d_bot.command()
@commands.guild_only()
@commands.has_role(console_controller_role_id)
async def stop(ctx):
    """
    Stops the minecraft server and stops the connection with RCON
    *Only works if you have the minecraft server console controller role*
    """

    if not getattr(d_bot, 'server_started', False):
        return await ctx.send('Server is not started yet\n\n`%start`')

    await ctx.send('Server is turning off')
    await mc_client.send_cmd('stop')

    d_bot.process.terminate()
    d_bot.server_started = False
    d_bot.process = None
    await mc_client.close()


@d_bot.command()
@commands.guild_only()
@commands.has_role(console_controller_role_id)
async def cmd(ctx, *, command: str):
    """
    Executes a command in the console using RCON
    *Only works if you have the minecraft server console controller role*
    """

    if not getattr(d_bot, 'server_started', False):
        return await ctx.send('Server is not started yet\n\n`%start`')

    await mc_client.connect(10)
    m = await mc_client.send_cmd(command)
    if m[0]:
        await ctx.send(m[0])


d_bot.run(d_bot_token)
