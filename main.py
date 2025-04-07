from discord_rp import RPC
from currently_playing import Song
import asyncio
import time
import os
from dotenv import load_dotenv
import psutil

REFRESH_INTERVAL = 5
load_dotenv()

def is_process_running(process_name):
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == process_name:
            return True
    return False

difference = False
current = Song()
active = is_process_running('AppleMusic.exe')
if active:
    asyncio.run(current.get_info(difference))
    current.convert_thumbnail()
known = [current.title, current.artist, current.album, current.playing]
indices = [0, 1, 2, 5]

if __name__ == '__main__':
    while True:
        if is_process_running('AppleMusic.exe'):
            asyncio.run(current.get_info(difference))
        print(current)
        new = [current.title, current.artist, current.album, current.playing]
        difference = known == new
        if not difference or not is_process_running('AppleMusic.exe'):
            if None in new or not is_process_running('AppleMusic.exe'):    # playing to exited client or none in info
                active = False   # client not active
                try:
                    discord.rpc.disconnect()   # kill discord
                    print("Killed RPC!")
                    current.reset()
                except NameError:
                    print("RPC not active! Skipped killing RPC")
                except SystemExit:
                    print("RPC tried to kill the script! Continuing loop")
                    del discord
            elif known[0] == new[0] and known[1] == new[1] and known[2] == new[2]:   # paused -> playing or reverse
                active = True
                try:
                    discord.update_activity(current)
                except NameError:
                    discord = RPC()
                    discord.update_activity(current)
            else:
                active = True
                asyncio.run(current.get_info(True))
                current.convert_thumbnail()
                try:
                    discord.update_activity(current)
                except NameError:
                    discord = RPC()
                    discord.update_activity(current)
        else:
            if active:
                if None in new or not is_process_running('AppleMusic.exe'):  # playing to exited client or none in info
                    active = False  # client not active
                    try:
                        discord.rpc.disconnect()  # kill discord
                        print("Killed RPC!")
                        current.reset()
                        del discord
                    except NameError:
                        print("RPC not active! Skipped killing RPC")
                else:
                    try:
                        discord.update_activity(current)
                    except NameError:
                        discord = RPC()
                        discord.update_activity(current)
        known = new
        difference = False
        time.sleep(REFRESH_INTERVAL)