import os
import discordrpc
import time
from dotenv import load_dotenv

load_dotenv()
DISCORD_CLIENT_ID = int(os.getenv("DISCORD_CLIENT_ID"))
class RPC:
    def __init__(self):
        self.rpc = discordrpc.RPC(DISCORD_CLIENT_ID)

    def update_activity(self, info):
        if info.playing:
            self.rpc.set_activity(
                details=info.title,
                state=info.artist,
                large_text=info.album,
                large_image=info.image,
                act_type=2,
                ts_start=info.ts[0],
                ts_end=info.ts[1],
            )
        elif not info.playing:
            self.rpc.set_activity(
                details=info.title,
                state=info.artist,
                large_text=info.album,
                large_image=info.image,
                small_image="pause",
                small_text="Paused",
                act_type=2,
                ts_start=int(time.time())
            )



