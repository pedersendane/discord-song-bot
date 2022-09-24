import asyncio
from ctypes.wintypes import tagRECT
import datetime
import getopt
import os
import string
import sys
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
from models.queue_item import QueueItem, QueueItemEncoder
import playlist_service, insult_service, queue_service

load_dotenv()
token = os.environ['DISCORD_TOKEN']
# client = discord.Client()
# intents = discord.Intents.default()
# intents.members = True
# qBot = commands.Bot(command_prefix=["$"])
# sessions = []
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
shared_playlist_name = 'Soup Shared'

current_song_id = ''


def main(argv):
    song1 = ''
    song2 = ''
    try:
        opts, args = getopt.getopt(argv,"hs:q:")
    except getopt.GetoptError:
        print('tests.py -s "song name 1" -q "song name 2"')
        sys.exit(2)
    for opt, arg in opts:
        print(opt, arg)
        if opt == '-h':
            print ('tests.py -s "song name 1" -q "song name 2"')
            sys.exit()
        elif opt == ("-s"):
            song1 = arg
        elif opt == ("-q"):
            song2 = arg

    print(f'Songs - {song1}, {song2}')
    asyncio.run(run_tests(song1,song2))
    
    

async def run_tests(song1,song2):
    #Find song 1, add to queue, show info
    # queue_item = await search_for_song(song1)
    queue_item = QueueItem("$UICIDEBOY$ - 1000 BLUNTS (Lyric Video)", 
    "https://i.ytimg.com/vi/VgjTx7RVJPI/hqdefault.jpg?sqp=-oaymwEbCKgBEF5IVfKriqkDDggBFQAAiEIYAXABwAEG&rs=AOn4CLCn_GLus2uCHYitXwywj_1G_pEJUg",
    "https://rr1---sn-q4flrnsd.googlevideo.com/videoplayback?expire=1663984829&ei=XRAuY9CHIuy5ir4Pxe-LUA&ip=99.109.61.83&id=o-ACILkpLGwt0bMPgmwLbIRIXuPiZxxhZVuwo-oKs_HFEL&itag=249&source=youtube&requiressl=yes&mh=zn&mm=31%2C29&mn=sn-q4flrnsd%2Csn-q4fl6nzy&ms=au%2Crdu&mv=m&mvi=1&pl=21&initcwndbps=843750&vprv=1&mime=audio%2Fwebm&ns=i5lp6LuDrNtbd5nRdOQU6vAI&gir=yes&clen=1160598&dur=175.501&lmt=1660871983210022&mt=1663963040&fvip=5&keepalive=yes&fexp=24001373%2C24007246&c=WEB&txp=4532434&n=n19mSxmehCxuvC-TI&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cvprv%2Cmime%2Cns%2Cgir%2Cclen%2Cdur%2Clmt&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=AG3C_xAwRQIhAK2-oYVVMvLjGT0G_8Rj9MuR5-ILqVVB61ij4wcKkQ7tAiAES7Ff1jYN9yBVU0OUOkzTXqJqcBtpsN40lybcPeTTjA%3D%3D&sig=AOq0QJ8wRQIhAPd1nI1RGlOgLyp4do3kpb5pZg8tSVuRdlzSlw4JDdvvAiAcP438AmVp_Y46C600Xnqid9C9tdyIQgRa1tWhRfCgew=="
    )
    await add_song_to_queue(queue_item)

    # #Find song 2, add to queue, show info
    # queue_item_2 = await search_for_song(song2)
    queue_item_2 = QueueItem("Eliza Rose - B.O.T.A. (Baddest Of Them All) (Lyrics)", 
    "Eliza Rose - B.O.T.A. (Baddest Of Them All) (Lyrics)",
    "https://rr1---sn-q4flrnsd.googlevideo.com/videoplayback?expire=1663984829&ei=XRAuY9CHIuy5ir4Pxe-LUA&ip=99.109.61.83&id=o-ACILkpLGwt0bMPgmwLbIRIXuPiZxxhZVuwo-oKs_HFEL&itag=249&source=youtube&requiressl=yes&mh=zn&mm=31%2C29&mn=sn-q4flrnsd%2Csn-q4fl6nzy&ms=au%2Crdu&mv=m&mvi=1&pl=21&initcwndbps=843750&vprv=1&mime=audio%2Fwebm&ns=i5lp6LuDrNtbd5nRdOQU6vAI&gir=yes&clen=1160598&dur=175.501&lmt=1660871983210022&mt=1663963040&fvip=5&keepalive=yes&fexp=24001373%2C24007246&c=WEB&txp=4532434&n=n19mSxmehCxuvC-TI&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cvprv%2Cmime%2Cns%2Cgir%2Cclen%2Cdur%2Clmt&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=AG3C_xAwRQIhAK2-oYVVMvLjGT0G_8Rj9MuR5-ILqVVB61ij4wcKkQ7tAiAES7Ff1jYN9yBVU0OUOkzTXqJqcBtpsN40lybcPeTTjA%3D%3D&sig=AOq0QJ8wRQIhAPd1nI1RGlOgLyp4do3kpb5pZg8tSVuRdlzSlw4JDdvvAiAcP438AmVp_Y46C600Xnqid9C9tdyIQgRa1tWhRfCgew=="
    )
    await add_song_to_queue(queue_item_2)

    #Get Queue items
    q = await get_queue()
    
    #Delete queue
    for item in q:
        await remove_song_from_queue(item)

