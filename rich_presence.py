from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus
from pypresence import Presence
import asyncio
import os

CLIENT_ID = os.getenv("CLIENT_ID")
POLL_INTERVAL = 5 # seconds

async def current_track():
    """
    Retrieves the current track information.

    Returns:
        tuple: A tuple containing the title, artist, and album of the current track.
               Returns (None, None, None) if no track is playing or if information is unavailable.
    """
    sessions = await MediaManager.request_async()
    if sessions is None:
        return None, None, None

    current_session = sessions.get_current_session()
    if current_session:
        info = current_session.get_playback_info()
        if info is None:
             return None, None, None

        if info.playback_status == PlaybackStatus.PLAYING:
            media_properties = await current_session.try_get_media_properties_async()
            if media_properties:
                artist_album = media_properties.artist or "Unknown Artist"
                title = media_properties.title or "Unknown Title"

                artist_album = artist_album if artist_album.strip() else "Unknown Artist"
                title = title if title.strip() else "Unknown Title"

                artist, album = artist_album.split("—")

                return title.strip(), artist.strip(), album.strip()
            else:
                return None, None, None

async def monitor_changes(current_state: list):
    last_title = None
    last_artist = None
    last_album = None

    while True:
        current_title, current_artist, current_album = await current_track()
        currently_playing = bool(current_artist or current_title or current_album)

        state_changed = False
        if currently_playing != current_state[0]:
            state_changed = True
        elif currently_playing and (current_artist != last_artist or current_title != last_title or current_album != last_album):
            state_changed = True

        if state_changed:
            # Update last known state
            last_artist = current_artist
            last_title = current_title
            current_state[0] = currently_playing

        # Wait before checking again
        await asyncio.sleep(POLL_INTERVAL)

async def presence_loop(mediainfo: list):
    rpc = Presence(CLIENT_ID)
    rpc.connect()

    while True:
        latest = mediainfo[0]
        rpc.update(
            details=latest[0],
            state=latest[1],
            large_image="music",
            large_text=latest[2]
        )
        await asyncio.sleep(POLL_INTERVAL)

async def main():
    initial = current_track()
    if initial[0] or initial[1] or initial[2]:
        current_state = [True]
    else:
        current_state = [False]
    try:
        last_known = current_state[0]
        mediainfo = [current_track()]
        asyncio.run(monitor_changes(current_state))
        asyncio.run(presence_loop(mediainfo))
        while True:
            if last_known != current_state[0]:
                mediainfo = [current_track()]
            await asyncio.sleep(POLL_INTERVAL)


    except KeyboardInterrupt:
        monitor_task.cancel()
