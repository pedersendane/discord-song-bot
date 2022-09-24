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
from models.queue_item import QueueItem
import playlist_service, insult_service, queue_service

from .objectid import PydanticObjectId

class Queue:
    """
    A class used to represent a queue.

    This class handles all sort of Queue operations, making it easy to just
    call these methods in main.py without worrying about breaking anything in queue.

    Attributes
    ----------
    current_music_url : str
        The current url of the current music the bot is playing.

    current_music_title : str
        The current name of the current music the bot is playing.

    current_music_thumb : str
        The current thumbnail url of the current music the bot is playing.

    last_title_enqueued : str
        The title of the last music enqueued.

    queue : tuple list
        The actual queue of songs to play.
        (title, url, thumb)

    Methods
    -------
    enqueue(music_title, music_url, music_thumb)
        Handles enqueue process appending the music tuple to the queue
        while setting last_title_enqueued and the current_music variables as needed

    dequeue()
        TO DO!
        Removes the last music enqueued from the queue.

    previous()
        Goes back one place in queue, ensuring that the previous song isn't a negative index.
        current_music variables are set accordingly.

    next()
        Sets the next music in the queue as the current one.

    theres_next()
        Checks if there is a music in the queue after the current one.

    clear_queue()
        Clears the queue, resetting all variables.

    """
    def __init__(self):
        # self.music = namedtuple('music', ('title', 'url', 'thumb'))
        # self.current_music = self.music('', '', '')

        # self.last_title_enqueued = ''
        self.queue = []
        self.current_queue_item = QueueItem('','','')

    def set_current_queue_item(self):
        """
        Sets last music as current.

        :return: None
        """
        index = len(self.queue) - 1
        if index >= 0:
            self.current_queue_item = self.queue[index]

    async def enqueue(self, queue_item):
        """
        Handles enqueue process appending the music tuple to the queue
        while setting last_title_enqueued and the current_music variables as needed

        :param music_title: str
            The music title to be added to queue
        :param music_url: str
            The music url to be added to queue
        :param music_thumb: str
            The music thumbnail url to be added to queue
        :return: None
        """
        inserted_id = await queue_service.create_queue_item(queue_item)
        if inserted_id is not None:
            queue_item.id = inserted_id
            await self.get_queue()
            if len(self.queue) == 0:
                self.current_queue_item = queue_item
            return queue_item
        else:
            return None
        
    async def dequeue_last_song(self):
        deleted_count = None
        if self.queue:
            deleted_count = await queue_service.delete_queue_item(self.current_queue_item)
        return deleted_count
        

    def previous(self):
        """
        Goes back one place in queue, ensuring that the previous song isn't a negative index.
        current_music variables are set accordingly.

        :return: None
        """
        index = self.queue.index(self.current_music) - 1
        if index > 0:
            self.current_music = self.queue[index]

    async def get_queue(self):
        self.queue = await queue_service.get_all_queue_items()

    # def next(self):
    #     """
    #     Sets the next music in the queue as the current one.

    #     :return: None
    #     """
    #     if self.queue:


    #     else:
    #         self.clear_queue()

    def theres_next(self):
        """
        Checks if there is a music in the queue after the current one.

        :return: bool
            True if there is a next song in queue.
            False if there isn't a next song in queue.
        """
        if self.queue.index(self.current_music) + 1 > len(self.queue) - 1:
            return False
        else:
            return True

    async def clear_queue(self):
        """
        Clears the queue, resetting all variables.

        :return: None
        """
        await self.get_queue()
        if self.queue:
            for i in self.queue:
                await queue_service.delete_queue_item(i)
            self.queue.clear()
            self.current_queue_item = QueueItem('','','')

class Session:
    """
    A class used to represent an instance of the bot.

    To avoid mixed queues when there's more than just one guild sending commands to the bot, I came up with the concept
    of sessions. Each session is identified by its guild and voice channel where the bot is connected playing audio, so
    it's impossible to send a music from one guild to another by mistake. :)

    Attributes
    ----------
    id : int
        Session's number ID.

    guild : str
        Guild's name where the bot is connected.

    channel : str
        Voice channel where the bot is connected.
    """
    def __init__(self, guild, channel, id=0):
        """
        :param guild: str
             Guild's name where the bot is connected.
        :param channel: str
            Voice channel where the bot is connected.
        :param id: int
            Session's number ID.
        """
        self.id = id
        self.guild = guild
        self.channel = channel
        self.q = Queue()
