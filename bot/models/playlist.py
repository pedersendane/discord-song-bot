# FastAPI's jsonable_encoder handles converting various non-JSON types,
# such as datetime between JSON types and native Python types.
import json
from optparse import Option
from fastapi.encoders import jsonable_encoder

# Pydantic, and Python's built-in typing are used to define a schema
# that defines the structure and types of the different objects stored
# in the recipes collection, and managed by this API.
from pydantic import BaseModel, Field
from typing import List, Optional, Union
from datetime import datetime

from .objectid import PydanticObjectId


class PlaylistItem():
    id: Optional[PydanticObjectId] = Field(None, alias="_id")
    playlist_id: str
    title: str
    url: str
    thumb: str
    date_added: Optional[datetime]
    date_updated: Optional[datetime]

    def __init__(self, playlist_id, title, url, thumb):
        self.playlist_id = playlist_id
        self.title = title
        self.url = url
        self.thumb = thumb

    def to_json(self):
        return jsonable_encoder(self, exclude_none=True)  

    


    
class PlaylistItemEncoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__



class Playlist():
    id: Optional[PydanticObjectId] = Field(None, alias="_id")
    name: str
    songs: Optional[List[PlaylistItem]]

    def __init__(self, name):
        self.name = name

    def to_json(self):
        return jsonable_encoder(self, exclude_none=True)

    def to_bson(self):
        data = self.dict(by_alias=True, exclude_none=True)
        if data.get("_id") is None:
            data.pop("_id", None)
        return data