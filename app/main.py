"""
Created by externo6. v1.0a

By design this is a basic discord music bot that plays from youtube. I built this for my friends as the bot we used to use stopped functioning due to youtube blocking IP's without login, plus its a nice little project for myself.
A small note, I do not plan to provide any support for this, you use this at your own risk.
Another note, my error catching is pretty basic/meh. In reality, I dont really care what the error is just print it and continue. If there is an error its most likely due to a service error or something I f'ed up.

While basic, it can auth via oauth2 to get around youtubes login requirements however this may break TOS so use that feature at your own risk (configurable via config)

Features include: 
* Playing music from Youtube
* Queue system with skipping etc
* 'ish' lyric searching (though in my very minimal testing it wasnt very accurate / gave no results?)
* Supports been in multiple guilds with the same bot.

There are no planned updates. Updates will most likely come when my friends request somethign, or it stops working for whatever reason.

Recommended to use docker though cant see why it cant be used on baremetal (not tested baremetal), check out the Dockerfile for pip packages / system packages required.
If using oauth2 I suggest either using a host mount or perm docker volume for storage as the yt-dlp_cache holds the oauth data, if you dont then you'll need to re-auth everytime the container starts.
In the docker-compose file I use a host mount. If you dont plan to use oauth then ignore this.


Build the compose: docker compose build
Run the compose: docker compose run
This should generate a config.ini in the root of the app. Fill that in with your perfered prefix and docker token, then re-run the bot - If all is well you should have a working basic bot! :)


When using oauth2:
If the yt-dlp_cache does not have the oauth2 token the bot will pause and ask you to login with a link. You should only need to do this once as long as the cache is persistant. 
(I only experienced it asking me to login via oauth2 IF youtube was forcing a login, if not then it just played the music without issue.)
"""

import discord
import asyncio
import configparser
import os
import sys
import random
import yt_dlp as youtube_dl

from discord.ext import commands, tasks
from youtubesearchpython import VideosSearch, Playlist
from azapi import AZlyrics


# Generate config
config = configparser.ConfigParser()
if not os.path.exists('config.ini'):
    config['DEFAULT'] = {'command_prefix': '!', 'zack_disabled': True, 'token': '', 'oauth_support': False}
    config.write(open('config.ini', 'w'))
    print("Add your token to config.ini")
    sys.exit()
else:
    config.read('config.ini')
    if config.get('DEFAULT', 'token') == '':
        print("Add your token to config.ini")
        sys.exit()

# Silence errors from youtube_dl
youtube_dl.utils.bug_reports_message = lambda: ''

# Set bot prefix from config.
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=config.get('DEFAULT', 'command_prefix'), intents=intents)

# Should the bot attempt to use oauth?
# as this is not a bool, make it a bool based off the string.
if config.get('DEFAULT', 'oauth_support') == 'True':
    oauth = True
else:
    oauth = False

# Def Lyrics (uses https://github.com/elmoiv/azapi)
_lyrics = AZlyrics("duckduckgo", accuracy=0.5)

# Dict to hold queues.
queues = {}

# Dict to hold vars, with guild ID's
bot_vars = {}


# On Ready
@bot.event
async def on_ready():
    check_voice_channel.start()
    print('Ready')

# Join channel
async def join_channel(ctx):
    channel = ctx.author.voice.channel
    if ctx.voice_client is not None:
        await ctx.voice_client.move_to(channel)
    else:
        await channel.connect()


# Search for youtube video and returns the first result.
async def search_yt(ctx, query):
    try:
        videos_search = VideosSearch(query, limit=1)
        if videos_search.result():
            return videos_search.result()['result'][0]
        else:
            await ctx.send(f"Sorry! I couldnt find a result for {query}")
    except Exception as e:
        await ctx.send(f"🎵😔 Issue when searching for {query}: {e}")


# Returns a dict of songs from a playlist. Playlist must be public.
async def playlist_search_yt(ctx, query):
    try:
        videos_search = Playlist.getVideos(query)
        if 'videos' in videos_search:
            return videos_search['videos']
        else:
            await ctx.send(f"Sorry! I couldnt find a result for {query}")
    except Exception as e:
        await ctx.send(f"🎵😔 Issue when searching for {query}: {e}")


