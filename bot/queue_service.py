from contextlib import nullcontext
from datetime import date, datetime
import os
import json
from unicodedata import name
import requests
from models.playlist import PlaylistItem, Playlist
from models.queue_item import QueueItem, QueueItemEncoder
from dotenv import load_dotenv

load_dotenv()
token = os.environ['DISCORD_TOKEN']
base_api_url = os.environ['API_BASE_URL']
database = os.environ['DISCORD_DATABASE']
data_source = os.environ['DISCORD_DATA_SOURCE']

song_api_key = os.environ['PLAYLIST_ITEM_API_KEY']
song_collection = os.environ['SONG_COLLECTION']

playlist_api_key = os.environ['PLAYLIST_API_KEY']
playlist_collection = os.environ['PLAYLIST_COLLECTION']

queue_item_api_key = os.environ['QUEUE_ITEM_API_KEY']
queue_item_collection = os.environ['QUEUE_ITEM_COLLECTION']


# Get all items
async def get_all_queue_items():
    queue = []
    url = f"{base_api_url}/action/find"
    headers = {
        'Content-Type': 'application/json',
        'api-key': queue_item_api_key, 
    }
    payload = json.dumps({
        "collection": queue_item_collection,
        "database": database,
        "dataSource": data_source
    })

    response = requests.request("POST", url, headers=headers, data=payload )
    if(response.status_code == 200):
        res = json.loads(response.text)
        documents = res['documents']
        for i in documents:
            q = QueueItem(i['title'],i['url'],i['thumb'])
            q.id = i['_id']
            q.date_added = i['date_added']
            queue.append(q)

    return queue

#Get single song
async def get_queue_item_by_id(id):
    url = f"{base_api_url}/action/findOne"
    headers = {
        'Content-Type': 'application/json',
        'api-key': queue_item_api_key, 
    }
    payload = json.dumps({
        "collection": queue_item_collection,
        "database": database,
        "dataSource": data_source,
        "filter": {
            "id":id
        }
    })

    response = requests.request("POST", url, headers=headers, data=payload )
    if(response.status_code == 200):
        try:
            res = json.loads(response.text)
            document = res['document']
            queue_item = QueueItem(document['title'],document['url'],document['thumb'])
            queue_item.id = document['_id']
            queue_item.date_added = document['date_added']
            return queue_item
        except:
            return None

            
#Get single song
async def get_queue_item_by_name(name):
    url = f"{base_api_url}/action/findOne"
    headers = {
        'Content-Type': 'application/json',
        'api-key': queue_item_api_key, 
    }
    payload = json.dumps({
        "collection": queue_item_collection,
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
            queue_item = QueueItem(document['title'],document['url'],document['thumb'])
            queue_item.id = document['_id']
            queue_item.date_added = document['date_added']
            return queue_item
        except:
            return None
    
#Insert Song Into Queue
async def create_queue_item(queue_item):
    queue_item.date_added = datetime.now()
    queue_item.date_updated = datetime.now()
    
    # existing_song = await get_queue_item_by_name(queue_item.title)
    # #if the song exists
    # if existing_song is not None:
    #     return None
    # else:
    url = f"{base_api_url}/action/insertOne"
    headers = {
        'Content-Type': 'application/json',
        'api-key': queue_item_api_key, 
    }
    payload = json.dumps({
        "collection": queue_item_collection,
        "database": database,
        "dataSource": data_source,
        "document": queue_item.to_json()
    })
    response = requests.request("POST", url, headers=headers, data=payload )
    try:
        doc = json.loads(response.text)
        return doc['insertedId']
    except:
        return None

#Delete Song
async def delete_queue_item(queue_item):
    url = f"{base_api_url}/action/deleteOne"
    headers = {
        'Content-Type': 'application/json',
        'api-key': queue_item_api_key, 
    }
    payload = json.dumps({
        "collection": queue_item_collection,
        "database": database,
        "dataSource": data_source,
        "filter": { "_id": { "$oid": queue_item.id } }
    })
    response = requests.request("POST", url, headers=headers, data=payload )
    try:
        doc = json.loads(response.text)
        deletedCount = doc['deletedCount']
        return deletedCount
    except:
        return None
