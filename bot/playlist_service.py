from contextlib import nullcontext
from datetime import date, datetime
import os
import json
from unicodedata import name
import requests
from models.playlist import PlaylistItemEncoder
from models.playlist import Playlist, PlaylistItem
from dotenv import load_dotenv

load_dotenv()
token = os.environ['DISCORD_TOKEN']
base_api_url = os.environ['API_BASE_URL']
song_api_key = os.environ['PLAYLIST_ITEM_API_KEY']
playlist_api_key = os.environ['PLAYLIST_API_KEY']
song_collection = os.environ['SONG_COLLECTION']
playlist_collection = os.environ['PLAYLIST_COLLECTION']
database = os.environ['PLAYLIST_DATABASE']
data_source = os.environ['PLAYLIST_DATA_SOURCE']

# Get all playlists
def get_all_playlists():
    playlists = []
    url = f"{base_api_url}/action/find"
    headers = {
        'Content-Type': 'application/json',
        'api-key': playlist_api_key, 
    }
    payload = json.dumps({
        "collection": playlist_collection,
        "database": database,
        "dataSource": data_source
    })

    response = requests.request("POST", url, headers=headers, data=payload )
    if(response.status_code == 200):
        res = json.loads(response.text)
        documents = res['documents']
        for i in documents:
            playlist = Playlist
            playlist.id = i['_id']
            playlist.name = i['name']
            playlists.append(playlist)

    return playlists


#Get single playlist by name
def get_playlist_by_name(name):
    playlist = Playlist
    url = f"{base_api_url}/action/findOne"
    headers = {
        'Content-Type': 'application/json',
        'api-key': playlist_api_key, 
    }
    payload = json.dumps({
        "collection": playlist_collection,
        "database": database,
        "dataSource": data_source,
        "filter": {
            "name":name
        }
    })

    response = requests.request("POST", url, headers=headers, data=payload )
    if(response.status_code == 200):
        try:
            res = json.loads(response.text)
            document = res['document']
            playlist.id = document['_id']
            playlist.name= document['name']
        except:
            return
    
    return playlist

    #Insert Playlist
def create_playlist(playlist_name):
    new_playlist =  Playlist(playlist_name)
    json_playlist = new_playlist.to_json()
    url = f"{base_api_url}/action/insertOne"
    headers = {
        'Content-Type': 'application/json',
        'api-key': playlist_api_key, 
    }
    payload = json.dumps({
        "collection": playlist_collection,
        "database": database,
        "dataSource": data_source,
        "document": json_playlist
    })
    response = requests.request("POST", url, headers=headers, data=payload )
    try:
        doc = json.loads(response.text)
        insertedId = doc['insertedId']
        return f"**Added new playlist:**\n>>> {new_playlist.name}"
    except:
        return None


# Get all songs
def get_all_songs():
    songs = []
    url = f"{base_api_url}/action/find"
    headers = {
        'Content-Type': 'application/json',
        'api-key': song_api_key, 
    }
    payload = json.dumps({
        "collection": song_collection,
        "database": database,
        "dataSource": data_source
    })

    response = requests.request("POST", url, headers=headers, data=payload )
    if(response.status_code == 200):
        res = json.loads(response.text)
        documents = res['documents']
        for i in documents:
            song = PlaylistItem(i['playlist_id'], i['title'], i['url'], i['thumb'])
            song.id = i['_id']
            song.date_added = i['date_added']
            song.date_updated = i['date_updated']
            songs.append(song)

    return songs

#Get single song
def get_song_by_name(name):
    url = f"{base_api_url}/action/findOne"
    headers = {
        'Content-Type': 'application/json',
        'api-key': song_api_key, 
    }
    payload = json.dumps({
        "collection": song_collection,
        "database": database,
        "dataSource": data_source,
        "filter": {
            "title":name
        }
    })

    response = requests.request("POST", url, headers=headers, data=payload )
    if(response.status_code == 200):
        try:
            res = json.loads(response.text)
            document = res['document']
            song = PlaylistItem(document['playlist_id'],document['title'],document['url'],document['thumb'],)
            song.id= document['_id']
            return song
        except:
            return None
    
#Insert Song Into Playlist
def create_song(song):
    new_song = PlaylistItem(song.playlist_id, song.title, song.url, song.thumb)
    new_song.date_added = datetime.now()
    new_song.date_updated = datetime.now()
    
    existing_song = get_song_by_name(new_song.title)
    if existing_song is not None:
        return f"**{new_song.title} is already in the playlist**"
    else:
        url = f"{base_api_url}/action/insertOne"
        headers = {
            'Content-Type': 'application/json',
            'api-key': playlist_api_key, 
        }
        payload = json.dumps({
            "collection": song_collection,
            "database": database,
            "dataSource": data_source,
            "document": new_song.to_json()
        })
        response = requests.request("POST", url, headers=headers, data=payload )
        try:
            doc = json.loads(response.text)
            insertedId = doc['insertedId']
            print(insertedId)
            return f"**Added to playlist:**\n>>> {new_song.title}"
        except:
            return f"**There was an error adding {new_song.title} to the playlist**"

#Delete Song
def delete_song(song):
    url = f"{base_api_url}/action/deleteOne"
    headers = {
        'Content-Type': 'application/json',
        'api-key': song_api_key, 
    }
    payload = json.dumps({
        "collection": song_collection,
        "database": database,
        "dataSource": data_source,
        "filter": { "_id": { "$oid": song.id } }
    })
    response = requests.request("POST", url, headers=headers, data=payload )
    try:
        doc = json.loads(response.text)
        deletedCount = doc['deletedCount']
        print(deletedCount)
        return f"**{song.title} has been removed from the playlist**"
    except:
        return f"**There was an error deleting {song.title} from the playlist**"