# Play video via streaming using ffmpeg. Uses FFmpegOpusAudio over FFmpegPCMAudio as FFmpegOpusAudio 'should' be more efficent in cpu cycles.
async def stream_yt(ctx, url):
    try:
        guild_id = ctx.guild.id
        if oauth: # If oauth is true use the below ydl_opts. 
            ydl_opts = {'format': 'bestaudio','username': 'oauth2','password': '',}
        else:
            ydl_opts = {'format': 'bestaudio',}

        ffmpeg_options = {'options': '-vn','before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'} #-vn disable video
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            message = await ctx.send(f"🎵 Loading... {info["title"]}")
            ctx.voice_client.play(discord.FFmpegOpusAudio(info['url'], **ffmpeg_options), after=lambda e: asyncio.run_coroutine_threadsafe(play_queue(ctx, guild_id), bot.loop))
            
            # set now playing:
            vars = bot_vars.get(guild_id, {})
            vars['nowplaying'] = info['title']
            await message.edit(content=f'🎵 Now playing: {info["title"]}')
    except Exception as e:
        await ctx.send(f"🎵😔 Something didnt happen as expected (Stream). {e}")


# Play music from the queue
async def play_queue(ctx, guild_id):
    queue = queues.get(guild_id, [])
    if queue:
        url = queue.pop(0)
        await stream_yt(ctx, url['url'])


"""
Current commands:
play - Plays music
stop - Stops music (Hard stop, clears queue too.)
pause - Pauses
resume - Resumes from paused state
clear_queue - Clears queue - Alias: clear, clearqueue
disconnect - Disconnect from current channel - Alias: leave, goaway, exit (goaway is my persional favorite, bot uprising?)
lyrics - Bad lyric searching
nowplaying - Shows the current playing - Alias: np
queue - Shows the current queue
imZack - Plays the youtube video Im Zack (inside meme/joke) Can be disabled in the config, (disabled by default) - Alias: imzack, zack, playzack -

"""

@bot.command()
async def play(ctx , *, query):
    queue = queues.setdefault(ctx.guild.id, []) # Set the default queue based on the guild id, allows having multiple guilds powered by one bot
    bot_vars.setdefault(ctx.guild.id, {}) # Set the default vars for requested guild
    message = await ctx.send(f"🎵 Searching for {query}")
    """ 
    Search youtube and check if list is in the URL. If list is in the URL its most likley a playlist so we'll treat it as such.
    If so use the playlist search to get a list of songs in that playlist. If list is in the query, we assume its a playlist.
    (Playlists have been somewhat tested, though when a playlist goes private it throws abit off an odd error... Still works when playlists are public) 
    """
    if 'list' in query:
        search_results = await playlist_search_yt(ctx, query)
        playlist = True
    else:
        search_results = await search_yt(ctx, query)
        playlist = False
    await join_channel(ctx)

    # If the playlist bool is set, we'll loop through and add them all to the queue, else we'll just add the returned result.
    if(playlist):
        if not search_results:
            await ctx.send(f"🎵😔 No results for that playlist?")
            return
        for result in search_results:
            # We'll use the ID instead of link, as we dont want the playlist link.
            queue.append({'url':f"https://www.youtube.com/watch?v={result['id']}", 'title':result['title']})
        await ctx.send(content=f'🎵 Added {len(search_results)} videos to the queue.')
    else:
        queue.append({'url':search_results['link'], 'title':search_results['title']})
        if ctx.voice_client.is_playing():
            await message.edit(content=f'🎵 Added to queue: {search_results['title']}')

    # Start playing the queue if its not already playing.
    if not ctx.voice_client.is_playing():
        await play_queue(ctx, ctx.guild.id)  # Pass ctx argument to play function


@bot.command()
async def stop(ctx):
    # Ensure queue is clear and clear vars.
    queue = queues.get(ctx.guild.id)
    queue.clear()
    bot_vars.get(ctx.guild.id).clear()
    if ctx.voice_client and ctx.voice_client.is_playing():
        if len(queue) == 0:
            ctx.voice_client.stop()
            await ctx.send("🎵 Stopping playback...")
    else:
        await ctx.send("🎵 Nothing is playing? 😖")

