from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
from winsdk.windows.storage.streams import DataReader, IRandomAccessStreamReference
import asyncio
import io
import re
import os
import time
from dotenv import load_dotenv
import requests

load_dotenv()
IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID")

class Song:
    def __init__(self):
        self.title = None
        self.artist = None
        self.album = None
        self.image = None
        self.ts = None
        self.playing = False

    def __str__(self):
        return f"Title: {self.title} \nArtist: {self.artist} \nAlbum: {self.album} \nImage: {self.image} \nTimestamps: {self.ts} \nPlaying: {self.playing} \n"

    async def get_info(self, difference):
        current_time = int(time.time())
        sessions = await MediaManager.request_async()   # Setup session
        if sessions is None:   # If no sessions available, return nothing
            self.title = None
            self.artist = None
            self.album = None
            self.image = None
            self.ts = []
            self.playing = False
            return

        current_session = sessions.get_current_session()   # get current session
        if current_session is None:
            self.title = None
            self.artist = None
            self.album = None
            self.image = None
            self.ts = []
            self.playing = False
            return

        info = current_session.get_playback_info()
        if info is None:
            self.title = None
            self.artist = None
            self.album = None
            self.image = None
            self.ts = []
            self.playing = False
            return

        # Get playback info
        if info.playback_status == PlaybackStatus.PLAYING:
            self.playing = True
        else:
            self.playing = False

        # Get timeline information
        timeline_properties = current_session.get_timeline_properties()
        if timeline_properties:
            position = int(timeline_properties.position.total_seconds())
            end_time = int(timeline_properties.end_time.total_seconds())
            self.ts = [current_time - position, current_time + (end_time - position)]
        else:
            self.ts = []



        # Get media properties
        media_properties = await current_session.try_get_media_properties_async()
        if media_properties:   # always set available media properties
            artist_album = media_properties.artist or None
            title = media_properties.title or None
            if self.image is None or difference:
                self.image = media_properties.thumbnail

            artist_album = artist_album or None
            title = title or None

            if artist_album:
                artist_album = artist_album.strip()
                artist_album = re.sub(r" — [^—]*?['’]s Station$", "", artist_album)
                artist, album = artist_album.split("—")
            else:
                artist, album = None, None
            print(artist_album)

            if title:
                self.title = title.strip()
            if artist:
                self.artist = artist.strip()
            if album:
                self.album = album.strip()

        else:
            self.title = None
            self.artist = None
            self.album = None
            self.image = None

    def convert_thumbnail(self):
        async def process_thumbnail():
            stream = await self.image.open_read_async()
            reader = DataReader(stream)
            size = stream.size
            await reader.load_async(size)
            buffer = reader.read_buffer(size)
            image_bytes = bytes(memoryview(buffer))
            return io.BytesIO(image_bytes)

        def upload(image):
            image.seek(0)
            files = {'image': image}
            headers = {'Authorization': 'Client-ID' + f" {IMGUR_CLIENT_ID}"}
            url = "https://api.imgur.com/3/image"
            response = requests.post(url, headers=headers, files=files)
            if response.status_code == 200:
                return response.json().get('data').get('link')
            else:
                print("Upload failed:", response.status_code)
        if isinstance(self.image, IRandomAccessStreamReference):
            self.image = upload(asyncio.run(process_thumbnail()))
        else:
            if self.image is None:
                self.image = "default"

    def reset(self):
        self.title = None
        self.artist = None
        self.album = None
        self.image = None
        self.ts = None
        self.playing = False
