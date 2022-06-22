import asyncio
import os
import discord
import requests
import youtube_dl
import utilities
import json
import random
from discord.ext import commands
from dotenv import load_dotenv
from replit import db

load_dotenv()
client = discord.Client()
token = os.environ['discordToken']
intents = discord.Intents.default()
intents.members = True
qBot = commands.Bot(command_prefix=["$"])
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
sessions = []

def check_session(ctx):
    """
    Checks if there is a session with the same characteristics (guild and channel) as ctx param.

    :param ctx: discord.ext.commands.Context

    :return: session()
    """
    if len(sessions) > 0:
        for i in sessions:
            if i.guild == ctx.guild and i.channel == ctx.author.voice.channel:
                return i
        session = utilities.Session(
            ctx.guild, ctx.author.voice.channel, id=len(sessions))
        sessions.append(session)
        return session
    else:
        session = utilities.Session(ctx.guild, ctx.author.voice.channel, id=0)
        sessions.append(session)
        return session


def prepare_continue_queue(ctx):
    """
    Used to call next song in queue.

    Because lambda functions cannot call async functions, I found this workaround in discord's api documentation
    to let me continue playing the queue when the current song ends.

    :param ctx: discord.ext.commands.Context
    :return: None
    """
    fut = asyncio.run_coroutine_threadsafe(continue_queue(ctx), qBot.loop)
    try:
        fut.result()
    except Exception as e:
        print(e)


async def continue_queue(ctx):
    """
    Check if there is a next in queue then proceeds to play the next song in queue.

    As you can see, in this method we create a recursive loop using the prepare_continue_queue to make sure we pass
    through all songs in queue without any mistakes or interaction.

    :param ctx: discord.ext.commands.Context
    :return: None
    """
    session = check_session(ctx)
    if not session.q.theres_next():
        await ctx.send("The queue is over brother.")
        return

    session.q.next()

    voice = discord.utils.get(qBot.voice_clients, guild=session.guild)
    source = await discord.FFmpegOpusAudio.from_probe(session.q.current_music.url, **FFMPEG_OPTIONS)

    if voice.is_playing():
        voice.stop()

    voice.play(source, after=lambda e: prepare_continue_queue(ctx))
    await ctx.send(session.q.current_music.thumb)
    await ctx.send(f"Now Playing: {session.q.current_music.title}")



@qBot.command(name='play', aliases=['add'])
async def play(ctx, *, arg):
    """
    Checks where the command's author is, searches for the music required, joins the same channel as the command's
    author and then plays the audio directly from YouTube.

    :param ctx: discord.ext.commands.Context
    :param arg: str
        arg can be url to video on YouTube or just as you would search it normally.
    :return: None
    """
    try:
        voice_channel = ctx.author.voice.channel

    # If command's author isn't connected, return.
    except AttributeError as e:
        print(e)
        await ctx.send("You're not in a voice channel you fucking idiot")
        return

    # Finds author's session.
    session = check_session(ctx)

    # Searches for the video
    with youtube_dl.YoutubeDL({'format': 'bestaudio', 'noplaylist': 'True'}) as ydl:
        try:
            requests.get(arg)
        except Exception as e:
            print(e)
            info = ydl.extract_info(f"ytsearch:{arg}", download=False)[
                'entries'][0]
            await ctx.send(f"No url given. Searching YouTube for '{arg}'")
        else:
            info = ydl.extract_info(arg, download=False)

    url = info['formats'][0]['url']
    thumb = info['thumbnails'][0]['url']
    title = info['title']

    session.q.enqueue(title, url, thumb)

    # Finds an available voice client for the bot.
    voice = discord.utils.get(qBot.voice_clients, guild=ctx.guild)
    if not voice:
        await voice_channel.connect()
        voice = discord.utils.get(qBot.voice_clients, guild=ctx.guild)

    # If it is already playing something, adds to the queue
    if voice.is_playing():
        await ctx.send(thumb)
        await ctx.send(f"Added {title} to the queue")
        return
    else:
        await ctx.send(thumb)
        await ctx.send(f"Now Playing - {title}")

        # Guarantees that the requested music is the current music.
        session.q.set_last_as_current()

        source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
        voice.play(source, after=lambda ee: prepare_continue_queue(ctx))

