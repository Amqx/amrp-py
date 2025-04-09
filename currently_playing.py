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
    """
    Represents currently playing song and its metadata
    """
    def __init__(self):
        self.title = None
        self.artist = None
        self.album = None
        self.image = None
        self.ts = None
        self.playing = False
        self.paused = None

    def __str__(self) -> str:
        return f"Title: {self.title} \nArtist: {self.artist} \nAlbum: {self.album} \nImage: {self.image} \nTimestamps: {self.ts} \nPlaying: {self.playing} \nPause timer: {self.paused}"

    def listview(self) -> list:
        """
        Quick access to non-static information
        :return: List containing title, artist, album, and bool of playing status
        """
        return [self.title, self.artist, self.album, self.playing]

    def pause(self) -> None:
        """
        Pauses the song and begins the pause timer if not active
        :return: None
        """
        if self.paused is None:
            self.paused = int(time.time())

    def play(self) -> None:
        """
        Resets the pause timer back to None
        :return: None
        """
        self.paused = None

    async def get_info(self, difference: bool) -> None:
        """

        :param difference: Force update the song's thumbnail
        :return: None
        """

        current_time = int(time.time())
        sessions = await MediaManager.request_async()

        # Early return if no media session available
        if not sessions or not sessions.get_current_session():
            self.reset()
            return

        current_session = sessions.get_current_session()
        info = current_session.get_playback_info()

        # Early return if no playback info
        if not info:
            self.reset()
            return

        # Get playback status
        self.playing = (info.playback_status == PlaybackStatus.PLAYING)

        # Get timeline information
        timeline = current_session.get_timeline_properties()
        if timeline:
            position = int(timeline.position.total_seconds())
            end_time = int(timeline.end_time.total_seconds())
            self.ts = [current_time - position, current_time + (end_time - position)]
        else:
            self.ts = []

        # Get media properties
        media = await current_session.try_get_media_properties_async()
        if not media:
            self.reset()
            return

        # Update thumbnail if needed
        if self.image is None or difference:
            self.image = media.thumbnail

        # Parse artist and album
        artist_album = media.artist or None
        if artist_album:
            artist_album = artist_album.strip()

            # Remove station if present
            artist_album = re.sub(r" — [^—]*?['’]s Station$", "", artist_album)

            # If EM-dash is available to seperate albums, split it
            if "—" in artist_album:
                artist, album = artist_album.split("—")
                self.artist = artist.strip()
                self.album = album.strip()

            # If EM-dash not available define artist and album both as album
            else:
                self.artist = artist_album.strip()
                self.album = artist_album.strip()

        # Set title
        if media.title:
            self.title = media.title.strip()

    def convert_thumbnail(self) -> None:
        """
        Converts the current song's self.image to a link if its a IRandomAccessStreamReference object. Otherwise sets it to default.
        :return: None
        """
        async def process_thumbnail() -> io.BytesIO:
            """
            Transforms IRandomAccessStreamReference into
            :return: io.BytesIO object containing thumbnail info
            """
            stream = await self.image.open_read_async()
            reader = DataReader(stream)
            size = stream.size
            await reader.load_async(size)
            buffer = reader.read_buffer(size)
            return io.BytesIO(bytes(memoryview(buffer)))

        def upload(image: io.BytesIO) -> str:
            """
            Uploads the image to Imgur and returns the link. On any error, returns 'default' instead.
            :param image: io.BytesIO object containing thumbnail info
            :return: Either imgur link or 'default'
            """
            image.seek(0)
            headers = {'Authorization': f'Client-ID {IMGUR_CLIENT_ID}'}
            response = requests.post(
                "https://api.imgur.com/3/image",
                headers=headers,
                files={'image': image}
            )
            if response.status_code == 200:
                return response.json().get('data').get('link')
            else:
                return str('default')

        if isinstance(self.image, IRandomAccessStreamReference):
            self.image = upload(asyncio.run(process_thumbnail()))
        else:
            self.image = 'default'


    def reset(self) -> None:
        """
        Resets all of the song's attributes
        :return: None
        """
        self.title = None
        self.artist = None
        self.album = None
        self.image = None
        self.ts = None
        self.playing = False
        self.paused = None
