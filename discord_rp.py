import os
import logging
import discordrpc
from dotenv import load_dotenv
from currently_playing import Song

load_dotenv()
DISCORD_CLIENT_ID = int(os.getenv("DISCORD_CLIENT_ID"))

class RPC:
    """
    Class to manage Discord Rich Presence calls.

    This class handles the connection to Discord and updates the rich presence
    status based on the currently playing song.
    """

    def __init__(self) -> None:
        """
        Initialize the Discord RPC connection.

        Creates a new RPC connection using the Discord client ID from environment variables.
        """
        logging.info("Initializing Discord RPC connection")
        self.rpc = discordrpc.RPC(DISCORD_CLIENT_ID)

    def update_activity(self, info: Song) -> None:
        """
        Updates Discord Rich Presence activity using a Song object.

        Args:
            info: Song object containing the current song information

        Returns:
            None
        """
        if info.playing:
            logging.info(f"Updating Discord activity: Playing '{info.title}' by {info.artist}")
            self.rpc.set_activity(
                details=info.title,
                state=info.artist,
                large_text=info.album,
                large_image=info.image,
                act_type=2,
                ts_start=info.ts[0],
                ts_end=info.ts[1],
            )
        else:
            logging.info(f"Updating Discord activity: Paused '{info.title}' by {info.artist}")
            self.rpc.set_activity(
                details=info.title,
                state=info.artist,
                large_text=info.album,
                large_image=info.image,
                small_image="pause",
                small_text="Paused",
                act_type=2,
                ts_start=info.paused,
            )
