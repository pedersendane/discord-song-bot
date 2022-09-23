from contextlib import nullcontext
from datetime import date, datetime
import os
import json
from unicodedata import name
import requests
from models.playlist import PlaylistItemEncoder
from models.playlist import Playlist, PlaylistItem
from models.queue import Queue,QueueItem, QueueItemEncoder
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
def get_all_queue_items():
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
def get_queue_item_by_id(id):
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
def get_queue_item_by_name(name):
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
def create_queue_item(queue_item):
    new_queue_item = QueueItem(queue_item.title, queue_item.url, queue_item.thumb)
    new_queue_item.date_added = datetime.now()
    new_queue_item.date_updated = datetime.now()
    
    existing_song = get_queue_item_by_name(new_queue_item.title)
    if existing_song is not None:
        return f"**{new_queue_item.title} is already in the playlist**"
    else:
        url = f"{base_api_url}/action/insertOne"
        headers = {
            'Content-Type': 'application/json',
            'api-key': queue_item_api_key, 
        }
        payload = json.dumps({
            "collection": queue_item_collection,
            "database": database,
            "dataSource": data_source,
            "document": new_queue_item.to_json()
        })
        response = requests.request("POST", url, headers=headers, data=payload )
        try:
            doc = json.loads(response.text)
            insertedId = doc['insertedId']
            print(insertedId)
            return f"**Added to queue:**\n>>> {new_queue_item.title}"
        except:
            return f"**There was an error adding {new_queue_item.title} to the queue**"

#Delete Song
def delete_queue_item(queue_item):
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
        print(deletedCount)
        return f"**{queue_item.title} has been removed from the queue**"
    except:
        return f"**There was an error deleting {queue_item.title} from the playlist**"