@bot.command(aliases=['clear', 'clearqueue'])
async def clear_queue(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("🎵 Stopping playback...")
        queues.get(ctx.guild.id).clear()
        bot_vars.get(ctx.guild.id)['nowplaying'] = ''
        await ctx.send("🎵 Queue Cleared.")
    else:
        await ctx.send("🎵 Nothing is playing? 😖")

@bot.command(aliases=['next', 'nextsong'])
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("🎵 Skipping the current song ⏭️")
    else:
        await ctx.send("🎵 Nothing is playing? 😖")

@bot.command()
async def queue(ctx):
    queue = queues.setdefault(ctx.guild.id, [])
    if len(queue) == 0:
        await ctx.send("🎵 Queue is empty! 😔")
    else:
        await ctx.send(f"🎵 Current Queue:")
        queueList = ''
        for index, item in enumerate(queue):
            # Discord respects the \n so create a string with \n for new line, 2000 char limit? Probs should add a catch if the queue is REALLY long (like for lyrics), but I doubt anyone will do this...
            queueList += f"{index+1}: {item['title']}\n"
        await ctx.send(queueList)

@bot.command()
async def pause(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send(f"🎵 Paused ⏸️")
    else:
        await ctx.send("🎵 Nothing is playing? 😖")

@bot.command()
async def resume(ctx):
    if not ctx.voice_client.is_playing():
        ctx.voice_client.resume()
        await ctx.send(f"🎵 Resuming ▶️")
    else:
        await ctx.send("🎵 Nothing is playing? 😖")

@bot.command(aliases=['leave', 'goaway', 'exit'])
async def disconnect(ctx):
    random_exit = ["Cya folks!", "Bye for now!", "Until next time!", "Aww, I was enjoying your conversation"]
    await ctx.send(f"🎵 {random.choice(random_exit)}")
    await ctx.voice_client.disconnect()

@bot.command()
async def lyrics(ctx):
    vars = bot_vars.get(ctx.guild.id)
    if ctx.voice_client and ctx.voice_client.is_playing():
        # Search for the song using the nowplaying song.
        _lyrics.title = vars['nowplaying']
        song = _lyrics.getLyrics()
        if song:
            # Split the lyrics to avoid message length limits, we'll send them in chunks.
            chunks = [song[i:i+2000] for i in range(0, len(song), 2000)]
            for chunk in chunks:
                await ctx.send(chunk)
        else:
            await ctx.send("No lyrics found for the given song.")
    else:
        await ctx.send("🎵 Nothing is playing? 😖")

@bot.command(aliases=['np'])
async def nowplaying(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        vars = bot_vars.get(ctx.guild.id)
        await ctx.send(f"🎵 Now playing: {vars['nowplaying']}")
    else:
        await ctx.send("🎵 Nothing is playing? 😖")


"""
Im Zack Command, can be enabled in config.
Inside joke with my friends, no real use to anyone else and disabled by default.
"""
if config.get('DEFAULT', 'zack_disabled') == 'False': # Not a bool with ini
    @bot.command(aliases=['zack', 'imzack', 'playzack'])
    async def imZack(ctx):
        # First check if its playing anything.
        await join_channel(ctx)
        if not ctx.voice_client.is_playing():
            await stream_yt(ctx, "https://www.youtube.com/watch?v=Qc_PO32nT4g")
        else:
            # Playing something. Lets stop the music and play zack. Dont need to join, already in channel if stopping.
            ctx.ctx.voice_client.stop()
            await stream_yt(ctx, "https://www.youtube.com/watch?v=Qc_PO32nT4g")




# Every 30 seconds, check if there is anyone in the channel. If not, leave. We dont really want to be sitting in a channel forever!
@tasks.loop(seconds=30)
async def check_voice_channel():
    for vc in bot.voice_clients:
        if len(vc.channel.members) == 1:
            await vc.disconnect()



bot.run(config.get('DEFAULT', 'token'))
