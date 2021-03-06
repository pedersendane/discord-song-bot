import asyncio
import datetime
import os
import discord
import requests
import youtube_dl
import json
import random
import time
import ffmpeg
from discord.ext import commands
from discord import FFmpegOpusAudio
from dotenv import load_dotenv
from keep_alive import keep_alive
from models.queue import Queue,Session
from models.playlist import PlaylistItem, Playlist
import playlist_service

load_dotenv()
token = os.environ['DISCORD_TOKEN']
client = discord.Client()
intents = discord.Intents.default()
intents.members = True
qBot = commands.Bot(command_prefix=["$"])
sessions = []
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
shared_playlist_name = 'Soup Shared'

#Check for multiple sessions
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
        session = Session(
            ctx.guild, ctx.author.voice.channel, id=len(sessions))
        sessions.append(session)
        return session
    else:
        session = Session(ctx.guild, ctx.author.voice.channel, id=0)
        sessions.append(session)
        return session

#Call Next song in queue
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


#Check queue and keep it going
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


#Play a song
@qBot.command(name='play', aliases=['add', 'p'])
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

    session = check_session(ctx)

    with youtube_dl.YoutubeDL({'format': 'bestaudio', 'noplaylist': 'True'}) as ydl:
        try:
            requests.get(arg)
        except Exception as e:
            print(e)
            info = ydl.extract_info(f"ytsearch:{arg}", download=False)[
                'entries'][0]
            #await ctx.send(f"Searching YouTube for **{arg}**")
        else:
            info = ydl.extract_info(arg, download=False)

    url = info['formats'][0]['url']
    thumb = info['thumbnails'][0]['url']
    title = info['title']

    session.q.enqueue(title, url, thumb)

    voice = discord.utils.get(qBot.voice_clients, guild=ctx.guild)
    if not voice:
        await voice_channel.connect()
        voice = discord.utils.get(qBot.voice_clients, guild=ctx.guild)

    if voice.is_playing():
        await ctx.send(thumb)
        await ctx.send(f"**Added to queue:**\n>>> {title}")
        return
    else:
        await ctx.send(thumb)
        await ctx.send(f"**Now Playing:**\n>>> {title}")

        session.q.set_last_as_current()

        source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
        voice.play(source, after=lambda ee: prepare_continue_queue(ctx))

#Pause Song
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

#Resume
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

#Skip to next song
@qBot.command(name='next', aliases=['skip'])
async def skip(ctx):
    """
    Skips the current song, playing the next one in queue if there is one.

    :param ctx: discord.ext.commands.Context
    :return: None
    """
    session = check_session(ctx)
    if not session.q.theres_next():
        await ctx.send("The queue is empty")
        return

    voice = discord.utils.get(qBot.voice_clients, guild=session.guild)

    if voice.is_playing():
        voice.stop()
        return
    else:
        session.q.next()
        source = await discord.FFmpegOpusAudio.from_probe(session.q.current_music.url, **FFMPEG_OPTIONS)
        voice.play(source, after=lambda e: prepare_continue_queue(ctx))
        return

#Clear queue
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

#Kick Jockie out and clear queue
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

#Show Current Queue
@qBot.command(name='q')
async def print_info(ctx):
    """
    A debug command to find session id, what is current playing and what is on the queue.
    :param ctx: discord.ext.commands.Context
    :return: None
    """
    session = check_session(ctx)
    if(session.q.current_music.title != ''):
      await ctx.send(f"**Now Playing:**\n>>> {session.q.current_music.title}\n\n")

    if(len(session.q.queue) > 0): 
      queue_string = '**Up Next:**\n>>> '
      index = 0
      for i in session.q.queue:
        title = i[0]
        url = i[1]
        thumb = i[2]
        if(index != 0):
          queue_string += f"{title}\n"
        index += 1
    else:
      queue_string = "**The queue is empty**"

    await ctx.send(queue_string)
        
#Add song to playlist
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
            #await ctx.send(f"Searching YouTube for '{arg}'")
        else:
            info = ydl.extract_info(arg, download=False)

    playlist = playlist_service.get_playlist_by_name(shared_playlist_name)
    if playlist is not None:
        song = PlaylistItem(playlist.id, info['title'], info['formats'][0]['url'], info['thumbnails'][0]['url'])
        message = playlist_service.create_song(song)
        await ctx.send(message)


#Show all playlist items
@qBot.command(name='playlist')
async def show_playlist_items(ctx):
  playlist_string = '**Current Playlist:**'
  playlist_items = playlist_service.get_all_songs()
  if(len(playlist_items) > 0):
    index = 0
    for i in playlist_items:
        playlist_string += f"\n> {index + 1}. {i.title}"
        index += 1
    await ctx.send(playlist_string)
    await ctx.send(f'**$pl 1** - Play song 1\n**$dpl 1** - Delete song 1')