async def search_for_song(song_name):
    print(f'\n-------------------------Starting search_for_song("{song_name}")-----------------------')
    with youtube_dl.YoutubeDL({'format': 'bestaudio', 'noplaylist': 'True'}) as ydl:
        try:
            requests.get(song_name)
        except Exception as e:
            #if they didn't type an actual url
            if e.args[0][0:11] == "Invalid URL":
                info = ydl.extract_info(f"ytsearch:{song_name}", download=False)['entries'][0]
            else:
                print(f"There was an error playing **{song_name}**.\nTry adding **lyrics** to the end, or kick me out and try again.")
        else:
            info = ydl.extract_info(song_name, download=False)
    song = QueueItem(info['title'],info['thumbnails'][0]['url'],info['formats'][0]['url'])
    return song

async def add_song_to_queue(queue_item):
    print(f'\n-------------------------Starting add_song_to_queue()-----------------------')
    message = await queue_service.create_queue_item(queue_item)
    print(message)


async def get_queue():
    print(f'\n-------------------------Starting get_queue()-----------------------')
    items = await queue_service.get_all_queue_items()
    for i in items:
        print(f'{i.title} - {i.date_added}')
    return items
    
    
async def remove_song_from_queue(queue_item):
    print(f'\n-------------------------Starting remove_song_from_queue()-----------------------')
    message = await queue_service.delete_queue_item(queue_item)
    print(message)



async def skip_song():
    print(f'\n-------------------------Starting skip_song()-----------------------')


async def add_song_to_playlist():
    print(f'\n-------------------------Starting add_song_to_playlist()-----------------------')
    playlist = playlist_service.get_playlist_by_name(shared_playlist_name)
    if playlist is not None:
        # song = PlaylistItem(playlist.id, info['title'], info['formats'][0]['url'], info['thumbnails'][0]['url'])
        song = PlaylistItem(playlist.id, title, url, thumb)
        message = await playlist_service.create_song(song)
        print(message)

async def delete_playlist_item():
    print(f'\n-------------------------Starting add_song_to_playlist()-----------------------')
    playlist_items = playlist_service.get_all_songs()
    for i in playlist_items:
        if i.title == title:
            await playlist_service.delete_song(i)
            print(f'**{title}** has been removed from the playlist')
        

async def show_playlist_items(ctx):
    print(f'\n-------------------------Starting add_song_to_playlist()-----------------------')
    playlist_string = '**Current Playlist:**'
    playlist_items = await playlist_service.get_all_songs()
    if(len(playlist_items) > 0):
        index = 0
        for i in playlist_items:
            playlist_string += f"\n> {index + 1}. {i.title}"
            index += 1
        print(playlist_string)
    

if __name__ == "__main__":
    main(sys.argv[1:])