@qBot.command(name='pause')
async def pause(ctx):
    """
    If playing audio, pause it.

    :param ctx: discord.ext.commands.Context
    :return: None
    """
    voice = discord.utils.get(qBot.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
    else:
        await ctx.send("I'm not playing anything you fucking moron")

@qBot.command(name='resume')
async def resume(ctx):
    """
    If audio is paused, resumes playing it.

    :param ctx: discord.ext.commands.Context
    :return: None
    """
    voice = discord.utils.get(qBot.voice_clients, guild=ctx.guild)
    if voice.is_paused:
        voice.resume()
    else:
        await ctx.send("I wasn't paused dumbass")

@qBot.command(name='next', aliases=['skip'])
async def skip(ctx):
    """
    Skips the current song, playing the next one in queue if there is one.

    :param ctx: discord.ext.commands.Context
    :return: None
    """
    # Finds author's session.
    session = check_session(ctx)
    # If there isn't any song to be played next, return.
    if not session.q.theres_next():
        await ctx.send("No song up next")
        return

    # Finds an available voice client for the bot.
    voice = discord.utils.get(qBot.voice_clients, guild=session.guild)

    # If it is playing something, stops it. This works because of the "after" argument when calling voice.play as it is
    # a recursive loop and the current song is already going to play the next song when it stops.
    if voice.is_playing():
        voice.stop()
        return
    else:
        # If nothing is playing, finds the next song and starts playing it.
        session.q.next()
        source = await discord.FFmpegOpusAudio.from_probe(session.q.current_music.url, **FFMPEG_OPTIONS)
        voice.play(source, after=lambda e: prepare_continue_queue(ctx))
        return

@qBot.command(name='stop')
async def stop(ctx):
    """
    Stops playing audio and clears the session's queue.

    :param ctx: discord.ext.commands.Context
    :return: None
    """
    session = check_session(ctx)
    voice = discord.utils.get(qBot.voice_clients, guild=ctx.guild)
    if voice.is_playing:
        voice.stop()
        session.q.clear_queue()
    else:
        await ctx.send("Did you hear music playing? Didn't think so.")

@qBot.command(name='gtfo')
async def leave(ctx):
    """
    If bot is connected to a voice channel, it leaves it.

    :param ctx: discord.ext.commands.Context
    :return: None
    """
    voice = discord.utils.get(qBot.voice_clients, guild=ctx.guild)
    if voice.is_connected:
        check_session(ctx).q.clear_queue()
        await voice.disconnect()
    else:
        await ctx.send("Bot not connected, so it can't leave.")
      
@qBot.command(name='print')
async def print_info(ctx):
    """
    A debug command to find session id, what is current playing and what is on the queue.
    :param ctx: discord.ext.commands.Context
    :return: None
    """
    session = check_session(ctx)
    await ctx.send(f"Session ID: {session.id}")
  
    if(session.q.current_music.title != ''):
      await ctx.send(f"Now Playing: {session.q.current_music.title}")
      
    queue = [q[0] for q in session.q.queue]
    if(queue.len() == 0):
      await ctx.send(f"Queue: {queue}")


@qBot.command(name='atp')
async def add_song_to_playlist(ctx, *, arg):
  session = check_session(ctx)
  # Searches for the video
  with youtube_dl.YoutubeDL({'format': 'bestaudio', 'noplaylist': 'True'}) as ydl:
      try:
          requests.get(arg)
      except Exception as e:
          print(e)
          info = ydl.extract_info(f"ytsearch:{arg}", download=False)[
              'entries'][0]
          await ctx.send(f"Searching YouTube for '{arg}'")
      else:
          info = ydl.extract_info(arg, download=False)
        
  url = info['formats'][0]['url']
  thumb = info['thumbnails'][0]['url']
  title = info['title']
  json_song = {"url": f"{url}", "thumb" : f"{thumb}","title" : f"{title}"}
  db_song_key = f"playlist_item: {title}"
  db_keys = db.keys()
  
  if db_song_key not in db_keys:
    db[f"playlist_item: {title}"] = json.dumps(json_song)
    await ctx.send(thumb)
    await ctx.send(f"Added '{title}' to the playlist")
    await ctx.send(f"Playlist now contains {db_keys.len()} songs")
  else:
    await ctx.send(f"{title} is already in the playlist")
  print(db[f"playlist_item: {title}"])
  
@qBot.command(name='playlistInfo')
async def show_playlist_info(ctx):
  session = check_session(ctx)
  playlist_items = db.prefix("playlist_item:")
  await ctx.send(f"There are currently {playlist_items.len()} songs in the playlist")
  if(playlist_items.len() > 0):
    await ctx.send(f"Type '$shuffle' to shuffle through them or '$showPlaylist' to see all of the songs")
  else:
    await ctx.send(f"Type '$atp song name' to add some songs to the playlist")
    

@qBot.command(name='shuffle')
async def shuffle_playlist(ctx):
  session = check_session(ctx)
  playlist_items = db.prefix("playlist_item:")
  shuffled_items = random.shuffle(playlist_items)
  for i in shuffled_items:
    song = json.loads(db[f"{i}"])
    song_title = song["title"]
    song_url = song["url"]
    song_thumb = song["thumb"]
    await ctx.invoke(qBot.get_command('add'), query=f"{song_title}")
  
# Runs bot's loop.
qBot.run(token)

