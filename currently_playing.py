from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
from winsdk.windows.storage.streams import DataReader, IRandomAccessStreamReference
import asyncio
import io
import re
import os
import time
import logging
from dotenv import load_dotenv
import requests
from typing import List, Optional, Union


load_dotenv()
IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID")

class Song:
    """
    Represents currently playing song and its metadata.

    This class handles fetching, storing, and managing information about the
    currently playing song in Apple Music, including its metadata and playback status.
    """
    def __init__(self) -> None:
        """
        Initialize a new Song object with default values.

        All attributes are initialized to None or default values and will be
        populated when get_info() is called.
        """
        logging.info("Initializing new Song object")
        self.title: Optional[str] = None
        self.artist: Optional[str] = None
        self.album: Optional[str] = None
        self.image: Optional[Union[IRandomAccessStreamReference, str]] = None
        self.ts: Optional[List[int]] = None
        self.playing: bool = False
        self.paused: Optional[int] = None

    def __str__(self) -> str:
        """
        Return a string representation of the Song object.

        Returns:
            A formatted string with all song attributes.
        """
        return f"Title: {self.title} \nArtist: {self.artist} \nAlbum: {self.album} \nImage: {self.image} \nTimestamps: {self.ts} \nPlaying: {self.playing} \nPause timer: {self.paused}"

    def listview(self) -> List[Optional[Union[str, bool]]]:
        """
        Get quick access to non-static song information.

        Returns:
            List containing title, artist, album, and playing status.
        """
        return [self.title, self.artist, self.album, self.playing]

    def pause(self) -> None:
        """
        Pause the song and begin the pause timer if not already active.

        Sets the paused timestamp to the current time if it's not already set.
        """
        if self.paused is None:
            logging.info("Song paused, starting pause timer")
            self.paused = int(time.time())

    def play(self) -> None:
        """
        Mark the song as playing by resetting the pause timer.

        Sets the paused timestamp back to None.
        """
        if self.paused is not None:
            logging.info("Song resumed, resetting pause timer")
            self.paused = None

    async def get_info(self, difference: bool) -> None:
        """
        Fetch and update song information from the media session.

        Gets the current song information from the Windows Media API and updates
        the Song object's attributes accordingly.

        Args:
            difference: If True, forces an update of the song's thumbnail

        Returns:
            None
        """
        logging.info("Fetching current song information")
        current_time = int(time.time())
        sessions = await MediaManager.request_async()

        # Early return if no media session available
        if not sessions or not sessions.get_current_session():
            logging.info("No media session available, resetting song info")
            self.reset()
            return

        current_session = sessions.get_current_session()
        info = current_session.get_playback_info()

        # Early return if no playback info
        if not info:
            logging.info("No playback info available, resetting song info")
            self.reset()
            return

        # Get playback status
        previous_state = self.playing
        self.playing = (info.playback_status == PlaybackStatus.PLAYING)
        if previous_state != self.playing:
            logging.info(f"Playback status changed: {'Playing' if self.playing else 'Paused'}")

        # Get timeline information
        timeline = current_session.get_timeline_properties()
        if timeline:
            position = int(timeline.position.total_seconds())
            end_time = int(timeline.end_time.total_seconds())
            self.ts = [current_time - position, current_time + (end_time - position)]
            logging.debug(f"Timeline updated: position={position}s, end_time={end_time}s")
        else:
            self.ts = []
            logging.debug("No timeline information available")

        # Get media properties
        media = await current_session.try_get_media_properties_async()
        if not media:
            logging.info("No media properties available, resetting song info")
            self.reset()
            return

        # Update thumbnail if needed
        if self.image is None or difference:
            logging.info("Updating song thumbnail")
            self.image = media.thumbnail

        # Parse artist and album
        artist_album = media.artist or None
        if artist_album:
            artist_album = artist_album.strip()

            # Remove station if present
            artist_album = re.sub(r" — [^—]*?['’]s Station$", "", artist_album)

            # If EM-dash is available to separate albums, split it
            if "—" in artist_album:
                artist, album = artist_album.split("—")
                self.artist = artist.strip()
                self.album = album.strip()
                logging.debug(f"Parsed artist: '{self.artist}' and album: '{self.album}'")
            # If EM-dash not available define artist and album both as album
            else:
                self.artist = artist_album.strip()
                self.album = artist_album.strip()
                logging.debug(f"Using artist_album as both artist and album: '{artist_album}'")

        # Set title
        if media.title:
            previous_title = self.title
            self.title = media.title.strip()
            if previous_title != self.title:
                logging.info(f"Song title updated: '{self.title}'")
        else:
            logging.debug("No title available in media properties")

    async def convert_thumbnail(self) -> None:
        """
        Convert the song's thumbnail to a usable image URL.

        If the image is an IRandomAccessStreamReference object, converts it to a BytesIO
        object and uploads it to Imgur. Otherwise, sets it to 'default'.

        Returns:
            None
        """
        logging.info("Converting song thumbnail")

        async def process_thumbnail() -> io.BytesIO:
            """
            Transform IRandomAccessStreamReference into a BytesIO object.

            Returns:
                An io.BytesIO object containing the thumbnail data.
            """
            logging.debug("Processing thumbnail from IRandomAccessStreamReference")
            stream = await self.image.open_read_async()
            reader = DataReader(stream)
            size = stream.size
            await reader.load_async(size)
            buffer = reader.read_buffer(size)
            return io.BytesIO(bytes(memoryview(buffer)))

        def upload(image: io.BytesIO) -> str:
            """
            Upload the image to Imgur and return the link.

            Args:
                image: BytesIO object containing the thumbnail data

            Returns:
                Either an Imgur link or 'default' if upload fails
            """
            logging.info("Uploading thumbnail to Imgur")
            image.seek(0)
            headers = {'Authorization': f'Client-ID {IMGUR_CLIENT_ID}'}
            try:
                response = requests.post(
                    "https://api.imgur.com/3/image",
                    headers=headers,
                    files={'image': image}
                )
                if response.status_code == 200:
                    link = response.json().get('data').get('link')
                    logging.info(f"Thumbnail uploaded successfully: {link}")
                    return link
                else:
                    logging.warning(f"Failed to upload thumbnail: HTTP {response.status_code}")
                    return 'default'
            except Exception as e:
                logging.error(f"Error uploading thumbnail: {e}")
                return 'default'

        if isinstance(self.image, IRandomAccessStreamReference):
            thumbnail_data = await process_thumbnail()
            self.image = upload(thumbnail_data)
        else:
            logging.info("No valid thumbnail found, using default")
            self.image = 'default'


    def reset(self) -> None:
        """
        Reset all the song's attributes to their default values.

        This is typically called when no song is playing or when the media session
        is no longer available.

        Returns:
            None
        """
        logging.info("Resetting song information")
        self.title = None
        self.artist = None
        self.album = None
        self.image = None
        self.ts = None
        self.playing = False
        self.paused = None
