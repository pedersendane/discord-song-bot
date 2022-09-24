from collections import namedtuple
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
class QueueItem:
    id: Optional[PydanticObjectId] = Field(None, alias="_id")
    title: str
    url: str
    thumb: str
    date_added: Optional[datetime]
    date_updated: Optional[datetime]

    def __init__(self, title, url, thumb):
        self.title = title
        self.url = url
        self.thumb = thumb
    

    def to_json(self):
        return jsonable_encoder(self, exclude_none=True)  

class QueueItemEncoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__