#Play a specific playlist song
@qBot.command(name='pl')
async def play_playlist_item(ctx, *, arg):
    session = check_session(ctx)
    try:
        voice_channel = ctx.author.voice.channel
    except AttributeError as e:
        print(e)
        await ctx.send("You're not in a voice channel you fucking idiot")
        return

    try:
        index = int(arg) - 1
    except ValueError as e:
        print(e)
        await ctx.send("Are you fucking retarded?")
        return

    playlist_items = playlist_service.get_all_songs()
    if(len(playlist_items) > 0):
        if(index >= 0 and index <= len(playlist_items)):
            song = playlist_items[index]
            title = song.title
            url = song.url
            thumb = song.thumb
            voice = discord.utils.get(qBot.voice_clients, guild=ctx.guild)
            if not voice:
                await voice_channel.connect()
                voice = discord.utils.get(qBot.voice_clients, guild=ctx.guild)
        
            if voice.is_playing():
                await ctx.send(thumb)
                await ctx.send(f"**Added to queue:**\n>>> {title}")
                return
            else:
                await ctx.send(thumb)
                await ctx.send(f"**Now Playing:**\n>>> {title}")
                session.q.set_last_as_current()
                source = await discord.FFmpegOpusAudio.from_probe(url,**FFMPEG_OPTIONS)
                voice.play(source, after=lambda ee: prepare_continue_queue(ctx))
        else:
            await ctx.send("Are you fucking retarded?")
    else:
        await ctx.send("There are no songs in the playlist")
  
# #Delete a specific playlist song
@qBot.command(name='dpl')
async def delete_playlist_item(ctx, *, arg):
  try:
    index = int(arg) - 1
  except AttributeError as e:
    print(e)
    await ctx.send("Are you fucking retarded?")
    return
    
  playlist_items = playlist_service.get_all_songs()
  if(len(playlist_items) > 0):
    if(index >= 0 and index <= len(playlist_items)):
        song = playlist_items[index]
        title = song.title
        confirm_string = f"**{title}** has been removed from the playlist"
        playlist_service.delete_song(song)
        await ctx.send(confirm_string)
    
  
  


# #Shuffle Playlist
@qBot.command(name='shuffle')
async def shuffle_playlist(ctx):
  session = check_session(ctx)
  try:
    voice_channel = ctx.author.voice.channel

  except AttributeError as e:
    print(e)
    await ctx.send("You're not in a voice channel you fucking idiot")
    return
  
  playlist_items = playlist_service.get_all_songs()
  shuffled_items = random.sample(playlist_items, k=len(playlist_items))
  for i in shuffled_items:
    title = i.title
    url = i.url
    thumb = i.thumb
    session.q.enqueue(title, url, thumb)

  voice = discord.utils.get(qBot.voice_clients, guild=ctx.guild)
  if not voice:
    await voice_channel.connect()
    voice = discord.utils.get(qBot.voice_clients, guild=ctx.guild)

  if voice.is_playing():
    await ctx.send(thumb)
    await ctx.send(f"Added {title} to the queue")
    return
  else:
    await ctx.send(thumb)
    await ctx.send(f"Now Playing - {title}")
    session.q.set_last_as_current()
    source = await discord.FFmpegOpusAudio.from_probe(url,**FFMPEG_OPTIONS)
    voice.play(source, after=lambda ee: prepare_continue_queue(ctx))
  



#Help 
@qBot.command(name='sos')
async def show_help(ctx):
  await ctx.send("\n__Queue/Song Commands__\n>>> " + 
                "**$p _song name_** - Play song name \n" + 
                 "**$add _song name_** - Add song name to the queue\n" + 
                 "**$pause** - Pause the music\n" + 
                 "**$resume** - Resume the music\n" + 
                 "**$next _or_ $skip** - Go to next song in queue\n" + 
                 "**$stop** - Clears the queue and stops the music\n" +
                 "**$q** - Show song and queue info\n" +
                 "**$gtfo** - Kicks bot out of chat\n" 
                )

  await ctx.send("\n__Playlist Commands__\n>>> " +
                 "**$atp _song name_** - Add song name to playlist\n" +
                 "**$playlist** - Show all playlist items\n" +
                 "**$pl 2** - Play playlist item number 2\n" +
                 "**$dpl 2** - Delete playlist item number 2\n" +
                 "**$shuffle** - Shuffle and play the playlist\n"
                )



print("Running...")
# Runs bot's loop.
qBot.run(token)

#Run Web Server
#keep_alive()
