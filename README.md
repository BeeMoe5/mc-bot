# mc-bot
 a discord bot written in discord.py to manage a minecraft server. \
this bot is designed for self-hosting a discord bot and minecraft server and
 is under the assumption you know basic programming and python
### Variables
First, make a file "creds.py" in the same directory as main.py then add all the variables you see below \
ip (type: str) - The ip of the server you are connecting the RCON client to \
port (type: int) - The port for the RCON client \
password (type: str) - The password you set for RCON (Recommended that you set a password) \
console_controller_role_id (type: int) - The ID of the role you want to have required to use most commands \
server_folder_path (type: r-str) - The folder that you have your server jar file in \
console_channel_outp_id (type: int) - The ID of the channel you want console output to go \
d_bot_token (type: str) - Your discord bot token
log_file (type: str) - The file you want to log info in (tbh, i don't even use this because its broken and never bothered to fix it) \
jar_file (type: str) - The server jar file name including the extension 
