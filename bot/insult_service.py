from contextlib import nullcontext
from datetime import date, datetime
import os
import json
from unicodedata import name
from wsgiref import headers
import requests
from models.playlist import PlaylistItemEncoder
from models.playlist import Playlist, PlaylistItem
from dotenv import load_dotenv


load_dotenv()
base_insult_url = os.environ['INSULTS_BASE_URL']
insult_types = [
    "/insult.json?who=",
    "/en/insult.json?who=", 
    "/en_corporate/insult.json?who="
    ]

def get_insult_for_name(name, insult_type):
    try:
        index = int(insult_type) - 1
        if(index) > 2:
            index = 0
    except ValueError as e:
        index = 0


    url = f"{base_insult_url}{insult_types[index]}{name}"
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("GET", url, headers=headers)
    if(response.status_code == 200):
        res = json.loads(response.text)
        insult = res['insult']
        return insult

